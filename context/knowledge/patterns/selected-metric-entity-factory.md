# Pattern: Selected Metric Entity Factory

## Description

Create only the report entities selected for a monitor, expanding period-aware metrics once for each selected reporting period.

## When to Use

Use this pattern when introducing a selectable metric, a new reporting period, or a monitor-type-specific supplementary entity.

## Pattern

Define the metrics that require a period. At platform setup, iterate through user-selected metrics; create one entity per selected period for period-aware metrics and one entity otherwise. Give each entity a stable identifier derived from the monitor, metric, and optional period.

## Example

```python
for metric in metrics:
    if metric in PERIOD_METRICS:
        entities.extend(
            ActivityMetricSensor(runtime, metric, period) for period in periods
        )
    else:
        entities.append(ActivityMetricSensor(runtime, metric))
```

## Files Using This Pattern

- [sensor.py](../../../custom_components/activity_tracker/sensor.py) - creates selected sensors and calculates their values.
- [const.py](../../../custom_components/activity_tracker/const.py) - defines supported metrics and periods.
- [test_sensor.py](../../../tests/test_sensor.py) - verifies current, period, application, and availability values.

## Related

- [Decision: Home Assistant Config-Entry Integration](../../decisions/002-home-assistant-integration-architecture.md)
- [Feature: Activity Reporting](../../intent/feature-activity-reporting.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active
