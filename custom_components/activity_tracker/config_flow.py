"""Guided configuration for unified activity rules."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util
import voluptuous as vol

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
    PERIODS,
)
from .rules import expression_matches, expression_next_deadline

_TEMPLATE_CUSTOM = "custom"
_TEMPLATE_ZONE = "zone_presence"


class _RuleEditor:
    """Shared step implementation for creation and complete monitor editing."""

    _data: dict[str, Any]
    _options: dict[str, Any]
    _conditions: dict[str, list[list[dict[str, Any]]]]
    _condition_phase: str
    _periods: list[str]
    _period_index: int

    def _start_editor(
        self,
        data: Mapping[str, Any] | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> None:
        self._data = dict(data or {})
        self._options = dict(options or {})
        rule = self._data.get(CONF_RULE, {})
        rule = rule if isinstance(rule, Mapping) else {}
        self._conditions = {
            "start": _expression_groups(rule.get("start_when", {})),
            "stop": _expression_groups(rule.get("stop_when", {})),
        }
        period_metrics = self._data.get(CONF_PERIOD_METRICS, {})
        self._periods = (
            list(period_metrics) if isinstance(period_metrics, Mapping) else []
        )
        self._period_index = 0
        self._condition_phase = "start"

    async def _async_template_step(
        self, step_id: str, user_input: dict[str, Any] | None
    ):
        if user_input is not None:
            self._data[CONF_TEMPLATE] = user_input[CONF_TEMPLATE]
            return await self.async_step_source()
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TEMPLATE,
                        default=self._data.get(CONF_TEMPLATE, _TEMPLATE_CUSTOM),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[_TEMPLATE_ZONE, _TEMPLATE_CUSTOM],
                            translation_key="template",
                        )
                    )
                }
            ),
        )

    async def async_step_source(self, user_input: dict[str, Any] | None = None):
        template = self._data.get(CONF_TEMPLATE, _TEMPLATE_CUSTOM)
        if user_input is not None:
            name = str(user_input.get(CONF_NAME, "")).strip()
            if not name:
                return self.async_show_form(
                    step_id="source",
                    data_schema=self._source_schema(template),
                    errors={CONF_NAME: "required"},
                )
            self._data[CONF_NAME] = name
            if template == _TEMPLATE_ZONE:
                tracker = user_input["entity_id"]
                zone_id = user_input["zone_entity_id"]
                self._data[CONF_RULE] = _zone_rule(
                    tracker, _zone_state_value(self.hass, zone_id)
                )
                self._conditions = {
                    "start": _expression_groups(self._data[CONF_RULE]["start_when"]),
                    "stop": _expression_groups(self._data[CONF_RULE]["stop_when"]),
                }
                return await self.async_step_behavior()
            return await self.async_step_start_condition()
        return self.async_show_form(
            step_id="source", data_schema=self._source_schema(template)
        )

    def _source_schema(self, template: str) -> vol.Schema:
        fields: dict[Any, Any] = {
            vol.Required(CONF_NAME, default=self._data.get(CONF_NAME, "")): str,
        }
        if template == _TEMPLATE_ZONE:
            zone_defaults = _zone_source_defaults(self.hass, self._data.get(CONF_RULE))
            fields.update(
                {
                    vol.Required(
                        "entity_id", default=zone_defaults["entity_id"]
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["person", "device_tracker"]
                        )
                    ),
                    vol.Required(
                        "zone_entity_id", default=zone_defaults["zone_entity_id"]
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="zone")
                    ),
                }
            )
        return vol.Schema(fields)

    async def async_step_start_condition(self, user_input=None):
        return await self._async_condition_step("start", user_input)

    async def async_step_stop_condition(self, user_input=None):
        return await self._async_condition_step("stop", user_input)

    async def _async_condition_step(
        self, phase: str, user_input: dict[str, Any] | None
    ):
        errors: dict[str, str] = {}
        if user_input is not None:
            editor_action = user_input["editor_action"]
            self._condition_phase = phase
            if editor_action == "add":
                return await self.async_step_condition()
            if editor_action == "remove":
                return await self.async_step_remove_condition()
            transition = self._finish_condition_phase(phase, errors)
            if transition is not None:
                return await self._async_condition_transition(transition)
        return self.async_show_form(
            step_id=f"{phase}_condition",
            errors=errors,
            data_schema=_condition_menu_schema(
                has_conditions=_has_conditions(self._conditions[phase])
            ),
            description_placeholders={
                "conditions": _conditions_summary(self._conditions[phase]),
                "status": _conditions_status(
                    self.hass, self._conditions[phase], phase
                ),
            },
        )

    async def async_step_condition(self, user_input: dict[str, Any] | None = None):
        """Add one condition after a user chooses the expression to change."""
        errors: dict[str, str] = {}
        if user_input is not None:
            condition = _condition(user_input)
            if condition is None:
                errors["states"] = "required"
            else:
                phase = self._condition_phase
                self._conditions[phase][-1].append(condition)
                if user_input["next_action"] == "or":
                    self._conditions[phase].append([])
                if user_input["next_action"] == "finish":
                    transition = self._finish_condition_phase(phase, errors)
                    if transition is not None:
                        return await self._async_condition_transition(transition)
                else:
                    return await getattr(self, f"async_step_{phase}_condition")()
        return self.async_show_form(
            step_id="condition",
            errors=errors,
            data_schema=_condition_schema(),
        )

    async def async_step_remove_condition(
        self, user_input: dict[str, Any] | None = None
    ):
        """Remove a selected saved condition without requiring a new one."""
        phase = self._condition_phase
        errors: dict[str, str] = {}
        if user_input is not None:
            if _remove_condition(
                self._conditions[phase], user_input.get("condition_id")
            ):
                return await getattr(self, f"async_step_{phase}_condition")()
            errors["condition_id"] = "condition_required"
        return self.async_show_form(
            step_id="remove_condition",
            errors=errors,
            data_schema=_remove_condition_schema(
                _condition_choices(self._conditions[phase])
            ),
            description_placeholders={
                "conditions": _conditions_summary(self._conditions[phase]),
            },
        )

    async def _async_condition_transition(self, transition: str):
        if transition == "stop":
            return await self.async_step_stop_condition()
        return await self.async_step_behavior()

    def _finish_condition_phase(
        self, phase: str, errors: dict[str, str]
    ) -> str | None:
        if not _has_conditions(self._conditions[phase]):
            errors["editor_action"] = "conditions_required"
            return None
        if phase == "start":
            return "stop"
        self._data[CONF_RULE] = {
            "start_when": _expression(self._conditions["start"]),
            "stop_when": _expression(self._conditions["stop"]),
        }
        return "behavior"

    async def async_step_behavior(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_periods()
        return self.async_show_form(
            step_id="behavior", data_schema=_behavior_schema(self._options)
        )

    async def async_step_periods(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = user_input.get("periods", [])
            selected = selected if isinstance(selected, list) else []
            previous = _previous_day_periods(user_input.get("previous_days", ""))
            if previous is None:
                errors["previous_days"] = "invalid_previous_days"
            self._periods = list(dict.fromkeys([*selected, *(previous or [])]))
            if not self._periods:
                errors["periods"] = "required"
            if not errors:
                existing = self._data.get(CONF_PERIOD_METRICS, {})
                existing = existing if isinstance(existing, Mapping) else {}
                self._data[CONF_PERIOD_METRICS] = {
                    period: list(existing.get(period, [])) for period in self._periods
                }
                self._period_index = 0
                return await self.async_step_period_metrics()
        current_periods = [
            period
            for period in self._periods
            if not period.startswith(PERIOD_PREVIOUS_DAY_PREFIX)
        ]
        previous_days = ", ".join(
            period.split(":", 1)[1]
            for period in self._periods
            if period.startswith(PERIOD_PREVIOUS_DAY_PREFIX)
        )
        return self.async_show_form(
            step_id="periods",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "periods", default=current_periods or [PERIODS[0]]
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=list(PERIODS),
                            translation_key="report_period",
                            multiple=True,
                        )
                    ),
                    vol.Optional("previous_days", default=previous_days): str,
                }
            ),
        )

    async def async_step_period_metrics(
        self, user_input: dict[str, Any] | None = None
    ):
        period = self._periods[self._period_index]
        errors: dict[str, str] = {}
        if user_input is not None:
            metrics = [
                item
                for item in user_input.get(CONF_PERIOD_METRICS, [])
                if item in PERIOD_METRICS
            ]
            if not metrics:
                errors[CONF_PERIOD_METRICS] = "required"
            else:
                self._data[CONF_PERIOD_METRICS][period] = metrics
                self._period_index += 1
                if self._period_index < len(self._periods):
                    return await self.async_step_period_metrics()
                return await self.async_step_metrics()
        return self.async_show_form(
            step_id="period_metrics",
            errors=errors,
            description_placeholders={"period": _period_summary(period)},
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PERIOD_METRICS,
                        default=self._data[CONF_PERIOD_METRICS].get(period, []),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=sorted(PERIOD_METRICS),
                            translation_key="metric",
                            multiple=True,
                        )
                    )
                }
            ),
        )

    async def async_step_metrics(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._data[CONF_ENABLED_METRICS] = [
                item
                for item in user_input.get(CONF_ENABLED_METRICS, [])
                if item in NON_PERIOD_METRICS
            ]
            return await self.async_step_review()
        return self.async_show_form(
            step_id="metrics",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ENABLED_METRICS,
                        default=self._data.get(CONF_ENABLED_METRICS, []),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=sorted(NON_PERIOD_METRICS),
                            translation_key="metric",
                            multiple=True,
                        )
                    )
                }
            ),
        )

    async def async_step_review(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return await self._async_save_monitor()
        metrics = sum(len(value) for value in self._data[CONF_PERIOD_METRICS].values())
        metrics += len(self._data[CONF_ENABLED_METRICS])
        return self.async_show_form(
            step_id="review",
            description_placeholders={
                "name": self._data[CONF_NAME],
                "source": self._data[CONF_TEMPLATE],
                "metrics": str(metrics),
                "periods": ", ".join(_period_summary(item) for item in self._periods),
                "start_conditions": _conditions_summary(self._conditions["start"]),
                "stop_conditions": _conditions_summary(self._conditions["stop"]),
                "status": _rule_status(self.hass, self._data[CONF_RULE]),
            },
            data_schema=vol.Schema({}),
        )


class ActivityTrackerConfigFlow(_RuleEditor, config_entries.ConfigFlow, domain=DOMAIN):
    """Create one monitor from a zone preset or a custom rule."""

    VERSION = 3

    def __init__(self) -> None:
        self._start_editor()

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        return await self._async_template_step("user", user_input)

    async def _async_save_monitor(self):
        return self.async_create_entry(
            title=self._data[CONF_NAME], data=self._data, options=self._options
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return ActivityTrackerOptionsFlow()


class ActivityTrackerOptionsFlow(_RuleEditor, config_entries.OptionsFlow):
    """Edit the full monitor contract and clear changed rules after confirmation."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if not hasattr(self, "_data"):
            self._start_editor(self.config_entry.data, self.config_entry.options)
        return await self._async_template_step("init", user_input)

    async def _async_save_monitor(self):
        rule_changed = self.config_entry.data.get(CONF_RULE) != self._data[CONF_RULE]
        policy_changed = self.config_entry.options.get(
            OPT_CROSS_MIDNIGHT_POLICY
        ) != self._options.get(OPT_CROSS_MIDNIGHT_POLICY)
        if rule_changed or policy_changed:
            return await self.async_step_confirm_history()
        return await self._async_apply_update()

    async def async_step_confirm_history(
        self, user_input: dict[str, Any] | None = None
    ):
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get("confirm_history_action"):
                runtime = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
                if runtime is not None:
                    await runtime.async_clear_history()
                return await self._async_apply_update()
            errors["confirm_history_action"] = "confirmation_required"
        return self.async_show_form(
            step_id="confirm_history",
            errors=errors,
            data_schema=vol.Schema(
                {vol.Optional("confirm_history_action", default=False): bool}
            ),
        )

    async def _async_apply_update(self):
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            title=self._data[CONF_NAME],
            data=self._data,
            options=self._options,
        )
        return self.async_create_entry(title="", data={})


