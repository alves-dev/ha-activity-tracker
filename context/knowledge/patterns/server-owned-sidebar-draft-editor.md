# Pattern: Server-Owned Sidebar Draft Editor

## Description

Keep browser editing temporary and let the integration backend own
normalization, validation, previews, review data, and persistence.

## When to Use

Use this pattern for an administrator-only Home Assistant panel that edits a
config entry with a nested contract or rules that must share backend runtime
validation.

## Pattern

Open an existing entry as a JSON-compatible draft, or create a default draft.
Send the draft to a protected validation command before applying it. The
server returns normalized data, live previews, and a change summary. Apply the
same draft through a protected command that calls the config-entry API; the
browser never writes the entry directly.

## Example

```python
preview = draft_preview(hass, draft, entry)
data, options = normalize_draft(hass, draft)
hass.config_entries.async_update_entry(
    entry, title=data[CONF_NAME], data=data, options=options
)
```

## Files Using This Pattern

- [panel.py](../../../custom_components/activity_tracker/panel.py) - exposes
  admin-only websocket open, validate, apply, and subscription commands.
- [panel_editor.py](../../../custom_components/activity_tracker/panel_editor.py)
  - owns draft hydration, normalization, preview, and persistence.
- [activity-rules-panel.js](../../../custom_components/activity_tracker/frontend/activity-rules-panel.js)
  - holds unsaved drafts and renders the server responses.
- [test_panel.py](../../../tests/test_panel.py) - verifies the protected panel
  contract and editor behavior.

## Related

- [Decision: Sidebar Draft Editor](../../decisions/021-sidebar-draft-editor.md)
- [Decision: Sidebar Rule Workbench](../../decisions/019-sidebar-rule-workbench.md)
- [Decision: Home Assistant Config-Entry Integration](../../decisions/002-home-assistant-integration-architecture.md)
- [Feature: Guided Monitor Management](../../intent/feature-guided-monitor-management.md)
- [Feature: Flexible Activity Monitoring](../../intent/feature-flexible-activity-monitoring.md)

## Status

- **Created**: 2026-09-19
- **Status**: Active
