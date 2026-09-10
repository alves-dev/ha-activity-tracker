"""Selected Activity Tracker metric sensors."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .configuration import monitor_metric_selections, period_metric_selections
from .const import (
    DOMAIN,
    DURATION_UNITS,
    INTEGRATION_NAME,
    METRIC_AVERAGE_DAILY_DURATION,
    METRIC_AVERAGE_END_TIME,
    METRIC_AVERAGE_SESSION_DURATION,
    METRIC_AVERAGE_START_TIME,
    METRIC_CURRENT_SESSION_DURATION,
    METRIC_LAST_SESSION_DURATION,
    METRIC_LAST_SESSION_END,
    METRIC_LAST_SESSION_START,
    METRIC_LONGEST_SESSION_DURATION,
    METRIC_SESSION_COUNT,
    METRIC_SHORTEST_SESSION_DURATION,
    METRIC_TIME_SINCE_LAST_SESSION,
    METRIC_TOTAL_DURATION,
    METRIC_WEEKDAY_MAX,
    OPT_DURATION_UNIT,
)
from .models import average_time_of_day, format_duration
from .runtime import ActivityTrackerRuntime


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime: ActivityTrackerRuntime = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for period, metrics in period_metric_selections(entry.data).items():
        entities.extend(
            ActivityMetricSensor(runtime, metric, period) for metric in metrics
        )
    entities.extend(
        ActivityMetricSensor(runtime, metric)
        for metric in monitor_metric_selections(entry.data)
    )
    async_add_entities(entities)


class ActivityMetricSensor(SensorEntity):
    """One selected monitor metric, optionally scoped to a period."""

    _attr_has_entity_name = True

    def __init__(
        self, runtime: ActivityTrackerRuntime, metric: str, period: str | None = None
    ) -> None:
        self._runtime, self._metric, self._period = runtime, metric, period
        suffix = f"_{period}" if period else ""
        self._attr_unique_id = f"{runtime.entry.entry_id}_{metric}{suffix}"
        self._attr_name = _metric_name(metric, period)
        self._attr_icon = _metric_icon(metric)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, runtime.entry.entry_id)},
            name=runtime.entry.title,
            manufacturer=INTEGRATION_NAME,
            model="Activity monitor",
        )
        if metric in _DURATION_METRICS:
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_native_unit_of_measurement = self._duration_unit
            self._attr_state_class = (
                SensorStateClass.TOTAL_INCREASING
                if metric == METRIC_TOTAL_DURATION and period == "current_day"
                else SensorStateClass.MEASUREMENT
            )
        elif metric in (METRIC_LAST_SESSION_START, METRIC_LAST_SESSION_END):
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        elif metric == METRIC_SESSION_COUNT:
            self._attr_state_class = SensorStateClass.TOTAL

    @property
    def _duration_unit(self) -> UnitOfTime:
        """Return this monitor's selected presentation unit."""
        unit = self._runtime.entry.options.get(OPT_DURATION_UNIT, UnitOfTime.HOURS)
        return UnitOfTime(unit) if unit in DURATION_UNITS else UnitOfTime.SECONDS

    def _duration_value(self, seconds: float | int | None) -> float | int | None:
        """Convert canonical seconds to this monitor's presentation unit."""
        if seconds is None or self._duration_unit == UnitOfTime.SECONDS:
            return seconds
        divisor = 60 if self._duration_unit == UnitOfTime.MINUTES else 3600
        return seconds / divisor

    @property
    def native_value(self) -> Any:
        value, _ = self._value_and_attributes()
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        _, attributes = self._value_and_attributes()
        if self._period or getattr(self._runtime, "storage_error", None) is not None:
            _, availability = self._runtime.period_availability(
                self._period or "current_day"
            )
            attributes.update(availability)
        return attributes

    @property
    def available(self) -> bool:
        if getattr(self._runtime, "storage_error", None) is not None:
            return False
        return not self._period or self._runtime.period_availability(self._period)[0]

    def _value_and_attributes(  # noqa: PLR0911, PLR0912
        self,
    ) -> tuple[Any, dict[str, Any]]:
        if self._metric == METRIC_CURRENT_SESSION_DURATION:
            session = self._runtime.session
            seconds = 0
            if session:
                seconds = (dt_util.now() - session.started_at).total_seconds()
            return self._duration_value(seconds), {
                "formatted": format_duration(seconds)
            }
        last = self._runtime.last_completed
        if self._metric.startswith("last_session"):
            if not last:
                return None, {}
            key = {
                METRIC_LAST_SESSION_DURATION: "duration_seconds",
                METRIC_LAST_SESSION_START: "started_at",
                METRIC_LAST_SESSION_END: "ended_at",
            }[self._metric]
            value: Any = last[key]
            if self._metric != METRIC_LAST_SESSION_DURATION:
                value = datetime.fromisoformat(value)
            return (
                self._duration_value(value)
                if self._metric == METRIC_LAST_SESSION_DURATION
                else value
            ), {
                "quality": last["quality"],
                "formatted": format_duration(last["duration_seconds"]),
            }
        if self._metric == METRIC_TIME_SINCE_LAST_SESSION:
            if not last:
                return None, {}
            seconds = (
                dt_util.now() - datetime.fromisoformat(last["ended_at"])
            ).total_seconds()
            return self._duration_value(seconds), {
                "formatted": format_duration(seconds)
            }
        summaries, start, end = self._runtime.period_summaries(
            self._period or "current_day"
        )
        base_attrs = {"period_start": start.isoformat(), "period_end": end.isoformat()}
        if self._period and self._period.startswith("previous_day:"):
            base_attrs["previous_day_offset"] = int(self._period.split(":", 1)[1])
        if self._metric == METRIC_WEEKDAY_MAX:
            return self._weekday_max()
        total = sum(summary.total_seconds for summary in summaries)
        if self._metric == METRIC_AVERAGE_START_TIME:
            return average_time_of_day(
                sum(summary.start_time_sin for summary in summaries),
                sum(summary.start_time_cos for summary in summaries),
                sum(summary.start_time_count for summary in summaries),
            ), base_attrs
        if self._metric == METRIC_AVERAGE_END_TIME:
            return average_time_of_day(
                sum(summary.end_time_sin for summary in summaries),
                sum(summary.end_time_cos for summary in summaries),
                sum(summary.end_time_count for summary in summaries),
            ), base_attrs
        count = sum(summary.sessions_started for summary in summaries)
        if self._metric == METRIC_TOTAL_DURATION:
            return self._duration_value(total), {
                **base_attrs,
                "formatted": format_duration(total),
            }
        if self._metric == METRIC_SESSION_COUNT:
            return count, base_attrs
        if self._metric == METRIC_AVERAGE_DAILY_DURATION:
            return self._duration_value(
                total / len(summaries) if summaries else 0
            ), base_attrs
        if self._metric == METRIC_AVERAGE_SESSION_DURATION:
            return self._duration_value(total / count if count else None), base_attrs
        longest = max(
            (summary.longest_session_seconds for summary in summaries), default=0
        )
        if self._metric == METRIC_LONGEST_SESSION_DURATION:
            return self._duration_value(longest), base_attrs
        if self._metric == METRIC_SHORTEST_SESSION_DURATION:
            values = [
                summary.shortest_session_seconds
                for summary in summaries
                if summary.shortest_session_seconds is not None
            ]
            return self._duration_value(min(values) if values else None), base_attrs
        return None, {}

    def _weekday_max(self) -> tuple[str | None, dict[str, Any]]:
        totals: dict[str, float] = defaultdict(float)
        days: dict[str, int] = defaultdict(int)
        for date, summary in self._runtime.daily_summaries.items():
            weekday = datetime.fromisoformat(date).strftime("%A").lower()
            totals[weekday] += summary.total_seconds
            days[weekday] += 1
        if not totals:
            return None, {}
        winner = max(totals, key=totals.get)
        return winner, {
            day: {"total_seconds": totals[day], "observed_days": days[day]}
            for day in totals
        }

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._runtime.signal, self.async_write_ha_state
            )
        )


