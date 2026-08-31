# Decision: Calendar Boundaries and Local Time

## Context

Reports are calendar based, but the current week begins on Monday in code and the
boundary behavior around daylight-saving transitions is not yet contractually
defined.

## Proposed Decision

Use Home Assistant's configured local timezone and first weekday for all calendar
boundaries.

- A day runs from local midnight to the next local midnight. Durations use aware
  instants, so a local day can be shorter or longer during daylight-saving changes.
- Current-day, current-week, and current-month periods begin at their configured
  local calendar boundary and end at the current instant.
- A rolling `N`-day period covers the current local day and its preceding `N - 1`
  local dates. It is a calendar-day range, not an exact `N × 24`-hour interval.
- Week start comes from the Home Assistant locale/configuration API. If that
  setting is unavailable, use the platform's documented default and expose no
  private integration-specific preference.
- Import, retention, aggregation, availability, and display calculations use the
  same boundary helper so month/year and DST transitions cannot disagree.

## Rationale

Users interpret reports in their Home Assistant calendar rather than in UTC or a
hard-coded locale. A shared boundary rule prevents aggregation and availability
from describing different time windows.

## Alternatives Considered

- Fixed Monday weeks. Rejected because it ignores the user's configured locale.
- Exact-hour rolling windows. Rejected because the product describes rolling
  calendar days and daily aggregates are the durable storage unit.
- Store aggregates in UTC dates. Rejected because it makes local reports harder
  to explain and changes their dates around timezone boundaries.

## Outcomes

Implemented on 2026-08-27 for local report windows. Week start reads the
available Home Assistant configuration and uses the platform default when absent;
rolling windows remain local calendar-date ranges.

## Related

- [Feature: Activity Reporting](../intent/feature-activity-reporting.md)
- [Feature: Durable Activity History](../intent/feature-durable-activity-history.md)
- [Decision: Compact Daily Summary Storage](004-compact-daily-summary-storage.md)
- [Pattern: Calendar-Day Session Aggregation](../knowledge/patterns/calendar-day-session-aggregation.md)

## Status

- **Created**: 2026-08-27
- **Status**: Accepted
