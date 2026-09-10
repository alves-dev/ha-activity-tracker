# Decision: Sidebar Rule Workbench

## Context

The native options flow is the authoritative editor, but it is too linear to
make a multi-condition activity easy to inspect. Users need a live visual view
of all monitors, their start/stop trees, and current condition results without
duplicating save behavior in browser code.

## Decision

Add an admin-only **Activity Rules** sidebar panel, served locally by the
integration as a standards-based custom element. Register a read-only websocket
subscription that returns all monitor rules, recursive condition snapshots,
current result, observed state, and pending deadline. The panel adapts through
Home Assistant CSS theme variables; it contains no hard-coded light or dark
palette.

The later complete editor is defined by [Decision: Sidebar Draft
Editor](021-sidebar-draft-editor.md). It validates and applies browser drafts
through an admin-only backend contract instead of hosting flows or allowing
browser-side entry mutation.

## Rationale

One read model lets a user understand a rule spatially while keeping the
existing config-entry validation, permissions, and destructive-history
safeguards intact. A local module avoids external-resource approval and works
with Home Assistant themes.

## Alternatives Considered

- Build editing directly into the first panel release. Deferred because it
  would duplicate options-flow validation and confirmation semantics.
- Use hard-coded colors. Rejected because it breaks light, dark, and custom
  Home Assistant themes.
- Expose snapshots to every authenticated user. Rejected because rule values
  and current entity state can reveal sensitive activity information.

## Outcomes

Implemented and smoke-tested on 2026-09-10. The integration serves a local
custom-element module, registers an admin-only sidebar panel, and streams
read-only snapshots through a protected websocket subscription. The panel
renders recursive start/stop trees, current state/template result, and pending
deadlines using Home Assistant theme variables. Its later write-surface
decision is recorded in [Decision 021](021-sidebar-draft-editor.md).

## Related

- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Plan: Activity Rule Control Workbench](../evolution/2026-09-10-rule-control-workbench-plan.md)
- [Decision: Native Rule Inspection and Control](017-rule-editor-inspection-and-control.md)
- [Decision: Sidebar Draft Editor](021-sidebar-draft-editor.md)

## Status

- **Created**: 2026-09-10
- **Status**: Accepted