_DURATION_METRICS = {
    METRIC_TOTAL_DURATION,
    METRIC_CURRENT_SESSION_DURATION,
    METRIC_LAST_SESSION_DURATION,
    METRIC_AVERAGE_DAILY_DURATION,
    METRIC_AVERAGE_SESSION_DURATION,
    METRIC_LONGEST_SESSION_DURATION,
    METRIC_SHORTEST_SESSION_DURATION,
    METRIC_TIME_SINCE_LAST_SESSION,
}


def _metric_name(metric: str, period: str | None) -> str:
    labels = {
        item: item.replace("_", " ").title()
        for item in _DURATION_METRICS
        | {
            METRIC_SESSION_COUNT,
            METRIC_TIME_SINCE_LAST_SESSION,
            METRIC_AVERAGE_START_TIME,
            METRIC_AVERAGE_END_TIME,
            METRIC_WEEKDAY_MAX,
            METRIC_LAST_SESSION_START,
            METRIC_LAST_SESSION_END,
        }
    }
    period_label = (
        (period or "").replace("current_", "Current ").replace("previous_day:", "Last ")
    )
    return f"{labels.get(metric, metric)} {period_label}".strip()


def _metric_icon(metric: str) -> str:
    return "mdi:counter" if metric == METRIC_SESSION_COUNT else "mdi:timer-outline"
