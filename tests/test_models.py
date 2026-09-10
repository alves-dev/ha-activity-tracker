"""Tests for pure activity accounting behavior."""

from __future__ import annotations

from datetime import datetime, timedelta

from custom_components.activity_tracker.accounting import commit_session
from custom_components.activity_tracker.models import (
    DailySummary,
    attribute_session,
    average_time_of_day,
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
    )
    summary.add_start_time(
        datetime(2026, 9, 8, 23, 59, tzinfo=datetime.now().astimezone().tzinfo)
    )

    restored = DailySummary.from_dict(summary.as_dict())

    assert restored.total_seconds == 4500
    assert restored.sessions_started == 2
    assert restored.shortest_session_seconds == 300
    assert restored.start_time_count == 1


def test_format_duration_returns_concise_display() -> None:
    assert format_duration(4500) == "1h 15min"
    assert format_duration(59) == "59s"


def test_attribute_session_uses_selected_cross_midnight_policy() -> None:
    tz = datetime.now().astimezone().tzinfo
    start = datetime(2026, 9, 8, 23, 30, tzinfo=tz)
    end = datetime(2026, 9, 9, 1, 30, tzinfo=tz)

    assert attribute_session(start, end, "started_day") == [("2026-09-08", 7200)]
    assert attribute_session(start, end, "ended_day") == [("2026-09-09", 7200)]
    assert attribute_session(start, end, "split_at_midnight") == [
        ("2026-09-08", 1800),
        ("2026-09-09", 5400),
    ]


def test_daily_summary_circular_start_and_end_averages_wrap_midnight() -> None:
    tz = datetime.now().astimezone().tzinfo
    summary = DailySummary()
    summary.add_start_time(datetime(2026, 9, 8, 23, 59, tzinfo=tz))
    summary.add_start_time(datetime(2026, 9, 9, 0, 1, tzinfo=tz))
    summary.add_end_time(datetime(2026, 9, 9, 6, 0, tzinfo=tz))

    restored = DailySummary.from_dict(summary.as_dict())

    assert (
        average_time_of_day(
            restored.start_time_sin,
            restored.start_time_cos,
            restored.start_time_count,
        )
        == "00:00"
    )
    assert (
        average_time_of_day(
            restored.end_time_sin,
            restored.end_time_cos,
            restored.end_time_count,
        )
        == "06:00"
    )


def test_commit_session_keeps_timings_on_actual_dates_and_split_allocations() -> None:
    tz = datetime.now().astimezone().tzinfo
    start = datetime(2026, 9, 8, 23, 30, tzinfo=tz)
    end = datetime(2026, 9, 9, 1, 30, tzinfo=tz)
    summaries: dict[str, object] = {}

    duration = commit_session(summaries, start, end, "split_at_midnight")
    first = DailySummary.from_dict(summaries["2026-09-08"])
    second = DailySummary.from_dict(summaries["2026-09-09"])

    assert duration == 7200
    assert first.total_seconds == 1800
    assert second.total_seconds == 5400
    assert first.sessions_started == second.sessions_started == 1
    assert first.start_time_count == 1
    assert second.end_time_count == 1
