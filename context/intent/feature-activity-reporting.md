# Feature: Activity Reporting

## What

Each monitor can expose user-selected measurements, including activity duration, session count, current and latest sessions, timing, averages, extremes, and weekday summaries. Reports cover today, the current week, the current month, and user-selected rolling calendar-day ranges.

## Why

Users need concise answers to both current and historical questions about activity, such as how long something was used, how frequently it happened, and when it last occurred.

## Acceptance Criteria

- [ ] Users can select which measurements a monitor exposes.
- [ ] Duration and count reports are available for selected calendar and rolling periods.
- [ ] Current activity and latest completed activity information are available when relevant.
- [ ] A report indicates when a requested rolling range exceeds retained history.

## Delivered Behavior (2026-08-27)

- [x] Reports distinguish observed-to-date values from periods without sufficient
  complete history, with a user-actionable reason.
- [x] Week and rolling-day reports use the available Home Assistant local calendar
  configuration, with Monday as the documented platform fallback.

## Related

- [Project Intent](project-intent.md)
- [Decision: Home Assistant Config-Entry Integration](../decisions/002-home-assistant-integration-architecture.md)
- [Decision: Compact Daily Summary Storage](../decisions/004-compact-daily-summary-storage.md)
- [Decision: Data Quality and Period Completeness](../decisions/007-data-quality-and-period-completeness.md)
- [Decision: Calendar Boundaries and Local Time](../decisions/009-calendar-boundaries.md)
- [Pattern: Selected Metric Entity Factory](../knowledge/patterns/selected-metric-entity-factory.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Active (already implemented)
