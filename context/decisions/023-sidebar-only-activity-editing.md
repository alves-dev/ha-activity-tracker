# Decision: Sidebar-Only Activity Editing

## Context

The complete Activity Rules editor now provides the only interface that can
reliably present recursive rules, live condition results, review diffs, and
history-impact confirmation. Exposing the legacy options flow from the
integration configuration page would create a second, incomplete editing path.

## Decision

Do not expose an options flow from `ConfigFlow`. Existing activities are edited
only in the admin-only Activity Rules sidebar, through its server-owned draft
validation and apply commands. The native configuration flow remains available
for initial setup.

## Outcome

Implemented on 2026-09-10. The options-flow implementation remains in the
module for compatibility with existing unit coverage, but Home Assistant no
longer advertises it as the integration's configure action.

## Status

- **Status**: Accepted
