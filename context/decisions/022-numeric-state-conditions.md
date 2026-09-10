# Decision: Numeric State Conditions

## Context

Many Home Assistant entities expose measurements as numeric state strings or
numeric attributes. Textual `state` equality cannot safely express thresholds
such as temperature, battery level, or power limits.

## Decision

Add a `numeric_state` leaf to the unified rule contract. It compares the entity
state, or an optional numeric attribute, with a decimal threshold using
`greater_than`, `greater_or_equal`, `less_than`, `less_or_equal`, `equals`, or
`not_equals`. Numeric parsing uses exact decimal arithmetic. Non-numeric,
`unknown`, and `unavailable` values are false. The existing `for_seconds`
duration semantics remain unchanged.

## Rationale

Keeping numeric comparison separate from textual state matching makes the UI
clear and prevents accidental lexicographic comparisons. Decimal arithmetic
keeps equality deterministic for values represented as strings.

## Outcomes

Implemented on 2026-09-10 in the evaluator, native and sidebar validation, and
the complete sidebar condition editor.

## Related

- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Decision: Unified Activity Rules](014-unified-activity-rules.md)
- [Pattern: Unified Rule Evaluation](../knowledge/patterns/unified-rule-evaluation.md)

## Status

- **Created**: 2026-09-10
- **Status**: Accepted
