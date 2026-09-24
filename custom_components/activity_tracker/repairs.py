"""Repairs for Activity Tracker configuration metadata."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import CONF_IMAGE_URL, DOMAIN

ISSUE_MISSING_IMAGE = "missing_image"


def async_update_image_issue(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Create or clear the missing-activity-image repair."""
    issue_id = f"{ISSUE_MISSING_IMAGE}_{entry.entry_id}"
    image_url = entry.data.get(CONF_IMAGE_URL)
    if isinstance(image_url, str) and image_url.strip():
        ir.async_delete_issue(hass, DOMAIN, issue_id)
        return
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=False,
        is_persistent=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_MISSING_IMAGE,
        translation_placeholders={"activity_name": entry.title},
    )
