"""Admin-only sidebar workbench and safe draft-editor transport."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.frontend import async_panel_exists
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .const import CONF_RULE, DOMAIN, INTEGRATION_VERSION, update_signal
from .panel_editor import (
    DraftValidationError,
    async_apply_draft,
    draft_preview,
    entry_draft,
    new_draft,
)
from .rules import (
    expression_matches,
    expression_next_deadline,
    referenced_entity_ids,
)

_PANEL_PATH = "activity-rules"
_STATIC_PATH = "/activity_tracker_panel"
_PANEL_ELEMENT = "activity-rules-panel"
_PANEL_REGISTERED = f"{DOMAIN}_panel_registered"
_WEBSOCKET_SUBSCRIBE = f"{DOMAIN}/rules/subscribe"
_WEBSOCKET_EDITOR_OPEN = f"{DOMAIN}/editor/open"
_WEBSOCKET_EDITOR_VALIDATE = f"{DOMAIN}/editor/validate"
_WEBSOCKET_EDITOR_APPLY = f"{DOMAIN}/editor/apply"
_PANEL_ASSET_REVISION = "7"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Serve and register the admin-only custom panel once per Home Assistant."""
    if hass.data.get(_PANEL_REGISTERED) or async_panel_exists(hass, _PANEL_PATH):
        return
    frontend_path = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(_STATIC_PATH, str(frontend_path), cache_headers=False)]
    )
    websocket_api.async_register_command(hass, websocket_subscribe)
    websocket_api.async_register_command(hass, websocket_editor_open)
    websocket_api.async_register_command(hass, websocket_editor_validate)
    websocket_api.async_register_command(hass, websocket_editor_apply)
    await panel_custom.async_register_panel(
        hass=hass,
        frontend_url_path=_PANEL_PATH,
        webcomponent_name=_PANEL_ELEMENT,
        sidebar_title="Activity Rules",
        sidebar_icon="mdi:clock-outline",
        module_url=(
            f"{_STATIC_PATH}/activity-rules-panel.js?"
            f"v={INTEGRATION_VERSION}-{_PANEL_ASSET_REVISION}"
        ),
        require_admin=True,
    )
    hass.data[_PANEL_REGISTERED] = True


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): _WEBSOCKET_SUBSCRIBE})
def websocket_subscribe(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Stream live, admin-only rule snapshots to the sidebar panel."""

    @callback
    def send_snapshot() -> None:
        connection.send_event(msg["id"], {"monitors": _monitor_snapshots(hass)})

    unsubscribers = [
        async_dispatcher_connect(hass, update_signal(entry.entry_id), send_snapshot)
        for entry in hass.config_entries.async_entries(DOMAIN)
    ]

    @callback
    def unsubscribe() -> None:
        for unsub in unsubscribers:
            unsub()

    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"])
    send_snapshot()


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): _WEBSOCKET_EDITOR_OPEN,
        vol.Optional("entry_id"): str,
    }
)
@websocket_api.async_response
async def websocket_editor_open(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Open a new or existing entry as an unsaved browser draft."""
    entry = _entry(hass, msg.get("entry_id"))
    if msg.get("entry_id") and entry is None:
        connection.send_error(msg["id"], "not_found", "Activity was not found")
        return
    connection.send_result(
        msg["id"], {"draft": entry_draft(entry) if entry else new_draft()}
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): _WEBSOCKET_EDITOR_VALIDATE,
        vol.Required("draft"): dict,
        vol.Optional("entry_id"): str,
    }
)
@websocket_api.async_response
async def websocket_editor_validate(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Validate, preview, and diff a draft without writing configuration."""
    entry = _entry(hass, msg.get("entry_id"))
    if msg.get("entry_id") and entry is None:
        connection.send_error(msg["id"], "not_found", "Activity was not found")
        return
    try:
        result = draft_preview(hass, msg["draft"], entry)
    except DraftValidationError as error:
        connection.send_result(msg["id"], {"valid": False, "errors": error.errors})
        return
    connection.send_result(msg["id"], {"valid": True, **result})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): _WEBSOCKET_EDITOR_APPLY,
        vol.Required("draft"): dict,
        vol.Optional("entry_id"): str,
        vol.Optional("confirm_history_clear", default=False): bool,
    }
)
@websocket_api.async_response
async def websocket_editor_apply(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Persist a validated draft; history clearing is explicitly server-gated."""
    entry = _entry(hass, msg.get("entry_id"))
    if msg.get("entry_id") and entry is None:
        connection.send_error(msg["id"], "not_found", "Activity was not found")
        return
    try:
        result = await async_apply_draft(
            hass, msg["draft"], entry, msg["confirm_history_clear"]
        )
    except DraftValidationError as error:
        connection.send_result(msg["id"], {"applied": False, "errors": error.errors})
        return
    connection.send_result(msg["id"], result)


def _entry(hass: HomeAssistant, entry_id: object):
    """Return an Activity Tracker entry only; never trust an arbitrary ID."""
    if not isinstance(entry_id, str):
        return None
    return next(
        (
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.entry_id == entry_id
        ),
        None,
    )


def _monitor_snapshots(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Build a frontend-safe, current view of every configured monitor rule."""
    now = dt_util.now()
    runtimes = hass.data.get(DOMAIN, {})
    snapshots = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        rule = entry.data.get(CONF_RULE, {})
        if not isinstance(rule, Mapping):
            rule = {}
        runtime = runtimes.get(entry.entry_id)
        template_results = getattr(runtime, "_template_results", {})
        template_results = (
            template_results if isinstance(template_results, Mapping) else {}
        )
        entity_ids = referenced_entity_ids(rule.get("start_when", {}))
        entity_ids |= referenced_entity_ids(rule.get("stop_when", {}))
        states = {
            entity_id: state
            for entity_id in entity_ids
            if (state := hass.states.get(entity_id)) is not None
        }
        snapshots.append(
            {
                "entry_id": entry.entry_id,
                "name": entry.title,
                "active": bool(getattr(runtime, "session", None)),
                "template": entry.data.get("template", "custom"),
                "start": _expression_snapshot(
                    rule.get("start_when", {}), states, now, template_results
                ),
                "stop": _expression_snapshot(
                    rule.get("stop_when", {}), states, now, template_results
                ),
            }
        )
    return snapshots


def _expression_snapshot(
    expression: object,
    states: Mapping[str, Any],
    now,
    template_results: Mapping[str, bool],
) -> dict[str, Any]:
    """Return a recursive expression and leaf-state inspection snapshot."""
    if not isinstance(expression, Mapping):
        return {"operator": "any", "conditions": [], "matched": False}
    children = expression.get("conditions")
    if isinstance(children, list):
        return {
            "operator": expression.get("operator", "any"),
            "matched": expression_matches(expression, states, now, template_results),
            "conditions": [
                _expression_snapshot(child, states, now, template_results)
                for child in children
                if isinstance(child, Mapping)
            ],
        }
    entity_id = expression.get("entity_id")
    state = states.get(entity_id) if isinstance(entity_id, str) else None
    deadline = expression_next_deadline(expression, states, now)
    value_template = expression.get("value_template")
    attribute = expression.get("attribute")
    attributes = getattr(state, "attributes", {})
    current_value = (
        attributes.get(attribute)
        if isinstance(attribute, str) and isinstance(attributes, Mapping)
        else getattr(state, "state", None)
    )
    template_result = (
        template_results.get(value_template)
        if isinstance(value_template, str)
        else None
    )
    return {
        "type": expression.get("type", "unknown"),
        "entity_id": entity_id,
        "states": expression.get("states", []),
        "operator": expression.get("operator", "equals"),
        "for_seconds": expression.get("for_seconds", 0),
        "value_template": value_template,
        "current_state": getattr(state, "state", None),
        "current_value": current_value,
        "template_result": template_result,
        "deadline": deadline.isoformat() if deadline else None,
        "matched": expression_matches(expression, states, now, template_results),
    }
