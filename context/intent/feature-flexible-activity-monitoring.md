# Feature: Flexible Activity Monitoring

## What

Users define an activity with independent start and stop expressions over one or
more Home Assistant entities. A monitor represents one activity and exposes
whether it is active now.

## Acceptance Criteria

- [x] Start and stop rules support state, state-duration, and report-silence
  conditions with AND/OR groups.
- [x] Rules support numeric state or attribute comparisons with threshold
  operators and optional durations.
- [x] `unavailable` and `unknown` are explicit stop-condition values.
- [x] A delayed unavailable/unknown stop closes accounting at its first bad
  observation after confirmation at the requested deadline.
- [x] Zone presence and native-template rules are guided templates; other
  activities use custom rules.
- [x] While editing a custom rule, users can inspect its saved start and stop
  conditions, add or remove conditions, and see a current-state snapshot of
  each condition and expression.
- [x] A template-rule monitor accepts independent Home Assistant templates for
  start and stop, including expressions over entity attributes.
- [x] An admin can inspect every monitor's live start/stop condition tree from
  the Activity Rules sidebar, using the active Home Assistant theme.
- [x] An admin can add and edit monitors on one Activity Rules sidebar screen,
  including recursive AND/OR conditions, templates, live results, and pending
  deadlines before the monitor is saved.

## Related

- [Project Intent](project-intent.md)
- [Decision: Unified Activity Rules](../decisions/014-unified-activity-rules.md)
- [Decision: Native Rule Inspection and Control](../decisions/017-rule-editor-inspection-and-control.md)
- [Decision: Template Activity Rules](../decisions/018-template-activity-rules.md)
- [Decision: Numeric State Conditions](../decisions/022-numeric-state-conditions.md)
- [Decision: Sidebar Rule Workbench](../decisions/019-sidebar-rule-workbench.md)
- [Decision: Sidebar Draft Editor](../decisions/021-sidebar-draft-editor.md)
- [Pattern: Unified Rule Evaluation](../knowledge/patterns/unified-rule-evaluation.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active; template rules delivered on 2026-09-10
