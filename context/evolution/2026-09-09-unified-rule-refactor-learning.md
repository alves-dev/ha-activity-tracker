# Learning: Unified Rules Need Explicitly Incompatible Boundaries

## Insight

A compact retained aggregate is only trustworthy while its rule, source-health,
and day-attribution semantics stay the same. Converting older monitor summaries
or trying to replay Recorder history would create values that look exact but are
not evidence-equivalent to a live unified rule.

## Outcome

The integration uses a reset-only schema, explicit confirmation before a rule or
midnight-policy edit clears summaries, and exact deadline-driven live evaluation.
The same boundary keeps configuration, runtime, accounting, diagnostics, and
sensor contracts small and internally consistent.

## Status

- **Created**: 2026-09-09
- **Status**: Active learning
