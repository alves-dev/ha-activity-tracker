# Decision: Recorder History Reconstruction

## Context

New or changed monitors may need retained summaries initialized from state history already available in Home Assistant, while Recorder may be disabled or unavailable.

## Decision

Offer an optional one-time import that reconstructs closed activity sessions from Recorder state changes within the retention window, then writes compact summaries and clears the import request.

## Rationale

The optional import gives users a path to useful recent reporting without making Recorder a permanent dependency for normal monitor operation. Failure during startup is handled without preventing the monitor from starting. Rationale is inferred from the runtime and Recorder-import code.

## Alternatives Considered

Always importing history would add startup work and replace current summaries unnecessarily. Maintaining Recorder as the only source of reports would conflict with compact independent retention. Alternatives are otherwise not documented in the existing codebase.

## Outcomes

Outcomes to be documented as project evolves.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Durable Activity History](../intent/feature-durable-activity-history.md)
- [Decision: Compact Daily Summary Storage](004-compact-daily-summary-storage.md)
- [Pattern: Calendar-Day Session Aggregation](../knowledge/patterns/calendar-day-session-aggregation.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation
