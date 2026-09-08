# Learning: Unchanged State Reports Can Be Heartbeats

## Observation

The Companion App's periodic `last_update_trigger` report can retain the same
state value. Home Assistant publishes that successful write as `state_reported`,
not `state_changed`.

## Reusable Insight

Any feature that interprets a Home Assistant entity as a liveness heartbeat must
listen to both changed and unchanged reports. A state-change listener or
`last_updated` alone is insufficient for an entity that routinely republishes
the same value.

## Application

The mobile-device monitor listens to both event types and persists its latest
heartbeat independently of its interactive state. Its session logic does not
turn a heartbeat into an activity observation.

The Interactive binary sensor also needs an explicit rule in the shared
classifier: it represents activity only when its state is `on`. Relying on the
generic configured-active-state branch is incorrect because this monitor type
deliberately derives its sources from the selected device instead of asking the
user to configure active states.

## Status

- **Created**: 2026-09-08
- **Status**: Active
