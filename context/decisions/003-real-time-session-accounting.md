# Decision: Real-Time Session Accounting

## Context

Activity reports require reliable recognition of starts, ends, state changes, active sessions, and application switches while the integration is running.

## Decision

Observe configured source state changes in real time, classify each observed state into activity, maintain one active session per monitor, and refresh the current-session display on a minute interval. Treat a foreground application identifier change as a session boundary.

## Rationale

This approach produces immediate current-state reporting and captures sessions as they happen. It preserves one logical session when an entity changes between configured active states, while retaining application-level boundaries where the user expects them. Rationale is inferred from the runtime implementation and tests.

## Alternatives Considered

An exclusively query-based approach using historical records would not provide live current-session state and would depend on external history retention. Polling every source is not used; the existing implementation subscribes to state-change events and uses only a periodic display refresh.

## Outcomes

Outcomes to be documented as project evolves.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Feature: Foreground Application Insights](../intent/feature-foreground-application-insights.md)
- [Decision: Compact Daily Summary Storage](004-compact-daily-summary-storage.md)
- [Pattern: Activity State Classification](../knowledge/patterns/activity-state-classification.md)
- [Pattern: Calendar-Day Session Aggregation](../knowledge/patterns/calendar-day-session-aggregation.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation
