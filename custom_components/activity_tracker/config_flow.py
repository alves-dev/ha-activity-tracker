"""Compatibility shim for existing Activity Tracker config entries."""

from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class ActivityTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Keep the legacy flow module importable without exposing an editor."""

    VERSION = 3

    async def async_step_user(self, _user_input=None):
        """Reject native creation; new activities belong in the admin panel."""
        return self.async_abort(reason="panel_only")


class ActivityTrackerOptionsFlow(config_entries.OptionsFlow):
    """Reject the removed native options editor for old entries."""

    async def async_step_init(self, _user_input=None):
        """Keep old option-flow imports safe during Home Assistant startup."""
        return self.async_abort(reason="panel_only")
