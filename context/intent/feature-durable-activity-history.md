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

## Related

- [Project Intent](project-intent.md)
- [Decision: Compact Daily Summary Storage](../decisions/004-compact-daily-summary-storage.md)
- [Decision: Recorder History Reconstruction](../decisions/005-recorder-history-reconstruction.md)
- [Pattern: Calendar-Day Session Aggregation](../knowledge/patterns/calendar-day-session-aggregation.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Active (already implemented)
