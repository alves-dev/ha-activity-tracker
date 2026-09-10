"""Pure evaluation for unified activity rules."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any

STATE_UNAVAILABLE = "unavailable"
STATE_UNKNOWN = "unknown"

GROUP_ALL = "all"
GROUP_ANY = "any"
CONDITION_STATE = "state"
CONDITION_REPORT_SILENCE = "report_silence"


def referenced_entity_ids(expression: Mapping[str, Any]) -> set[str]:
    """Return every entity used by a valid expression."""
    if _group_children(expression) is not None:
        return set().union(
            *(referenced_entity_ids(child) for child in _group_children(expression))
        )
    entity_id = expression.get("entity_id")
    return {entity_id} if isinstance(entity_id, str) else set()


def expression_matches(
    expression: Mapping[str, Any], states: Mapping[str, Any], now: datetime
) -> bool:
    """Return whether an expression is true from the observed source states."""
    children = _group_children(expression)
    if children is not None:
        if expression.get("operator") == GROUP_ALL:
            return bool(children) and all(
                expression_matches(child, states, now) for child in children
            )
        return any(expression_matches(child, states, now) for child in children)
    return _condition_matches(expression, states, now)


def expression_next_deadline(  # noqa: PLR0911
    expression: Mapping[str, Any], states: Mapping[str, Any], now: datetime
) -> datetime | None:
    """Return the earliest future instant at which a leaf may become true."""
    children = _group_children(expression)
    if children is not None:
        deadlines = [
            deadline
            for child in children
            if (deadline := expression_next_deadline(child, states, now)) is not None
        ]
        return min(deadlines, default=None)

    entity_id = expression.get("entity_id")
    if not isinstance(entity_id, str):
        return None
    state = states.get(entity_id)
    if state is None:
        return None
    seconds = _positive_seconds(expression.get("for_seconds"))
    if seconds == 0:
        return None
    if expression.get("type") == CONDITION_REPORT_SILENCE:
        reported_at = _reported_at(state)
        if reported_at is None:
            return None
        deadline = reported_at + timedelta(seconds=seconds)
        return deadline if deadline > now else None
    if expression.get("type") != CONDITION_STATE or not _state_value_matches(
        expression, str(getattr(state, "state", ""))
    ):
        return None
    changed_at = _changed_at(state)
    if changed_at is None:
        return None
    deadline = changed_at + timedelta(seconds=seconds)
    return deadline if deadline > now else None


def _group_children(expression: Mapping[str, Any]) -> list[Mapping[str, Any]] | None:
    children = expression.get("conditions")
    if not isinstance(children, list):
        return None
    return [child for child in children if isinstance(child, Mapping)]


def _condition_matches(  # noqa: PLR0911
    condition: Mapping[str, Any], states: Mapping[str, Any], now: datetime
) -> bool:
    entity_id = condition.get("entity_id")
    if not isinstance(entity_id, str):
        return False
    state = states.get(entity_id)
    if state is None:
        return False
    if condition.get("type") == CONDITION_REPORT_SILENCE:
        reported_at = _reported_at(state)
        seconds = _positive_seconds(condition.get("for_seconds"))
        return (
            reported_at is not None
            and seconds > 0
            and now >= reported_at + timedelta(seconds=seconds)
        )
    if condition.get("type") != CONDITION_STATE:
        return False
    if not _state_value_matches(condition, str(getattr(state, "state", ""))):
        return False
    seconds = _positive_seconds(condition.get("for_seconds"))
    if seconds == 0:
        return True
    changed_at = _changed_at(state)
    return changed_at is not None and now >= changed_at + timedelta(seconds=seconds)


def _state_value_matches(condition: Mapping[str, Any], value: str) -> bool:
    values = condition.get("states")
    if not isinstance(values, list) or not all(
        isinstance(item, str) for item in values
    ):
        return False
    matches = value in values
    return not matches if condition.get("operator") == "not_equals" else matches


def _positive_seconds(value: object) -> int:
    return value if isinstance(value, int) and value > 0 else 0


def _changed_at(state: Any) -> datetime | None:
    changed_at = getattr(state, "last_changed", None)
    return changed_at if isinstance(changed_at, datetime) else None


def _reported_at(state: Any) -> datetime | None:
    reported_at = getattr(state, "last_reported", None)
    if isinstance(reported_at, datetime):
        return reported_at
    return _changed_at(state)
