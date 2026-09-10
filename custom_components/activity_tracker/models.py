"""Pure activity accounting models and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from math import atan2, cos, pi, sin
from typing import Any


@dataclass
class DailySummary:
    """Compact aggregate for one local calendar date."""

    total_seconds: float = 0
    sessions_started: int = 0
    longest_session_seconds: float = 0
    shortest_session_seconds: float | None = None
    exact_seconds: float = 0
    start_time_sin: float = 0
    start_time_cos: float = 0
    start_time_count: int = 0
    end_time_sin: float = 0
    end_time_cos: float = 0
    end_time_count: int = 0

    def as_dict(self) -> dict[str, Any]:
        """Serialize the summary."""
        return {
            "total_seconds": self.total_seconds,
            "sessions_started": self.sessions_started,
            "longest_session_seconds": self.longest_session_seconds,
            "shortest_session_seconds": self.shortest_session_seconds,
            "exact_seconds": self.exact_seconds,
            "start_time_sin": self.start_time_sin,
            "start_time_cos": self.start_time_cos,
            "start_time_count": self.start_time_count,
            "end_time_sin": self.end_time_sin,
            "end_time_cos": self.end_time_cos,
            "end_time_count": self.end_time_count,
        }

    @classmethod
    def from_dict(cls, value: object) -> DailySummary:
        """Safely deserialize a persisted summary."""
        if not isinstance(value, dict):
            return cls()
        summary = cls()
        for key in (
            "total_seconds",
            "longest_session_seconds",
            "exact_seconds",
            "start_time_sin",
            "start_time_cos",
            "end_time_sin",
            "end_time_cos",
        ):
            raw = value.get(key, 0)
            setattr(summary, key, float(raw) if isinstance(raw, (int, float)) else 0)
        for key in (
            "sessions_started",
            "start_time_count",
            "end_time_count",
        ):
            raw = value.get(key, 0)
            setattr(summary, key, int(raw) if isinstance(raw, int) else 0)
        shortest = value.get("shortest_session_seconds")
        summary.shortest_session_seconds = (
            float(shortest) if isinstance(shortest, (int, float)) else None
        )
        return summary

    def add_start_time(self, when: datetime) -> None:
        """Add one actual local session-start time to the circular aggregate."""
        sine, cosine = _time_components(when)
        self.start_time_sin += sine
        self.start_time_cos += cosine
        self.start_time_count += 1

    def add_end_time(self, when: datetime) -> None:
        """Add one actual local session-end time to the circular aggregate."""
        sine, cosine = _time_components(when)
        self.end_time_sin += sine
        self.end_time_cos += cosine
        self.end_time_count += 1


@dataclass
class Session:
    """In-memory/persisted checkpoint for one logical activity session."""

    started_at: datetime
    last_observed_at: datetime

    def as_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "last_observed_at": self.last_observed_at.isoformat(),
        }


def split_interval(
    start: datetime, end: datetime
) -> list[tuple[str, datetime, datetime]]:
    """Split a local-time interval at calendar-midnight boundaries."""
    if end <= start:
        return []
    parts: list[tuple[str, datetime, datetime]] = []
    cursor = start
    while cursor.date() < end.date():
        midnight = datetime.combine(
            cursor.date() + timedelta(days=1), time.min, cursor.tzinfo
        )
        parts.append((cursor.date().isoformat(), cursor, midnight))
        cursor = midnight
    parts.append((cursor.date().isoformat(), cursor, end))
    return parts


def attribute_session(
    start: datetime, end: datetime, policy: str
) -> list[tuple[str, float]]:
    """Return local-day duration allocations for one completed logical session."""
    if end <= start:
        return []
    duration = (end - start).total_seconds()
    if policy == "started_day":
        return [(start.date().isoformat(), duration)]
    if policy == "ended_day":
        return [(end.date().isoformat(), duration)]
    return [
        (date, (part_end - part_start).total_seconds())
        for date, part_start, part_end in split_interval(start, end)
    ]


def average_time_of_day(sine: float, cosine: float, count: int) -> str | None:
    """Return a circular local-time average in compact ``HH:MM`` form."""
    if count <= 0 or (sine == 0 and cosine == 0):
        return None
    radians = atan2(sine, cosine) % (2 * pi)
    seconds = round(radians * 86_400 / (2 * pi)) % 86_400
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}"


def _time_components(when: datetime) -> tuple[float, float]:
    seconds = (
        when.hour * 3600 + when.minute * 60 + when.second + when.microsecond / 1_000_000
    )
    radians = seconds * 2 * pi / 86_400
    return sin(radians), cos(radians)


def format_duration(seconds: float | int | None) -> str | None:
    """Return a compact human-readable duration."""
    if seconds is None:
        return None
    total = max(0, round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}min"
    if minutes:
        return f"{minutes}min {seconds}s"
    return f"{seconds}s"
