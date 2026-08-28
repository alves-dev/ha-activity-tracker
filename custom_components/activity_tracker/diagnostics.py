"""Redacted diagnostics for Activity Tracker monitors."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ENTITY_ID,
    CONF_MONITOR_TYPE,
    CONF_PRESENCE_ENTITY_ID,
    DOMAIN,
    OPT_RETENTION_DAYS,
)


def _redact_source_id(source_id: object) -> str | None:
    """Return a stable opaque identifier without disclosing the source entity."""
    if not isinstance(source_id, str) or not source_id:
        return None
    return f"sha256:{sha256(source_id.encode()).hexdigest()[:12]}"


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return the allow-listed operational state for one monitor."""
    runtime = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    data = getattr(runtime, "_data", {}) if runtime is not None else {}
    summaries = data.get("daily_summaries", {}) if isinstance(data, dict) else {}
    dates = sorted(date for date in summaries if isinstance(date, str))
    checkpoint = data.get("checkpoint") if isinstance(data, dict) else None
    last_import = data.get("last_recorder_import") if isinstance(data, dict) else None
    rule_versions = [
        value.get("rule_version", 1)
        for value in summaries.values()
        if isinstance(value, dict) and isinstance(value.get("rule_version", 1), int)
    ]
    warnings = last_import.get("warnings", []) if isinstance(last_import, dict) else []
    import_result = (
        {
            key: last_import[key]
            for key in (
                "status",
                "rebuilt_days",
                "preserved_days",
                "processed_sessions",
            )
            if key in last_import
        }
        | {"warning_count": len(warnings) if isinstance(warnings, list) else 0}
        if isinstance(last_import, dict)
        else None
    )
    return {
        "monitor_type": entry.data.get(CONF_MONITOR_TYPE),
        "source_id": _redact_source_id(
            entry.data.get(CONF_PRESENCE_ENTITY_ID, entry.data.get(CONF_ENTITY_ID))
        ),
        "rule_version": max(rule_versions, default=1),
        "retention_days": entry.options.get(OPT_RETENTION_DAYS),
        "stored_date_range": {"from": dates[0], "to": dates[-1]} if dates else None,
        "summary_count": len(dates),
        "checkpoint_state": (
            checkpoint.get("state") if isinstance(checkpoint, dict) else None
        ),
        "last_import": import_result,
        "last_cleanup": data.get("last_cleanup") if isinstance(data, dict) else None,
        "availability_reason": getattr(runtime, "storage_error", None),
    }
