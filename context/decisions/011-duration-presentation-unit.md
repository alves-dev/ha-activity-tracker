# Decision: Per-Monitor Duration Presentation Unit

## Context

Activity durations are accounted for and stored as seconds, and every duration
sensor currently publishes seconds as its native unit. This is precise but makes
common activity reports less readable when they span many minutes or hours.
Users need to select a familiar display unit independently for each monitor.

## Decision

Keep seconds as the canonical accounting and storage unit. Store a
presentation-only duration-unit option on each monitor and publish all of that
monitor's duration sensors in the selected native Home Assistant time unit.

- New monitors default to hours.
- Existing monitors without the option continue to publish seconds, preserving
  their current entity state contract.
- Supported units are seconds, minutes, and hours.
- A duration-unit edit is presentation-only: it neither changes retained
  summaries nor offers history clear or Recorder reimport actions.

## Rationale

Canonical seconds avoid rounding and keep session accounting, retained data, and
calculations independent of how a user reads the reports. Publishing one stable
native unit per monitor gives Home Assistant a numeric sensor value with the
correct unit while making the primary UI value useful for typical long-running
activities. Preserving seconds for existing monitors avoids silently changing
values consumed by dashboards or automations.

## Alternatives Considered

- Keep seconds and rely only on a formatted attribute. Rejected because the
  primary Home Assistant sensor state remains difficult to read.
- Use an automatically changing unit based on each value. Rejected because one
  sensor would not have a stable numeric unit for displays, history, or
  automations.
- Convert persisted summaries to the selected unit. Rejected because it loses
  precision and couples accounting to presentation.

## Outcomes

Implemented on 2026-08-28. New monitors offer hours as their default display
unit, while existing monitors keep their previous seconds output until changed.

## Related

- [Feature: Activity Reporting](../intent/feature-activity-reporting.md)
- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Decision: Compact Daily Summary Storage](004-compact-daily-summary-storage.md)
- [Decision: Administrative History Actions and Redacted Diagnostics](010-administrative-history-and-diagnostics.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)

## Status

- **Created**: 2026-08-28
- **Status**: Accepted
