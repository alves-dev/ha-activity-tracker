"""Versioned per-monitor storage."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 1


class ActivityTrackerStorage:
    """Persist daily summaries and the small runtime checkpoint."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}"
        )

    async def async_load(self) -> dict[str, Any]:
        data = await self._store.async_load()
        if not isinstance(data, dict):
            return {"daily_summaries": {}, "applications": {}}
        data.setdefault("daily_summaries", {})
        data.setdefault("applications", {})
        return data

    async def async_save(self, payload: dict[str, Any]) -> None:
        payload["version"] = STORAGE_VERSION
        await self._store.async_save(payload)

    async def async_remove(self) -> None:
        await self._store.async_remove()
