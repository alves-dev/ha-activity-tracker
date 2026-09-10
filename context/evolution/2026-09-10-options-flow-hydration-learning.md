# Learning: Hydrate Existing Config-Flow Collections Before Editing

## Observation

The unified-rule editor correctly built a serializable expression while
creating a monitor, but options editing recreated its condition collection as
empty. The persisted rule therefore existed and the runtime honored it, while
the editor presented no evidence of it to the user.

## Learning

For an options flow that edits a persisted collection, reconstruct the local
editing representation before the first form is shown and preserve it when a
user revisits an earlier step. Do not combine a collection action such as
inspect/remove/finish with fields required to create an item: Home Assistant
will require all form fields before submitting. Use a focused action screen,
then a separate add or remove screen.

Evaluating the persisted item with the same pure evaluator used by the runtime
provides a trustworthy diagnostic snapshot without introducing a second rules
engine or a frontend-specific behavior contract.

## Applies To

- Future Activity Tracker options-flow editors for persisted lists or trees.
- Other Home Assistant config flows that need to explain the current effect of
  a saved rule before changing it.

## Related

- [Decision: Native Rule Inspection and Control](../decisions/017-rule-editor-inspection-and-control.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)
- [Pattern: Unified Rule Evaluation](../knowledge/patterns/unified-rule-evaluation.md)

## Status

- **Created**: 2026-09-10
- **Status**: Active
