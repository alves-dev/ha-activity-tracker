# Feature: Foreground Application Insights

## What

Users can monitor the application currently in the foreground on a chosen device source. The monitor identifies the current application and reports activity separately when the foreground application changes.

## Why

This gives users a practical view of application use without trying to infer unreported background behavior or classify applications on their behalf.

## Acceptance Criteria

- [ ] A user can select a source for foreground-application activity.
- [ ] An application change ends the previous activity and begins the next one.
- [ ] The current foreground application is visible while activity is active.
- [ ] Application activity is included in retained reports.

## Related

- [Project Intent](project-intent.md)
- [Decision: Real-Time Session Accounting](../decisions/003-real-time-session-accounting.md)
- [Pattern: Activity State Classification](../knowledge/patterns/activity-state-classification.md)
- [Pattern: Calendar-Day Session Aggregation](../knowledge/patterns/calendar-day-session-aggregation.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Active (already implemented)
