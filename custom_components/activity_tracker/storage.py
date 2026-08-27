"""Versioned per-monitor storage."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 2


class ActivityTrackerStorage:
    """Persist daily summaries and the small runtime checkpoint."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            # Keep Home Assistant's envelope at v1; the payload has an explicit
            # integration schema version and can migrate without losing v1 data.
            hass, 1, f"{DOMAIN}.{entry_id}", atomic_writes=True
        )

    async def async_load(self) -> dict[str, Any]:
        data = await self._store.async_load()
        if data is None:
            return {"daily_summaries": {}, "applications": {}}
        if not isinstance(data, dict):
            raise ValueError("Activity Tracker storage payload is not an object")
        version = data.get("version", 1)
        if version == 1:
            data = self._migrate_v1(data)
        elif version != STORAGE_VERSION:
            raise ValueError(f"Unsupported Activity Tracker storage version: {version}")
        if not isinstance(data.get("daily_summaries", {}), dict):
            raise ValueError("Activity Tracker daily summaries are invalid")
        data.setdefault("daily_summaries", {})
        data.setdefault("applications", {})
        return data

    async def async_save(self, payload: dict[str, Any]) -> None:
        data = dict(payload)
        data["version"] = STORAGE_VERSION
        await self._store.async_save(data)

    async def async_remove(self) -> None:
        await self._store.async_remove()

    @staticmethod
    def _migrate_v1(payload: dict[str, Any]) -> dict[str, Any]:
        """Return a v2 copy of a valid legacy payload without writing it yet."""
        migrated = dict(payload)
        migrated["version"] = STORAGE_VERSION
        migrated.setdefault("daily_summaries", {})
        migrated.setdefault("applications", {})
        for summary in migrated["daily_summaries"].values():
            if isinstance(summary, dict):
                # v1 did not prove that a retained date was fully observed.
                summary.setdefault("complete", False)
                summary.setdefault("rule_version", 1)
        checkpoint = migrated.get("checkpoint")
        if isinstance(checkpoint, dict):
            checkpoint = dict(checkpoint)
            checkpoint.setdefault("state", "active")
            checkpoint.setdefault(
                "active_segment_started_at", checkpoint.get("started_at")
            )
            checkpoint.setdefault("active_seconds", 0)
            checkpoint.setdefault("pending_days", {})
            migrated["checkpoint"] = checkpoint
        return migrated
