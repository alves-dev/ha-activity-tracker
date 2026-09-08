# Decision: Data Quality and Period Completeness

## Context

Daily summaries already carry exact and unknown duration plus a completeness flag,
but reports do not define their meaning consistently. Users need to distinguish a
zero result from a result that lacks enough observed history.

## Proposed Decision

Treat each local calendar day as a quality-bearing aggregate.

- A day is **partial** when observation did not cover its full local-day window,
  including the monitor's initial day, Recorder import boundary days, days with
  unrecoverable unknown time, and the in-progress current day.
- A complete day is eligible for complete-history analytics only when it has full
  local-day observation under one rule version. Rule changes create a new quality
  boundary; aggregates from incompatible rules are not silently combined.
- Calendar reports for today, current week, and current month stay available as
  observed-to-date values. Rolling reports that claim complete history require the
  requested number of complete local days.
- When a report is unavailable, expose structured attributes: `reason`,
  `required_days`, `available_days`, and `available_from`. Valid reasons include
  insufficient complete history, retention limit, incompatible rule history, and
  unavailable source data.
- `exact_seconds` is directly observed activity; `unknown_seconds` is time for
  which the selected policy could not classify the source. Observation coverage is
  calculated from eligible observed time divided by the local-day duration, which
  may be 23 or 25 hours at daylight-saving transitions. Estimated-duration metrics
  remain out of scope until separately approved.

## Rationale

The contract permits immediate, useful current reporting without presenting a new
monitor or imported boundary as a statistically complete period. Separating exact
and unknown time makes availability machine-readable and actionable.

## Alternatives Considered

- Treat every retained date as complete. Rejected because a storage entry does not
  prove full observation.
- Hide all calendar reports until complete history exists. Rejected because it
  withholds truthful observed-to-date information.
- Estimate missing activity automatically. Deferred to optional analytics because
  estimates require an explicit user-facing interpretation.

## Outcomes

Implemented on 2026-08-27 for retained report eligibility. Rolling reports now
publish structured insufficient-history and retention reasons, and unknown or
import-boundary time marks summaries incomplete.

## Related

- [Feature: Activity Reporting](../intent/feature-activity-reporting.md)
- [Feature: Durable Activity History](../intent/feature-durable-activity-history.md)
- [Decision: Compact Daily Summary Storage](004-compact-daily-summary-storage.md)

## Status

- **Created**: 2026-08-27
- **Status**: Accepted
