"""Server-owned validation and persistence contract for the sidebar draft."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any

from homeassistant.config_entries import SOURCE_USER, ConfigEntry
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import Template, result_as_boolean
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ENABLED_METRICS,
    CONF_NAME,
    CONF_PERIOD_METRICS,
    CONF_RULE,
    CONF_TEMPLATE,
    CROSS_MIDNIGHT_POLICIES,
    DEFAULT_CROSS_MIDNIGHT_POLICY,
    DEFAULT_DURATION_UNIT,
    DEFAULT_MINIMUM_SESSION_SECONDS,
    DEFAULT_RETENTION_DAYS,
    DOMAIN,
    NON_PERIOD_METRICS,
    OPT_CROSS_MIDNIGHT_POLICY,
    OPT_DURATION_UNIT,
    OPT_MINIMUM_SESSION_SECONDS,
    OPT_RETENTION_DAYS,
    PERIOD_METRICS,
    PERIOD_PREVIOUS_DAY_PREFIX,
)
from .rules import (
    CONDITION_NUMERIC_STATE,
    expression_matches,
    expression_next_deadline,
    referenced_entity_ids,
)

TEMPLATE_CUSTOM = "custom"
TEMPLATE_ZONE = "zone_presence"
TEMPLATE_RULE = "template_rule"
_TEMPLATES = {TEMPLATE_CUSTOM, TEMPLATE_ZONE, TEMPLATE_RULE}
_OPERATORS = {"all", "any"}
_STATE_OPERATORS = {"equals", "not_equals"}
_NUMERIC_OPERATORS = {
    "greater_than",
    "greater_or_equal",
    "less_than",
    "less_or_equal",
    "equals",
    "not_equals",
}
_LEAF_TYPES = {"state", "numeric_state", "report_silence", "template"}


class DraftValidationError(ValueError):
    """A safe, field-oriented validation error for an unsaved panel draft."""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Invalid activity draft")
        self.errors = errors


def entry_draft(entry: Any | None) -> dict[str, Any]:
    """Return a JSON-compatible editable representation of an entry."""
    data = dict(getattr(entry, "data", {}) or {})
    options = dict(getattr(entry, "options", {}) or {})
    draft = {
        "entry_id": getattr(entry, "entry_id", None),
        CONF_NAME: data.get(CONF_NAME, getattr(entry, "title", "")),
        CONF_TEMPLATE: data.get(CONF_TEMPLATE, TEMPLATE_CUSTOM),
        CONF_RULE: data.get(CONF_RULE, _empty_rule()),
        "options": {
            OPT_DURATION_UNIT: options.get(OPT_DURATION_UNIT, DEFAULT_DURATION_UNIT),
            OPT_RETENTION_DAYS: options.get(OPT_RETENTION_DAYS, DEFAULT_RETENTION_DAYS),
            OPT_MINIMUM_SESSION_SECONDS: options.get(
                OPT_MINIMUM_SESSION_SECONDS, DEFAULT_MINIMUM_SESSION_SECONDS
            ),
            OPT_CROSS_MIDNIGHT_POLICY: options.get(
                OPT_CROSS_MIDNIGHT_POLICY, DEFAULT_CROSS_MIDNIGHT_POLICY
            ),
        },
        CONF_PERIOD_METRICS: data.get(CONF_PERIOD_METRICS, {}),
        CONF_ENABLED_METRICS: data.get(CONF_ENABLED_METRICS, []),
    }
    if draft[CONF_TEMPLATE] == TEMPLATE_ZONE:
        start = draft[CONF_RULE].get("start_when", {})
        if isinstance(start, Mapping):
            draft["zone_entity_id"] = start.get("entity_id", "")
            states = start.get("states", [])
            if isinstance(states, list) and len(states) == 1:
                state = states[0]
                draft["zone_id"] = "zone.home" if state == "home" else f"zone.{state}"
    if draft[CONF_TEMPLATE] == TEMPLATE_RULE:
        rule = draft[CONF_RULE]
        draft["start_template"] = _template_value(rule.get("start_when"))
        draft["stop_template"] = _template_value(rule.get("stop_when"))
    return draft


def new_draft() -> dict[str, Any]:
    """Return defaults for a new activity without creating an entry."""
    return entry_draft(None)


def normalize_draft(hass, draft: object) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate a browser draft and return config-entry data and options."""
    if not isinstance(draft, Mapping):
        raise DraftValidationError({"draft": "invalid"})
    errors: dict[str, str] = {}
    name = _string(draft.get(CONF_NAME))
    model = _string(draft.get(CONF_TEMPLATE)) or TEMPLATE_CUSTOM
    if not name:
        errors[CONF_NAME] = "required"
    if model not in _TEMPLATES:
        errors[CONF_TEMPLATE] = "invalid"

    try:
        rule = _normalize_rule(hass, draft, model)
    except DraftValidationError as error:
        errors.update(error.errors)
        rule = _empty_rule()
    try:
        options = _normalize_options(draft.get("options"))
    except DraftValidationError as error:
        errors.update(error.errors)
        options = {}
    try:
        period_metrics = _normalize_period_metrics(draft.get(CONF_PERIOD_METRICS))
    except DraftValidationError as error:
        errors.update(error.errors)
        period_metrics = {}
    enabled_metrics = draft.get(CONF_ENABLED_METRICS, [])
    if not isinstance(enabled_metrics, list) or any(
        metric not in NON_PERIOD_METRICS for metric in enabled_metrics
    ):
        errors[CONF_ENABLED_METRICS] = "invalid"
        enabled_metrics = []
    if errors:
        raise DraftValidationError(errors)
    return (
        {
            CONF_NAME: name,
            CONF_TEMPLATE: model,
            CONF_RULE: rule,
            CONF_PERIOD_METRICS: period_metrics,
            CONF_ENABLED_METRICS: list(dict.fromkeys(enabled_metrics)),
        },
        options,
    )


