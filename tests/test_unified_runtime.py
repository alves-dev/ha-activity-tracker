"""Focused integration tests for the unified runtime."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from homeassistant.core import State

from custom_components.activity_tracker.const import (
    CONF_RULE,
    OPT_CROSS_MIDNIGHT_POLICY,
)
from custom_components.activity_tracker.models import Session
from custom_components.activity_tracker.runtime import ActivityTrackerRuntime


def _runtime(policy: str = "split_at_midnight") -> ActivityTrackerRuntime:
    hass = SimpleNamespace(data={}, states=SimpleNamespace(get=lambda _: None))
    entry = SimpleNamespace(
        entry_id="unified",
        title="Unified",
        data={
            CONF_RULE: {
                "start_when": {
                    "type": "state",
                    "entity_id": "input_boolean.activity",
                    "states": ["on"],
                },
                "stop_when": {
                    "type": "state",
                    "entity_id": "input_boolean.activity",
                    "states": ["off"],
                },
            }
        },
        options={
            "retention_days": 90,
            "minimum_session_seconds": 0,
            OPT_CROSS_MIDNIGHT_POLICY: policy,
        },
    )
    with patch("custom_components.activity_tracker.runtime.ActivityTrackerStorage"):
        runtime = ActivityTrackerRuntime(hass, entry)
    runtime._storage.async_save = AsyncMock()
    runtime._notify = lambda: None
    return runtime


async def test_runtime_commits_session_from_unified_rule() -> None:
    runtime = _runtime()
    start = datetime.now().astimezone().replace(microsecond=0)

    await runtime.async_process_state(State("input_boolean.activity", "on"), start)
    await runtime.async_process_state(
        State("input_boolean.activity", "off"), start + timedelta(minutes=10)
    )

    assert runtime.session is None
    assert runtime.last_completed["duration_seconds"] == 600
    assert runtime.daily_summaries[start.date().isoformat()].total_seconds == 600


async def test_restart_closes_a_restored_session_at_its_last_observation() -> None:
    runtime = _runtime()
    start = datetime.now().astimezone().replace(microsecond=0)
    restored = Session(start, start + timedelta(minutes=2))
    runtime._session = runtime._session_from_checkpoint(restored.as_dict())
    runtime._engine.started_at = start

    await runtime._async_finish(runtime._session.last_observed_at)

    assert runtime.session is None
    assert runtime.last_completed["duration_seconds"] == 120


def test_previous_day_period_selects_one_closed_local_date() -> None:
    runtime = _runtime()
    now = datetime(2026, 9, 9, 13, tzinfo=datetime.now().astimezone().tzinfo)
    runtime._data["daily_summaries"] = {
        "2026-09-07": {"total_seconds": 7},
        "2026-09-08": {"total_seconds": 8},
        "2026-09-09": {"total_seconds": 9},
    }
    with patch(
        "custom_components.activity_tracker.runtime.dt_util.now", return_value=now
    ):
        summaries, start, end = runtime.period_summaries("previous_day:1")

    assert [summary.total_seconds for summary in summaries] == [8]
    assert start.date().isoformat() == "2026-09-08"
    assert end.date().isoformat() == "2026-09-09"
