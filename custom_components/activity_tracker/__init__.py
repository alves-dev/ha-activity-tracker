"""Activity Tracker custom integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .runtime import ActivityTrackerRuntime


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an Activity Tracker monitor."""
    runtime = ActivityTrackerRuntime(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime
    await runtime.async_setup()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Activity Tracker monitor."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        runtime = hass.data[DOMAIN].pop(entry.entry_id, None)
        if runtime is not None:
            await runtime.async_unload()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove persisted monitor data with its config entry."""
    runtime = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if runtime is not None:
        await runtime.async_delete_storage()
    else:
        await ActivityTrackerRuntime.async_delete_entry_storage(hass, entry.entry_id)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the monitor after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
