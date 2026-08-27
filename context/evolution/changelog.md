# Changelog

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
