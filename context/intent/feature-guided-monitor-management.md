# Feature: Guided Monitor Management

## What

Users create and edit monitors through focused in-application steps for the
template, source, rule conditions, behavior, report periods, and sensors.

## Acceptance Criteria

- [x] New setup offers zone presence and custom rule choices.
- [x] After every custom condition, setup shows a readable summary of the
  expression collected so far and supports AND/OR grouping.
- [x] Setup requires at least one report period and a metric for each period.
- [x] Editing traverses the complete monitor contract.
- [x] Editing a rule or midnight policy clears incompatible summaries only after
  explicit confirmation.

## Related

- [Project Intent](project-intent.md)
- [Decision: Unified Activity Rules](../decisions/014-unified-activity-rules.md)
- [Decision: Unified Rule Data Reset](../decisions/016-unified-rule-data-reset-and-no-recorder-import.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active; delivered on 2026-09-09
