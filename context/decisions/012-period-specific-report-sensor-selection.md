# Decision: Period-Specific Report Sensor Selection

## Context

Report periods and selected metrics are currently configured independently. Every
period-aware metric is therefore exposed for every selected period. This creates
reports that the user did not request, such as a same-day average session length
when only a 30-day average is useful.

## Decision

Select period-aware report metrics independently for each chosen calendar or
rolling-day period. Sensors that describe the current or latest session remain
monitor-wide selections.

Existing monitor configurations migrate to the equivalent explicit selections,
so their exposed entities and values remain unchanged until the user edits the
monitor. Editing reporting selections is presentation-only and does not modify
retained activity history.

## Rationale

The relationship between a report question and its time range is meaningful.
Capturing that relationship directly avoids irrelevant entities while retaining
the concise, guided monitor setup and stable existing entity identities.

## Alternatives Considered

- Keep the global metric selection and hide unhelpful values. Rejected because
  it still creates unwanted entities and does not express the user's intent.
- Add an automatic rule that omits averages for short periods. Rejected because
  usefulness depends on the monitored activity and user goal, not a universal
  threshold.
- Require a separate monitor for each analytic range. Rejected because it
  duplicates activity accounting and makes related reports harder to manage.

## Outcomes

Implemented on 2026-08-31. New and edited monitors select period-aware sensors
one report period at a time. Config-entry migration converts legacy Cartesian
selections to their equivalent explicit pairs, retaining existing entity IDs and
values. Monitor-wide sensors remain optional, one-per-monitor selections.

## Related

- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Feature: Activity Reporting](../intent/feature-activity-reporting.md)
- [Decision: Home Assistant Config-Entry Integration](002-home-assistant-integration-architecture.md)
- [Decision: Administrative History Actions and Redacted Diagnostics](010-administrative-history-and-diagnostics.md)
- [Pattern: Selected Metric Entity Factory](../knowledge/patterns/selected-metric-entity-factory.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)

## Status

- **Created**: 2026-08-31
- **Status**: Accepted
