"""Versioned per-monitor storage."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 3


class ActivityTrackerStorage:
    """Persist daily summaries and the small runtime checkpoint."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            # The Home Assistant storage envelope remains v1. The payload is an
            # intentionally incompatible unified-rule schema with no migration.
            hass, 1, f"{DOMAIN}.{entry_id}", atomic_writes=True
        )

    async def async_load(self) -> dict[str, Any]:
        data = await self._store.async_load()
        if data is None:
            return {"version": STORAGE_VERSION, "daily_summaries": {}}
        if not isinstance(data, dict):
            raise ValueError("Activity Tracker storage payload is not an object")
        version = data.get("version")
        if version != STORAGE_VERSION:
            raise ValueError(f"Unsupported Activity Tracker storage version: {version}")
        if not isinstance(data.get("daily_summaries", {}), dict):
            raise ValueError("Activity Tracker daily summaries are invalid")
        data.setdefault("daily_summaries", {})
        return data

    async def async_save(self, payload: dict[str, Any]) -> None:
        data = dict(payload)
        data["version"] = STORAGE_VERSION
        await self._store.async_save(data)

    async def async_remove(self) -> None:
        await self._store.async_remove()
