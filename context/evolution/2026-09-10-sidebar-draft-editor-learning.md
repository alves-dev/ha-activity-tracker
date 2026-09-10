# Learning: Server-Owned Drafts Make Sidebar Editors Safe

## Observation

Embedding Home Assistant config and options flows in a custom panel made a
large activity contract linear and coupled the panel to transient HTTP form
schemas. Stale or over-complete browser form payloads produced HTTP 400 errors.

## Learning

For a complete custom sidebar editor, keep the browser state explicitly
unsaved and JSON-compatible. Expose a narrow, admin-protected backend contract
for opening a draft, validating and previewing it, reviewing a server-computed
diff, and applying it. Destructive effects must be classified and confirmed by
the backend at apply time, not merely acknowledged by a frontend dialog.

This preserves one server-side validation contract while allowing the UI to
present the whole activity model and recursive expression tree spatially.

During local smoke testing, a duplicate frontend method name silently shadowed
the asynchronous review action. Keep action handlers and render helpers named
distinctly, and include a browser-level check that an invalid draft produces
visible server validation errors.

## Applies To

- Future Activity Tracker workbench editors.
- Home Assistant custom panels that edit ConfigEntry-backed objects with
  destructive side effects.

## Related

- [Decision: Sidebar Draft Editor](../decisions/021-sidebar-draft-editor.md)
- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)

## Status

- **Created**: 2026-09-10
- **Status**: Active
