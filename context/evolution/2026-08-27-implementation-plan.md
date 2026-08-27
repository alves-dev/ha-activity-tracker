# Implementation Plan: Remaining MVP Specification Gaps

## Purpose

This is the persisted plan for completing requirements identified as **Partial** or **Planned** in [Legacy Specification Traceability](legacy-specification-traceability.md). It was created for handoff to a future session. It authorizes no implementation by itself: apply the mandatory **Plan → Approve → Execute** workflow in the [Context Mesh Framework](../.context-mesh-framework.md).

## Scope Decision

The plan covers incomplete MVP requirements. The candidates listed under *Future Evolution* in the traceability document—such as a custom dashboard, cross-monitor rankings, background application tracking, exports, and alerts—are excluded unless separately approved.

## Dependencies and Order

```text
0. ADRs and feature intent
        ↓
1. Correct session interruption accounting
        ↓
2. Time, completeness, and data-quality semantics
        ↓
3. Storage migration and retention safety
        ↓
4. Recorder import reliability
        ↓
5. Administrative UX and diagnostics
        ↓
6. Optional advanced metrics
```

## Phase 0: Define Contracts Before Code

### Work

- Create proposed ADR `006-interruption-and-session-state-machine.md`.
  - Define the logical states: active, observed-inactive pause, unavailable pending, and closed.
  - Define merge-gap and unavailable-tolerance timing, state transitions, and how activity/unknown duration are accounted for.
- Create proposed ADR `007-data-quality-and-period-completeness.md`.
  - Define partial days, complete history, coverage, unknown duration, availability reasons, and analytic eligibility.
- Create proposed ADR `008-storage-migration-and-import-safety.md`.
  - Define version migration, recovery on migration failure, atomic writes, import locking, and cleanup interaction.
- Create proposed ADR `009-calendar-boundaries.md`.
  - Define Home Assistant local timezone, DST, configured week boundary, and calendar/rolling range rules.
- Update affected feature-intent acceptance criteria with the user-visible behavior below. Keep all technical mechanics in the ADRs and patterns.

### Affected Context

- [Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Activity Reporting](../intent/feature-activity-reporting.md)
- [Durable Activity History](../intent/feature-durable-activity-history.md)
- [Foreground Application Insights](../intent/feature-foreground-application-insights.md)
- [Real-Time Session Accounting](../decisions/003-real-time-session-accounting.md)
- [Compact Daily Summary Storage](../decisions/004-compact-daily-summary-storage.md)
- [Recorder History Reconstruction](../decisions/005-recorder-history-reconstruction.md)

### Exit Criteria

- [x] ADRs 006–009 are accepted.
- [x] Feature intent distinguishes implemented behavior from planned behavior.
- [x] A migration strategy is approved before persisted-state changes.

### Planning Outcome (2026-08-27)

The contracts were drafted in ADRs 006–009. Their acceptance is the gate for
implementation of phases 1–3.

**Implementation recorded 2026-08-27:** The approved data-correctness slice has
been implemented and validated. The detailed plan below remains the traceability
record for this delivery.

## Detailed Execution Plan: Data-Correctness Slice

### 1. Runtime state machine

**Affected files:** `models.py`, `runtime.py`, `const.py`, and
`tests/test_runtime.py`.

1. Extend the checkpoint model with an explicit lifecycle state, its transition
   timestamp, accumulated observed activity, and compact pending per-day totals.
   The checkpoint holds aggregate contributions for only the open logical session,
   never a list of activity intervals.
2. Split classification into active, observed inactive, and unavailable results.
   Keep monitor-rule and foreground-application interpretation in the existing
   classifier pattern.
3. Make each state transition idempotent and reject timestamps not newer than the
   last true source observation. The minute refresh updates entity presentation
   only; it must not manufacture an observation.
4. Schedule the merge-gap and unavailable-tolerance deadlines explicitly. A
   successful active observation cancels the corresponding deadline; expiry closes
   at the first interruption timestamp.
5. Accumulate only observed active segments. Apply the minimum-duration rule once
   at logical-session close, then commit the pending per-day totals and whole
   session statistics. Application changes use the same finish-then-start path.
6. On setup, convert a restored checkpoint into a safely closed session at its
   last observation and apply the accepted downtime policy before processing the
   current source state.

