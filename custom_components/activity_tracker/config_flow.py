"""UI-only configuration and options flow for Activity Tracker."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
    CONF_ACTIVE_STATES,
    CONF_AREA_ID,
    CONF_ENABLED_METRICS,
    CONF_ENTITY_ID,
    CONF_LABEL_ATTRIBUTE,
    CONF_MONITOR_TYPE,
    CONF_NAME,
    CONF_PERIODS,
    CONF_PERSON_ENTITY_ID,
    CONF_PRESENCE_ENTITY_ID,
    CONF_VALUE_ATTRIBUTE,
    CONF_VALUE_SOURCE,
    CONF_ZONE_ENTITY_ID,
    DEFAULT_DURATION_UNIT,
    DEFAULT_MERGE_GAP_SECONDS,
    DEFAULT_MINIMUM_SESSION_SECONDS,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_UNAVAILABLE_BEHAVIOR,
    DEFAULT_UNAVAILABLE_TOLERANCE_SECONDS,
    DOMAIN,
    DURATION_UNITS,
    METRICS,
    MONITOR_TYPES,
    OPT_DURATION_UNIT,
    OPT_IMPORT_RECORDER_HISTORY,
    OPT_MERGE_GAP_SECONDS,
    OPT_MINIMUM_SESSION_SECONDS,
    OPT_RETENTION_DAYS,
    OPT_UNAVAILABLE_BEHAVIOR,
    OPT_UNAVAILABLE_TOLERANCE_SECONDS,
    PERIODS,
    TYPE_AREA_PRESENCE,
    TYPE_FOREGROUND_APPLICATION,
    TYPE_ZONE,
)


class ActivityTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create exactly one monitor per config entry."""

    VERSION = 1

    def __init__(self) -> None:
        self._monitor: dict[str, Any] = {}
        self._options: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._monitor[CONF_MONITOR_TYPE] = user_input[CONF_MONITOR_TYPE]
            return await self.async_step_source()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MONITOR_TYPE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=list(MONITOR_TYPES),
                            mode=selector.SelectSelectorMode.LIST,
                            translation_key="monitor_type",
                        )
                    )
                }
            ),
            description_placeholders={
                "monitor_examples": (
                    "Examples: a TV that is on, a person at a zone, or the app "
                    "currently in the foreground on a phone."
                )
            },
        )

    async def async_step_source(self, user_input: dict[str, Any] | None = None):
        monitor_type = self._monitor[CONF_MONITOR_TYPE]
        errors: dict[str, str] = {}
        if user_input is not None:
            active_states = _split_states(user_input.get(CONF_ACTIVE_STATES, ""))
            if (
                monitor_type not in (TYPE_ZONE, TYPE_FOREGROUND_APPLICATION)
                and not active_states
            ):
                errors[CONF_ACTIVE_STATES] = "required"
            elif (
                monitor_type == TYPE_FOREGROUND_APPLICATION
                and user_input.get(CONF_VALUE_SOURCE) == "attribute"
                and not str(user_input.get(CONF_VALUE_ATTRIBUTE, "")).strip()
            ):
                errors[CONF_VALUE_ATTRIBUTE] = "required"
            else:
                self._monitor.update(user_input)
                if active_states:
                    self._monitor[CONF_ACTIVE_STATES] = active_states
                self._monitor[CONF_NAME] = user_input[CONF_NAME].strip()
                return await self.async_step_behavior()
        return self.async_show_form(
            step_id="source",
            data_schema=_source_schema(monitor_type),
            errors=errors,
            description_placeholders={
                "monitor_type_guidance": _source_guidance(monitor_type),
            },
        )

    async def async_step_behavior(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_periods()
        return self.async_show_form(
            step_id="behavior",
            data_schema=_behavior_schema(include_recorder_import=True),
        )

    async def async_step_periods(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            periods = list(user_input.get(CONF_PERIODS, []))
            rolling, invalid_rolling = _rolling_periods(
                user_input.get("rolling_days", "")
            )
            if not periods and not rolling:
                errors[CONF_PERIODS] = "required"
            elif invalid_rolling:
                errors["rolling_days"] = "invalid_rolling_days"
            else:
                self._monitor[CONF_PERIODS] = periods + rolling
                return await self.async_step_metrics()
        schema = vol.Schema(
            {
                vol.Optional(CONF_PERIODS, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=list(PERIODS),
                        multiple=True,
                        translation_key="report_period",
                    )
                ),
                vol.Optional("rolling_days", default=""): str,
            }
        )
        return self.async_show_form(
            step_id="periods", data_schema=schema, errors=errors
        )

    async def async_step_metrics(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            metrics = list(user_input.get(CONF_ENABLED_METRICS, []))
            if not metrics:
                errors[CONF_ENABLED_METRICS] = "required"
            else:
                self._monitor[CONF_ENABLED_METRICS] = metrics
                return await self.async_step_review()
        return self.async_show_form(
            step_id="metrics",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ENABLED_METRICS): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=list(METRICS),
                            multiple=True,
                            translation_key="metric",
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_review(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(None)
            return self.async_create_entry(
                title=self._monitor[CONF_NAME],
                data=self._monitor,
                options=self._options,
            )
        return self.async_show_form(
            step_id="review",
            description_placeholders={
                "name": self._monitor[CONF_NAME],
                "source": self._monitor.get(
                    CONF_ENTITY_ID, self._monitor.get(CONF_PRESENCE_ENTITY_ID, "")
                ),
                "periods": ", ".join(self._monitor[CONF_PERIODS]),
                "metrics": str(len(self._monitor[CONF_ENABLED_METRICS])),
            },
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ActivityTrackerOptionsFlow()


class ActivityTrackerOptionsFlow(config_entries.OptionsFlow):
    """Reconfigure every part of an existing monitor."""

    def __init__(self) -> None:
        self._monitor: dict[str, Any] = {}
        self._options: dict[str, Any] = {}
        self._history_action = "keep"

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._monitor = dict(self.config_entry.data)
            self._monitor[CONF_MONITOR_TYPE] = user_input[CONF_MONITOR_TYPE]
            self._options = dict(self.config_entry.options)
            self._options.setdefault(OPT_DURATION_UNIT, "s")
            return await self.async_step_source()
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MONITOR_TYPE,
                        default=self.config_entry.data.get(CONF_MONITOR_TYPE),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=list(MONITOR_TYPES),
                            mode=selector.SelectSelectorMode.LIST,
                            translation_key="monitor_type",
                        )
                    )
                }
            ),
        )

    async def async_step_source(self, user_input: dict[str, Any] | None = None):
        monitor_type = self._monitor[CONF_MONITOR_TYPE]
        errors: dict[str, str] = {}
        if user_input is not None:
            active_states = _split_states(user_input.get(CONF_ACTIVE_STATES, ""))
            if (
                monitor_type not in (TYPE_ZONE, TYPE_FOREGROUND_APPLICATION)
                and not active_states
            ):
                errors[CONF_ACTIVE_STATES] = "required"
            elif (
                monitor_type == TYPE_FOREGROUND_APPLICATION
                and user_input.get(CONF_VALUE_SOURCE) == "attribute"
                and not str(user_input.get(CONF_VALUE_ATTRIBUTE, "")).strip()
            ):
                errors[CONF_VALUE_ATTRIBUTE] = "required"
            else:
                self._monitor.update(user_input)
                if active_states:
                    self._monitor[CONF_ACTIVE_STATES] = active_states
                self._monitor[CONF_NAME] = user_input[CONF_NAME].strip()
                return await self.async_step_behavior()
        return self.async_show_form(
            step_id="source",
            data_schema=_source_schema(monitor_type, self._monitor),
            errors=errors,
            description_placeholders={
                "monitor_type_guidance": _source_guidance(monitor_type)
            },
        )

    async def async_step_behavior(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._options.update(user_input)
            self._options.pop(OPT_IMPORT_RECORDER_HISTORY, None)
            return await self.async_step_periods()
        return self.async_show_form(
            step_id="behavior", data_schema=_behavior_schema(self._options)
        )

    async def async_step_periods(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            periods = list(user_input.get(CONF_PERIODS, []))
            rolling, invalid_rolling = _rolling_periods(
                user_input.get("rolling_days", "")
            )
            if not periods and not rolling:
                errors[CONF_PERIODS] = "required"
            elif invalid_rolling:
                errors["rolling_days"] = "invalid_rolling_days"
            else:
                self._monitor[CONF_PERIODS] = periods + rolling
                return await self.async_step_metrics()
        current_periods = self._monitor.get(CONF_PERIODS, [])
        rolling = ", ".join(
            item.split(":", 1)[1]
            for item in current_periods
            if item.startswith("rolling_days:")
        )
        return self.async_show_form(
            step_id="periods",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_PERIODS,
                        default=[
                            item
                            for item in current_periods
                            if not item.startswith("rolling_days:")
                        ],
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=list(PERIODS),
                            multiple=True,
                            translation_key="report_period",
                        )
                    ),
                    vol.Optional("rolling_days", default=rolling): str,
                }
            ),
            errors=errors,
        )

    async def async_step_metrics(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            metrics = list(user_input.get(CONF_ENABLED_METRICS, []))
            if not metrics:
                errors[CONF_ENABLED_METRICS] = "required"
            else:
                self._monitor[CONF_ENABLED_METRICS] = metrics
                if _is_rule_changing(
                    self.config_entry.data,
                    self.config_entry.options,
                    self._monitor,
                    self._options,
                ):
                    return await self.async_step_history()
                return await self._async_save_options()
        return self.async_show_form(
            step_id="metrics",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ENABLED_METRICS,
                        default=self._monitor.get(CONF_ENABLED_METRICS, []),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=list(METRICS),
                            multiple=True,
                            translation_key="metric",
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_history(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            action = user_input["history_action"]
            self._history_action = action
            if action == "keep":
                return await self._async_save_options()
            return await self.async_step_confirm_history()
        return self.async_show_form(
            step_id="history",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "history_action", default="keep"
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["keep", "clear", "reimport"],
                            mode=selector.SelectSelectorMode.LIST,
                            translation_key="history_action",
                        )
                    )
                }
            ),
        )

    async def async_step_confirm_history(
        self, user_input: dict[str, Any] | None = None
    ):
        """Require a distinct confirmation before a destructive history action."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get("confirm_history_action") is not True:
                errors["confirm_history_action"] = "confirmation_required"
            else:
                return await self._async_save_options()
        return self.async_show_form(
            step_id="confirm_history",
            data_schema=vol.Schema(
                {vol.Required("confirm_history_action", default=False): bool}
            ),
            errors=errors,
            description_placeholders={"action": self._history_action},
        )

    async def _async_save_options(self):
        """Save the edited monitor and apply a previously confirmed action."""
        if self._history_action == "reimport":
            self._options[OPT_IMPORT_RECORDER_HISTORY] = True
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=self._monitor,
            title=self._monitor[CONF_NAME],
        )
        if self._history_action == "clear":
            runtime = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
            if runtime is not None:
                await runtime.async_clear_history()
        return self.async_create_entry(title="", data=self._options)


def _is_rule_changing(
    previous_data: dict[str, Any],
    previous_options: dict[str, Any],
    updated_data: dict[str, Any],
    updated_options: dict[str, Any],
) -> bool:
    """Return whether an edit changes the meaning of retained activity."""
    rule_data_keys = (
        CONF_MONITOR_TYPE,
        CONF_ENTITY_ID,
        CONF_ACTIVE_STATES,
        CONF_ZONE_ENTITY_ID,
        CONF_PRESENCE_ENTITY_ID,
        CONF_VALUE_SOURCE,
        CONF_VALUE_ATTRIBUTE,
    )
    rule_option_keys = (
        OPT_MINIMUM_SESSION_SECONDS,
        OPT_MERGE_GAP_SECONDS,
        OPT_UNAVAILABLE_BEHAVIOR,
        OPT_UNAVAILABLE_TOLERANCE_SECONDS,
    )
    return any(
        previous_data.get(key) != updated_data.get(key) for key in rule_data_keys
    ) or any(
        previous_options.get(key) != updated_options.get(key)
        for key in rule_option_keys
    )


def _source_schema(
    monitor_type: str, defaults: dict[str, Any] | None = None
) -> vol.Schema:
    """Build the source form for a monitor type, optionally prefilled."""
    defaults = defaults or {}

    def required(
        key: str, validator: Any, fallback: Any = vol.UNDEFINED
    ) -> tuple[Any, Any]:
        default = defaults.get(key, fallback)
        return (
            vol.Required(key, default=default)
            if default is not vol.UNDEFINED
            else vol.Required(key),
            validator,
        )

    fields = [required(CONF_NAME, str)]
    if monitor_type == TYPE_ZONE:
        fields.extend(
            (
                required(
                    CONF_ENTITY_ID,
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["person", "device_tracker"]
                        )
                    ),
                ),
                required(
                    CONF_ZONE_ENTITY_ID,
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="zone")
                    ),
                ),
            )
        )
    elif monitor_type == TYPE_AREA_PRESENCE:
        fields.extend(
            (
                required(
                    CONF_PERSON_ENTITY_ID,
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="person")
                    ),
                ),
                required(CONF_AREA_ID, selector.AreaSelector()),
                required(
                    CONF_PRESENCE_ENTITY_ID,
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                ),
                required(CONF_ACTIVE_STATES, str, "on"),
            )
        )
    elif monitor_type == TYPE_FOREGROUND_APPLICATION:
        fields.extend(
            (
                required(CONF_ENTITY_ID, selector.EntitySelector()),
                required(
                    CONF_VALUE_SOURCE,
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["state", "attribute"],
                            mode=selector.SelectSelectorMode.LIST,
                            translation_key="application_value_source",
                        )
                    ),
                    "state",
                ),
                (
                    vol.Optional(
                        CONF_VALUE_ATTRIBUTE,
                        default=defaults.get(CONF_VALUE_ATTRIBUTE, ""),
                    ),
                    str,
                ),
                (
                    vol.Optional(
                        CONF_LABEL_ATTRIBUTE,
                        default=defaults.get(CONF_LABEL_ATTRIBUTE, ""),
                    ),
                    str,
                ),
            )
        )
    else:
        fields.extend(
            (
                required(CONF_ENTITY_ID, selector.EntitySelector()),
                required(CONF_ACTIVE_STATES, str),
            )
        )
    return vol.Schema(dict(fields))


def _behavior_schema(
    defaults: dict[str, Any] | None = None, *, include_recorder_import: bool = False
) -> vol.Schema:
    defaults = defaults or {}
    fields: dict[Any, Any] = {
        vol.Required(
            OPT_DURATION_UNIT,
            default=defaults.get(OPT_DURATION_UNIT, DEFAULT_DURATION_UNIT),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=list(DURATION_UNITS),
                mode=selector.SelectSelectorMode.LIST,
                translation_key="duration_unit",
            )
        ),
        vol.Required(
            OPT_RETENTION_DAYS,
            default=defaults.get(OPT_RETENTION_DAYS, DEFAULT_RETENTION_DAYS),
        ): vol.All(vol.Coerce(int), vol.Range(min=7)),
        vol.Required(
            OPT_MINIMUM_SESSION_SECONDS,
            default=defaults.get(
                OPT_MINIMUM_SESSION_SECONDS, DEFAULT_MINIMUM_SESSION_SECONDS
            ),
        ): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required(
            OPT_UNAVAILABLE_BEHAVIOR,
            default=defaults.get(
                OPT_UNAVAILABLE_BEHAVIOR, DEFAULT_UNAVAILABLE_BEHAVIOR
            ),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["end", "pending", "unknown"],
                mode=selector.SelectSelectorMode.LIST,
                translation_key="unavailable_behavior",
            )
        ),
        vol.Required(
            OPT_UNAVAILABLE_TOLERANCE_SECONDS,
            default=defaults.get(
                OPT_UNAVAILABLE_TOLERANCE_SECONDS,
                DEFAULT_UNAVAILABLE_TOLERANCE_SECONDS,
            ),
        ): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required(
            OPT_MERGE_GAP_SECONDS,
            default=defaults.get(OPT_MERGE_GAP_SECONDS, DEFAULT_MERGE_GAP_SECONDS),
        ): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
    if include_recorder_import:
        fields[
            vol.Optional(
                OPT_IMPORT_RECORDER_HISTORY,
                default=defaults.get(OPT_IMPORT_RECORDER_HISTORY, False),
            )
        ] = selector.BooleanSelector()
    return vol.Schema(fields)


def _split_states(value: object) -> list[str]:
    return (
        [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, str)
        else []
    )


def _rolling_periods(value: object) -> tuple[list[str], bool]:
    """Parse user-entered rolling-day periods and identify invalid values."""
    if not isinstance(value, str):
        return [], False
    result: list[str] = []
    invalid = False
    for item in value.split(","):
        if not item.strip():
            continue
        try:
            days = int(item.strip())
        except ValueError:
            invalid = True
            continue
        if days > 0:
            result.append(f"rolling_days:{days}")
        else:
            invalid = True
    return result, invalid


def _source_guidance(monitor_type: str) -> str:
    """Return a short source-specific explanation shown in the form."""
    guidance = {
        TYPE_ZONE: (
            "The selected person or device is active only while its state exactly "
            "matches the selected zone."
        ),
        TYPE_AREA_PRESENCE: (
            "Choose the person and area for the monitor name, then choose the binary "
            "sensor that authoritatively reports whether that person is present."
        ),
        TYPE_FOREGROUND_APPLICATION: (
            "Every non-empty application value is activity. A different application "
            "value starts a new application session."
        ),
    }
    return guidance.get(
        monitor_type,
        "The monitor is active whenever the source entity state matches one of the "
        "states you enter.",
    )