def _condition_menu_schema(has_conditions: bool) -> vol.Schema:
    actions = ["add", "finish"]
    if has_conditions:
        actions.insert(1, "remove")
    return vol.Schema(
        {
            vol.Required("editor_action", default="add"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=actions,
                    translation_key="condition_editor_action",
                )
            )
        }
    )


def _condition_schema() -> vol.Schema:
    fields: dict[Any, Any] = {
        vol.Required("entity_id"): selector.EntitySelector(),
        vol.Required("condition_type", default="state"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["state", "report_silence"],
                    translation_key="condition_type",
                )
        ),
        vol.Optional("states", default=""): str,
        vol.Required("operator", default="equals"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["equals", "not_equals"],
                    translation_key="state_operator",
                )
        ),
        vol.Required("for_seconds", default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0)
        ),
        vol.Required("next_action", default="finish"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["and", "or", "finish"],
                    translation_key="condition_next_action",
                )
        ),
    }
    return vol.Schema(fields)


def _remove_condition_schema(condition_choices: list[str]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("condition_id"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=condition_choices)
            )
        }
    )


def _behavior_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                OPT_DURATION_UNIT,
                default=defaults.get(OPT_DURATION_UNIT, DEFAULT_DURATION_UNIT),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["s", "min", "h"], translation_key="duration_unit"
                )
            ),
            vol.Required(
                OPT_RETENTION_DAYS,
                default=defaults.get(OPT_RETENTION_DAYS, DEFAULT_RETENTION_DAYS),
            ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            vol.Required(
                OPT_MINIMUM_SESSION_SECONDS,
                default=defaults.get(
                    OPT_MINIMUM_SESSION_SECONDS, DEFAULT_MINIMUM_SESSION_SECONDS
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Required(
                OPT_CROSS_MIDNIGHT_POLICY,
                default=defaults.get(
                    OPT_CROSS_MIDNIGHT_POLICY, DEFAULT_CROSS_MIDNIGHT_POLICY
                ),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=list(CROSS_MIDNIGHT_POLICIES),
                    translation_key="cross_midnight_policy",
                )
            ),
        }
    )