**Focused tests:** merge return before/after deadline; each unavailable behavior
with zero and positive tolerance; restart in every lifecycle state; duplicate and
out-of-order events; cross-midnight minimum-duration exclusion; application
switches during and after interruptions.

### 2. Calendar, quality, and report contract

**Affected files:** `models.py`, `runtime.py`, `sensor.py`, `const.py`,
`tests/test_models.py`, `tests/test_runtime.py`, and `tests/test_sensor.py`.

1. Create one timezone-aware boundary helper for local-day start/end, period
windows, rolling calendar dates, and configured week start. Its day duration is
computed from aware instants rather than assumed to be 24 hours.
2. Add summary quality metadata for observed coverage, unknown duration,
partialness, and rule compatibility. Existing v1 summaries receive conservative
defaults during migration rather than being presented as newly proven complete.
3. Mark monitor-start, import-boundary, restart-unknown, and current-day ranges
partial as defined by ADR 007. Keep current calendar reports readable as
observed-to-date.
4. Centralize report eligibility in the runtime. Sensors consume its value and
structured availability attributes rather than independently checking retention.
5. Apply the same eligibility to all period-aware metrics, including averages and
weekday aggregation, while leaving current-session display available.

**Focused tests:** sufficient and insufficient complete history; all unavailability
reasons and attributes; retention shorter than requested range; local midnight;
month/year transitions; configured week start; and short/long DST local days.

### 3. Storage migration, locking, and retention

**Affected files:** `storage.py`, `runtime.py`, `models.py`, `__init__.py`,
`tests/test_storage_and_binary_sensor.py`, and `tests/test_runtime.py`.

1. Raise the storage schema version and implement explicit v1-to-current payload
normalization, including the old checkpoint and daily-summary shape.
2. Validate before migration and before persistence. Preserve the original Store
payload when validation or migration fails; surface a safe runtime-unavailable
reason rather than defaulting to an empty history.
3. Add a per-entry async mutation lock around import, cleanup, clear, session
commit, and checkpoint persistence. Build a complete replacement payload before
each save so a failed operation cannot publish a partly transformed in-memory
object.
4. Rework Recorder import to select and replace only its usable local-date range,
record progress/result metadata, and preserve summaries outside that range.
5. Run cleanup after all successful mutations and via a local-midnight schedule;
confirm entry removal targets only its monitor store.

**Focused tests:** v1 migration preserves totals and latest-session metadata;
malformed payload recovery; failed migration leaves storage untouched; retention
cutoff inclusivity; import idempotency and preserved outer dates; and concurrent
mutation serialization.

### Execution Order and Gates

1. Implement and test the pure model/boundary helpers.
2. Implement the runtime state machine behind the migrated checkpoint shape.
3. Add report-quality eligibility and entity attributes.
4. Add import locking, migration failure handling, and scheduled cleanup.
5. Run focused tests after each step, then `uv run pytest`, `uv run ruff check .`,
   and the integration-structure validator. Update ADR outcomes, traceability,
   changelog, translations, and patterns in the same implementation change.

## Phase 1: Session Interruption Correctness

### Work

- Separate source activity from the presence of a persisted session checkpoint.
- Implement observed inactive merge gaps: a short gap keeps one logical session, excludes the gap from active duration, and closes at the initial inactive time after its deadline expires.
- Implement unavailable behavior and configured tolerance: end, remain pending, or account for unknown time.
- On Home Assistant restart, account only for observed activity; classify the unobserved interval according to the approved policy and resume only from a new observation.
- Preserve whole-session minimum-duration evaluation across midnight and exclusions.
- Ensure foreground application switches still close one session and start the next.

### Validation

- [ ] Short and expired merge gaps.
- [ ] All unavailable behaviors with zero and non-zero tolerance.
- [ ] Restart during active, paused, and unavailable-pending session states.
- [ ] Duplicate events do not duplicate sessions.
- [ ] Unknown time is not counted as active duration.
- [ ] Application changes and midnight crossing retain correct session counts.

## Phase 2: Time, Completeness, and Data Quality

### Work

- Mark initial and imported boundary days as partial when full observation is unavailable.
- Make complete-history reports unavailable until they have sufficient complete local days.
- Add structured availability attributes: reason, required days, available days, and available-from date.
- Calculate observed coverage and unknown duration consistently.
- Derive week boundaries from Home Assistant configuration/API rather than a fixed Monday rule.
- Make all period calculations timezone-aware and safe across DST, month, and year boundaries.

