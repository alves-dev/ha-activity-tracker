"""Tests for unified-rule selected report sensors."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

from homeassistant.components.sensor import SensorStateClass

from custom_components.activity_tracker.const import (
    CONF_ENABLED_METRICS,
    CONF_PERIOD_METRICS,
    DOMAIN,
    METRIC_AVERAGE_END_TIME,
    METRIC_AVERAGE_START_TIME,
    METRIC_SESSION_COUNT,
    METRIC_TIME_SINCE_LAST_SESSION,
    METRIC_TOTAL_DURATION,
    OPT_DURATION_UNIT,
)
from custom_components.activity_tracker.models import DailySummary, Session
from custom_components.activity_tracker.sensor import (
    ActivityMetricSensor,
    async_setup_entry,
)


def _runtime() -> SimpleNamespace:
    now = datetime.now().astimezone()
    summary = DailySummary(total_seconds=7_200, sessions_started=2)
    summary.add_start_time(now.replace(hour=23, minute=59))
    summary.add_start_time(now.replace(hour=0, minute=1))
    summary.add_end_time(now.replace(hour=6, minute=0))
    return SimpleNamespace(
        entry=SimpleNamespace(
            entry_id="one", title="Test", options={OPT_DURATION_UNIT: "h"}
        ),
        session=Session(now - timedelta(seconds=30), now),
        last_completed={
            "started_at": (now - timedelta(minutes=10)).isoformat(),
            "ended_at": now.isoformat(),
            "duration_seconds": 600,
            "quality": "exact",
        },
        daily_summaries={now.date().isoformat(): summary},
        signal="test",
        storage_error=None,
        period_availability=lambda _period: (True, {}),
        period_summaries=lambda _period: ([summary], now, now),
    )


def test_daily_total_uses_sum_statistics_and_new_timing_metrics() -> None:
    runtime = _runtime()

    daily = ActivityMetricSensor(runtime, METRIC_TOTAL_DURATION, "current_day")
    start = ActivityMetricSensor(runtime, METRIC_AVERAGE_START_TIME, "current_day")
    end = ActivityMetricSensor(runtime, METRIC_AVERAGE_END_TIME, "current_day")
    age = ActivityMetricSensor(runtime, METRIC_TIME_SINCE_LAST_SESSION)

    assert daily.native_value == 2
    assert daily.state_class is SensorStateClass.TOTAL_INCREASING
    assert start.native_value == "00:00"
    assert end.native_value == "06:00"
    assert age.native_value is not None
    assert age.native_unit_of_measurement == "h"


async def test_sensor_factory_creates_only_explicit_unified_pairs() -> None:
    runtime = _runtime()
    entry = SimpleNamespace(
        entry_id="one",
        title="Test",
        options={OPT_DURATION_UNIT: "h"},
        data={
            CONF_PERIOD_METRICS: {
                "current_day": [METRIC_TOTAL_DURATION],
                "previous_day:1": [METRIC_SESSION_COUNT],
            },
            CONF_ENABLED_METRICS: [METRIC_TIME_SINCE_LAST_SESSION],
        },
    )
    runtime.entry = entry
    entities: list[ActivityMetricSensor] = []

    await async_setup_entry(
        SimpleNamespace(data={DOMAIN: {entry.entry_id: runtime}}),
        entry,
        entities.extend,
    )

    assert {(entity._metric, entity._period) for entity in entities} == {
        (METRIC_TOTAL_DURATION, "current_day"),
        (METRIC_SESSION_COUNT, "previous_day:1"),
        (METRIC_TIME_SINCE_LAST_SESSION, None),
    }
