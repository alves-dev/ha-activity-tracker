# Feature: Guided Monitor Management

## What

Users create, edit, and copy monitors through the complete Activity Rules
sidebar editor.

## Why

Users need a discoverable way to create and safely change monitors without
assembling serialized rules or losing track of what will be saved.

## Acceptance Criteria

- [x] The sidebar offers zone presence and custom rule choices for new monitors.
- [x] After every custom condition, setup shows a readable summary of the
  expression collected so far and supports AND/OR grouping.
- [x] Setup requires at least one report period and a metric for each period.
- [x] Editing traverses the complete monitor contract.
- [x] Editing a rule or midnight policy preserves retained summaries and
  applies the new behavior to future evaluations.
- [x] Rule editing starts from the monitor's saved conditions and exposes their
  current evaluation snapshot before the user changes them.
- [x] Setup and editing validate template-rule start and stop expressions before
  the monitor is saved.
- [x] The Activity Rules sidebar lets an admin create or edit the complete
  monitor contract without leaving the workspace, then shows a server-computed
  review before applying it.
- [x] The native integration configuration flow is not exposed; the sidebar is
  the only monitor management path.

## Related

- [Project Intent](project-intent.md)
- [Decision: Closed Rolling Report Windows and Panel-Only Editing](../decisions/026-closed-rolling-report-windows-and-panel-only-editing.md)
- [Decision: Unified Activity Rules](../decisions/014-unified-activity-rules.md)
- [Decision: Unified Rule Data Reset](../decisions/016-unified-rule-data-reset-and-no-recorder-import.md)
- [Decision: Native Rule Inspection and Control](../decisions/017-rule-editor-inspection-and-control.md)
- [Decision: Template Activity Rules](../decisions/018-template-activity-rules.md)
- [Decision: Sidebar Rule Workbench](../decisions/019-sidebar-rule-workbench.md)
- [Decision: Sidebar Draft Editor](../decisions/021-sidebar-draft-editor.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active; panel-only management delivered on 2026-09-24
