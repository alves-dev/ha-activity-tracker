"""Real-time monitor runtime and durable activity accounting."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)

from .const import (
    CONF_ACTIVE_STATES,
    CONF_ENTITY_ID,
    CONF_LABEL_ATTRIBUTE,
    CONF_MONITOR_TYPE,
    CONF_PRESENCE_ENTITY_ID,
    CONF_VALUE_ATTRIBUTE,
    CONF_VALUE_SOURCE,
    CONF_ZONE_ENTITY_ID,
    DEFAULT_MERGE_GAP_SECONDS,
    DEFAULT_MINIMUM_SESSION_SECONDS,
    OPT_IMPORT_RECORDER_HISTORY,
    OPT_MERGE_GAP_SECONDS,
    OPT_MINIMUM_SESSION_SECONDS,
    TYPE_AREA_PRESENCE,
    TYPE_FOREGROUND_APPLICATION,
    TYPE_ZONE,
    update_signal,
)
from .models import DailySummary, Session, split_interval
from .recorder_import import async_get_sessions
from .storage import ActivityTrackerStorage

_LOGGER = logging.getLogger(__name__)


class ActivityTrackerRuntime:
    """Observe a configured source and aggregate compact daily summaries."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._storage = ActivityTrackerStorage(hass, entry.entry_id)
        self._data: dict[str, Any] = {}
        self._session: Session | None = None
        self._unsubscribers: list[callback] = []
        self._last_completed: dict[str, Any] | None = None

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
    def daily_summaries(self) -> dict[str, DailySummary]:
        raw = self._data.setdefault("daily_summaries", {})
        return {date: DailySummary.from_dict(value) for date, value in raw.items()}

    async def async_setup(self) -> None:
        """Restore data, resume safely, and subscribe to source state changes."""
        self._data = await self._storage.async_load()
        if self.entry.options.get(OPT_IMPORT_RECORDER_HISTORY):
            try:
                await self.async_import_recorder_history()
            except Exception:  # Recorder may be disabled or unavailable at startup.
                _LOGGER.exception(
                    "Unable to import Recorder history for %s", self.entry.title
                )
            else:
                options = dict(self.entry.options)
                options[OPT_IMPORT_RECORDER_HISTORY] = False
                self.hass.config_entries.async_update_entry(self.entry, options=options)
        self._last_completed = self._data.get("last_completed_session")
        checkpoint = self._data.get("checkpoint")
        if isinstance(checkpoint, dict):
            self._session = self._session_from_checkpoint(checkpoint)
        entity_id = self._source_entity_id
        if entity_id:
            self._unsubscribers.append(
                async_track_state_change_event(
                    self.hass, [entity_id], self._async_source_event
                )
            )
        self._unsubscribers.append(
            async_track_time_interval(
                self.hass, self._async_minute_tick, timedelta(minutes=1)
            )
        )
        now = datetime.now().astimezone()
        state = self.hass.states.get(entity_id) if entity_id else None
        # A prior process could not observe the outage: close at its last observation.
        if self._session is not None:
            await self._async_finish_session(self._session.last_observed_at)
        if state is not None:
            await self.async_process_state(state, now)

    async def async_unload(self) -> None:
        """Persist the checkpoint and release listeners."""
        if self._session is not None:
            self._session.last_observed_at = datetime.now().astimezone()
        await self._async_save()
        for unsub in self._unsubscribers:
            unsub()
        self._unsubscribers.clear()

    async def async_delete_storage(self) -> None:
        await self._storage.async_remove()

    async def async_clear_history(self) -> None:
        """Remove completed aggregates while retaining any in-progress checkpoint."""
        self._data["daily_summaries"] = {}
        self._data.pop("last_completed_session", None)
        self._last_completed = None
        await self._async_save()

    async def async_import_recorder_history(self) -> None:
        """Replace retained summaries with sessions reconstructed from Recorder."""
        entity_id = self._source_entity_id
        if not entity_id:
            return
        now = datetime.now().astimezone()
        retention = self.entry.options.get("retention_days", 90)
        retention = retention if isinstance(retention, int) and retention > 0 else 90
        start = datetime.combine(
            now.date() - timedelta(days=retention - 1), datetime.min.time(), now.tzinfo
        )
        sessions = await async_get_sessions(
            self.hass, entity_id, start, now, self._classify_state
        )
        summaries = self._data.setdefault("daily_summaries", {})
        for date in list(summaries):
            if start.date().isoformat() <= date <= now.date().isoformat():
                summaries.pop(date)
        self._last_completed = None
        for session_start, session_end, app_id, app_label in sessions:
            duration = (session_end - session_start).total_seconds()
            minimum = self.entry.options.get(
                OPT_MINIMUM_SESSION_SECONDS, DEFAULT_MINIMUM_SESSION_SECONDS
            )
            if not isinstance(minimum, int) or duration < minimum:
                continue
            session = Session(session_start, session_start, app_id, app_label)
            self._commit_session(session, session_end, duration)
            self._last_completed = {
                "started_at": session_start.isoformat(),
                "ended_at": session_end.isoformat(),
                "duration_seconds": duration,
                "quality": "imported",
                "crossed_midnight": session_start.date() != session_end.date(),
            }
        self._data["last_completed_session"] = self._last_completed
        self._data["last_recorder_import"] = now.isoformat()
        await self._async_cleanup(now.date())
        await self._async_save()

    @classmethod
    async def async_delete_entry_storage(
        cls, hass: HomeAssistant, entry_id: str
    ) -> None:
        await ActivityTrackerStorage(hass, entry_id).async_remove()

    @property
    def _source_entity_id(self) -> str | None:
        if self.entry.data.get(CONF_MONITOR_TYPE) == TYPE_AREA_PRESENCE:
            return self.entry.data.get(CONF_PRESENCE_ENTITY_ID)
        return self.entry.data.get(CONF_ENTITY_ID)

    async def _async_source_event(self, event: Event) -> None:
        state = event.data.get("new_state")
        if isinstance(state, State):
            await self.async_process_state(state, datetime.now().astimezone())

    async def _async_minute_tick(self, now: datetime) -> None:
        if self._session is not None:
            self._session.last_observed_at = now
            self._notify()

    async def async_process_state(self, state: State, now: datetime) -> None:
        """Apply a logical source observation. Public for focused tests."""
        active, app_id, app_label = self._classify_state(state)
        if active:
            if self._session is None:
                self._session = Session(now, now, app_id, app_label)
                await self._async_save()
            elif app_id is not None and app_id != self._session.application_id:
                await self._async_finish_session(now)
                self._session = Session(now, now, app_id, app_label)
                await self._async_save()
            else:
                self._session.last_observed_at = now
        elif self._session is not None:
            gap = self.entry.options.get(
                OPT_MERGE_GAP_SECONDS, DEFAULT_MERGE_GAP_SECONDS
            )
            if isinstance(gap, int) and gap > 0:
                self._session.paused_at = now
                self._session.last_observed_at = now
                await self._async_save()
            else:
                await self._async_finish_session(now)
        self._notify()

    def _classify_state(self, state: State) -> tuple[bool, str | None, str | None]:
        monitor_type = self.entry.data.get(CONF_MONITOR_TYPE)
        if state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return False, None, None
        if monitor_type == TYPE_ZONE:
            return state.state == self.entry.data.get(CONF_ZONE_ENTITY_ID), None, None
        if monitor_type == TYPE_FOREGROUND_APPLICATION:
            value = (
                state.state
                if self.entry.data.get(CONF_VALUE_SOURCE, "state") == "state"
                else state.attributes.get(self.entry.data.get(CONF_VALUE_ATTRIBUTE))
            )
            if value in (None, "", STATE_UNKNOWN, STATE_UNAVAILABLE):
                return False, None, None
            identifier = str(value)
            label = state.attributes.get(self.entry.data.get(CONF_LABEL_ATTRIBUTE))
            return (
                True,
                identifier,
                str(label) if label not in (None, "") else identifier,
            )
        active_states = self.entry.data.get(CONF_ACTIVE_STATES, [])
        return state.state in active_states, None, None

    async def _async_finish_session(self, ended_at: datetime) -> None:
        if self._session is None:
            return
        session = self._session
        self._session = None
        if ended_at <= session.started_at:
            await self._async_save()
            return
        duration = (ended_at - session.started_at).total_seconds()
        minimum = self.entry.options.get(
            OPT_MINIMUM_SESSION_SECONDS, DEFAULT_MINIMUM_SESSION_SECONDS
        )
        if not isinstance(minimum, int):
            minimum = DEFAULT_MINIMUM_SESSION_SECONDS
        if duration >= minimum:
            self._commit_session(session, ended_at, duration)
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

    def _commit_session(
        self, session: Session, ended_at: datetime, duration: float
    ) -> None:
        summaries = self._data.setdefault("daily_summaries", {})
        for index, (date, part_start, part_end) in enumerate(
            split_interval(session.started_at, ended_at)
        ):
            summary = DailySummary.from_dict(summaries.get(date))
            seconds = (part_end - part_start).total_seconds()
            summary.total_seconds += seconds
            summary.exact_seconds += seconds
            if index == 0:
                summary.sessions_started += 1
                summary.first_active_at = (
                    summary.first_active_at or part_start.timetz().isoformat()
                )
            else:
                summary.continued_sessions += 1
            summary.last_inactive_at = part_end.timetz().isoformat()
            summary.longest_session_seconds = max(
                summary.longest_session_seconds, duration
            )
            summary.shortest_session_seconds = (
                duration
                if summary.shortest_session_seconds is None
                else min(summary.shortest_session_seconds, duration)
            )
            if session.application_id:
                app = summary.applications.setdefault(
                    session.application_id,
                    {
                        "display_name": session.application_label
                        or session.application_id,
                        "total_seconds": 0,
                        "sessions_started": 0,
                        "longest_session_seconds": 0,
                    },
                )
                app["total_seconds"] += seconds
                if index == 0:
                    app["sessions_started"] += 1
                app["longest_session_seconds"] = max(
                    app["longest_session_seconds"], duration
                )
            summaries[date] = summary.as_dict()

    async def _async_cleanup(self, today) -> None:
        retention = self.entry.options.get("retention_days", 90)
        if not isinstance(retention, int):
            return
        cutoff = (today - timedelta(days=retention - 1)).isoformat()
        summaries = self._data.setdefault("daily_summaries", {})
        for date in list(summaries):
            if date < cutoff:
                summaries.pop(date)

    async def _async_save(self) -> None:
        self._data["checkpoint"] = self._session.as_dict() if self._session else None
        await self._storage.async_save(self._data)

    def _session_from_checkpoint(self, raw: dict[str, Any]) -> Session | None:
        try:
            started = datetime.fromisoformat(raw["started_at"])
            observed = datetime.fromisoformat(
                raw.get("last_observed_at", raw["started_at"])
            )
        except KeyError, TypeError, ValueError:
            return None
        return Session(
            started, observed, raw.get("application_id"), raw.get("application_label")
        )

    def period_summaries(
        self, period: str
    ) -> tuple[list[DailySummary], datetime, datetime]:
        """Return period summaries plus local window boundaries."""
        now = datetime.now().astimezone()
        if period.startswith("rolling_days:"):
            days = max(1, int(period.split(":", 1)[1]))
            start_date = now.date() - timedelta(days=days - 1)
        elif period == "current_week":
            start_date = now.date() - timedelta(days=now.weekday())
        elif period == "current_month":
            start_date = now.date().replace(day=1)
        else:
            start_date = now.date()
        summaries = self.daily_summaries
        selected = [
            summary
            for date, summary in summaries.items()
            if date >= start_date.isoformat() and date <= now.date().isoformat()
        ]
        return (
            selected,
            datetime.combine(start_date, datetime.min.time(), now.tzinfo),
            now,
        )

    def _notify(self) -> None:
        async_dispatcher_send(self.hass, self.signal)
