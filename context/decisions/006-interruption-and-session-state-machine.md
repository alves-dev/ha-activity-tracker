# Decision: Interruption and Session State Machine

## Context

An observed inactive state, an unavailable source, and an integration restart have
different evidentiary meaning. The current single checkpoint cannot yet distinguish
them reliably, which makes merge gaps and unavailable-source options incomplete.

## Proposed Decision

Represent one monitor with the logical states **closed**, **active**,
**observed-inactive pause**, and **unavailable pending**. Persist only the current
checkpoint and its state, never an archive of intervals.

- An active observation starts or continues activity. An application identifier
  change closes the current application session and starts another immediately.
- An observed inactive state starts an observed-inactive pause. If an active state
  returns before the configured merge-gap deadline, it resumes the same logical
  session; the observed inactive interval is excluded from activity duration. If
  the deadline expires, close the session at the first inactive observation.
- For an unavailable or unknown source state, `end` closes at that observation;
  `pending` waits up to the unavailable-tolerance deadline for a new observation;
  and `unknown` records the interval as unknown time rather than activity. A
  pending session resumes only after an active observation within its deadline;
  otherwise it closes at the unavailable observation.
- On restart, close any restored session at its last observed timestamp. Do not
  infer activity during downtime or resume a checkpoint until a new source
  observation. Apply the selected unavailable policy to the unobserved interval:
  it is excluded for `end` and `pending`, and recorded as unknown for `unknown`.
- Ignore duplicate or out-of-order observations at or before the checkpoint's last
  observation, except when they provide no newer state. Evaluate the minimum
  duration against the whole logical session's accumulated active duration, not
  an individual calendar-day fragment.

## Rationale

This preserves the product distinction between activity, observed non-activity,
and missing evidence. It also keeps reports conservative: neither a pause nor an
outage silently becomes active time. Foreground-application changes remain the
only active-to-active boundary because they represent a different activity.

## Alternatives Considered

- Count every merge gap or unavailable interval as activity. Rejected because it
  overstates measured use.
- Close every interruption immediately. Rejected because it defeats the existing
  merge-gap and unavailable-tolerance settings.
- Persist every pause and unknown interval. Rejected because it creates a detailed
  activity archive contrary to compact-storage intent.

## Outcomes

Implemented on 2026-08-27. The runtime checkpoint now records its lifecycle
state and compact pending daily totals; active segments, pauses, unavailable
time, restart recovery, and application switches follow the accepted contract.

## Related

- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Feature: Foreground Application Insights](../intent/feature-foreground-application-insights.md)
- [Decision: Real-Time Session Accounting](003-real-time-session-accounting.md)
- [Decision: Compact Daily Summary Storage](004-compact-daily-summary-storage.md)

## Status

- **Created**: 2026-08-27
- **Status**: Accepted
