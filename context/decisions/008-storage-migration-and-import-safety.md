# Decision: Storage Migration and Import Safety

## Context

The per-monitor payload is schema version 1. The planned interruption and quality
contracts need additional checkpoint and summary metadata, while an import can
currently replace retained dates during normal startup.

## Proposed Decision

Use an explicit, forward-only payload migration for each stored schema version.

- Validate a loaded payload before use; migrate supported older versions into a
  new in-memory payload; then persist the migrated payload atomically only after
  validation succeeds.
- A migration or validation failure must retain the original stored value,
  leave that monitor's entities safely unavailable with a machine-readable reason,
  and provide redacted diagnostics. It must never replace history with an empty
  payload.
- Serialize mutating operations per monitor. Recorder import, cleanup, clear
  history, runtime commits, and checkpoint persistence cannot interleave.
- A rebuild replaces only the selected reconstructible local-date range. It
  preserves summaries outside that range, records import provenance and progress,
  and is idempotent for the same request.
- Run retention cleanup after every completed mutating operation and at a local-day
  boundary. It removes only summaries older than the configured inclusive
  retention window. Entry removal deletes only that entry's storage.

## Rationale

The migration makes persisted history an explicit compatibility contract. A
per-monitor mutation boundary prevents partial import or cleanup from racing with
live accounting, without changing the compact daily-aggregate storage model.

## Alternatives Considered

- Reset unreadable data automatically. Rejected because it silently loses a
  user's durable history.
- Keep a global lock for all monitors. Rejected because independent monitors do
  not share state and should not block each other.
- Replace all retained summaries on every import. Rejected because Recorder may
  not cover the full retained window.

## Outcomes

Implemented on 2026-08-27. The payload now migrates from v1 to v2 without
resetting summaries, writes atomically, serializes clear/import operations, and
keeps entities safely unavailable if a payload cannot be loaded.

## Related

- [Feature: Durable Activity History](../intent/feature-durable-activity-history.md)
- [Decision: Compact Daily Summary Storage](004-compact-daily-summary-storage.md)
- [Decision: Recorder History Reconstruction](005-recorder-history-reconstruction.md)

## Status

- **Created**: 2026-08-27
- **Status**: Accepted
