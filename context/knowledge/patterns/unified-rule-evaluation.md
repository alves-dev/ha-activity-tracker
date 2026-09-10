# Pattern: Unified Rule Evaluation and Exact Deadlines

## Description

Evaluate an activity's start or stop rule as a pure recursive expression over a
snapshot of Home Assistant states. Schedule the earliest elapsed-time condition
deadline rather than polling the rule.

## When to Use

Use this pattern for every unified monitor start/stop decision and for any
future source-health condition that depends on state duration or report silence.

Template leaves use Home Assistant's template-result tracker to turn a
template's current boolean result into evaluator input; they do not attempt to
extract entity IDs or introduce a polling deadline.

## Pattern

Persist expressions as `all` or `any` groups with state, numeric-state,
report-silence, and template leaf conditions. Keep expression evaluation independent of Home Assistant event
subscription and session accounting. Given a state snapshot and aware `now`, the
evaluator reports whether the expression matches and the earliest future time a
currently eligible leaf can become true.

The runtime subscribes to all entity IDs returned by the expression and
re-evaluates only after an observed state/report event or scheduled deadline.
For a state-duration leaf use `last_changed`; for report silence prefer
`last_reported`, falling back to `last_changed` only where the platform does not
provide it. A missing state or malformed condition is false, never an implicit
source-health failure.

## Files Using This Pattern

- [rules.py](../../../custom_components/activity_tracker/rules.py) - pure
  expression evaluation, referenced entity discovery, and deadline calculation.
- [test_rules.py](../../../tests/test_rules.py) - nested boolean, duration,
  report-silence, and negation coverage.

## Related

- [Decision: Unified Activity Rules and Source Health](../../decisions/014-unified-activity-rules.md)
- [Feature: Flexible Activity Monitoring](../../intent/feature-flexible-activity-monitoring.md)
- [Decision: Template Activity Rules](../../decisions/018-template-activity-rules.md)
- [Decision: Numeric State Conditions](../../decisions/022-numeric-state-conditions.md)

## Status

- **Created**: 2026-09-09
- **Status**: Active
