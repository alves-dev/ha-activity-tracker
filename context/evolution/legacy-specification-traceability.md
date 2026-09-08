# Legacy Specification Traceability

## Purpose

This document preserves the product and engineering information from the former `ACTIVITY-TRACKER-SPEC.md` after that source file was retired on 2026-08-27. It records where each specification topic belongs in Context Mesh and whether the current implementation satisfies it. It is not a feature intent: entries marked **Planned** or **Partial** must not be treated as completed behavior.

## Product Scope and Terminology

| Former specification topics | Context destination | Current status |
| --- | --- | --- |
| Purpose, identity, UI languages, custom-integration distribution, and the goal of durable activity reporting | [Project Intent](../intent/project-intent.md) | Implemented |
| Goals: measure duration, sessions, latest session, zones, areas, applications, and rolling periods | [Project Intent](../intent/project-intent.md), [Activity Reporting](../intent/feature-activity-reporting.md) | Implemented, except where noted below |
| MVP non-goals and future scope | [Project Intent](../intent/project-intent.md), [Future Evolution](#future-evolution) | Documented scope boundary |
| Terms: monitor, activity, session, daily summary, checkpoint, and period | [Compact Daily Summary Storage](../decisions/004-compact-daily-summary-storage.md), [Real-Time Session Accounting](../decisions/003-real-time-session-accounting.md) | Implemented concepts |

## Functional Scope

| Former specification topics | Context destination | Current status |
| --- | --- | --- |
| Entity active-state and generic state monitors | [Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md), [Activity State Classification](../knowledge/patterns/activity-state-classification.md) | Implemented |
| Person/device zone monitors and explicit person-area presence monitors | [Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md) | Implemented |
| Foreground application from state or a selected attribute; stable identifier with display label | [Foreground Application Insights](../intent/feature-foreground-application-insights.md), [Activity State Classification](../knowledge/patterns/activity-state-classification.md) | Implemented |
| One config entry and virtual device per monitor; UI-only setup; selected periods and metrics | [Home Assistant Config-Entry Integration](../decisions/002-home-assistant-integration-architecture.md), [Guided Monitor Management](../intent/feature-guided-monitor-management.md) | Implemented |
| Default 90-day retention, zero minimum duration, seven-day validation floor, minute current-session refresh, and HA-local time | [Compact Daily Summary Storage](../decisions/004-compact-daily-summary-storage.md), [Real-Time Session Accounting](../decisions/003-real-time-session-accounting.md) | Implemented |
| Current day/week/month and positive rolling calendar-day periods | [Activity Reporting](../intent/feature-activity-reporting.md) | Implemented; week currently begins on Monday in code rather than using a configurable HA week boundary |
| Complete-history/partial-day coverage semantics and reason attributes | [Data Quality and Diagnostics Gaps](#data-quality-and-diagnostics-gaps) | Partial |
| Start, continuation, end, minimum duration, latest completed session, and midnight split rules | [Real-Time Session Accounting](../decisions/003-real-time-session-accounting.md), [Calendar-Day Session Aggregation](../knowledge/patterns/calendar-day-session-aggregation.md) | Implemented for normal observed sessions |
| Unavailable tolerance, unknown downtime, and merge-gap semantics | [Interruption Handling Gaps](#interruption-handling-gaps) | Partial |
| Compact per-monitor daily storage, checkpoint, latest-session metadata, retention cleanup, and entry-removal cleanup | [Compact Daily Summary Storage](../decisions/004-compact-daily-summary-storage.md) | Implemented core; schema and cleanup scheduling are partial |
| Recorder bootstrap/rebuild | [Recorder History Reconstruction](../decisions/005-recorder-history-reconstruction.md) | Implemented core; diagnostics and boundary metadata are partial |
| User-selected sensor catalog, native duration values, current activity, session statistics, weekday total | [Activity Reporting](../intent/feature-activity-reporting.md), [Selected Metric Entity Factory](../knowledge/patterns/selected-metric-entity-factory.md) | Implemented for the current metric set |
| Comparison metrics, coverage percentage, estimated duration, application rankings, and per-application entities | [Data Quality and Diagnostics Gaps](#data-quality-and-diagnostics-gaps) | Planned |
| Barber zone-monitor scenario | [Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md), [Activity Reporting](../intent/feature-activity-reporting.md) | Supported by the implemented monitor, period, and latest-session behavior; duration-to-service inference remains out of scope |
| Setup steps, options editing, keep/clear/reimport action | [Guided Monitor Management](../intent/feature-guided-monitor-management.md), [Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md) | Implemented core |
| Clear-history and reimport administrative actions | [Durable Activity History](../intent/feature-durable-activity-history.md), [Recorder History Reconstruction](../decisions/005-recorder-history-reconstruction.md) | Implemented through options flow; explicit confirmation/progress controls are partial |
| Stable entity IDs and one-device grouping | [Home Assistant Config-Entry Integration](../decisions/002-home-assistant-integration-architecture.md), [Selected Metric Entity Factory](../knowledge/patterns/selected-metric-entity-factory.md) | Implemented |
| Versioned storage and test coverage goals | [Tech Stack](../decisions/001-tech-stack.md), [Compact Daily Summary Storage](../decisions/004-compact-daily-summary-storage.md) | Storage version and focused tests implemented; complete specified test matrix is partial |

## Interruption Handling Gaps

The specification defined separate semantics for observed inactive merge gaps, unavailable-source tolerance, unknown intervals during Home Assistant downtime, and safe session resumption. The current implementation stores the unavailable behavior and tolerance settings in monitor options, but the runtime classifier currently ends activity for unavailable/unknown states and does not account for unknown duration. A positive merge-gap option currently pauses a session but has no complete resolution path. These are specification requirements that remain **partial**, not existing guarantees.

## Data Quality and Diagnostics Gaps

The current daily model contains `unknown_seconds`, `complete`, and `rule_version`, and rolling metrics become unavailable when their configured length exceeds retention. However, the following specification requirements are not fully implemented: sufficient-history availability, coverage/estimated-duration calculations, structured unavailability reasons, partial-day exclusion from analytics, diagnostics data, migration-failure handling, configurable week boundaries, and comprehensive DST/boundary handling.

## Architecture and Operational Guidance

The retired specification's implementation guidance maps to the existing architecture as follows:

- Keep session classification and accounting outside sensor entities; current code places these responsibilities in `runtime.py` and pure helpers in `models.py`.
- Use timezone-aware timestamps and split at local midnight; see [Calendar-Day Session Aggregation](../knowledge/patterns/calendar-day-session-aggregation.md).
- Persist only aggregates, a checkpoint, and latest-session metadata; do not create an accidental detailed-session archive.
- Use event-driven updates and an active-session minute refresh; avoid per-second updates and normal reporting queries against Recorder.
- Derive unique entity IDs from stable monitor and metric identifiers rather than mutable names.
- Treat foreground-application measurements as activity reported by a source, not definitive screen-on time.
- Keep location and application history out of verbose logs and diagnostics.

## Test Coverage Traceability

Current tests cover classification, normal session lifecycle, foreground-app changes, minimum-duration discard, midnight splitting, storage load/save/removal, selected metric calculations, and main configuration-flow journeys. The legacy requirements still lacking dedicated coverage include merge/unavailable behavior, restart/downtime semantics, DST and configured week boundaries, storage migrations/corruption, import idempotency and boundary-day preservation, full availability diagnostics, and delete warnings.

## Future Evolution

The retired specification recorded these future candidates: custom dashboards; temporary detailed sessions and corrections; grouped/ranking monitors; additional generic rules and multi-entity conditions; background media/application tracking; native collectors; configurable duration labeling; goals and alerts; data export/repair; more translations; and long-term aggregate tiers. None are commitments in the current active feature scope.

## Status

- **Created**: 2026-08-27
- **Status**: Active historical traceability
- **Note**: Consolidated from the retired implementation specification; current implementation status was verified against the codebase before removal.
