# Learning: Keep a Custom Panel Read-Only Until Its Save Contract Exists

## Observation

A sidebar rule tree makes multi-condition activities much easier to understand,
but direct browser mutation would bypass the options flow's validation and
retained-history confirmation. The Home Assistant custom-panel API provides the
`hass` connection and theme context without requiring an external application.

## Learning

Serve the panel locally, make its websocket contract read-only and admin-only,
and use `--primary-background-color`, `--card-background-color`,
`--primary-text-color`, and other Home Assistant CSS variables instead of a
hard-coded palette. Keep the config-entry options flow as the sole write path
until a server-side draft, validation, diff, and confirmation contract is ready.

## Applies To

- Future Activity Rules editor phases.
- Home Assistant custom panels that expose sensitive configuration or state.

## Related

- [Decision: Sidebar Rule Workbench](../decisions/019-sidebar-rule-workbench.md)
- [Plan: Activity Rule Control Workbench](2026-09-10-rule-control-workbench-plan.md)

## Status

- **Created**: 2026-09-10
- **Status**: Active; its write-path guidance was superseded on 2026-09-10 by
  [Sidebar Draft Editor](2026-09-10-sidebar-draft-editor-learning.md)