### Validation

- [ ] Current calendar reports remain available immediately.
- [ ] Rolling complete-history reports expose a reason until sufficient history exists.
- [ ] Retention shorter than a requested period reports unavailability clearly.
- [ ] Tests cover local midnight, month/year boundaries, DST short/long days, rolling 35 days, and configured week starts.

## Phase 3: Storage, Migration, and Retention

### Work

- Increment the storage schema version and provide an explicit migration from existing data.
- Persist the data required for interruption state, excluded/unknown intervals, coverage, partialness, rule version, and import progress.
- Preserve the principle of retaining daily aggregates and a small checkpoint only—not a permanent session archive.
- Run retention cleanup reliably at local-day boundaries as well as after relevant mutating operations.
- Make migration failure preserve prior data and leave the affected entry safely unavailable rather than silently resetting history.

### Validation

- [ ] v1 data migrates without losing totals or last-session metadata.
- [ ] Corrupt or incomplete payloads fail safely.
- [ ] Retention cleanup removes only out-of-range data.
- [ ] Entry removal clears all per-monitor persisted data.
- [ ] Separate monitors never share application or summary data.

## Phase 4: Recorder Import Reliability

### Work

- Run import asynchronously without delaying normal integration startup.
- Determine the usable Recorder range when practical and expose import progress/result safely.
- Rebuild only the reconstructible date range, preserving retained summaries outside it.
- Mark boundary days partial and imported data with appropriate quality metadata.
- Prevent concurrent import and cleanup; make reimport idempotent.
- Support selected application attributes when Recorder history contains them.

### Validation

- [ ] Reimporting the same range does not duplicate totals.
- [ ] Existing summaries outside Recorder range remain unchanged.
- [ ] Boundary days and unavailable Recorder cases are handled safely.
- [ ] Failure or cancellation cannot corrupt stored data.
- [ ] Result includes rebuilt/preserved days, processed sessions, range, and warnings.

## Phase 5: Administrative UX and Diagnostics

### Work

- Require explicit confirmation before clearing history or replacing summaries with reimported data.
- Show keep/clear/reimport choices only when a rule-changing edit can invalidate history.
- Add redacted diagnostics: monitor type, source ID, rule version, retention, stored date range, checkpoint state, last import/cleanup, and summary count.
- Make entity unavailability actionable without exposing detailed location or application history in logs or diagnostics.

### Validation

- [ ] Destructive history actions require confirmation.
- [ ] Presentation-only edits do not prompt for history handling.
- [ ] Diagnostics contain no detailed activity history or sensitive raw data.
- [ ] Entity availability reasons are machine-readable and user-actionable.

## Phase 6: Optional Advanced Metrics

This phase requires separate scope approval after phases 1–5, because its usefulness depends on trustworthy completeness and interruption accounting.

### Candidates

- Previous equivalent-period comparison, absolute difference, and percentage change with zero-baseline handling.
- Observation coverage and estimated-duration metrics.
- Foreground-application ranking, count, switch count, and selected per-application entities.
- User controls for discovered applications: include, hide individual entities, or ignore.

### Validation

- [ ] Metrics use the approved completeness contract.
- [ ] Zero baseline never produces infinite percentage values.
- [ ] Application identity remains stable when its display label changes.
- [ ] No monitor combines application history from another device.

## Delivery Slices

1. **Data-correctness release:** phases 0–3, including migration and focused regression tests.
2. **Operational release:** phases 4–5, including import safety and diagnostics.
3. **Analytics release:** phase 6, only after explicit approval.

## Definition of Done Per Slice

- [ ] Relevant ADRs are accepted before implementation.
- [ ] Feature intent reflects the delivered user behavior.
- [ ] Patterns include reusable implementation guidance if new structures are introduced.
- [ ] Focused tests pass, then the complete `uv run pytest` and `uv run ruff check .` suite passes.
- [ ] Compatibility, translations, and Home Assistant entity metadata are updated where affected.
- [ ] Decision outcomes, traceability status, and `context/evolution/changelog.md` are updated.

## Status

- **Created**: 2026-08-27
- **Status**: Implemented — data-correctness slice delivered
- **Note**: Phases 4–6 remain separate future work.
