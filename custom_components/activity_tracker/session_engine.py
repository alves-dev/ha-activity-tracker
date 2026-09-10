"""Pure lifecycle engine for one unified activity rule."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .rules import (
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    expression_matches,
    expression_next_deadline,
)


@dataclass(frozen=True)
class SessionTransition:
    """A session lifecycle change produced from an observed rule evaluation."""

    action: str
    occurred_at: datetime
    accounting_ended_at: datetime | None = None


class UnifiedSessionEngine:
    """Open and close one activity session from start and stop expressions."""

    def __init__(self, rule: Mapping[str, Any]) -> None:
        self._start_when = _expression(rule.get("start_when"))
        self._stop_when = _expression(rule.get("stop_when"))
        self.started_at: datetime | None = None

    @property
    def is_running(self) -> bool:
        """Return whether the engine currently has an open session."""
        return self.started_at is not None

    def process(
        self,
        states: Mapping[str, Any],
        now: datetime,
        template_results: Mapping[str, bool] | None = None,
    ) -> SessionTransition | None:
        """Evaluate one observed state snapshot and return at most one transition."""
        if self.started_at is not None:
            if expression_matches(self._stop_when, states, now, template_results):
                ended_at = (
                    _unavailable_anchor(self._stop_when, states, now, template_results)
                    or now
                )
                ended_at = max(ended_at, self.started_at)
                self.started_at = None
                return SessionTransition("stopped", now, ended_at)
            return None
        if expression_matches(self._start_when, states, now, template_results):
            self.started_at = now
            return SessionTransition("started", now)
        return None

    def next_deadline(
        self, states: Mapping[str, Any], now: datetime
    ) -> datetime | None:
        """Return the next relevant start or stop-condition deadline."""
        expressions = (
            (self._stop_when,) if self.started_at is not None else (self._start_when,)
        )
        deadlines = [
            deadline
            for expression in expressions
            if (deadline := expression_next_deadline(expression, states, now))
            is not None
        ]
        return min(deadlines, default=None)


def _expression(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _unavailable_anchor(
    expression: Mapping[str, Any],
    states: Mapping[str, Any],
    now: datetime,
    template_results: Mapping[str, bool] | None = None,
) -> datetime | None:
    """Return an unavailable condition's first observation when it ended a rule."""
    children = expression.get("conditions")
    if isinstance(children, list):
        anchors = [
            anchor
            for child in children
            if isinstance(child, Mapping)
            and (anchor := _unavailable_anchor(child, states, now, template_results))
            is not None
        ]
        return min(anchors, default=None)
    values = expression.get("states")
    entity_id = expression.get("entity_id")
    if (
        expression.get("type") != "state"
        or not isinstance(values, list)
        or not {STATE_UNAVAILABLE, STATE_UNKNOWN}.intersection(values)
        or not isinstance(entity_id, str)
        or not expression_matches(expression, states, now, template_results)
    ):
        return None
    state = states.get(entity_id)
    changed_at = getattr(state, "last_changed", None)
    if not isinstance(changed_at, datetime):
        return None
    return changed_at.astimezone(now.tzinfo)
