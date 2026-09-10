# Decision: Sidebar Native-Flow Editor

## Context

The Activity Rules sidebar makes multi-condition monitors understandable, but a
user must leave the workspace to add an activity or change the monitor they
are inspecting. Directly writing a config entry from the browser would bypass
the validated setup journey and the explicit retained-history confirmation
required for rule changes.

## Decision

Let the admin-only Activity Rules sidebar start and render Home Assistant's
existing configuration and options flows in the panel. Adding starts this
integration's config flow; editing starts the selected monitor's options flow.
The frontend submits only to Home Assistant's permission-checked config-flow
HTTP endpoints and renders the flow's serialized schema with Home Assistant's
native form component.

The integration retains ownership of fields, validation, review, entry
creation, updates, template previews, and retained-history confirmation. When
a flow completes, the sidebar re-subscribes to its live rule snapshot so the
new or updated monitor is visible immediately.

## Rationale

This gives the workbench creation and editing controls without creating a
second, drifting monitor contract. It also retains the platform's standard
administrator and config-entry permissions instead of adding a custom write
websocket API.

## Alternatives Considered

- Implement a separate browser-side editor and custom mutation endpoint.
  Rejected because it would duplicate validation and risk bypassing the
  history-clear confirmation.
- Navigate users away to the integrations page. Rejected because it breaks
  the rule-inspection context and does not satisfy in-workbench editing.
- Continue with a read-only panel. Rejected because users need to create and
  edit from the place where they understand the current rule tree.

## Outcomes

Implemented and validated on 2026-09-10. The existing configuration and
options flows are the single write contract; the panel is their themed host and
does not persist monitor data itself. The frontend syntax check, full test
suite, Ruff, integration-structure validation, and local static-module smoke
test passed.

## Related

- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Decision: Sidebar Rule Workbench](019-sidebar-rule-workbench.md)
- [Decision: Native Rule Inspection and Control](017-rule-editor-inspection-and-control.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)

## Superseded By

[Decision: Sidebar Draft Editor](021-sidebar-draft-editor.md)

## Status

- **Created**: 2026-09-10
- **Status**: Superseded on 2026-09-10 by Decision 021
