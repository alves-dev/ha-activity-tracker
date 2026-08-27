# Feature: Flexible Activity Monitoring

## What

Users can define a monitor for an entity's active states, a person or device in a zone, a person's presence in an internal area, or a general state-based activity. Each monitor represents one activity and shows whether it is active now.

## Why

Different household and device activities report their status in different ways. Supporting these activity rules lets users measure meaningful real-world activity without changing the sources they already use.

## Acceptance Criteria

- [ ] A user can create an independent monitor for each supported activity rule.
- [ ] A monitor identifies whether its activity is currently active.
- [ ] State changes among configured active conditions remain part of the same activity.
- [ ] A location monitor counts activity only in the location selected by the user.

## Delivered Behavior (2026-08-27)

- [x] Brief observed inactive gaps can remain one logical activity without being
  counted as active duration.
- [x] Source unavailability is reported according to the user's selected handling
  policy and never silently counted as activity.
- [x] A zone monitor recognizes the state Home Assistant reports for the selected
  zone, including the special `home` state.

## Related

- [Project Intent](project-intent.md)
- [Decision: Home Assistant Config-Entry Integration](../decisions/002-home-assistant-integration-architecture.md)
- [Decision: Real-Time Session Accounting](../decisions/003-real-time-session-accounting.md)
- [Decision: Interruption and Session State Machine](../decisions/006-interruption-and-session-state-machine.md)
- [Pattern: Activity State Classification](../knowledge/patterns/activity-state-classification.md)

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Active (already implemented)
