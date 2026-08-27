# Decision: Tech Stack

## Context

Activity Tracker is distributed as a Home Assistant custom integration and needs to expose device entities, configure monitors in the Home Assistant UI, persist monitor data, and be tested against a known platform version.

## Decision

Use Python 3.14 with Home Assistant 2026.8 as the runtime platform. Manage development dependencies with `uv`; use pytest with pytest-asyncio and pytest-cov for tests, Ruff for linting, and SonarQube project configuration for static-analysis reporting.

## Rationale

The implementation imports Home Assistant integration APIs directly, declares `homeassistant==2026.8.0`, and uses platform-native configuration, entities, storage, and event services. The pinned platform and project tooling provide a reproducible compatibility target. Rationale is inferred from project configuration and implementation.

## Alternatives Considered

Alternatives are not documented in the existing codebase. A standalone service or a generic Python event framework would not integrate with Home Assistant's device, entity, configuration, and state model used by this project.

## Outcomes

Outcomes to be documented as project evolves.

## Related

- [Project Intent](../intent/project-intent.md)
- [Decision: Home Assistant Config-Entry Integration](002-home-assistant-integration-architecture.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation
