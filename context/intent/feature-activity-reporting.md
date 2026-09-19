# Feature: Activity Reporting

## What

Each monitor exposes only the report and monitor-wide measurements selected by
the user. Reports cover current local day, week, month, and selected closed
historical days.

## Why

Users can answer both immediate and historical questions about an activity
without interpreting raw state changes or maintaining separate helper sensors.

## Acceptance Criteria

- [x] Users select report metrics independently for every report period.
- [x] `Last 1` is yesterday and `Last 2` is the day before yesterday.
- [x] Average start and end times use circular local-time averages.
- [x] Time since the latest completed session uses the selected duration unit.
- [x] Reports do not present unclassified duration as if it were measured
  activity.
- [x] The current-day total behaves as a daily increasing total, while other
  totals represent the selected report at the time it is viewed.

## Related

- [Project Intent](project-intent.md)
- [Decision: Session Day Attribution](../decisions/015-session-day-attribution-and-report-periods.md)
- [Pattern: Selected Metric Entity Factory](../knowledge/patterns/selected-metric-entity-factory.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active; delivered on 2026-09-09
