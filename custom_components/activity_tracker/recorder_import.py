"""Rebuild compact activity summaries from Home Assistant Recorder history."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.recorder import history
from homeassistant.core import HomeAssistant, State

Classifier = Callable[[State], tuple[bool, str | None, str | None]]


@dataclass(frozen=True)
class RecorderImport:
    """Recorder reconstruction plus the range actually evidenced by Recorder."""

    sessions: list[tuple[datetime, datetime, str | None, str | None]]
    start: datetime | None
    end: datetime


async def async_get_sessions(
    hass: HomeAssistant,
    entity_id: str,
    start: datetime,
    end: datetime,
    classify: Classifier,
) -> list[tuple[datetime, datetime, str | None, str | None]]:
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
) -> list[tuple[datetime, datetime, str | None, str | None]]:
    """Turn ordered state changes into closed activity intervals."""
    active_since: datetime | None = None
    active_id: str | None = None
    active_label: str | None = None
    sessions: list[tuple[datetime, datetime, str | None, str | None]] = []

    for state in states:
        observed_at = max(start, state.last_changed)
        is_active, app_id, app_label = classify(state)
        if not is_active:
            if active_since is not None and observed_at > active_since:
                sessions.append((active_since, observed_at, active_id, active_label))
            active_since = active_id = active_label = None
            continue
        if active_since is None:
            active_since, active_id, active_label = observed_at, app_id, app_label
        elif app_id is not None and app_id != active_id:
            if observed_at > active_since:
                sessions.append((active_since, observed_at, active_id, active_label))
            active_since, active_id, active_label = observed_at, app_id, app_label

    if active_since is not None and end > active_since:
        sessions.append((active_since, end, active_id, active_label))
    return sessions
