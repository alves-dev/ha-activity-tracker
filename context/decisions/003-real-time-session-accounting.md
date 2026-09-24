# Decision: Real-Time Session Accounting

## Context

Activity reports require reliable recognition of starts, ends, state changes,
active sessions, and elapsed-time conditions while the integration is running.

## Decision

Observe configured source state changes and template results in real time,
maintain one active session per monitor, and refresh current-session displays on
the presentation interval. Schedule condition deadlines rather than polling.

## Rationale

This approach produces immediate current-state reporting and captures sessions
as they happen. The evaluator and lifecycle engine remain independent from
entity subscriptions and storage. Rationale is inferred from the runtime
implementation and tests.

## Alternatives Considered

An exclusively query-based approach using historical records would not provide live current-session state and would depend on external history retention. Polling every source is not used; the existing implementation subscribes to state-change events and uses only a periodic display refresh.

## Outcomes

Outcomes to be documented as project evolves.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Decision: Unified Activity Rules and Source Health](014-unified-activity-rules.md)
- [Decision: Compact Daily Summary Storage](004-compact-daily-summary-storage.md)
- [Decision: Interruption and Session State Machine](006-interruption-and-session-state-machine.md)
- [Pattern: Unified Rule Evaluation and Exact Deadlines](../knowledge/patterns/unified-rule-evaluation.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Superseded by Decision 014 on 2026-09-09
- **Note**: Documented from existing implementation
