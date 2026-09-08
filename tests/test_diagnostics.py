"""Tests for redacted monitor diagnostics."""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.activity_tracker.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_allow_only_redacted_operational_metadata() -> None:
    entry = SimpleNamespace(
        entry_id="monitor-1",
        data={"monitor_type": "foreground_application", "entity_id": "sensor.phone"},
        options={"retention_days": 30},
    )
    runtime = SimpleNamespace(
        _data={
            "daily_summaries": {
                "2026-08-20": {"rule_version": 1, "applications": {"secret": {}}},
                "2026-08-21": {"rule_version": 2},
            },
            "checkpoint": {"state": "active", "started_at": "sensitive"},
            "last_recorder_import": {
                "status": "completed",
                "rebuilt_days": 2,
                "preserved_days": 4,
                "processed_sessions": 3,
                "warnings": ["boundary"],
                "range": {"start": "sensitive"},
            },
            "last_cleanup": "2026-08-21T00:00:00+00:00",
        },
        storage_error=None,
    )
    hass = SimpleNamespace(data={"activity_tracker": {entry.entry_id: runtime}})

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["source_id"].startswith("sha256:")
    assert "sensor.phone" not in str(diagnostics)
    assert diagnostics["rule_version"] == 2
    assert diagnostics["summary_count"] == 2
    assert diagnostics["last_import"] == {
        "status": "completed",
        "rebuilt_days": 2,
        "preserved_days": 4,
        "processed_sessions": 3,
        "warning_count": 1,
    }
    assert "secret" not in str(diagnostics)
    assert "sensitive" not in str(diagnostics)
