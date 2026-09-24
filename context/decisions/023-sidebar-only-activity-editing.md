# Decision: Sidebar-Only Activity Editing

## Context

The complete Activity Rules editor now provides the only interface that can
reliably present recursive rules, live condition results, review diffs, and
history-impact confirmation. Exposing the legacy options flow from the
integration configuration page would create a second, incomplete editing path.

## Decision

Do not expose a config or options flow. Existing and new activities are managed
only in the admin-only Activity Rules sidebar, through its server-owned draft
validation and apply commands.

## Outcome

Implemented on 2026-09-24. The native editor and its unit coverage were
removed, and the manifest no longer advertises a config flow. A minimal
compatibility module remains so Home Assistant can restore existing entries
without importing the removed editor.

## Status

- **Status**: Accepted