def _condition(value: Mapping[str, Any]) -> dict[str, Any] | None:
    if value["condition_type"] == "report_silence":
        return {
            "type": "report_silence",
            "entity_id": value["entity_id"],
            "for_seconds": value["for_seconds"],
        }
    states = [item.strip() for item in value["states"].split(",") if item.strip()]
    if not states:
        return None
    return {
        "type": "state",
        "entity_id": value["entity_id"],
        "states": states,
        "operator": value["operator"],
        "for_seconds": value["for_seconds"],
    }


def _expression(groups: list[list[dict[str, Any]]]) -> dict[str, Any]:
    """Build an OR of AND groups, including `(A and B) or (C and D)`."""
    return {
        "operator": "any",
        "conditions": [
            {"operator": "all", "conditions": group} for group in groups if group
        ],
    }


def _expression_groups(expression: object) -> list[list[dict[str, Any]]]:
    """Return editable OR-of-AND groups without losing an existing rule."""
    if not isinstance(expression, Mapping):
        return [[]]
    if "conditions" not in expression:
        return [[dict(expression)]] if expression else [[]]
    groups: list[list[dict[str, Any]]] = []
    children = expression.get("conditions")
    if expression.get("operator") != "any" or not isinstance(children, list):
        return [[]]
    for group in children:
        if not isinstance(group, Mapping) or group.get("operator") != "all":
            return [[]]
        leaves = group.get("conditions")
        if not isinstance(leaves, list) or not all(
            isinstance(item, Mapping) and "conditions" not in item for item in leaves
        ):
            return [[]]
        groups.append([dict(item) for item in leaves])
    return groups or [[]]


