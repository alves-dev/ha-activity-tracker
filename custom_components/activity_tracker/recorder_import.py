"""Rebuild compact activity summaries from Home Assistant Recorder history."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.recorder import history
from homeassistant.core import HomeAssistant, State

Classifier = Callable[[State], tuple[bool, str | None, str | None]]
SessionInterval = tuple[datetime, str | None, str | None]
ClosedSession = tuple[datetime, datetime, str | None, str | None]


@dataclass(frozen=True)
class RecorderImport:
    """Recorder reconstruction plus the range actually evidenced by Recorder."""

    sessions: list[ClosedSession]
    start: datetime | None
    end: datetime


async def async_get_sessions(
    hass: HomeAssistant,
    entity_id: str,
    start: datetime,
    end: datetime,
    classify: Classifier,
) -> list[ClosedSession]:
    """Return closed activity intervals reconstructed from Recorder states."""
    result = await async_get_import(hass, entity_id, start, end, classify)
    return result.sessions


async def async_get_import(
    hass: HomeAssistant,
    entity_id: str,
    start: datetime,
    end: datetime,
    classify: Classifier,
) -> RecorderImport:
    """Return sessions and the Recorder window that can safely be replaced."""
    states_by_entity = await _async_get_states(
        hass, entity_id, start, end
    )
    states = states_by_entity.get(entity_id.lower(), [])
    if not states:
        return RecorderImport([], None, end)
    return RecorderImport(
        _sessions_from_states(states, start, end, classify),
        max(start, states[0].last_changed),
        end,
    )


async def _async_get_states(
    hass: HomeAssistant, entity_id: str, start: datetime, end: datetime
) -> dict[str, list[State]]:
    """Query Recorder without blocking Home Assistant's event loop."""
    return await hass.async_add_executor_job(
        history.state_changes_during_period,
        hass,
        start,
        end,
        entity_id,
        False,
        False,
        None,
        True,
    )


def _sessions_from_states(
    states: list[State],
    start: datetime,
    end: datetime,
    classify: Classifier,
) -> list[ClosedSession]:
    """Turn ordered state changes into closed activity intervals."""
    active: SessionInterval | None = None
    sessions: list[ClosedSession] = []

    for state in states:
        observed_at = max(start, state.last_changed)
        active = _apply_state(active, observed_at, classify(state), sessions)

    _close_session(active, end, sessions)
    return sessions


def _apply_state(
    active: SessionInterval | None,
    observed_at: datetime,
    classification: tuple[bool, str | None, str | None],
    sessions: list[ClosedSession],
) -> SessionInterval | None:
    """Apply one Recorder state to the open reconstructed interval."""
    is_active, app_id, app_label = classification
    if not is_active:
        _close_session(active, observed_at, sessions)
        return None
    if active is None:
        return observed_at, app_id, app_label
    if app_id is not None and app_id != active[1]:
        _close_session(active, observed_at, sessions)
        return observed_at, app_id, app_label
    return active


def _close_session(
    active: SessionInterval | None, ended_at: datetime, sessions: list[ClosedSession]
) -> None:
    """Append an interval only when its end follows its start."""
    if active is not None and ended_at > active[0]:
        sessions.append((active[0], ended_at, active[1], active[2]))
