# Feature: Guided Monitor Management

## What

Users set up and edit monitors through a guided in-application flow. They choose the activity definition, reporting periods, and the measurements they want to see, then can revise those choices later.

## Why

The setup experience makes activity tracking available to Home Assistant users without requiring manual configuration files, while allowing each monitor to match the user's reporting needs.

## Acceptance Criteria

- [ ] Setup guides the user through choosing an activity, behavior, reporting periods, and measurements.
- [ ] Setup requires at least one reporting period and one measurement.
- [ ] Users can edit an existing monitor's definition and reporting choices.
- [ ] The monitor has a user-provided name.

## Delivered Behavior (2026-08-28)

- [x] A rule-changing edit clearly offers keep, clear, or Recorder-reimport of
  retained history; presentation-only edits do not.
- [x] Clearing or reimporting history requires an explicit final confirmation.
- [x] Users can choose the duration display unit for each monitor without a
  history action.

## Related

- [Project Intent](project-intent.md)
- [Decision: Home Assistant Config-Entry Integration](../decisions/002-home-assistant-integration-architecture.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)
- [Decision: Administrative History Actions and Redacted Diagnostics](../decisions/010-administrative-history-and-diagnostics.md)
- [Decision: Per-Monitor Duration Presentation Unit](../decisions/011-duration-presentation-unit.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Active (already implemented)
