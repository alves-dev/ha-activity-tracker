# Decision: Unified Activity Rules and Source Health

## Context

Monitor types duplicate activity interpretation in the configuration flow,
runtime classifier, and Recorder importer. They cannot express a start condition
and a different stop condition across several entities, including conditions
which become true only after elapsed time.

## Decision

Each monitor uses one serializable activity rule instead of a runtime monitor
type. A rule has independent `start_when` and `stop_when` boolean expressions.
Expressions are recursive `all` (AND) and `any` (OR) groups containing leaf
conditions:

- an entity state matching or not matching a finite set of state values;
- a matching state held continuously for a configured duration; and
- an entity that has not reported for a configured duration.

The runtime subscribes to every entity referenced by the rule and schedules the
next elapsed-time deadline. It evaluates the expressions from observed current
state; a deadline never invents a source observation.

While idle, a true start expression opens a session. While running, a true stop
expression closes it. A stop expression takes precedence if both expressions
are true. A normal delayed state condition closes at the instant its duration
completes. A delayed unavailable/unknown condition is confirmed at its deadline
but closes at the first unavailable observation, so no unobservable interval is
counted as activity.

Unavailable and unknown are ordinary explicit stop-condition values; there is no
global unavailable policy, unavailable tolerance, merge-gap policy, or
unknown-duration accounting. A **zone presence** template only prepopulates a
normal rule using the selected tracker and zone. All other activities use the
custom-rule editor in this release.

## Rationale

One evaluator makes combinations such as sleep, device use with a freshness
guard, and state transitions possible without multiplying monitor types. Making
health a stop condition gives the user control over what is evidence of an
unavailable source while preserving conservative duration accounting.

## Alternatives Considered

- Add logical operators to each existing monitor type. Rejected because the
  rule and lifecycle branches would still be duplicated and incompatible.
- Count the delay before a source-health failure as activity. Rejected because
  a source already known to be unavailable provides no evidence of activity.
- Use a polling interval for timers. Rejected because it makes closure time
  imprecise and needlessly evaluates rules without a state or deadline event.

## Outcomes

Implemented on 2026-09-09. The pure evaluator, exact deadline scheduling,
runtime subscriptions, and delayed-unavailability accounting follow this
contract. This decision supersedes the monitor-type classifier parts of
Decisions 003, 006, and 013.

## Related

- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Decision: Real-Time Session Accounting](003-real-time-session-accounting.md)
- [Decision: Interruption and Session State Machine](006-interruption-and-session-state-machine.md)
- [Decision: Mobile Device Interaction Heartbeat](013-mobile-device-interaction-heartbeat.md)
- [Pattern: Unified Rule Evaluation and Exact Deadlines](../knowledge/patterns/unified-rule-evaluation.md)
- [Unified-rule refactor plan](../evolution/2026-09-09-unified-rule-refactor-implementation-plan.md)

## Status

- **Created**: 2026-09-09
- **Status**: Accepted
