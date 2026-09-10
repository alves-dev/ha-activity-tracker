# Decision: Home Assistant Config-Entry Integration

## Context

Every tracked activity needs separate settings, lifecycle management, and Home Assistant entities, while users should configure it from the Home Assistant UI rather than from YAML.

## Decision

Model each monitor as one Home Assistant config entry backed by a runtime
instance. The native configuration flow remains available for initial setup;
activity editing is exposed only through the Activity Rules sidebar, which uses
the server-owned draft-editor contract in
[Decision 021](021-sidebar-draft-editor.md) for its complete in-panel editing
experience. Expose a binary sensor plus only the user-selected metric sensors
under a corresponding virtual device.

## Rationale

Config entries provide independent monitor lifecycle, UI configuration, updates, and removal. A virtual device groups the activity state and selected reports without creating unused entities. This is inferred from `manifest.json`, configuration-flow code, platform setup, and entity construction.

## Alternatives Considered

YAML configuration is explicitly excluded by project documentation. A single global entry with multiple monitors would be possible, but the existing implementation instead uses one entry and one device per monitor for independent management.

## Outcomes

The sidebar draft editor was added on 2026-09-10 without changing the one-entry
per-monitor lifecycle; browser code never mutates ConfigEntry data.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Feature: Activity Reporting](../intent/feature-activity-reporting.md)
- [Decision: Tech Stack](001-tech-stack.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)
- [Pattern: Selected Metric Entity Factory](../knowledge/patterns/selected-metric-entity-factory.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation
