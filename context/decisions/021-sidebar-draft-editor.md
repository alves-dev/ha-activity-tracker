# Decision: Sidebar Draft Editor

## Context

The Activity Rules sidebar needs to be the complete, spatial editor for an
activity: it must show all of the monitor contract, nested AND/OR expressions,
template results, and the review before a save. Hosting the native config and
options flows in the panel made the experience linear and caused HTTP 400
errors when the panel serialized form values outside the active flow schema.

## Decision

Replace the hosted config/options-flow UI with an admin-only draft editor in the
local Activity Rules panel. The browser owns only an unsaved JSON-compatible
draft. It calls permission-checked integration WebSocket commands to obtain a
draft, validate it, inspect its live condition results and template previews,
review a server-computed diff, and request an apply.

The server owns normalization, full-contract validation, template validation
and rendering, entry creation, and entry update.
No browser code calls config-flow HTTP endpoints or updates a config entry.
Rule edits preserve retained history; see [Decision 024](024-preserve-history-on-rule-edit.md).
The panel may also open an existing activity as a detached, unsaved copy; it
never carries the source entry identifier into that draft.

The draft editor supports recursive `all`/`any` groups and state,
state-duration, report-silence, and template leaves. Zone presence and complete
template-rule activities remain convenient models which generate their normal
unified rule contract. Existing native flows remain supported as an alternate
Home Assistant integration-page path, but are not embedded by the panel.

## Rationale

The server-side contract gives the workbench a single comprehensive screen
without trusting browser input or bypassing backend safeguards. A
draft preview makes conditions explainable before data is persisted, and keeps
the runtime evaluator, storage, and entry lifecycle independent of the UI.

## Alternatives Considered

- Continue hosting config and options flows. Rejected: it is inherently
  stepwise, cannot present the whole contract together, and has already caused
  unsupported form submissions and HTTP 400 failures.
- Let the browser update ConfigEntry data. Rejected: it would permit bypassing
  validation and runtime lifecycle handling.
- Require a new helper entity for template previews. Rejected: Home Assistant
  can validate and render the draft template without persisting an activity.

## Outcomes

Implemented on 2026-09-10. The panel no longer hosts native flows. Its draft
commands validate and apply only through the integration backend; browser code
does not directly mutate ConfigEntry data. The UI renders the full monitor
contract, candidate snapshots, and a diff.

## Related

- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Decision: Home Assistant Config-Entry Integration](002-home-assistant-integration-architecture.md)
- [Decision: Unified Activity Rules](014-unified-activity-rules.md)
- [Decision: Unified-Rule Data Reset](016-unified-rule-data-reset-and-no-recorder-import.md)
- [Decision: Sidebar Rule Workbench](019-sidebar-rule-workbench.md)
- [Decision: Sidebar Native-Flow Editor](020-sidebar-native-flow-editor.md)
- [Pattern: Unified Rule Evaluation](../knowledge/patterns/unified-rule-evaluation.md)

## Status

- **Created**: 2026-09-10
- **Status**: Accepted
