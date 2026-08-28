# Pattern: Multi-Step Configuration Flow

## Description

Build setup and editing as a sequence of focused UI steps that collect validated monitor data before creating or updating a monitor.

## When to Use

Use this pattern when adding monitor settings, new activity-rule inputs, or validation that should give users feedback before a monitor is saved.

## Pattern

Keep intermediate monitor data and options in flow-local dictionaries. Each step validates only its own inputs and advances on success. Validate cross-field requirements before moving forward, then use a final review step before the entry is created or updated. When an edit can destroy or replace persisted history, add a separate unselected confirmation step and perform the mutation only after it succeeds.

## Example

```python
async def async_step_metrics(self, user_input: dict[str, Any] | None = None):
    errors: dict[str, str] = {}
    if user_input is not None:
        metrics = list(user_input.get(CONF_ENABLED_METRICS, []))
        if not metrics:
            errors[CONF_ENABLED_METRICS] = "required"
        else:
            self._monitor[CONF_ENABLED_METRICS] = metrics
            return await self.async_step_review()
    return self.async_show_form(step_id="metrics", errors=errors)
```

## Files Using This Pattern

- [config_flow.py](../../../custom_components/activity_tracker/config_flow.py) - implements setup, options editing, per-step validation, review, and history actions.
- [test_config_flow.py](../../../tests/test_config_flow.py) - exercises complete journeys and validation failures.

## Related

- [Decision: Home Assistant Config-Entry Integration](../../decisions/002-home-assistant-integration-architecture.md)
- [Feature: Guided Monitor Management](../../intent/feature-guided-monitor-management.md)
- [Decision: Administrative History Actions and Redacted Diagnostics](../../decisions/010-administrative-history-and-diagnostics.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active
