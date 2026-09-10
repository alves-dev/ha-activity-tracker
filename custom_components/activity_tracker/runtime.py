"""Runtime for unified activity rules."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    TrackTemplate,
    async_track_point_in_time,
    async_track_state_change_event,
    async_track_state_report_event,
    async_track_template_result,
    async_track_time_interval,
)
from homeassistant.helpers.template import Template, result_as_boolean
from homeassistant.util import dt as dt_util

from .accounting import commit_session
from .const import (
    CONF_RULE,
    CROSS_MIDNIGHT_POLICIES,
    DEFAULT_CROSS_MIDNIGHT_POLICY,
    DEFAULT_MINIMUM_SESSION_SECONDS,
    DEFAULT_RETENTION_DAYS,
    OPT_CROSS_MIDNIGHT_POLICY,
    OPT_MINIMUM_SESSION_SECONDS,
    OPT_RETENTION_DAYS,
    PERIOD_PREVIOUS_DAY_PREFIX,
    update_signal,
)
from .models import DailySummary, Session
from .rules import referenced_entity_ids, template_values
from .session_engine import UnifiedSessionEngine
from .storage import ActivityTrackerStorage


class ActivityTrackerRuntime:
    """Observe all referenced entities and retain completed sessions."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass, self.entry = hass, entry
        self._storage = ActivityTrackerStorage(hass, entry.entry_id)
        self._data: dict[str, Any] = {"daily_summaries": {}}
        self._states: dict[str, State] = {}
        self._template_results: dict[str, bool] = {}
        self._session: Session | None = None
        self._engine = UnifiedSessionEngine(self._rule)
        self._unsubscribers: list[callback] = []
        self._deadline_unsubscribe: callback | None = None
        self._mutation_lock = asyncio.Lock()
        self._last_completed: dict[str, Any] | None = None
        self._storage_error: str | None = None
        self._last_cleanup_date = None

    @property
    def signal(self) -> str:
        return update_signal(self.entry.entry_id)

    @property
    def session(self) -> Session | None:
        return self._session

    @property
    def last_completed(self) -> dict[str, Any] | None:
        return self._last_completed

    @property
    def storage_error(self) -> str | None:
        return self._storage_error

    @property
    def daily_summaries(self) -> dict[str, DailySummary]:
        return {
            date: DailySummary.from_dict(value)
            for date, value in self._data.setdefault("daily_summaries", {}).items()
        }

    @property
    def _rule(self) -> dict[str, Any]:
        value = self.entry.data.get(CONF_RULE)
        return dict(value) if isinstance(value, dict) else {}

    async def async_setup(self) -> None:
        try:
            self._data = await self._storage.async_load()
        except ValueError:
            self._storage_error = "storage_schema_incompatible"
            return
        self._last_completed = self._data.get("last_completed_session")
        self._session = self._session_from_checkpoint(self._data.get("checkpoint"))
        entity_ids = referenced_entity_ids(self._rule.get("start_when", {}))
        entity_ids |= referenced_entity_ids(self._rule.get("stop_when", {}))
        for entity_id in entity_ids:
            if (state := self.hass.states.get(entity_id)) is not None:
                self._states[entity_id] = state
        if entity_ids:
            self._unsubscribers.extend(
                (
                    async_track_state_change_event(
                        self.hass, entity_ids, self._async_event
                    ),
                    async_track_state_report_event(
                        self.hass, entity_ids, self._async_event
                    ),
                )
            )
        self._async_track_templates()
        self._unsubscribers.append(
            async_track_time_interval(
                self.hass, self._async_minute_tick, timedelta(minutes=1)
            )
        )
        now = dt_util.now()
        if self._session is not None:
            # Preserve an in-flight session across config-entry reloads. The
            # next state/template event (or an existing deadline) evaluates the
            # current rule; reloading must not retroactively end the session.
            self._engine.started_at = self._session.started_at
            self._schedule_deadline(now)
            self._notify()
        else:
            await self._async_evaluate(now)

    async def async_unload(self) -> None:
        async with self._mutation_lock:
            await self._async_save()
        self._cancel_deadline()
        for unsubscribe in self._unsubscribers:
            unsubscribe()
        self._unsubscribers.clear()

    async def async_delete_storage(self) -> None:
        await self._storage.async_remove()

    @classmethod
    async def async_delete_entry_storage(
        cls, hass: HomeAssistant, entry_id: str
    ) -> None:
        await ActivityTrackerStorage(hass, entry_id).async_remove()

    async def async_clear_history(self) -> None:
        async with self._mutation_lock:
            self._data["daily_summaries"] = {}
            self._last_completed = None
            self._data.pop("last_completed_session", None)
            await self._async_save()
            self._notify()

    async def async_process_state(self, state: State, now: datetime) -> None:
        async with self._mutation_lock:
            self._states[state.entity_id] = state
            if self._session is not None:
                self._session.last_observed_at = now
            await self._async_evaluate(now)

    async def _async_event(self, event: Event) -> None:
        state = event.data.get("new_state")
        if isinstance(state, State):
            await self.async_process_state(state, dt_util.now())

    def _async_track_templates(self) -> None:
        """Track native templates and let Home Assistant discover dependencies."""
        values = template_values(self._rule.get("start_when", {}))
        values |= template_values(self._rule.get("stop_when", {}))
        if not values:
            return
        tracker = async_track_template_result(
            self.hass,
            [TrackTemplate(Template(value, self.hass), None) for value in values],
            self._async_template_result,
        )
        self._unsubscribers.append(tracker.async_remove)

    @callback
    def _async_template_result(self, _event, updates) -> None:
        """Store changed boolean results and evaluate the same session engine."""
        for update in updates:
            self._template_results[update.template.template] = result_as_boolean(
                update.result
            )
        self.hass.async_create_task(self._async_process_template_results(dt_util.now()))

    async def _async_process_template_results(self, now: datetime) -> None:
        async with self._mutation_lock:
            if self._session is not None:
                self._session.last_observed_at = now
            await self._async_evaluate(now)

    async def _async_deadline(self, now: datetime) -> None:
        async with self._mutation_lock:
            await self._async_evaluate(now)

    async def _async_minute_tick(self, now: datetime) -> None:
        async with self._mutation_lock:
            if self._last_cleanup_date != now.date():
                await self._async_cleanup(now.date())
                self._last_cleanup_date = now.date()
                await self._async_save()
            self._notify()

    async def _async_evaluate(self, now: datetime) -> None:
        if self._storage_error is not None:
            return
        transition = self._engine.process(self._states, now, self._template_results)
        if transition and transition.action == "started":
            self._session = Session(now, now)
            await self._async_save()
        elif transition:
            await self._async_finish(transition.accounting_ended_at or now)
        self._schedule_deadline(now)
        self._notify()

    async def _async_finish(self, ended_at: datetime) -> None:
        session, self._session = self._session, None
        self._engine.started_at = None
        if session is None or ended_at <= session.started_at:
            await self._async_save()
            return
        duration = (ended_at - session.started_at).total_seconds()
        minimum = self.entry.options.get(
            OPT_MINIMUM_SESSION_SECONDS, DEFAULT_MINIMUM_SESSION_SECONDS
        )
        if not isinstance(minimum, int):
            minimum = DEFAULT_MINIMUM_SESSION_SECONDS
        if duration >= minimum:
            commit_session(
                self._data.setdefault("daily_summaries", {}),
                session.started_at,
                ended_at,
                self._cross_midnight_policy,
            )
            self._last_completed = {
                "started_at": session.started_at.isoformat(),
                "ended_at": ended_at.isoformat(),
                "duration_seconds": duration,
                "quality": "exact",
                "crossed_midnight": session.started_at.date() != ended_at.date(),
            }
            self._data["last_completed_session"] = self._last_completed
        await self._async_cleanup(ended_at.date())
        await self._async_save()

    @property
    def _cross_midnight_policy(self) -> str:
        value = self.entry.options.get(
            OPT_CROSS_MIDNIGHT_POLICY, DEFAULT_CROSS_MIDNIGHT_POLICY
        )
        return (
            value if value in CROSS_MIDNIGHT_POLICIES else DEFAULT_CROSS_MIDNIGHT_POLICY
        )

    async def _async_cleanup(self, today) -> None:
        retention = self.entry.options.get(OPT_RETENTION_DAYS, DEFAULT_RETENTION_DAYS)
        retention = retention if isinstance(retention, int) else DEFAULT_RETENTION_DAYS
        cutoff = (today - timedelta(days=retention - 1)).isoformat()
        summaries = self._data.setdefault("daily_summaries", {})
        for date in tuple(summaries):
            if date < cutoff:
                summaries.pop(date)

    async def _async_save(self) -> None:
        self._data["checkpoint"] = self._session.as_dict() if self._session else None
        await self._storage.async_save(self._data)

    @staticmethod
    def _session_from_checkpoint(raw: object) -> Session | None:
        if not isinstance(raw, dict):
            return None
        try:
            started_at = datetime.fromisoformat(raw["started_at"])
            observed_at = datetime.fromisoformat(raw["last_observed_at"])
        except KeyError, TypeError, ValueError:
            return None
        return Session(started_at, observed_at)

    def _cancel_deadline(self) -> None:
        if self._deadline_unsubscribe:
            self._deadline_unsubscribe()
            self._deadline_unsubscribe = None

    def _schedule_deadline(self, now: datetime) -> None:
        self._cancel_deadline()
        if (deadline := self._engine.next_deadline(self._states, now)) is not None:
            self._deadline_unsubscribe = async_track_point_in_time(
                self.hass, self._async_deadline, deadline
            )

    def period_summaries(
        self, period: str
    ) -> tuple[list[DailySummary], datetime, datetime]:
        now = dt_util.now()
        if period.startswith(PERIOD_PREVIOUS_DAY_PREFIX):
            try:
                offset = max(1, int(period.split(":", 1)[1]))
            except ValueError:
                offset = 1
            date = now.date() - timedelta(days=offset)
            start_date, end_date = date, date
        elif period == "current_month":
            start_date, end_date = now.date().replace(day=1), now.date()
        elif period == "current_week":
            weekday = getattr(getattr(self.hass, "config", None), "first_weekday", 0)
            weekday = weekday if isinstance(weekday, int) else 0
            start_date = now.date() - timedelta(days=(now.weekday() - weekday) % 7)
            end_date = now.date()
        else:
            start_date = end_date = now.date()
        values = self.daily_summaries
        return (
            [
                value
                for date, value in values.items()
                if start_date.isoformat() <= date <= end_date.isoformat()
            ],
            datetime.combine(start_date, datetime.min.time(), now.tzinfo),
            datetime.combine(
                end_date + timedelta(days=1), datetime.min.time(), now.tzinfo
            ),
        )

    def period_availability(self, _period: str) -> tuple[bool, dict[str, str]]:
        if self._storage_error:
            return False, {"reason": self._storage_error}
        return True, {}

    def _notify(self) -> None:
        async_dispatcher_send(self.hass, self.signal)