def draft_preview(hass, draft: object, entry: Any | None = None) -> dict[str, Any]:
    """Validate a draft and make a safe review, diff, and live snapshot."""
    data, options = normalize_draft(hass, draft)
    previous_data = dict(getattr(entry, "data", {}) or {})
    previous_options = dict(getattr(entry, "options", {}) or {})
    clear_history = entry is not None and (
        previous_data.get(CONF_RULE) != data[CONF_RULE]
        or previous_options.get(OPT_CROSS_MIDNIGHT_POLICY)
        != options[OPT_CROSS_MIDNIGHT_POLICY]
    )
    submitted = dict(draft) if isinstance(draft, Mapping) else {}
    return {
        "draft": {**entry_draft(entry), **submitted, **data, "options": options},
        "preview": expression_snapshot(hass, data[CONF_RULE]),
        "template_previews": template_previews(hass, data[CONF_RULE]),
        "changes": _changes(previous_data, previous_options, data, options),
        "requires_history_clear": clear_history,
    }


async def async_apply_draft(
    hass, draft: object, entry: Any | None, confirm_history_clear: bool
) -> dict[str, Any]:
    """Apply a validated draft only after the server-enforced destructive gate."""
    preview = draft_preview(hass, draft, entry)
    if preview["requires_history_clear"] and not confirm_history_clear:
        return {"applied": False, **preview}
    data, options = normalize_draft(hass, draft)
    if entry is not None:
        if preview["requires_history_clear"]:
            runtime = hass.data.get(DOMAIN, {}).get(entry.entry_id)
            if runtime is not None:
                await runtime.async_clear_history()
        hass.config_entries.async_update_entry(
            entry, title=data[CONF_NAME], data=data, options=options
        )
        entry_id = entry.entry_id
    else:
        created = ConfigEntry(
            data=data,
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=1,
            options=options,
            source=SOURCE_USER,
            subentries_data=(),
            title=data[CONF_NAME],
            unique_id=None,
            version=3,
        )
        await hass.config_entries.async_add(created)
        entry_id = created.entry_id
    return {"applied": True, "entry_id": entry_id, **preview}


