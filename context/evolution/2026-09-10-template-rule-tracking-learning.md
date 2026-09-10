# Learning: Delegate Template Dependencies to Home Assistant

## Observation

An activity template can read entity attributes, use helper functions, and make
dynamic entity choices. Static parsing of its Jinja source cannot reliably
discover every update that should re-evaluate a session rule.

## Learning

Persist template text as rule data, but create `Template` instances only with
the active Home Assistant runtime. Use `async_track_template_result` rather
than extracting entity IDs: it tracks the dependencies observed during each
render, updates them when the template's access pattern changes, and handles
time-based dependencies. Feed only its boolean result into the existing pure
rule evaluator, keeping template execution and session accounting separate.

## Applies To

- Future Activity Tracker template leaves and template previews.
- Home Assistant integrations that need to turn a dynamic template into a
  stable domain decision without copying Home Assistant's dependency logic.

## Related

- [Decision: Template Activity Rules](../decisions/018-template-activity-rules.md)
- [Pattern: Unified Rule Evaluation](../knowledge/patterns/unified-rule-evaluation.md)

## Status

- **Created**: 2026-09-10
- **Status**: Active
