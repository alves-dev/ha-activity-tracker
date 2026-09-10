"""Tests for reset-only storage and redacted unified diagnostics."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.activity_tracker.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.activity_tracker.storage import (
    STORAGE_VERSION,
    ActivityTrackerStorage,
)


async def test_storage_rejects_every_non_unified_schema() -> None:
    with patch("custom_components.activity_tracker.storage.Store") as store_class:
        store = store_class.return_value
        storage = ActivityTrackerStorage(SimpleNamespace(), "entry")
        store.async_load = AsyncMock(return_value=None)
        assert await storage.async_load() == {
            "version": STORAGE_VERSION,
            "daily_summaries": {},
        }
        store.async_load = AsyncMock(return_value={"version": 2, "daily_summaries": {}})
        with pytest.raises(ValueError, match="Unsupported"):
            await storage.async_load()


async def test_diagnostics_redacts_rule_sources_and_activity_details() -> None:
    entry = SimpleNamespace(
        entry_id="monitor",
        data={
            "template": "custom",
            "rule": {
                "start_when": {
                    "type": "state",
                    "entity_id": "sensor.private",
                    "states": ["on"],
                },
                "stop_when": {},
            },
        },
        options={"retention_days": 30},
    )
    runtime = SimpleNamespace(
        _data={
            "daily_summaries": {"2026-09-01": {"total_seconds": 60}},
            "checkpoint": {"started_at": "private"},
        },
        storage_error=None,
    )
    result = await async_get_config_entry_diagnostics(
        SimpleNamespace(data={"activity_tracker": {"monitor": runtime}}), entry
    )

    assert result["source_count"] == 1
    assert "sensor.private" not in str(result)
    assert "private" not in str(result)
