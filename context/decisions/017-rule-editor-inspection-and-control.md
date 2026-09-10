# Decision: Native Rule Inspection and Control

## Context

The unified-rule configuration flow recreated its in-memory condition collection
when an existing monitor was edited. Users therefore could not see the start
and stop conditions already assigned to an activity, let alone tell whether a
condition currently matched. A custom sidebar panel could offer a live rule
workbench, but it would add a separately bundled frontend, websocket contract,
permission model, and an additional configuration surface for an integration
whose monitor settings already belong to config entries.

## Decision

Keep rule inspection and changes in the monitor options flow. Hydrate its
editable condition groups from the persisted unified rule, show a readable
start/stop summary, and let a user add or remove conditions while preserving
the AND/OR group model. A removed condition can be recreated in a different
group to change its relationship to the other conditions.

Whenever the condition form is rendered, evaluate each displayed leaf and its
whole start or stop expression against the then-current Home Assistant state
snapshot. Show the match result, current value, and any pending duration or
report-silence deadline. This is explicitly an inspection snapshot, not a live
frontend subscription.

Do not add a sidebar panel in this delivery. Reconsider one only for a future
cross-monitor live workbench or bulk-management capability; it is not needed
to make one monitor's rule understandable and safely editable.

## Rationale

The options flow is the established, permission-aware home for a monitor's
contract. Reusing it keeps destructive-history confirmation server-enforced and
avoids duplicating rule validation. Snapshot status explains a condition at the
point it is being changed without promising a real-time UI that a config flow
cannot provide.

## Alternatives Considered

- Add a custom sidebar panel now. Rejected for this delivery because its
  frontend and backend lifecycle is disproportionate to the per-monitor edit
  need.
- Show only the saved rule text. Rejected because it does not explain why an
  activity is or is not starting/stopping at the time of diagnosis.
- Mutate a stored rule directly from a client-side form. Rejected because it
  could bypass config-entry validation and the mandatory retained-history
  confirmation.

## Outcomes

Implemented and validated on 2026-09-10. The options flow hydrates its editable
AND/OR groups from the saved rule, keeps them intact when the user revisits the
source step, and separates the actions to manage, add, and remove conditions so
no new-condition fields are required merely to inspect or remove a condition.
Its snapshots use the existing pure evaluator and deadline calculator. The
complete test suite, Ruff, integration-structure validation, and diff check
passed.

## Related

- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Decision: Home Assistant Config-Entry Integration](002-home-assistant-integration-architecture.md)
- [Decision: Unified Activity Rules](014-unified-activity-rules.md)
- [Decision: Unified-Rule Data Reset](016-unified-rule-data-reset-and-no-recorder-import.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)
- [Pattern: Unified Rule Evaluation](../knowledge/patterns/unified-rule-evaluation.md)

## Status

- **Created**: 2026-09-10
- **Status**: Accepted
