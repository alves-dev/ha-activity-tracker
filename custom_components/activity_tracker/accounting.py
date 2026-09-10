"""Compact daily accounting for completed unified-rule sessions."""

from __future__ import annotations

from collections.abc import MutableMapping
from datetime import datetime
from typing import Any

from .models import DailySummary, attribute_session


def commit_session(
    summaries: MutableMapping[str, Any],
    started_at: datetime,
    ended_at: datetime,
    cross_midnight_policy: str,
) -> float:
    """Commit one completed session and return its logical duration in seconds."""
    duration = max(0.0, (ended_at - started_at).total_seconds())
    if duration == 0:
        return 0
    allocations = attribute_session(started_at, ended_at, cross_midnight_policy)
    for date, seconds in allocations:
        summary = DailySummary.from_dict(summaries.get(date))
        summary.total_seconds += seconds
        summary.exact_seconds += seconds
        summary.sessions_started += 1
        summary.longest_session_seconds = max(summary.longest_session_seconds, seconds)
        summary.shortest_session_seconds = (
            seconds
            if summary.shortest_session_seconds is None
            else min(summary.shortest_session_seconds, seconds)
        )
        summaries[date] = summary.as_dict()

    _add_timing_sample(summaries, started_at, "start")
    _add_timing_sample(summaries, ended_at, "end")
    return duration


def _add_timing_sample(
    summaries: MutableMapping[str, Any], when: datetime, kind: str
) -> None:
    date = when.date().isoformat()
    summary = DailySummary.from_dict(summaries.get(date))
    if kind == "start":
        summary.add_start_time(when)
    else:
        summary.add_end_time(when)
    summaries[date] = summary.as_dict()
