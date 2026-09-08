# Decision: Mobile Device Interaction Heartbeat

## Context

The mobile companion application's interactive sensor records whether a phone's
screen is interactive. If the phone loses power or connectivity while that
sensor is on, Home Assistant retains its last state and an entity-state monitor
can remain active indefinitely. Requiring users to select separate interaction
and heartbeat entities is error-prone.

## Decision

Provide a **mobile device in use** monitor type for eligible `mobile_app`
devices. The setup flow selects one device and resolves its enabled
`binary_sensor` interactive entity and `sensor` last-update-trigger entity from
the entity registry. It refuses a device that does not provide both entities.

- The interactive entity remains the activity source; only its `on` state can
  start or resume a session.
- The last-update-trigger entity is a heartbeat. Both changed and unchanged
  reports refresh it, because Home Assistant emits an unchanged state update as
  `state_reported` rather than `state_changed`.
- While interaction is active, absence of a heartbeat beyond the configured
  silence tolerance is handled as source unavailability at the deadline. New
  mobile-device monitors default to ending the session at that point.
- A heartbeat never starts or resumes a session by itself. This avoids treating
  a returned phone as in use merely because Home Assistant still has an old
  interactive state.
- The most recent heartbeat is stored with the monitor checkpoint so an
  Activity Tracker restart cannot make restored mobile state appear newly
  reported.
- Recorder reconstruction is not offered for this monitor type. It can replay
  interactive state transitions but cannot faithfully reconstruct unchanged
  heartbeat reports, and must not create historical sessions with misleading
  continuity.

## Rationale

Device selection preserves the Companion App's device/entity relationship and
prevents a monitor from accidentally pairing one phone's screen state with
another phone's heartbeat. Treating silence as unavailability reuses the
existing interruption contract while bounding sessions when the device cannot
send an explicit `off` state.

## Alternatives Considered

- Ask the user to choose both entities. Rejected because it invites mismatched
  devices and exposes mobile-app implementation details.
- Use only the interactive entity's `last_updated` timestamp. Rejected because
  unchanged sensor reports are not state changes and can leave that timestamp
  stale even while the phone communicates.
- Let a returned heartbeat resume an old interactive session. Rejected because
  heartbeat proves communication, not that the screen remains on.
- Reconstruct mobile-device history from Recorder. Rejected because reported
  heartbeat continuity is not a reliable historical state-transition stream.

## Outcomes

Implemented on 2026-09-08. The guided flow validates mobile-app device
capabilities, the runtime classifies the Interactive entity's `on` state as
activity, and it maintains a persisted heartbeat deadline before applying the
established unavailable-source policy.

## Related

- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Decision: Real-Time Session Accounting](003-real-time-session-accounting.md)
- [Decision: Interruption and Session State Machine](006-interruption-and-session-state-machine.md)
- [Pattern: Activity State Classification](../knowledge/patterns/activity-state-classification.md)
- [Pattern: Multi-Step Configuration Flow](../knowledge/patterns/multi-step-configuration-flow.md)

## Status

- **Created**: 2026-09-08
- **Status**: Accepted
