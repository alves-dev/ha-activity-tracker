"""Tests for selected monitor sensor values."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

from custom_components.activity_tracker.const import (
    METRIC_AVERAGE_DAILY_DURATION,
    METRIC_AVERAGE_SESSION_DURATION,
    METRIC_CURRENT_SESSION_DURATION,
    METRIC_DAYS_SINCE_LAST_SESSION,
    METRIC_FIRST_ACTIVITY_TIME,
    METRIC_LAST_ACTIVITY_TIME,
    METRIC_LAST_SESSION_DURATION,
    METRIC_LAST_SESSION_END,
    METRIC_LAST_SESSION_START,
    METRIC_LONGEST_SESSION_DURATION,
    METRIC_SESSION_COUNT,
    METRIC_SHORTEST_SESSION_DURATION,
    METRIC_TOTAL_DURATION,
    METRIC_UNKNOWN_DURATION,
    METRIC_WEEKDAY_MAX,
    OPT_DURATION_UNIT,
    OPT_RETENTION_DAYS,
)
from custom_components.activity_tracker.models import DailySummary, Session
from custom_components.activity_tracker.sensor import (
    ActivityMetricSensor,
    CurrentApplicationSensor,
    _metric_icon,
    _metric_name,
)


def _runtime() -> SimpleNamespace:
    now = datetime.now().astimezone()
    summary = DailySummary(
        total_seconds=600,
        sessions_started=2,
        longest_session_seconds=400,
        shortest_session_seconds=100,
        unknown_seconds=10,
        first_active_at="08:00:00",
        last_inactive_at="09:00:00",
    )
    return SimpleNamespace(
        entry=SimpleNamespace(
            entry_id="one", title="Test", options={OPT_RETENTION_DAYS: 90}
        ),
        session=Session(now - timedelta(seconds=30), now, "app", "Application"),
        last_completed={
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "ended_at": now.isoformat(),
            "duration_seconds": 300,
            "quality": "exact",
        },
        daily_summaries={now.date().isoformat(): summary},
        signal="test",
        period_availability=lambda _period: (True, {}),
        period_summaries=lambda _period: (
            [summary],
            now.replace(hour=0, minute=0),
            now,
        ),
    )


def test_metric_sensors_cover_period_current_and_latest_values() -> None:
    runtime = _runtime()
    expected = {
        METRIC_TOTAL_DURATION: 600,
        METRIC_SESSION_COUNT: 2,
        METRIC_UNKNOWN_DURATION: 10,
        METRIC_AVERAGE_DAILY_DURATION: 600,
        METRIC_AVERAGE_SESSION_DURATION: 300,
        METRIC_LONGEST_SESSION_DURATION: 400,
        METRIC_SHORTEST_SESSION_DURATION: 100,
        METRIC_FIRST_ACTIVITY_TIME: "08:00:00",
        METRIC_LAST_ACTIVITY_TIME: "09:00:00",
        METRIC_LAST_SESSION_DURATION: 300,
    }
    for metric, value in expected.items():
        sensor = ActivityMetricSensor(runtime, metric, "current_day")
        assert sensor.native_value == value
    assert ActivityMetricSensor(runtime, METRIC_LAST_SESSION_START).native_value
    assert ActivityMetricSensor(runtime, METRIC_LAST_SESSION_END).native_value
    assert (
        ActivityMetricSensor(runtime, METRIC_DAYS_SINCE_LAST_SESSION).native_value == 0
    )
    assert (
        ActivityMetricSensor(runtime, METRIC_CURRENT_SESSION_DURATION).native_value
        >= 30
    )


def test_metric_availability_weekday_and_application_values() -> None:
    runtime = _runtime()
    runtime.period_availability = lambda _period: (
        False,
        {"reason": "retention_limit"},
    )
    rolling = ActivityMetricSensor(runtime, METRIC_TOTAL_DURATION, "rolling_days:91")
    assert rolling.available is False
    assert rolling.extra_state_attributes["reason"] == "retention_limit"
    weekday = ActivityMetricSensor(runtime, METRIC_WEEKDAY_MAX)
    assert weekday.native_value == datetime.now().astimezone().strftime("%A").lower()
    current = CurrentApplicationSensor(runtime)
    assert current.native_value == "Application"
    runtime.session = None
    assert current.native_value is None
    assert _metric_name(METRIC_TOTAL_DURATION, "rolling_days:35").endswith("Last 35")
    assert _metric_icon(METRIC_SESSION_COUNT) == "mdi:counter"


def test_duration_sensors_convert_only_their_presentation_values() -> None:
    runtime = _runtime()
    runtime.entry.options[OPT_DURATION_UNIT] = "h"

    total = ActivityMetricSensor(runtime, METRIC_TOTAL_DURATION, "current_day")
    latest = ActivityMetricSensor(runtime, METRIC_LAST_SESSION_DURATION)

    assert total.native_value == 600 / 3600
    assert latest.native_value == 300 / 3600
    assert total.native_unit_of_measurement == "h"
    assert total.extra_state_attributes["formatted"] == "10min 0s"
