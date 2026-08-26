"""Tests for pure activity accounting behavior."""

from __future__ import annotations

from datetime import datetime, timedelta

from custom_components.activity_tracker.models import (
    DailySummary,
    format_duration,
    split_interval,
)


def test_split_interval_splits_duration_at_local_midnight() -> None:
    tz = datetime.now().astimezone().tzinfo
    start = datetime(2026, 8, 24, 23, 30, tzinfo=tz)
    end = datetime(2026, 8, 25, 1, 30, tzinfo=tz)

    parts = split_interval(start, end)

    assert [date for date, _, _ in parts] == ["2026-08-24", "2026-08-25"]
    assert (parts[0][2] - parts[0][1]) == timedelta(minutes=30)
    assert (parts[1][2] - parts[1][1]) == timedelta(minutes=90)


def test_daily_summary_round_trip_preserves_aggregate_fields() -> None:
    summary = DailySummary(
        total_seconds=4500,
        sessions_started=2,
        shortest_session_seconds=300,
        applications={"com.example.app": {"total_seconds": 4500}},
    )

    restored = DailySummary.from_dict(summary.as_dict())

    assert restored.total_seconds == 4500
    assert restored.sessions_started == 2
    assert restored.shortest_session_seconds == 300
    assert restored.applications["com.example.app"]["total_seconds"] == 4500


def test_format_duration_returns_concise_display() -> None:
    assert format_duration(4500) == "1h 15min"
    assert format_duration(59) == "59s"