def expression_snapshot(hass, rule: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate a candidate rule without subscribing or changing runtime state."""
    now = dt_util.now()
    entity_ids = referenced_entity_ids(rule.get("start_when", {}))
    entity_ids |= referenced_entity_ids(rule.get("stop_when", {}))
    states = {
        entity_id: state
        for entity_id in entity_ids
        if (state := hass.states.get(entity_id)) is not None
    }
    template_results = {
        template: result
        for template, result in template_previews(hass, rule).items()
        if isinstance(result, bool)
    }
    return {
        "start": _expression_snapshot(
            rule.get("start_when", {}), states, now, template_results
        ),
        "stop": _expression_snapshot(
            rule.get("stop_when", {}), states, now, template_results
        ),
    }


def template_previews(hass, expression: Mapping[str, Any]) -> dict[str, bool | str]:
    """Render template leaves for an unsaved draft; errors remain non-persistent."""
    previews: dict[str, bool | str] = {}
    templates = _template_values(expression.get("start_when"))
    templates += _template_values(expression.get("stop_when"))
    for template in templates:
        try:
            rendered = Template(template, hass).async_render()
            previews[template] = result_as_boolean(rendered)
        except TemplateError:
            previews[template] = "invalid"
    return previews


def _normalize_rule(hass, draft: Mapping[str, Any], model: str) -> dict[str, Any]:
    if model == TEMPLATE_ZONE:
        entity_id = _string(draft.get("zone_entity_id"))
        zone_id = _string(draft.get("zone_id"))
        if not entity_id or not zone_id:
            raise DraftValidationError(
                {"zone_entity_id": "required", "zone_id": "required"}
            )
        zone = hass.states.get(zone_id)
        zone_value = "home" if zone_id == "zone.home" else getattr(zone, "name", None)
        if not isinstance(zone_value, str):
            zone_value = zone_id.removeprefix("zone.")
        return _zone_rule(entity_id, zone_value)
    if model == TEMPLATE_RULE:
        start = _string(draft.get("start_template"))
        stop = _string(draft.get("stop_template"))
        return {
            "start_when": _template_leaf(hass, start, "start_template"),
            "stop_when": _template_leaf(hass, stop, "stop_template"),
        }
    rule = draft.get(CONF_RULE)
    if not isinstance(rule, Mapping):
        raise DraftValidationError({CONF_RULE: "required"})
    return {
        "start_when": _normalize_expression(hass, rule.get("start_when"), "start"),
        "stop_when": _normalize_expression(hass, rule.get("stop_when"), "stop"),
    }


def _normalize_expression(  # noqa: PLR0912
    hass, value: object, path: str
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise DraftValidationError({path: "required"})
    children = value.get("conditions")
    if isinstance(children, list):
        operator = value.get("operator")
        if operator not in _OPERATORS or not children:
            raise DraftValidationError({path: "invalid_group"})
        return {
            "operator": operator,
            "conditions": [
                _normalize_expression(hass, child, f"{path}.{index}")
                for index, child in enumerate(children)
            ],
        }
    leaf_type = value.get("type")
    if leaf_type not in _LEAF_TYPES:
        raise DraftValidationError({path: "invalid_condition"})
    if leaf_type == "template":
        return _template_leaf(hass, _string(value.get("value_template")), path)
    entity_id = _string(value.get("entity_id"))
    seconds = _nonnegative(value.get("for_seconds"), path)
    if not entity_id:
        raise DraftValidationError({path: "entity_required"})
    if leaf_type == "report_silence":
        return {"type": leaf_type, "entity_id": entity_id, "for_seconds": seconds}
    if leaf_type == CONDITION_NUMERIC_STATE:
        raw_numeric = _string(value.get("value"))
        try:
            parsed_numeric = Decimal(raw_numeric)
        except (InvalidOperation, ValueError) as error:
            raise DraftValidationError({path: "numeric_value_required"}) from error
        if not parsed_numeric.is_finite():
            raise DraftValidationError({path: "numeric_value_required"})
        operator = value.get("operator", "greater_than")
        if operator not in _NUMERIC_OPERATORS:
            raise DraftValidationError({path: "invalid_numeric_operator"})
        return {
            "type": leaf_type,
            "entity_id": entity_id,
            "attribute": _string(value.get("attribute")) or None,
            "operator": operator,
            "value": raw_numeric,
            "for_seconds": seconds,
        }
    states = value.get("states")
    if not isinstance(states, list) or not (
        cleaned := [_string(item) for item in states]
    ):
        raise DraftValidationError({path: "states_required"})
    if not all(cleaned) or value.get("operator", "equals") not in _STATE_OPERATORS:
        raise DraftValidationError({path: "invalid_state"})
    return {
        "type": leaf_type,
        "entity_id": entity_id,
        "states": list(dict.fromkeys(cleaned)),
        "operator": value.get("operator", "equals"),
        "for_seconds": seconds,
    }


def _template_leaf(hass, value: str, path: str) -> dict[str, Any]:
    if not value:
        raise DraftValidationError({path: "template_required"})
    try:
        Template(value, hass).ensure_valid()
    except TemplateError as error:
        raise DraftValidationError({path: "invalid_template"}) from error
    return {"type": "template", "value_template": value}


def _normalize_options(value: object) -> dict[str, Any]:
    value = value if isinstance(value, Mapping) else {}
    unit = value.get(OPT_DURATION_UNIT, DEFAULT_DURATION_UNIT)
    policy = value.get(OPT_CROSS_MIDNIGHT_POLICY, DEFAULT_CROSS_MIDNIGHT_POLICY)
    errors = {}
    if unit not in {"s", "min", "h"}:
        errors[OPT_DURATION_UNIT] = "invalid"
    if policy not in CROSS_MIDNIGHT_POLICIES:
        errors[OPT_CROSS_MIDNIGHT_POLICY] = "invalid"
    retention = _nonnegative(
        value.get(OPT_RETENTION_DAYS, DEFAULT_RETENTION_DAYS), OPT_RETENTION_DAYS
    )
    minimum = _nonnegative(
        value.get(OPT_MINIMUM_SESSION_SECONDS, DEFAULT_MINIMUM_SESSION_SECONDS),
        OPT_MINIMUM_SESSION_SECONDS,
    )
    if retention < 1:
        errors[OPT_RETENTION_DAYS] = "minimum_one"
    if errors:
        raise DraftValidationError(errors)
    return {
        OPT_DURATION_UNIT: unit,
        OPT_RETENTION_DAYS: retention,
        OPT_MINIMUM_SESSION_SECONDS: minimum,
        OPT_CROSS_MIDNIGHT_POLICY: policy,
    }


def _normalize_period_metrics(value: object) -> dict[str, list[str]]:
    if not isinstance(value, Mapping) or not value:
        raise DraftValidationError({CONF_PERIOD_METRICS: "required"})
    normalized: dict[str, list[str]] = {}
    for period, metrics in value.items():
        if not _valid_period(period):
            raise DraftValidationError({CONF_PERIOD_METRICS: "invalid_period"})
        if (
            not isinstance(metrics, list)
            or not metrics
            or any(metric not in PERIOD_METRICS for metric in metrics)
        ):
            raise DraftValidationError({CONF_PERIOD_METRICS: "metrics_required"})
        normalized[period] = list(dict.fromkeys(metrics))
    return normalized


def _valid_period(value: object) -> bool:
    if value in {"current_day", "current_week", "current_month"}:
        return True
    if not isinstance(value, str) or not value.startswith(PERIOD_PREVIOUS_DAY_PREFIX):
        return False
    return (
        value.removeprefix(PERIOD_PREVIOUS_DAY_PREFIX).isdigit()
        and int(value.removeprefix(PERIOD_PREVIOUS_DAY_PREFIX)) > 0
    )


def _expression_snapshot(expression, states, now, template_results) -> dict[str, Any]:
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
            ],
        }
    entity_id = expression.get("entity_id")
    state = states.get(entity_id) if isinstance(entity_id, str) else None
    deadline = expression_next_deadline(expression, states, now)
    template = expression.get("value_template")
    attribute = expression.get("attribute")
    attributes = getattr(state, "attributes", {})
    current_value = (
        attributes.get(attribute)
        if isinstance(attribute, str) and isinstance(attributes, Mapping)
        else getattr(state, "state", None)
    )
    return {
        **dict(expression),
        "current_state": getattr(state, "state", None),
        "current_value": current_value,
        "template_result": template_results.get(template),
        "deadline": deadline.isoformat() if deadline else None,
        "matched": expression_matches(expression, states, now, template_results),
    }


def _template_values(value: object) -> list[str]:
    if not isinstance(value, Mapping):
        return []
    children = value.get("conditions")
    if isinstance(children, list):
        return [template for child in children for template in _template_values(child)]
    template = value.get("value_template")
    return (
        [template]
        if value.get("type") == "template" and isinstance(template, str)
        else []
    )


def _template_value(value: object) -> str:
    if not isinstance(value, Mapping) or value.get("type") != "template":
        return ""
    template = value.get("value_template")
    return template if isinstance(template, str) else ""


def _changes(previous_data, previous_options, data, options) -> list[dict[str, str]]:
    fields = (
        (CONF_NAME, "Name"),
        (CONF_TEMPLATE, "Activity model"),
        (CONF_RULE, "Start and stop rules"),
        (CONF_PERIOD_METRICS, "Periods and metrics"),
        (CONF_ENABLED_METRICS, "Additional metrics"),
    )
    changes = [
        {
            "field": label,
            "before": str(previous_data.get(key, "—")),
            "after": str(data[key]),
        }
        for key, label in fields
        if previous_data.get(key) != data[key]
    ]
    for key, label in (
        (OPT_DURATION_UNIT, "Duration unit"),
        (OPT_RETENTION_DAYS, "Retention"),
        (OPT_MINIMUM_SESSION_SECONDS, "Minimum session"),
        (OPT_CROSS_MIDNIGHT_POLICY, "Midnight policy"),
    ):
        if previous_options.get(key) != options[key]:
            changes.append(
                {
                    "field": label,
                    "before": str(previous_options.get(key, "—")),
                    "after": str(options[key]),
                }
            )
    return changes


def _zone_rule(entity_id: str, zone_state: str) -> dict[str, Any]:
    return {
        "start_when": {"type": "state", "entity_id": entity_id, "states": [zone_state]},
        "stop_when": {
            "type": "state",
            "entity_id": entity_id,
            "states": [zone_state],
            "operator": "not_equals",
        },
    }


def _empty_rule() -> dict[str, Any]:
    return {
        "start_when": {"operator": "all", "conditions": []},
        "stop_when": {"operator": "all", "conditions": []},
    }


def _string(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _nonnegative(value: object, path: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise DraftValidationError({path: "invalid_number"}) from error
    if result < 0:
        raise DraftValidationError({path: "invalid_number"})
    return result
