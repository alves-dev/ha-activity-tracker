# Implementation Plan: Unified Activity Rules

## Purpose

Replace the current monitor-type model with one rule engine capable of evaluating
combined entity-state conditions. This plan is intentionally incompatible with
the prior configuration and retained-storage formats: the user will remove all
existing monitors before installing this release.

## Approved Product Scope

- A monitor has one custom activity rule with separate start and stop
  expressions composed with `all` (AND) and `any` (OR) groups.
- A condition can test an entity state, a state held for a duration, or missing
  entity reports for a duration. An unavailable or unknown state is an explicit
  stop condition; it always ends the session once its configured condition is
  satisfied.
- The only guided template in this delivery is **zone presence**. It creates a
  normal rule from a selected person/device tracker and a selected zone. All
  other activities use the custom-rule flow.
- Retention, minimum completed-session duration, and per-monitor duration unit
  remain. Hours remain the default presentation unit.
- `Last 1` means yesterday; `Last 2` means the day before yesterday. These are
  individually closed local calendar days, not rolling ranges including today.
- Unknown-duration reporting is removed. Days-since-last-session becomes
  duration-since-last-session. Average local start and end times are added.
- Each monitor selects one cross-midnight policy: attribute all duration to the
  start date, attribute all duration to the end date, or split duration and
  session attribution at local midnight.

## Non-goals for This Delivery

- Compatibility migration of old config entries, entity IDs, retained summaries,
  or Recorder-import data.
- Recorder import and reimport. Complex rules can depend on simultaneous entity
  state, elapsed time, and unchanged reports that Recorder history cannot
  reconstruct faithfully. Retained history begins when the new monitor runs.
- Templates for phone use, foreground applications, areas, or generic entity
  states. This non-goal was superseded for complete start/stop template rules
  by [Decision 018](../decisions/018-template-activity-rules.md) on 2026-09-10;
  mixing templates within the guided AND/OR editor remains deferred.
- A permanent detailed session archive or automatic correction of existing Home
  Assistant long-term statistics.

## Architecture Gates

Before implementation, create and accept ADRs defining:

1. The persisted rule-expression contract and exact timer/transition semantics.
2. Daily attribution, session-count semantics, and compact timing aggregates.
3. The incompatible config/storage reset and removal of Recorder reconstruction.
4. The Home Assistant statistics contract for the current-day duration sensor.

The remaining unresolved detail is the timestamp used for a delayed stop rule.
The proposed default is: a normal `state for X` stop ends at its deadline; an
unavailability confirmation ends at the first unavailable observation, so time
without a usable source is never counted as activity.

## Delivery Phases

### Phase 0: Contracts and test matrix

- Update the affected feature intents and add the ADRs above.
- Replace the retired monitor-type/classifier and calendar aggregation patterns.
- Write a table-driven test matrix for boolean expressions, timer expiry,
  midnight policies, period offsets, and statistics metadata.

**Progress (2026-09-09):** Completed. ADRs 014–016 are accepted, the pure
evaluator and its focused expression/deadline tests are in place, and the
reusable evaluation pattern is documented. Accounting, periods, and statistics
cases remain for their respective delivery phases.

### Phase 1: Pure rule and session engine

- Add serializable rule nodes and an evaluator independent of Home Assistant UI.
- Subscribe to every referenced entity and schedule the earliest condition
  deadline; do not use periodic polling to make accounting decisions.
- Make start, stop, duplicate event, restart, and delayed-condition transitions
  deterministic and testable.

### Phase 2: Durable accounting

- Replace the storage payload with a new schema and initialize empty data when
  a new monitor is created.
- Implement start-date, end-date, and local-midnight split attribution.
- Persist compact start/end time circular aggregates and latest-session data.
- Keep retention cleanup and minimum-duration filtering at logical-session
  completion.

### Phase 3: Configuration experience

- Replace monitor-type selection with **Zone presence** and **Custom rule**.
- Build a focused, recursive condition/group editor with review validation.
- Make rule and cross-midnight edits require an explicit history-clear
  confirmation. Presentation, selected reports, and retention remain
  non-destructive edits.

### Phase 4: Reports and statistics

- Implement prior-day periods (`previous_day:N`) alongside current day/week/month.
- Add average start, average end, and duration-since-last-session sensors.
- Remove unknown-duration sensors and translations.
- Publish the current-day total as `total_increasing` and document `sum` as the
  statistics-graph aggregation. Other period totals remain measurements.

### Phase 5: Integration and release validation

- Remove obsolete monitor-specific paths, all Recorder-import paths, diagnostics fields,
  documentation, and translations.
- Validate with focused tests, `uv run pytest`, `uv run ruff check .`, and the
  integration-structure validator.
- Update ADR outcomes, feature intent, changelog, README, and a reusable
  learning record if implementation exposes a durable lesson.

## Status

- **Created**: 2026-09-09
- **Status**: Delivered on 2026-09-09; architecture gates accepted and outcomes
  recorded in ADRs 014–016.
