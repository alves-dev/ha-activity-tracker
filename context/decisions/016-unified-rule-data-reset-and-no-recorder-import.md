# Decision: Unified-Rule Data Reset and No Recorder Import

## Context

The new rule model, source-health semantics, day attribution, and report
metrics cannot faithfully reinterpret prior configuration or daily aggregates.
Historical Recorder states also cannot reconstruct rules dependent on elapsed
state, unchanged reports, or simultaneous conditions.

## Decision

The unified-rule release deliberately has no compatibility migration for old
config entries, entity identifiers, storage payloads, or long-term statistics.
The user removes existing monitors before installation. New entries start with
an empty schema dedicated to unified-rule summaries.

Recorder import and reimport are removed from configuration, runtime,
diagnostics, and user documentation. Retained history begins with live
observations made by the new monitor. Rule or cross-midnight-policy edits clear
incompatible retained summaries only after explicit confirmation.

## Rationale

Resetting intentionally is more truthful than silently converting values whose
definition changed. Excluding Recorder reconstruction avoids presenting guessed
historical activity as exact results.

## Alternatives Considered

- Convert old monitor types and retain their summaries. Rejected because their
  session boundaries and midnight attribution are not comparable.
- Replay Recorder entity histories for all conditions. Rejected because unchanged
  reports and elapsed conditions are not a complete event stream.
- Let users keep incompatible summaries after editing a rule. Rejected because
  mixed definitions make reports misleading.

## Outcomes

Implemented on 2026-09-09. Schema v3 rejects previous payloads, config-entry
version 3 rejects old entries, and Recorder code, dependencies, configuration,
diagnostics, and documentation have been removed. This decision supersedes
Recorder-import compatibility and preservation requirements from Decisions 005,
008, and 010 for this release.

## Related

- [Feature: Durable Activity History](../intent/feature-durable-activity-history.md)
- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Decision: Recorder History Reconstruction](005-recorder-history-reconstruction.md)
- [Decision: Storage Migration and Import Safety](008-storage-migration-and-import-safety.md)
- [Decision: Administrative History Actions and Redacted Diagnostics](010-administrative-history-and-diagnostics.md)
- [Unified-rule refactor plan](../evolution/2026-09-09-unified-rule-refactor-implementation-plan.md)

## Status

- **Created**: 2026-09-09
- **Status**: Accepted
