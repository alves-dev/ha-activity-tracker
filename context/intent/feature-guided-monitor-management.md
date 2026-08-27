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

## Related

- [Project Intent](project-intent.md)
- [Decision: Home Assistant Config-Entry Integration](../decisions/002-home-assistant-integration-architecture.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Active (already implemented)
