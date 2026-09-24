# Decision: Closed Rolling Report Windows and Panel-Only Editing

## Context

`previous_day:N` intentionally identifies one closed local calendar date, but
users also need reports over the last N complete dates before today. The native
config flow is now a second editing path and is incomplete relative to the
admin Activity Rules sidebar.

## Decision

- Keep `previous_day:N` as one exact closed date offset by N days.
- Add `rolling_window:N` as a closed rolling window containing the N complete
  local dates immediately before today. Its half-open boundary is
  `[today - N days at 00:00, today at 00:00)`.
- Expose the two period families with explicit labels and explanatory help in
  the Activity Rules sidebar. Sensors expose the selected window size or day
  offset as an attribute.
- Disable the native config flow and make the admin Activity Rules sidebar the
  sole creation and editing path. Keep only a non-editing compatibility shim
  for Home Assistant to restore existing entries safely.

## Rationale

The distinct serialized prefixes preserve existing `previous_day:N` entries
and entity IDs while making the new range semantics explicit. Half-open local
boundaries avoid second/microsecond rounding and include exactly N complete
calendar days. A single editor prevents the native flow from drifting behind
the recursive rule and live-preview capabilities of the sidebar.

## Alternatives Considered

- Change `previous_day:N` to mean a rolling range. Rejected because it changes
  existing sensor meanings and breaks retained user configuration.
- Keep both native and sidebar editors. Rejected because they provide unequal
  validation and user-visible capabilities.

## Related

- [Activity Reporting](../intent/feature-activity-reporting.md)
- [Decision: Sidebar-Only Activity Editing](023-sidebar-only-activity-editing.md)
- [Decision: Session Day Attribution and Report Periods](015-session-day-attribution-and-report-periods.md)

## Status

- **Created**: 2026-09-24
- **Status**: Accepted and implemented
