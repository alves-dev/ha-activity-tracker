# Pattern: Activity State Classification

## Description

Centralize the conversion from a Home Assistant state into an activity result. The result contains whether the source is active and, where relevant, a stable application identifier and display label.

## When to Use

Use this pattern whenever a monitor rule is added or session handling needs to decide whether an incoming state starts, continues, or ends activity.

## Pattern

Keep rule-specific interpretation in one classifier that returns `(active, identifier, label)`. Reject unavailable and unknown states before applying monitor-specific rules. Keep session transitions separate from classification so the same classification is reusable by live observation and history reconstruction.

## Example

```python
def _classify_state(self, state: State) -> tuple[bool, str | None, str | None]:
    if state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        return False, None, None
    if self.entry.data.get(CONF_MONITOR_TYPE) == TYPE_ZONE:
        return state.state == self.entry.data.get(CONF_ZONE_ENTITY_ID), None, None
    if self.entry.data.get(CONF_MONITOR_TYPE) == TYPE_FOREGROUND_APPLICATION:
        identifier = str(state.state)
        return True, identifier, identifier
    return state.state in self.entry.data.get(CONF_ACTIVE_STATES, []), None, None
```

## Files Using This Pattern

- [runtime.py](../../../custom_components/activity_tracker/runtime.py) - classifies live state observations and provides the callback used by history reconstruction.
- [recorder_import.py](../../../custom_components/activity_tracker/recorder_import.py) - receives the same classifier when reconstructing sessions.
- [test_runtime.py](../../../tests/test_runtime.py) - verifies state, zone, unavailable, and application cases.

## Related

- [Decision: Real-Time Session Accounting](../../decisions/003-real-time-session-accounting.md)
- [Feature: Flexible Activity Monitoring](../../intent/feature-flexible-activity-monitoring.md)
- [Feature: Foreground Application Insights](../../intent/feature-foreground-application-insights.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active
