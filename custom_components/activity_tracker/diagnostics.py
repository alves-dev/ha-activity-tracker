"""Redacted diagnostics for unified Activity Tracker monitors."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_RULE, CONF_TEMPLATE, DOMAIN, OPT_RETENTION_DAYS
from .rules import referenced_entity_ids


def _redact_source_id(source_id: str) -> str:
    return f"sha256:{sha256(source_id.encode()).hexdigest()[:12]}"


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return an allow-listed operational view without activity details."""
    runtime = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    data = getattr(runtime, "_data", {}) if runtime is not None else {}
    summaries = data.get("daily_summaries", {}) if isinstance(data, dict) else {}
    dates = sorted(date for date in summaries if isinstance(date, str))
    rule = entry.data.get(CONF_RULE, {})
    rule = rule if isinstance(rule, dict) else {}
    source_ids = referenced_entity_ids(rule.get("start_when", {}))
    source_ids |= referenced_entity_ids(rule.get("stop_when", {}))
    checkpoint = data.get("checkpoint") if isinstance(data, dict) else None
    return {
        "template": entry.data.get(CONF_TEMPLATE, "custom"),
        "source_count": len(source_ids),
        "source_ids": sorted(_redact_source_id(source) for source in source_ids),
        "retention_days": entry.options.get(OPT_RETENTION_DAYS),
        "stored_date_range": {"from": dates[0], "to": dates[-1]} if dates else None,
        "summary_count": len(dates),
        "checkpoint_open": isinstance(checkpoint, dict),
        "last_cleanup": data.get("last_cleanup") if isinstance(data, dict) else None,
        "availability_reason": getattr(runtime, "storage_error", None),
    }
