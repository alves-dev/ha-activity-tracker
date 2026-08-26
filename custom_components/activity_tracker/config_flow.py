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
    DEFAULT_MERGE_GAP_SECONDS,
    DEFAULT_MINIMUM_SESSION_SECONDS,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_UNAVAILABLE_BEHAVIOR,
    DEFAULT_UNAVAILABLE_TOLERANCE_SECONDS,
    DOMAIN,
    METRICS,
    MONITOR_TYPES,
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
                            options=_select_options(MONITOR_TYPES),
                            mode=selector.SelectSelectorMode.LIST,
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
        schema: dict[Any, Any] = {vol.Required(CONF_NAME): str}
        if monitor_type == TYPE_ZONE:
            schema.update(
                {
                    vol.Required(CONF_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["person", "device_tracker"]
                        )
                    ),
                    vol.Required(CONF_ZONE_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="zone")
                    ),
                }
            )
        elif monitor_type == TYPE_AREA_PRESENCE:
            schema.update(
                {
                    vol.Required(CONF_PERSON_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="person")
                    ),
                    vol.Required(CONF_AREA_ID): selector.AreaSelector(),
                    vol.Required(CONF_PRESENCE_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Required(CONF_ACTIVE_STATES, default="on"): str,
                }
            )
        elif monitor_type == TYPE_FOREGROUND_APPLICATION:
            schema.update(
                {
                    vol.Required(CONF_ENTITY_ID): selector.EntitySelector(),
                    vol.Required(
                        CONF_VALUE_SOURCE, default="state"
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=_select_options(("state", "attribute")),
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Optional(CONF_VALUE_ATTRIBUTE): str,
                    vol.Optional(CONF_LABEL_ATTRIBUTE): str,
                }
            )
        else:
            schema.update(
                {
                    vol.Required(CONF_ENTITY_ID): selector.EntitySelector(),
                    vol.Required(CONF_ACTIVE_STATES): str,
                }
            )
        return self.async_show_form(
            step_id="source",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={
                "monitor_type_guidance": _source_guidance(monitor_type),
            },
        )

    async def async_step_behavior(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_periods()
        return self.async_show_form(step_id="behavior", data_schema=_behavior_schema())

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
                        options=_select_options(PERIODS), multiple=True
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
                            options=_select_options(METRICS), multiple=True
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
    """Adjust runtime behavior and selected entity metrics."""

    def __init__(self) -> None:
        self._pending: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init", data_schema=_behavior_schema(self.config_entry.options)
        )


def _behavior_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
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
                    options=_select_options(("end", "pending", "unknown")),
                    mode=selector.SelectSelectorMode.LIST,
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
    )


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


def _select_options(values: tuple[str, ...]) -> list[dict[str, str]]:
    """Build user-friendly labels while retaining stable stored values."""
    labels = {
        "entity_state": "Entity is in one of several active states",
        "zone": "Person or device is in a zone",
        "area_presence": "Person is in an internal area (presence sensor)",
        "foreground_application": "Foreground application",
        "generic": "Generic state rule",
        "state": "Entity state",
        "attribute": "Entity attribute",
        "current_day": "Today",
        "current_week": "Current week",
        "current_month": "Current month",
        "total_duration": "Total activity duration",
        "session_count": "Session count",
        "current_session_duration": "Current session duration",
        "last_session_duration": "Last completed session duration",
        "last_session_start": "Last completed session start",
        "last_session_end": "Last completed session end",
        "days_since_last_session": "Days since last completed session",
        "average_daily_duration": "Average daily duration",
        "average_session_duration": "Average session duration",
        "longest_session_duration": "Longest session duration",
        "shortest_session_duration": "Shortest session duration",
        "first_activity_time": "First activity time today",
        "last_activity_time": "Last activity time today",
        "weekday_highest_total": "Weekday with the highest total activity",
        "unknown_duration": "Unknown-duration total",
        "end": "End the session",
        "pending": "Keep the session pending",
        "unknown": "Mark the interval as unknown",
    }
    return [{"value": value, "label": labels.get(value, value)} for value in values]