def _has_conditions(groups: list[list[dict[str, Any]]]) -> bool:
    return any(groups)


def _condition_choices(groups: list[list[dict[str, Any]]]) -> list[str]:
    """Return stable form values that identify a displayed condition."""
    return [
        f"{group_index}:{condition_index} — {_condition_summary(condition)}"
        for group_index, group in enumerate(groups)
        for condition_index, condition in enumerate(group)
    ]


def _remove_condition(groups: list[list[dict[str, Any]]], value: object) -> bool:
    """Remove one selected condition and keep a valid editor group available."""
    if not isinstance(value, str):
        return False
    key = value.partition(" — ")[0]
    try:
        group_index, condition_index = (int(part) for part in key.split(":", 1))
        groups[group_index].pop(condition_index)
    except (IndexError, ValueError):
        return False
    groups[:] = [group for group in groups if group]
    if not groups:
        groups.append([])
    return True


def _conditions_summary(groups: list[list[dict[str, Any]]]) -> str:
    alternatives = []
    for group in groups:
        labels = []
        for item in group:
            labels.append(_condition_summary(item))
        if labels:
            alternatives.append(" AND ".join(labels))
    return " OR ".join(f"({item})" for item in alternatives) or "No conditions yet."


def _condition_summary(condition: Mapping[str, Any]) -> str:
    """Render one persisted condition for a config-flow description."""
    if condition.get("type") == "report_silence":
        return (
            f"{condition.get('entity_id')} silent for "
            f"{condition.get('for_seconds', 0)}s"
        )
    comparison = "is not" if condition.get("operator") == "not_equals" else "is"
    duration = (
        f" for {condition['for_seconds']}s" if condition.get("for_seconds") else ""
    )
    states = condition.get("states", [])
    state_values = ", ".join(states) if isinstance(states, list) else "?"
    return f"{condition.get('entity_id')} {comparison} {state_values}{duration}"


