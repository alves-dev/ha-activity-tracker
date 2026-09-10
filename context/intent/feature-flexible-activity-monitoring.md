# Feature: Flexible Activity Monitoring

## What

Users define an activity with independent start and stop expressions over one or
more Home Assistant entities. A monitor represents one activity and exposes
whether it is active now.

## Acceptance Criteria

- [x] Start and stop rules support state, state-duration, and report-silence
  conditions with AND/OR groups.
- [x] `unavailable` and `unknown` are explicit stop-condition values.
- [x] A delayed unavailable/unknown stop closes accounting at its first bad
  observation after confirmation at the requested deadline.
- [x] Zone presence is the only guided template; other activities use custom
  rules.

## Related

- [Project Intent](project-intent.md)
- [Decision: Unified Activity Rules](../decisions/014-unified-activity-rules.md)
- [Pattern: Unified Rule Evaluation](../knowledge/patterns/unified-rule-evaluation.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active; delivered on 2026-09-09
