# Decision: Template Activity Rules

## Context

State and report-silence conditions cover common activities, but cannot express
comparisons against an entity attribute, calculations, or Home Assistant's
other native template helpers. Users need an escape hatch for these cases
without manually creating helper entities.

## Decision

Add **Template rule** as a monitor template. It collects one boolean Home
Assistant Jinja template for `start_when` and one for `stop_when`; both are
persisted as template leaves in the existing unified-rule contract.

At runtime, instantiate templates with the active `hass` instance and use
Home Assistant's `async_track_template_result` helper. It discovers and tracks
the entities and attributes each template actually reads, including dynamic
dependencies. A template result is true only when Home Assistant's standard
boolean conversion considers it true; render errors are false and do not start
or continue an activity. Template leaves have no elapsed-time deadline.

The guided state-condition editor remains for comprehensible simple rules. A
template rule owns its two complete expressions; mixing free-form templates
inside the guided AND/OR editor is deferred until a tree editor is available.

## Rationale

Using Home Assistant's template tracker avoids a fragile attempt to parse Jinja
or infer which attribute changes should cause a re-evaluation. Separate start
and stop templates retain the existing session lifecycle and stop precedence.
Restricting the first delivery to a complete template-rule monitor keeps the
editor honest about what it can safely display and modify.

## Alternatives Considered

- Require users to create a helper template entity. Rejected because it spreads
  one activity definition over multiple Home Assistant objects.
- Parse entity IDs from Jinja and subscribe to them directly. Rejected because
  it misses dynamic access and duplicates Home Assistant's dependency tracker.
- Allow template leaves anywhere in the current condition flow. Deferred: the
  current flat editor cannot clearly represent arbitrary mixed expressions.

## Outcomes

Implemented and validated on 2026-09-10. The template-rule flow persists
independent start and stop template leaves, and the runtime registers native
template-result tracking before evaluating sessions. The evaluator and session
engine consume the tracked boolean results without changing state-condition
deadlines. Syntax/configuration, template-result transitions, the full test
suite, Ruff, integration-structure validation, and diff check passed.

## Related

- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Decision: Unified Activity Rules](014-unified-activity-rules.md)
- [Pattern: Unified Rule Evaluation](../knowledge/patterns/unified-rule-evaluation.md)

## Status

- **Created**: 2026-09-10
- **Status**: Accepted
