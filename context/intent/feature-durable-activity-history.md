# Feature: Durable Activity History

## What

Completed activity is retained as compact daily summaries for a user-selected
number of local calendar days.

## Acceptance Criteria

- [x] Completed activity remains available for the configured retention period.
- [x] Sessions crossing midnight can be assigned to their start day, end day,
  or split at actual local midnight.
- [x] Split attribution records one session for every participating day.
- [x] Short completed sessions can be excluded by a user-selected threshold.
- [x] New monitors begin with empty retained history and never import Recorder
  history.

## Related

- [Project Intent](project-intent.md)
- [Decision: Session Day Attribution](../decisions/015-session-day-attribution-and-report-periods.md)
- [Decision: Unified Rule Data Reset](../decisions/016-unified-rule-data-reset-and-no-recorder-import.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active; delivered on 2026-09-09
