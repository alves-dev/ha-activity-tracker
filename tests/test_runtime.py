"""Tests for real-time session accounting."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import State

from custom_components.activity_tracker.const import (
    CONF_ACTIVE_STATES,
    CONF_ENTITY_ID,
    CONF_LABEL_ATTRIBUTE,
    CONF_MONITOR_TYPE,
    CONF_VALUE_ATTRIBUTE,
    CONF_VALUE_SOURCE,
    CONF_ZONE_ENTITY_ID,
    OPT_MERGE_GAP_SECONDS,
    OPT_UNAVAILABLE_BEHAVIOR,
    TYPE_FOREGROUND_APPLICATION,
    TYPE_ZONE,
)
from custom_components.activity_tracker.models import Session
from custom_components.activity_tracker.recorder_import import async_get_sessions
from custom_components.activity_tracker.runtime import ActivityTrackerRuntime


def _runtime(monitor_type: str = "entity_state") -> ActivityTrackerRuntime:
    hass = SimpleNamespace(data={}, states=SimpleNamespace(get=lambda _: None))
    entry = SimpleNamespace(
        entry_id="monitor-1",
        title="Test monitor",
        data={
            CONF_MONITOR_TYPE: monitor_type,
            CONF_ENTITY_ID: "input_boolean.activity",
            CONF_ACTIVE_STATES: ["on", "playing"],
        },
        options={"retention_days": 2, "minimum_session_seconds": 0},
    )
    with patch("custom_components.activity_tracker.runtime.ActivityTrackerStorage"):
        runtime = ActivityTrackerRuntime(hass, entry)
    runtime._storage.async_save = AsyncMock()
    runtime._storage.async_remove = AsyncMock()
    return runtime


def test_classify_state_supports_entity_zone_and_foreground_sources() -> None:
    runtime = _runtime()
    assert runtime._classify_state(State("input_boolean.x", "on")) == (True, None, None)
    assert runtime._classify_state(State("input_boolean.x", STATE_UNAVAILABLE)) == (
        False,
        None,
        None,
    )

    runtime.entry.data.update(
        {CONF_MONITOR_TYPE: TYPE_ZONE, CONF_ZONE_ENTITY_ID: "zone.gym"}
    )
    assert runtime._classify_state(State("input_boolean.x", "gym"))[0] is True
    assert runtime._classify_state(State("input_boolean.x", "home"))[0] is False

    runtime.hass.states.get = lambda _: State(
        "zone.gym", "0", {"friendly_name": "Gym"}
    )
    assert runtime._classify_state(State("input_boolean.x", "Gym"))[0] is True

    runtime.entry.data[CONF_ZONE_ENTITY_ID] = "zone.home"
    assert runtime._classify_state(State("input_boolean.x", "home"))[0] is True

    runtime.entry.data.update(
        {
            CONF_MONITOR_TYPE: TYPE_FOREGROUND_APPLICATION,
            CONF_VALUE_SOURCE: "attribute",
            CONF_VALUE_ATTRIBUTE: "package",
            CONF_LABEL_ATTRIBUTE: "label",
        }
    )
    assert runtime._classify_state(
        State("input_boolean.x", "ignored", {"package": "app.id", "label": "App"})
    ) == (True, "app.id", "App")
    assert runtime._classify_state(State("input_boolean.x", "ignored", {})) == (
        False,
        None,
        None,
    )


async def test_process_state_starts_and_finishes_a_session() -> None:
    runtime = _runtime()
    runtime._notify = lambda: None
    start = datetime.now().astimezone().replace(microsecond=0)

    await runtime.async_process_state(State("input_boolean.x", "on"), start)
    await runtime.async_process_state(
        State("input_boolean.x", "playing"), start + timedelta(minutes=5)
    )
    await runtime.async_process_state(
        State("input_boolean.x", "off"), start + timedelta(minutes=10)
    )

    assert runtime.session is None
    assert runtime.last_completed["duration_seconds"] == 600
    summary = runtime.daily_summaries[start.date().isoformat()]
    assert summary.total_seconds == 600
    assert summary.sessions_started == 1
    assert runtime._storage.async_save.await_count >= 2


async def test_foreground_application_switch_finishes_previous_session() -> None:
    runtime = _runtime(TYPE_FOREGROUND_APPLICATION)
    runtime.entry.data.update({CONF_VALUE_SOURCE: "state"})
    runtime._notify = lambda: None
    start = datetime.now().astimezone().replace(microsecond=0)

    await runtime.async_process_state(State("input_boolean.x", "first"), start)
    await runtime.async_process_state(
        State("input_boolean.x", "second"), start + timedelta(seconds=30)
    )

    assert runtime.session.application_id == "second"
    assert runtime.last_completed["duration_seconds"] == 30


async def test_short_sessions_are_discarded_and_old_data_is_cleaned() -> None:
    runtime = _runtime()
    runtime.entry.options["minimum_session_seconds"] = 60
    runtime._notify = lambda: None
    start = datetime.now().astimezone().replace(microsecond=0)
    runtime._data = {"daily_summaries": {"2000-01-01": {}}}

    await runtime.async_process_state(State("input_boolean.x", "on"), start)
    await runtime.async_process_state(
        State("input_boolean.x", "off"), start + timedelta(seconds=30)
    )

    assert runtime.last_completed is None
    assert "2000-01-01" not in runtime._data["daily_summaries"]


async def test_merge_gap_keeps_one_session_but_excludes_inactive_time() -> None:
    runtime = _runtime()
    runtime.entry.options[OPT_MERGE_GAP_SECONDS] = 30
    runtime._notify = lambda: None
    start = datetime.now().astimezone().replace(microsecond=0)

    await runtime.async_process_state(State("input_boolean.x", "on"), start)
    await runtime.async_process_state(
        State("input_boolean.x", "off"), start + timedelta(seconds=10)
    )
    await runtime.async_process_state(
        State("input_boolean.x", "on"), start + timedelta(seconds=20)
    )
    await runtime.async_process_state(
        State("input_boolean.x", "off"), start + timedelta(seconds=40)
    )
    await runtime._async_minute_tick(start + timedelta(seconds=71))

    assert runtime.session is None
    assert runtime.last_completed["duration_seconds"] == 30
    assert runtime.daily_summaries[start.date().isoformat()].total_seconds == 30


async def test_unknown_unavailability_is_not_counted_as_activity() -> None:
    runtime = _runtime()
    runtime.entry.options[OPT_UNAVAILABLE_BEHAVIOR] = "unknown"
    runtime._notify = lambda: None
    start = datetime.now().astimezone().replace(microsecond=0)

    await runtime.async_process_state(State("input_boolean.x", "on"), start)
    await runtime.async_process_state(
        State("input_boolean.x", STATE_UNAVAILABLE), start + timedelta(seconds=10)
    )
    await runtime.async_process_state(
        State("input_boolean.x", "on"), start + timedelta(seconds=25)
    )

    summary = runtime.daily_summaries[start.date().isoformat()]
    assert summary.total_seconds == 10
    assert summary.unknown_seconds == 15
    assert summary.complete is False


async def test_recorder_import_rebuilds_daily_summaries() -> None:
    runtime = _runtime()
    now = datetime.now().astimezone().replace(microsecond=0)
    with patch(
        "custom_components.activity_tracker.runtime.async_get_sessions",
        new=AsyncMock(
            return_value=[
                (now - timedelta(minutes=10), now - timedelta(minutes=5), None, None)
            ]
        ),
    ):
        await runtime.async_import_recorder_history()

    summary = runtime.daily_summaries[now.date().isoformat()]
    assert summary.total_seconds == 300
    assert runtime.last_completed["quality"] == "imported"
    assert "last_recorder_import" in runtime._data


async def test_recorder_session_reconstruction_closes_and_splits_applications() -> None:
    start = datetime.now().astimezone().replace(microsecond=0)
    states = [
        State("sensor.activity", "on", last_changed=start),
        State("sensor.activity", "off", last_changed=start + timedelta(minutes=2)),
    ]
    hass = SimpleNamespace(
        async_add_executor_job=AsyncMock(return_value={"sensor.activity": states})
    )

    sessions = await async_get_sessions(
        hass,
        "sensor.activity",
        start,
        start + timedelta(minutes=3),
        lambda state: (state.state == "on", None, None),
    )

    assert sessions == [(start, start + timedelta(minutes=2), None, None)]
    hass.async_add_executor_job.assert_awaited_once()


def test_commit_session_splits_midnight_and_tracks_application() -> None:
    runtime = _runtime(TYPE_FOREGROUND_APPLICATION)
    tz = datetime.now().astimezone().tzinfo
    start = datetime(2026, 8, 24, 23, 30, tzinfo=tz)
    end = datetime(2026, 8, 25, 1, 30, tzinfo=tz)

    runtime._commit_session(Session(start, start, "youtube", "YouTube"), end, 7200)

    monday = runtime.daily_summaries["2026-08-24"]
    tuesday = runtime.daily_summaries["2026-08-25"]
    assert (monday.total_seconds, tuesday.total_seconds) == (1800, 5400)
    assert (monday.sessions_started, tuesday.continued_sessions) == (1, 1)
    assert monday.applications["youtube"]["display_name"] == "YouTube"


def test_checkpoint_and_period_helpers_handle_valid_and_invalid_data() -> None:
    runtime = _runtime()
    now = datetime.now().astimezone().replace(microsecond=0)
    session = runtime._session_from_checkpoint(Session(now, now).as_dict())
    assert session is not None
    assert runtime._session_from_checkpoint({"started_at": "bad"}) is None
    runtime._data = {
        "daily_summaries": {
            now.date().isoformat(): {"total_seconds": 5},
            (now.date() - timedelta(days=1)).isoformat(): {"total_seconds": 6},
        }
    }
    summaries, _, _ = runtime.period_summaries("rolling_days:2")
    assert sum(summary.total_seconds for summary in summaries) == 11


def test_rolling_availability_requires_complete_history() -> None:
    runtime = _runtime()
    runtime.entry.options["retention_days"] = 90
    runtime._data = {
        "daily_summaries": {
            "2026-08-25": {"complete": True},
            "2026-08-26": {"complete": False},
        }
    }

    available, attributes = runtime.period_availability("rolling_days:3")

    assert available is False
    assert attributes == {
        "required_days": 3,
        "available_days": 1,
        "available_from": "2026-08-25",
        "reason": "insufficient_complete_history",
    }
