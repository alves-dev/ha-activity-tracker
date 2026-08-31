"""Tests for compatible report-selection configuration."""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.activity_tracker import async_migrate_entry
from custom_components.activity_tracker.configuration import (
    migrate_monitor_data,
    monitor_metric_selections,
    period_metric_selections,
)
from custom_components.activity_tracker.const import (
    CONF_ENABLED_METRICS,
    CONF_PERIOD_METRICS,
    CONF_PERIODS,
)


def test_legacy_cartesian_selection_migrates_without_losing_entities() -> None:
    legacy = {
        CONF_PERIODS: ["current_day", "rolling_days:30"],
        CONF_ENABLED_METRICS: [
            "total_duration",
            "average_session_duration",
            "last_session_duration",
        ],
    }

    migrated = migrate_monitor_data(legacy)

    assert CONF_PERIODS not in migrated
    assert migrated[CONF_PERIOD_METRICS] == {
        "current_day": ["total_duration", "average_session_duration"],
        "rolling_days:30": ["total_duration", "average_session_duration"],
    }
    assert migrated[CONF_ENABLED_METRICS] == ["last_session_duration"]
    assert period_metric_selections(legacy) == migrated[CONF_PERIOD_METRICS]
    assert monitor_metric_selections(legacy) == ["last_session_duration"]


async def test_config_entry_migration_updates_legacy_report_selection() -> None:
    entry = SimpleNamespace(
        version=1,
        data={
            CONF_PERIODS: ["current_day"],
            CONF_ENABLED_METRICS: ["total_duration"],
        },
    )
    updates: list[dict[str, object]] = []

    class Entries:
        def async_update_entry(self, updated_entry, **kwargs):
            assert updated_entry is entry
            updates.append(kwargs)

    hass = SimpleNamespace(config_entries=Entries())

    assert await async_migrate_entry(hass, entry)
    assert updates == [
        {
            "data": {
                CONF_PERIOD_METRICS: {"current_day": ["total_duration"]},
                CONF_ENABLED_METRICS: [],
            },
            "version": 2,
        }
    ]
