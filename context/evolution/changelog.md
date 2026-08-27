# Changelog

## [Developer Experience] - Local Home Assistant Control

- Added `dev/start-ha.sh` and `dev/stop-ha.sh` to start and gracefully stop the
  isolated local Home Assistant test instance, with its PID and logs kept under
  `/tmp`.
- Made both scripts POSIX `sh` compatible so they can be invoked with `sh` or
  directly.
- Documented the local instance lifecycle and exploratory-test access constraints
  in `AGENTS.md`.

## [Current State] - Context Mesh Added

### Existing Features (documented)

- Flexible activity monitoring - independent monitors for state, zone, area-presence, and general activity.
- Guided monitor management - UI setup and editing with selected periods and measurements.
- Activity reporting - duration, counts, session details, statistics, and calendar-based reports.
- Durable activity history - retained daily summaries with optional historical reconstruction.
- Foreground application insights - current-app and application-switch activity tracking.

### Tech Stack (documented)

- Python 3.14 and Home Assistant 2026.8.
- `uv`, pytest, pytest-asyncio, pytest-cov, and Ruff.
- Home Assistant config entries, entity platforms, event helpers, storage, and Recorder history APIs.

### Patterns Identified

- Activity state classification.
- Calendar-day session aggregation.
- Multi-step configuration flow.
- Selected metric entity factory.

---

*Context Mesh added: 2026-08-27*
*This changelog documents the state when Context Mesh was added.*
*Future changes will be tracked below.*

## [Documentation] - Legacy Specification Consolidated

- Moved the product and engineering scope of the retired implementation specification into Context Mesh through [legacy specification traceability](legacy-specification-traceability.md).
- Explicitly identified requirements that remain partial or planned so existing-code documentation does not overstate implementation status.

## [Planning] - Remaining MVP Gaps

- Added a proposed, phased implementation plan for the incomplete MVP requirements. No implementation is authorized by this entry.
- Drafted proposed ADRs for interruption handling, data-quality completeness,
  migration/import safety, and local calendar boundaries. They are awaiting
  approval and do not authorize implementation.

## [Planning] - Data-Correctness Contracts Approved

- Accepted ADRs 006–009 and added the detailed phase 1–3 execution plan.
- No product code has been changed; a separate execution request is required
  before implementation starts.

## [Implementation] - Data Correctness

- Added an interruption-aware session checkpoint that excludes observed pauses
  and unavailable time from activity totals while retaining logical sessions.
- Added unknown-time accounting, restart-safe checkpoint closure, and exact
  interruption deadlines.
- Migrated durable payloads to schema v2 with atomic writes, safe migration
  failure handling, and per-monitor import/clear serialization.
- Added structured rolling-history availability attributes and local-week support.
- Added focused regression coverage for merge gaps, unavailable time, migration,
  and report availability.

## [Development Tooling] - Local Home Assistant Startup

- Updated the local Home Assistant start script to isolate its runtime from the
  integration virtual environment and wait for the HTTP service to become ready.
