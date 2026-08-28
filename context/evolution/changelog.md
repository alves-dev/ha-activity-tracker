# Changelog

## 2026-08-28 — SonarQube follow-up cleanup

- Simplified diagnostics import-result construction and replaced mutation-safe
  list snapshots with tuple snapshots in runtime cleanup paths.

## 2026-08-28 — SonarQube maintainability remediation

- Split Recorder querying from interval reconstruction and extracted runtime
  session-transition and daily-summary helpers, preserving the existing
  accounting contracts while reducing cognitive complexity.

## 2026-08-28 — Local Home Assistant helper standardization

- Aligned the local Home Assistant start and stop helpers with the shared PID
  file convention and documented the integration deployment helper for agents.

## 2026-08-28 — Documentação de monitores e sensores

- Adicionadas ao README as tabelas dos cinco tipos de monitor e dos quinze
  sensores de relatório selecionáveis, incluindo como os sensores são criados.
- Adicionados casos de uso separados para cada tipo de monitor em `docs/` e
  vinculados a partir da tabela do README.
- Cada caso de uso agora apresenta o conteúdo em PT-BR e inglês no mesmo
  arquivo, identificado pelos rótulos `[pt-BR]` e `[en]`.
- As tabelas de tipos de monitor e sensores selecionáveis no README também têm
  versões em PT-BR e inglês identificadas pelos mesmos rótulos.

## 2026-08-28 — Local integration deployment

- Added `dev/copy-to-core.sh` to stop the local Home Assistant instance, deploy
  Activity Tracker to its configuration directory, and start the instance again.

## 2026-08-28 — Per-monitor duration display

- Added a presentation-only duration unit for each monitor: hours, minutes, or
  seconds. New monitors default to hours; existing monitors preserve seconds
  until edited.

## 2026-08-28 — Administrative UX and diagnostics

- Added explicit confirmation before a monitor edit clears retained history or
  requests a Recorder reimport; presentation-only edits now save directly.
- Added redacted monitor diagnostics and actionable availability attributes
  without exposing activity, location, or application history.

## 2026-08-27 — Phase 5 proposal

- Proposed the administrative-history confirmation and redacted-diagnostics
  contract for approval before implementation.

## 2026-08-27 — Recorder import reliability

- Moved optional Recorder reconstruction to a post-startup background task.
- Rebuilt only Recorder-backed dates while preserving retained summaries outside
  that range, with idempotent replacement and partial boundary-day quality.
- Recorded a compact import outcome with range, rebuilt/preserved days, processed
  sessions, and safe warnings; historical foreground-app attributes now follow
  the configured attribute selection.
- Fixed the SonarQube workflow to use the project's canonical analysis endpoint.

## [Fix] - Zone Monitor State Matching

- Corrected zone monitors to compare person and device-tracker states with the
  Home Assistant zone value (`home` or the zone name), rather than `zone.*` IDs.

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
