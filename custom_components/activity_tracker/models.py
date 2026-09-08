"""Pure activity accounting models and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Any


@dataclass
class DailySummary:
    """Compact aggregate for one local calendar date."""

    total_seconds: float = 0
    sessions_started: int = 0
    continued_sessions: int = 0
    longest_session_seconds: float = 0
    shortest_session_seconds: float | None = None
    exact_seconds: float = 0
    unknown_seconds: float = 0
    first_active_at: str | None = None
    last_inactive_at: str | None = None
    complete: bool = True
    rule_version: int = 1
    applications: dict[str, dict[str, Any]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Serialize the summary."""
        return {
            "total_seconds": self.total_seconds,
            "sessions_started": self.sessions_started,
            "continued_sessions": self.continued_sessions,
            "longest_session_seconds": self.longest_session_seconds,
            "shortest_session_seconds": self.shortest_session_seconds,
            "exact_seconds": self.exact_seconds,
            "unknown_seconds": self.unknown_seconds,
            "first_active_at": self.first_active_at,
            "last_inactive_at": self.last_inactive_at,
            "complete": self.complete,
            "rule_version": self.rule_version,
            "applications": self.applications,
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
            "unknown_seconds",
        ):
            raw = value.get(key, 0)
            setattr(summary, key, float(raw) if isinstance(raw, (int, float)) else 0)
        for key in ("sessions_started", "continued_sessions", "rule_version"):
            raw = value.get(key, 1 if key == "rule_version" else 0)
            setattr(summary, key, int(raw) if isinstance(raw, int) else 0)
        shortest = value.get("shortest_session_seconds")
        summary.shortest_session_seconds = (
            float(shortest) if isinstance(shortest, (int, float)) else None
        )
        for key in ("first_active_at", "last_inactive_at"):
            raw = value.get(key)
            setattr(summary, key, raw if isinstance(raw, str) else None)
        summary.complete = value.get("complete") is not False
        summary.applications = (
            value.get("applications")
            if isinstance(value.get("applications"), dict)
            else {}
        )
        return summary


@dataclass
class Session:
    """In-memory/persisted checkpoint for one logical activity session."""

    started_at: datetime
    last_observed_at: datetime
    application_id: str | None = None
    application_label: str | None = None
    paused_at: datetime | None = None
    state: str = "active"
    active_segment_started_at: datetime | None = None
    active_seconds: float = 0
    pending_days: dict[str, dict[str, Any]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "last_observed_at": self.last_observed_at.isoformat(),
            "application_id": self.application_id,
            "application_label": self.application_label,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "state": self.state,
            "active_segment_started_at": (
                self.active_segment_started_at.isoformat()
                if self.active_segment_started_at
                else None
            ),
            "active_seconds": self.active_seconds,
            "pending_days": self.pending_days,
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
