# Decision: Session Day Attribution and Report Periods

## Context

Daily summaries currently always split an activity at local midnight. Some
activities, notably sleep, are more useful when attributed only to the day they
end. Extra day reports also use a rolling range whose `Last 1` means today,
which conflicts with the requested closed-day meaning.

## Decision

Every monitor selects one cross-midnight policy:

- `started_day`: attribute the whole logical session and one session count to its
  local start date;
- `ended_day`: attribute the whole logical session and one session count to its
  local end date; or
- `split_at_midnight`: attribute each local-time fragment to its date and count
  one attributed session on every participating date.

Daily aggregates store compact duration, count, extrema, and circular local-time
components for actual logical session starts and ends. Average start time is
calculated from starts in the period; average end time is calculated from ends
in the period. It is therefore safe around midnight without retaining detailed
sessions.

`previous_day:N` is a single closed local date offset by N days: `N=1` is
yesterday. It replaces the ambiguous extra rolling-day setting. Current day,
week, and month remain observed-to-date calendar reports.

The current-day total-duration sensor is a `total_increasing` daily counter and
is graphed with `sum`. Other report totals are point-in-time measurements. The
duration-since-last-session sensor uses the selected duration unit and updates
on the regular presentation refresh. Unknown duration is not stored or exposed.

## Rationale

Attribution is a user-facing interpretation, so it belongs to each activity and
must affect every daily metric consistently. Circular components avoid an
incorrect noon average for start times close to midnight. A metered daily total
matches Home Assistant long-term-statistics semantics and makes daily graphs
reliable.

## Alternatives Considered

- Keep compulsory midnight splitting. Rejected because it cannot represent the
  common convention that one sleep belongs to the morning it ends.
- Keep `rolling_days:1` as today. Rejected because a named historical-day sensor
  must be a completed, stable date.
- Calculate timing averages from an archive of sessions. Rejected because the
  integration intentionally retains compact aggregates rather than a permanent
  activity archive.

## Outcomes

Implemented on 2026-09-09. Storage records compact circular timing components;
the three attribution policies, closed historical days, duration-since-last
session, and current-day `total_increasing` statistics are active. This decision
supersedes the mandatory splitting part of Decision 004.

## Related

- [Feature: Activity Reporting](../intent/feature-activity-reporting.md)
- [Feature: Durable Activity History](../intent/feature-durable-activity-history.md)
- [Decision: Compact Daily Summary Storage](004-compact-daily-summary-storage.md)
- [Decision: Calendar Boundaries and Local Time](009-calendar-boundaries.md)
- [Unified-rule refactor plan](../evolution/2026-09-09-unified-rule-refactor-implementation-plan.md)

## Status

- **Created**: 2026-09-09
- **Status**: Accepted
