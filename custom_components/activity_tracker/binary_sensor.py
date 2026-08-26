"""Current activity binary sensor."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, INTEGRATION_NAME
from .runtime import ActivityTrackerRuntime


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the monitor activity entity."""
    runtime: ActivityTrackerRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ActivityBinarySensor(runtime)])


class ActivityBinarySensor(BinarySensorEntity):
    """Expose whether the configured monitor is active now."""

    _attr_has_entity_name = True
    _attr_name = "Active"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:timer-play-outline"

    def __init__(self, runtime: ActivityTrackerRuntime) -> None:
        self._runtime = runtime
        self._attr_unique_id = f"{runtime.entry.entry_id}_active"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, runtime.entry.entry_id)},
            name=runtime.entry.title,
            manufacturer=INTEGRATION_NAME,
            model="Activity monitor",
        )

    @property
    def is_on(self) -> bool:
        return self._runtime.session is not None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._runtime.signal, self.async_write_ha_state
            )
        )
