# Decision: Administrative History Actions and Redacted Diagnostics

## Context

Editing a monitor can change the meaning of its retained summaries. The current
options flow always exposes keep, clear, and reimport choices, and applies a
destructive action without a separate confirmation. The integration also needs
diagnostics that help support a monitor without exporting location, application,
or detailed session history.

## Proposed Decision

Classify options edits before offering a history action.

- A **rule-changing edit** changes the source entity or monitor type, active
  states, selected zone/presence source, foreground-application identifier
  source or attribute, minimum session duration, merge gap, unavailable behavior,
  or unavailable tolerance. It shows keep, clear, and reimport choices.
- A **presentation-only edit** changes the monitor name, report periods, enabled
  metrics, retention, or foreground-application display-label attribute. It
  saves directly and never requests a history action.
- Clear and reimport require an unselected explicit confirmation on a separate
  final flow step. The confirmation states whether all retained summaries will
  be cleared or only the available Recorder-backed range will be replaced.
- Diagnostics expose only monitor type, a redacted stable source identifier,
  rule version, retention, stored date range, summary count, checkpoint
  lifecycle state, last import result, last cleanup time, and availability
  reason. They exclude raw states, entity attributes, summary totals by date,
  session timestamps, location names, and application identifiers or labels.
- Entity unavailability continues to use stable machine-readable reason codes;
  it also supplies a non-sensitive suggested action appropriate to that reason.

## Rationale

Users should not be asked to make a destructive-history decision when a change
does not alter accounting. When it does, a dedicated confirmation prevents an
accidental clear or replacement. A narrowly allow-listed diagnostic payload is
useful for support while preserving the integration's promise not to expose
activity history in logs or diagnostics.

## Alternatives Considered

- Ask for a history choice on every options edit. Rejected because it adds a
  destructive-looking decision to harmless presentation changes.
- Automatically clear history after every rule change. Rejected because users
  may deliberately retain prior results or choose a Recorder rebuild.
- Export the stored payload as diagnostics. Rejected because it contains
  sensitive activity timing and application/location information.
- Require confirmation only in a frontend dialog. Rejected because the config
  flow must enforce the safeguard independently of a particular frontend.

## Outcomes

Implemented on 2026-08-28. The options flow compares the original and edited
monitor contracts, bypasses history handling for presentation-only edits, and
requires an explicit confirmation before clear or Recorder reimport. Diagnostics
now use an allow-list with a stable hashed source identifier and omit detailed
activity, application, location, state, and attribute data. Unavailable report
entities provide a stable suggested action with their reason.

## Related

- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Feature: Activity Reporting](../intent/feature-activity-reporting.md)
- [Feature: Durable Activity History](../intent/feature-durable-activity-history.md)
- [Decision: Data Quality and Period Completeness](007-data-quality-and-period-completeness.md)
- [Decision: Storage Migration and Import Safety](008-storage-migration-and-import-safety.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)

## Status

- **Created**: 2026-08-27
- **Status**: Accepted
