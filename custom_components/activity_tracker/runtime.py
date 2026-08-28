"""Real-time monitor runtime and durable activity accounting."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from copy import deepcopy
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_HOME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_point_in_time,
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
    DEFAULT_UNAVAILABLE_BEHAVIOR,
    DEFAULT_UNAVAILABLE_TOLERANCE_SECONDS,
    OPT_IMPORT_RECORDER_HISTORY,
    OPT_MERGE_GAP_SECONDS,
    OPT_MINIMUM_SESSION_SECONDS,
    OPT_UNAVAILABLE_BEHAVIOR,
    OPT_UNAVAILABLE_TOLERANCE_SECONDS,
    TYPE_AREA_PRESENCE,
    TYPE_FOREGROUND_APPLICATION,
    TYPE_ZONE,
    update_signal,
)
from .models import DailySummary, Session, split_interval
from .recorder_import import async_get_import
from .storage import ActivityTrackerStorage

_LOGGER = logging.getLogger(__name__)

_AVAILABILITY_ACTIONS = {
    "insufficient_complete_history": "wait_for_complete_history",
    "retention_limit": "increase_retention_or_choose_shorter_period",
    "incompatible_rule_history": "reimport_or_wait_for_new_history",
    "unavailable_source_data": "check_source_entity",
    "storage_migration_failed": "restore_or_reconfigure_monitor",
}


class ActivityTrackerRuntime:
    """Observe a configured source and aggregate compact daily summaries."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._storage = ActivityTrackerStorage(hass, entry.entry_id)
        self._data: dict[str, Any] = {}
        self._session: Session | None = None
        self._unsubscribers: list[callback] = []
        self._deadline_unsubscribe: callback | None = None
        self._is_setup = False
        self._last_completed: dict[str, Any] | None = None
        self._unknown_started_at: datetime | None = None
        self._mutation_lock = asyncio.Lock()
        self._storage_error: str | None = None
        self._last_cleanup_date = None
        self._recorder_import_task: asyncio.Task[None] | None = None

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
        """Return a redacted storage failure reason, if loading was unsafe."""
        return self._storage_error

    @property
    def daily_summaries(self) -> dict[str, DailySummary]:
        raw = self._data.setdefault("daily_summaries", {})
        return {date: DailySummary.from_dict(value) for date, value in raw.items()}

    async def async_setup(self) -> None:
        """Restore data, resume safely, and subscribe to source state changes."""
        try:
            self._data = await self._storage.async_load()
        except ValueError:
            self._storage_error = "storage_migration_failed"
            _LOGGER.exception(
                "Unable to load Activity Tracker storage for %s", self.entry.title
            )
            self._data = {"daily_summaries": {}, "applications": {}}
            return
        self._last_completed = self._data.get("last_completed_session")
        raw_unknown_started = self._data.get("unknown_started_at")
        if isinstance(raw_unknown_started, str):
            try:
                self._unknown_started_at = datetime.fromisoformat(raw_unknown_started)
            except ValueError:
                self._unknown_started_at = None
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
            await self._async_restore_checkpoint(now)
        if state is not None:
            await self.async_process_state(state, now)
        self._is_setup = True
        self._schedule_interruption_deadline()
        if self.entry.options.get(OPT_IMPORT_RECORDER_HISTORY):
            self.async_schedule_recorder_import()

    async def async_unload(self) -> None:
        """Persist the checkpoint and release listeners."""
        if self._recorder_import_task is not None:
            self._recorder_import_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._recorder_import_task
        async with self._mutation_lock:
            if self._session is not None:
                self._session.last_observed_at = datetime.now().astimezone()
            await self._async_save()
        self._cancel_interruption_deadline()
        for unsub in self._unsubscribers:
            unsub()
        self._unsubscribers.clear()

    async def async_delete_storage(self) -> None:
        await self._storage.async_remove()

    async def async_clear_history(self) -> None:
        """Remove completed aggregates while retaining any in-progress checkpoint."""
        async with self._mutation_lock:
            self._data["daily_summaries"] = {}
            self._data.pop("last_completed_session", None)
            self._last_completed = None
            await self._async_save()

    async def async_import_recorder_history(self) -> None:
        """Rebuild only the queried Recorder window without losing outer dates."""
        entity_id = self._source_entity_id
        if not entity_id:
            return
        now = datetime.now().astimezone()
        retention = self.entry.options.get("retention_days", 90)
        retention = retention if isinstance(retention, int) and retention > 0 else 90
        start = datetime.combine(
            now.date() - timedelta(days=retention - 1), datetime.min.time(), now.tzinfo
        )
        recorder_import = await async_get_import(
            self.hass, entity_id, start, now, self._classify_state
        )
        sessions = recorder_import.sessions
        async with self._mutation_lock:
            # Do all replacement work on a complete copy. A cancelled or failed
            # Recorder query therefore cannot publish a partially rebuilt history.
            replacement = deepcopy(self._data)
            summaries = replacement.setdefault("daily_summaries", {})
            usable_start = recorder_import.start
            rebuilt_dates = {
                date
                for date in summaries
                if (
                    usable_start is not None
                    and usable_start.date().isoformat()
                    <= date
                    <= now.date().isoformat()
                )
            }
            preserved_days = len(summaries) - len(rebuilt_dates)
            for date in tuple(summaries):
                if date in rebuilt_dates:
                    summaries.pop(date)
            last_completed: dict[str, Any] | None = None
            processed_sessions = 0
            skipped_sessions = 0
            for session_start, session_end, app_id, app_label in sessions:
                duration = (session_end - session_start).total_seconds()
                minimum = self.entry.options.get(
                    OPT_MINIMUM_SESSION_SECONDS, DEFAULT_MINIMUM_SESSION_SECONDS
                )
                if not isinstance(minimum, int) or duration < minimum:
                    skipped_sessions += 1
                    continue
                session = Session(session_start, session_start, app_id, app_label)
                self._commit_session(session, session_end, duration, summaries)
                processed_sessions += 1
                last_completed = {
                    "started_at": session_start.isoformat(),
                    "ended_at": session_end.isoformat(),
                    "duration_seconds": duration,
                    "quality": "imported",
                    "crossed_midnight": session_start.date() != session_end.date(),
                }
            replacement["last_completed_session"] = last_completed
            boundaries = (
                (usable_start.date().isoformat(), now.date().isoformat())
                if usable_start is not None
                else ()
            )
            for boundary in boundaries:
                if boundary in summaries:
                    summary = DailySummary.from_dict(summaries[boundary])
                    summary.complete = False
                    summaries[boundary] = summary.as_dict()
            cutoff = (now.date() - timedelta(days=retention - 1)).isoformat()
            for date in tuple(summaries):
                if date < cutoff:
                    summaries.pop(date)
            warnings: list[str] = []
            if usable_start is None:
                warnings.append("no_recorder_states_in_requested_range")
            else:
                warnings.append("import_boundary_days_are_partial")
            if skipped_sessions:
                warnings.append("sessions_below_minimum_duration_skipped")
            result = {
                "status": "completed",
                "requested_at": now.isoformat(),
                "completed_at": now.isoformat(),
                "range": {
                    "start": usable_start.isoformat() if usable_start else None,
                    "end": now.isoformat(),
                },
                "rebuilt_days": len(rebuilt_dates),
                "preserved_days": preserved_days,
                "processed_sessions": processed_sessions,
                "warnings": warnings,
            }
            replacement["last_recorder_import"] = result
            await self._storage.async_save(replacement)
            self._data = replacement
            self._last_completed = last_completed

    def async_schedule_recorder_import(self) -> None:
        """Start the optional Recorder rebuild after normal startup is ready."""
        if self._recorder_import_task is not None:
            return
        self._recorder_import_task = self.hass.async_create_background_task(
            self._async_run_scheduled_recorder_import(),
            f"Activity Tracker Recorder import {self.entry.entry_id}",
        )

    async def _async_run_scheduled_recorder_import(self) -> None:
        """Run an import without making monitor startup depend on Recorder."""
        try:
            await self.async_import_recorder_history()
        except asyncio.CancelledError:
            raise
        except Exception:  # Recorder can be disabled, unavailable, or slow.
            _LOGGER.exception(
                "Unable to import Recorder history for %s", self.entry.title
            )
            async with self._mutation_lock:
                failed = deepcopy(self._data)
                failed["last_recorder_import"] = {
                    "status": "failed",
                    "requested_at": datetime.now().astimezone().isoformat(),
                    "warnings": ["recorder_unavailable"],
                }
                await self._storage.async_save(failed)
                self._data = failed
        else:
            options = dict(self.entry.options)
            options[OPT_IMPORT_RECORDER_HISTORY] = False
            self.hass.config_entries.async_update_entry(self.entry, options=options)
        finally:
            self._recorder_import_task = None
            self._notify()

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
        async with self._mutation_lock:
            if self._last_cleanup_date != now.date():
                await self._async_cleanup(now.date())
                self._data["last_cleanup"] = now.isoformat()
                self._last_cleanup_date = now.date()
                await self._async_save()
            if self._session is not None:
                await self._async_expire_interruption(now)
                self._notify()

    async def async_process_state(self, state: State, now: datetime) -> None:
        """Apply a logical source observation. Public for focused tests."""
        async with self._mutation_lock:
            await self._async_process_state(state, now)

    async def _async_process_state(self, state: State, now: datetime) -> None:
        """Apply an observation while the caller holds the mutation lock."""
        if self._storage_error is not None:
            return
        active, app_id, app_label = self._classify_state(state)
        unavailable = state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN)
        if self._session is not None and now <= self._session.last_observed_at:
            return
        if not unavailable and self._unknown_started_at is not None:
            await self._async_add_unknown(self._unknown_started_at, now)
            self._unknown_started_at = None
        if active:
            await self._async_handle_active(now, app_id, app_label)
        elif self._session is not None:
            if unavailable:
                await self._async_handle_unavailable(now)
            else:
                await self._async_handle_inactive(now)
        self._schedule_interruption_deadline()
        self._notify()

    async def _async_handle_active(
        self, now: datetime, app_id: str | None, app_label: str | None
    ) -> None:
        """Start, resume, or switch the session for an active observation."""
        if self._session is None:
            self._start_session(now, app_id, app_label)
        elif app_id is not None and app_id != self._session.application_id:
            await self._async_finish_session(now)
            self._start_session(now, app_id, app_label)
        elif self._is_unknown_interruption():
            await self._async_add_unknown(self._session.paused_at, now)
            await self._async_finish_session(self._session.paused_at)
            self._start_session(now, app_id, app_label)
        else:
            self._resume_session(now)
        await self._async_save()

    def _start_session(
        self, now: datetime, app_id: str | None, app_label: str | None
    ) -> None:
        self._session = Session(
            now, now, app_id, app_label, active_segment_started_at=now
        )

    def _is_unknown_interruption(self) -> bool:
        return (
            self._session is not None
            and self._session.state == "unavailable_pending"
            and self._unavailable_behavior == "unknown"
        )

    def _resume_session(self, now: datetime) -> None:
        assert self._session is not None
        if self._session.state != "active":
            self._session.state = "active"
            self._session.paused_at = None
            self._session.active_segment_started_at = now
        self._session.last_observed_at = now

    @property
    def _unavailable_behavior(self) -> str:
        behavior = self.entry.options.get(
            OPT_UNAVAILABLE_BEHAVIOR, DEFAULT_UNAVAILABLE_BEHAVIOR
        )
        return behavior if behavior in {"end", "pending", "unknown"} else "unknown"

    def _interruption_tolerance(self, state: str) -> int:
        option = (
            OPT_MERGE_GAP_SECONDS
            if state == "observed_inactive_pause"
            else OPT_UNAVAILABLE_TOLERANCE_SECONDS
        )
        default = (
            DEFAULT_MERGE_GAP_SECONDS
            if state == "observed_inactive_pause"
            else DEFAULT_UNAVAILABLE_TOLERANCE_SECONDS
        )
        value = self.entry.options.get(option, default)
        return value if isinstance(value, int) and value > 0 else 0

    async def _async_handle_inactive(self, now: datetime) -> None:
        """Pause or close a session on a known inactive observation."""
        assert self._session is not None
        if self._session.state == "active":
            self._accumulate_active_segment(self._session, now)
            if self._interruption_tolerance("observed_inactive_pause") == 0:
                await self._async_finish_session(now)
                return
            self._session.state = "observed_inactive_pause"
            self._session.paused_at = now
        self._session.last_observed_at = now
        await self._async_save()

    async def _async_handle_unavailable(self, now: datetime) -> None:
        """Apply the user-selected policy to an unavailable observation."""
        assert self._session is not None
        if self._unavailable_behavior == "end":
            await self._async_finish_session(now)
            return
        if self._unavailable_behavior == "unknown" and self._unknown_started_at is None:
            self._unknown_started_at = now
        if self._session.state == "active":
            self._accumulate_active_segment(self._session, now)
            self._session.state = "unavailable_pending"
            self._session.paused_at = now
        self._session.last_observed_at = now
        if self._interruption_tolerance("unavailable_pending") == 0:
            if self._unavailable_behavior == "unknown":
                await self._async_add_unknown(self._session.paused_at, now)
            await self._async_finish_session(self._session.paused_at)
            return
        await self._async_save()

    async def _async_expire_interruption(self, now: datetime) -> None:
        """Resolve a pause without treating the timer as a source observation."""
        if self._session is None or self._session.state == "active":
            return
        paused_at = self._session.paused_at
        if paused_at is None:
            return
        tolerance = self._interruption_tolerance(self._session.state)
        if now < paused_at + timedelta(seconds=tolerance):
            return
        if (
            self._session.state == "unavailable_pending"
            and self._unavailable_behavior == "unknown"
        ):
            unknown_end = paused_at + timedelta(seconds=tolerance)
            await self._async_add_unknown(paused_at, unknown_end)
            self._unknown_started_at = unknown_end
        await self._async_finish_session(paused_at)

    async def _async_deadline_reached(self, now: datetime) -> None:
        """Resolve an interruption at its configured deadline."""
        self._deadline_unsubscribe = None
        await self._async_expire_interruption(now)
        self._schedule_interruption_deadline()
        self._notify()

    def _cancel_interruption_deadline(self) -> None:
        if self._deadline_unsubscribe is not None:
            self._deadline_unsubscribe()
            self._deadline_unsubscribe = None

    def _schedule_interruption_deadline(self) -> None:
        """Schedule exact pause resolution after runtime setup."""
        self._cancel_interruption_deadline()
        if not self._is_setup or self._session is None:
            return
        if self._session.state == "active" or self._session.paused_at is None:
            return
        tolerance = self._interruption_tolerance(self._session.state)
        deadline = self._session.paused_at + timedelta(seconds=tolerance)
        self._deadline_unsubscribe = async_track_point_in_time(
            self.hass, self._async_deadline_reached, deadline
        )

    async def _async_restore_checkpoint(self, now: datetime) -> None:
        """Close a prior-process checkpoint without inferring downtime activity."""
        assert self._session is not None
        checkpoint = self._session
        if (
            self._unavailable_behavior == "unknown"
            and now > checkpoint.last_observed_at
        ):
            await self._async_add_unknown(checkpoint.last_observed_at, now)
        await self._async_finish_session(checkpoint.last_observed_at)

    def _accumulate_active_segment(self, session: Session, ended_at: datetime) -> None:
        """Add a directly observed active segment to the compact checkpoint."""
        started_at = session.active_segment_started_at
        if started_at is None or ended_at <= started_at:
            return
        for date, part_start, part_end in split_interval(started_at, ended_at):
            seconds = (part_end - part_start).total_seconds()
            pending = session.pending_days.setdefault(
                date,
                {
                    "total_seconds": 0.0,
                    "first_active_at": part_start.timetz().isoformat(),
                    "last_inactive_at": part_end.timetz().isoformat(),
                },
            )
            pending["total_seconds"] += seconds
            pending["last_inactive_at"] = part_end.timetz().isoformat()
            session.active_seconds += seconds
        session.active_segment_started_at = None

    async def _async_add_unknown(
        self, started_at: datetime | None, ended_at: datetime
    ) -> None:
        """Record an interval whose source state could not be observed."""
        if started_at is None or ended_at <= started_at:
            return
        summaries = self._data.setdefault("daily_summaries", {})
        for date, part_start, part_end in split_interval(started_at, ended_at):
            summary = DailySummary.from_dict(summaries.get(date))
            summary.unknown_seconds += (part_end - part_start).total_seconds()
            summary.complete = False
            summaries[date] = summary.as_dict()

    def _classify_state(self, state: State) -> tuple[bool, str | None, str | None]:
        monitor_type = self.entry.data.get(CONF_MONITOR_TYPE)
        if state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return False, None, None
        if monitor_type == TYPE_ZONE:
            return state.state == self._zone_state_value(), None, None
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

    def _zone_state_value(self) -> str | None:
        """Return the state a person or device tracker reports for its zone."""
        zone_entity_id = self.entry.data.get(CONF_ZONE_ENTITY_ID)
        if not isinstance(zone_entity_id, str):
            return None
        if zone_entity_id == "zone.home":
            return STATE_HOME

        zone = self.hass.states.get(zone_entity_id)
        if zone is not None:
            return zone.name
        return zone_entity_id.removeprefix("zone.")

    async def _async_finish_session(self, ended_at: datetime) -> None:
        if self._session is None:
            return
        self._cancel_interruption_deadline()
        session = self._session
        self._session = None
        if ended_at <= session.started_at:
            await self._async_save()
            return
        self._accumulate_active_segment(session, ended_at)
        duration = session.active_seconds
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
        self,
        session: Session,
        ended_at: datetime,
        duration: float,
        summaries: dict[str, Any] | None = None,
    ) -> None:
        if summaries is None:
            summaries = self._data.setdefault("daily_summaries", {})
        if session.pending_days:
            for index, (date, pending) in enumerate(
                sorted(session.pending_days.items())
            ):
                self._commit_summary_fragment(
                    summaries, date, float(pending["total_seconds"]),
                    pending.get("first_active_at"), pending.get("last_inactive_at"),
                    index == 0, session, duration,
                )
            return
        for index, (date, part_start, part_end) in enumerate(
            split_interval(session.started_at, ended_at)
        ):
            self._commit_summary_fragment(
                summaries, date, (part_end - part_start).total_seconds(),
                part_start.timetz().isoformat(), part_end.timetz().isoformat(),
                index == 0, session, duration,
            )

    def _commit_summary_fragment(  # noqa: PLR0917
        self, summaries: dict[str, Any], date: str, seconds: float,
        first_active_at: str | None, last_inactive_at: str | None,
        starts_session: bool, session: Session, duration: float,
    ) -> None:
        """Add one completed-session fragment to a daily aggregate."""
        summary = DailySummary.from_dict(summaries.get(date))
        summary.total_seconds += seconds
        summary.exact_seconds += seconds
        if starts_session:
            summary.sessions_started += 1
            summary.first_active_at = summary.first_active_at or first_active_at
        else:
            summary.continued_sessions += 1
        summary.last_inactive_at = last_inactive_at
        summary.longest_session_seconds = max(summary.longest_session_seconds, duration)
        summary.shortest_session_seconds = (
            duration if summary.shortest_session_seconds is None
            else min(summary.shortest_session_seconds, duration)
        )
        self._commit_application_fragment(
            summary, session, seconds, starts_session, duration
        )
        summaries[date] = summary.as_dict()

    @staticmethod
    def _commit_application_fragment(
        summary: DailySummary, session: Session, seconds: float,
        starts_session: bool, duration: float,
    ) -> None:
        if not session.application_id:
            return
        app = summary.applications.setdefault(
            session.application_id,
            {"display_name": session.application_label or session.application_id,
             "total_seconds": 0, "sessions_started": 0, "longest_session_seconds": 0},
        )
        app["total_seconds"] += seconds
        if starts_session:
            app["sessions_started"] += 1
        app["longest_session_seconds"] = max(app["longest_session_seconds"], duration)

    async def _async_cleanup(self, today) -> None:
        retention = self.entry.options.get("retention_days", 90)
        if not isinstance(retention, int):
            return
        cutoff = (today - timedelta(days=retention - 1)).isoformat()
        summaries = self._data.setdefault("daily_summaries", {})
        for date in tuple(summaries):
            if date < cutoff:
                summaries.pop(date)

    async def _async_save(self) -> None:
        self._data["checkpoint"] = self._session.as_dict() if self._session else None
        self._data["unknown_started_at"] = (
            self._unknown_started_at.isoformat() if self._unknown_started_at else None
        )
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
            first_weekday = getattr(
                getattr(self.hass, "config", None), "first_weekday", 0
            )
            if not isinstance(first_weekday, int) or not 0 <= first_weekday <= 6:
                first_weekday = 0
            start_date = now.date() - timedelta(
                days=(now.weekday() - first_weekday) % 7
            )
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

    def period_availability(self, period: str) -> tuple[bool, dict[str, Any]]:
        """Return whether a period has its required complete local-day history."""
        if self._storage_error is not None:
            return False, self._availability_attributes(self._storage_error)
        if not period.startswith("rolling_days:"):
            return True, {}
        required = max(1, int(period.split(":", 1)[1]))
        retention = self.entry.options.get("retention_days", 90)
        retention = retention if isinstance(retention, int) else 90
        now = datetime.now().astimezone()
        summaries = self.daily_summaries
        complete_dates = sorted(
            date
            for date, summary in summaries.items()
            if (
                summary.complete
                and summary.rule_version == 1
                and date != now.date().isoformat()
            )
        )
        attributes: dict[str, Any] = {
            "required_days": required,
            "available_days": len(complete_dates),
            "available_from": complete_dates[0] if complete_dates else None,
        }
        if required > retention:
            attributes.update(self._availability_attributes("retention_limit"))
            return False, attributes
        if len(complete_dates) < required:
            attributes.update(
                self._availability_attributes("insufficient_complete_history")
            )
            return False, attributes
        attributes["period_end"] = now.isoformat()
        return True, attributes

    @staticmethod
    def _availability_attributes(reason: str) -> dict[str, str]:
        """Return a stable, non-sensitive next step for an unavailable report."""
        return {
            "reason": reason,
            "suggested_action": _AVAILABILITY_ACTIONS.get(reason, "check_monitor"),
        }

    def _notify(self) -> None:
        async_dispatcher_send(self.hass, self.signal)
