# Feature: Activity Reporting

## What

Each monitor exposes only the report and monitor-wide measurements selected by
the user. Reports cover current local day, week, month, and selected closed
historical days.

## Acceptance Criteria

- [x] Users select report metrics independently for every report period.
- [x] `Last 1` is yesterday and `Last 2` is the day before yesterday.
- [x] Average start and end times use circular local-time averages.
- [x] Time since the latest completed session uses the selected duration unit.
- [x] Unknown-duration reporting is absent.
- [x] The current-day total is a `total_increasing` sensor with `sum`
  statistics; other totals are measurements.

## Related

- [Project Intent](project-intent.md)
- [Decision: Session Day Attribution](../decisions/015-session-day-attribution-and-report-periods.md)
- [Pattern: Selected Metric Entity Factory](../knowledge/patterns/selected-metric-entity-factory.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active; delivered on 2026-09-09
