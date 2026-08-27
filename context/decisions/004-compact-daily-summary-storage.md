# Decision: Compact Daily Summary Storage

## Context

Activity reports must remain useful beyond Recorder retention without permanently storing every completed session. Reporting also needs local calendar-day, weekly, monthly, and rolling-date aggregation.

## Decision

Persist versioned per-monitor daily aggregates, a minimal active-session checkpoint, and latest completed-session metadata in Home Assistant storage. Split completed intervals at local midnight and retain summaries only for each monitor's configured number of days.

## Rationale

Daily aggregates are small and directly support report periods while avoiding a full historical session archive. A checkpoint allows orderly restoration after lifecycle changes. Local calendar-day splitting makes daily reporting and rolling days align with how users interpret dates. Rationale is inferred from storage, runtime, model, and architecture documentation.

## Alternatives Considered

The project's specification explicitly rejects permanent storage of every historical session. Relying only on Recorder history conflicts with the stated aim of reporting beyond Recorder retention. Exact 24-hour rolling windows are not selected; the existing behavior uses local calendar dates.

## Outcomes

Outcomes to be documented as project evolves.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Activity Reporting](../intent/feature-activity-reporting.md)
- [Feature: Durable Activity History](../intent/feature-durable-activity-history.md)
- [Decision: Real-Time Session Accounting](003-real-time-session-accounting.md)
- [Decision: Data Quality and Period Completeness](007-data-quality-and-period-completeness.md)
- [Decision: Storage Migration and Import Safety](008-storage-migration-and-import-safety.md)
- [Decision: Calendar Boundaries and Local Time](009-calendar-boundaries.md)
- [Pattern: Calendar-Day Session Aggregation](../knowledge/patterns/calendar-day-session-aggregation.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation
