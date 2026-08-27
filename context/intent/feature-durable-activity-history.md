# Feature: Durable Activity History

## What

Completed activity is retained as daily summaries for a user-configured number of days. Activity crossing a calendar-day boundary contributes to both days, and users may optionally rebuild retained summaries from available historical records.

## Why

Users can keep useful reports after normal history retention has expired, while controlling how much monitor history is retained. Calendar-day accounting keeps daily and rolling reports understandable.

## Acceptance Criteria

- [ ] Completed activity remains available for the configured retention period.
- [ ] Activity spanning midnight is reflected in every affected calendar day.
- [ ] Short completed activity can be excluded using a user-selected threshold.
- [ ] Eligible users can request a rebuild from historical records.

## Delivered Behavior (2026-08-27)

- [x] Retained history remains safe through compatible storage upgrades; an
  unrecoverable storage problem does not silently erase it.
- [x] Imported and incomplete observation days are identified so complete-history
  reports do not overstate their coverage.
- [x] Recorder reconstruction runs after monitor startup, replaces only the
  Recorder-backed date range, preserves retained outer summaries, and records a
  compact result for safe reimport troubleshooting.

## Related

- [Project Intent](project-intent.md)
- [Decision: Compact Daily Summary Storage](../decisions/004-compact-daily-summary-storage.md)
- [Decision: Recorder History Reconstruction](../decisions/005-recorder-history-reconstruction.md)
- [Decision: Data Quality and Period Completeness](../decisions/007-data-quality-and-period-completeness.md)
- [Decision: Storage Migration and Import Safety](../decisions/008-storage-migration-and-import-safety.md)
- [Decision: Calendar Boundaries and Local Time](../decisions/009-calendar-boundaries.md)
- [Pattern: Calendar-Day Session Aggregation](../knowledge/patterns/calendar-day-session-aggregation.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Active (already implemented)