def _conditions_status(hass, groups: list[list[dict[str, Any]]], phase: str) -> str:
    """Describe the current result of each condition and its whole expression."""
    expression = _expression(groups)
    states = _condition_states(hass, groups)
    now = dt_util.utcnow()
    overall = expression_matches(expression, states, now)
    labels = [f"{phase.title()}: {'✓ matched' if overall else '✕ not matched'}"]
    for condition in (item for group in groups for item in group):
        labels.append(_condition_status(condition, states, now))
    return " | ".join(labels)


def _rule_status(hass, rule: Mapping[str, Any]) -> str:
    """Describe both saved expressions against one current-state snapshot."""
    start_groups = _expression_groups(rule.get("start_when", {}))
    stop_groups = _expression_groups(rule.get("stop_when", {}))
    return (
        f"{_conditions_status(hass, start_groups, 'start')}\n"
        f"{_conditions_status(hass, stop_groups, 'stop')}"
    )


def _condition_states(hass, groups: list[list[dict[str, Any]]]) -> dict[str, Any]:
    """Take the Home Assistant state snapshot required by these conditions."""
    getter = getattr(getattr(hass, "states", None), "get", None)
    if getter is None:
        return {}
    return {
        entity_id: state
        for condition in (item for group in groups for item in group)
        if isinstance((entity_id := condition.get("entity_id")), str)
        and (state := getter(entity_id)) is not None
    }


def _condition_status(
    condition: Mapping[str, Any], states: Mapping[str, Any], now: datetime
) -> str:
    """Render a leaf result with current state and an optional pending deadline."""
    entity_id = str(condition.get("entity_id", "?"))
    state = states.get(entity_id)
    if state is None:
        return f"✕ {entity_id}: entity unavailable"
    matched = expression_matches(condition, states, now)
    deadline = expression_next_deadline(condition, states, now)
    current = str(getattr(state, "state", "?"))
    result = "✓" if matched else "✕"
    detail = f"{result} {entity_id}: current {current}"
    if deadline is not None:
        seconds = max(0, int((deadline - now).total_seconds()))
        return f"{detail}; {seconds}s remaining"
    return detail


def _previous_day_periods(value: object) -> list[str] | None:
    text = str(value).strip()
    if not text:
        return []
    try:
        days = [int(item.strip()) for item in text.split(",")]
    except ValueError:
        return None
    if not days or any(day < 1 for day in days):
        return None
    return [f"{PERIOD_PREVIOUS_DAY_PREFIX}{day}" for day in dict.fromkeys(days)]


def _period_summary(period: str) -> str:
    if period.startswith(PERIOD_PREVIOUS_DAY_PREFIX):
        return f"Last {period.split(':', 1)[1]}"
    return period.replace("_", " ").title()


def _zone_state_value(hass, zone_id: str) -> str:
    if zone_id == "zone.home":
        return "home"
    zone = hass.states.get(zone_id)
    return zone.name if zone is not None else zone_id.removeprefix("zone.")


def _zone_source_defaults(hass, rule: object) -> dict[str, str]:
    """Recover the zone-template selectors from its persisted normal rule."""
    defaults = {"entity_id": "", "zone_entity_id": "zone.home"}
    if not isinstance(rule, Mapping):
        return defaults
    start = rule.get("start_when")
    if not isinstance(start, Mapping):
        return defaults
    entity_id = start.get("entity_id")
    states = start.get("states")
    if isinstance(entity_id, str):
        defaults["entity_id"] = entity_id
    if (
        not isinstance(states, list)
        or len(states) != 1
        or not isinstance(states[0], str)
    ):
        return defaults
    zone_state = states[0]
    if zone_state == "home":
        return defaults
    getter = getattr(getattr(hass, "states", None), "async_all", None)
    if getter is None:
        return defaults
    zone = next(
        (
            state
            for state in getter("zone")
            if getattr(state, "name", None) == zone_state
        ),
        None,
    )
    if zone is not None:
        defaults["zone_entity_id"] = zone.entity_id
    return defaults


def _zone_rule(entity_id: str, zone_state: str) -> dict[str, Any]:
    return {
        "start_when": {
            "type": "state",
            "entity_id": entity_id,
            "states": [zone_state],
        },
        "stop_when": {
            "type": "state",
            "entity_id": entity_id,
            "states": [zone_state],
            "operator": "not_equals",
        },
    }
