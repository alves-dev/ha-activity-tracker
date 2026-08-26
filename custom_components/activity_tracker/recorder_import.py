"""Rebuild compact activity summaries from Home Assistant Recorder history."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from homeassistant.components.recorder import history
from homeassistant.core import HomeAssistant, State

Classifier = Callable[[State], tuple[bool, str | None, str | None]]


async def async_get_sessions(
    hass: HomeAssistant,
    entity_id: str,
    start: datetime,
    end: datetime,
    classify: Classifier,
) -> list[tuple[datetime, datetime, str | None, str | None]]:
    """Return closed activity intervals reconstructed from Recorder states."""
    states_by_entity = await hass.async_add_executor_job(
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
    states = states_by_entity.get(entity_id.lower(), [])
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
