"""Tests for storage and the current-activity entity."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from custom_components.activity_tracker.binary_sensor import ActivityBinarySensor
from custom_components.activity_tracker.binary_sensor import (
    async_setup_entry as async_setup_binary,
)
from custom_components.activity_tracker.const import DOMAIN
from custom_components.activity_tracker.storage import ActivityTrackerStorage


async def test_storage_load_save_and_remove() -> None:
    hass = SimpleNamespace()
    with patch("custom_components.activity_tracker.storage.Store") as store_class:
        store = store_class.return_value
        storage = ActivityTrackerStorage(hass, "entry")
        store.async_load = AsyncMock(return_value=None)
        store.async_save = AsyncMock()
        store.async_remove = AsyncMock()
        assert await storage.async_load() == {"daily_summaries": {}, "applications": {}}
        store.async_load = AsyncMock(return_value={})
        loaded = await storage.async_load()
        assert loaded["daily_summaries"] == {}
        await storage.async_save({"daily_summaries": {}})
        assert store.async_save.await_args.args[0]["version"] == 1
        await storage.async_remove()
        store.async_remove.assert_awaited_once()


async def test_binary_sensor_is_added_for_runtime_and_reports_activity() -> None:
    runtime = SimpleNamespace(
        entry=SimpleNamespace(entry_id="entry", title="Monitor"),
        session=object(),
        signal="signal",
    )
    sensor = ActivityBinarySensor(runtime)
    assert sensor.is_on is True
    runtime.session = None
    assert sensor.is_on is False
    hass = SimpleNamespace(data={DOMAIN: {"entry": runtime}})
    added: list[object] = []
    await async_setup_binary(hass, runtime.entry, added.extend)
    assert isinstance(added[0], ActivityBinarySensor)
