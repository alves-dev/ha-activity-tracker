# Pattern: Selected Metric Entity Factory

## Description

Create only the report entities selected for a monitor. Period-aware metrics are
selected independently for each reporting period; monitor-wide metrics create
one entity each.

## When to Use

Use this pattern when introducing a selectable metric, a new reporting period, or a monitor-type-specific supplementary entity.

## Pattern

Define metrics that require a period separately from monitor-wide metrics. At
platform setup, iterate explicit `period → metrics` selections, then add the
monitor-wide metrics. Give each entity a stable identifier derived from the
monitor, metric, and optional period. Accept the legacy global-metrics plus
periods shape during migration by translating it to the equivalent pairs.

## Example

```python
for period, metrics in period_metric_selections(entry.data).items():
    entities.extend(ActivityMetricSensor(runtime, metric, period) for metric in metrics)
entities.extend(
    ActivityMetricSensor(runtime, metric)
    for metric in monitor_metric_selections(entry.data)
)
```

## Files Using This Pattern

- [sensor.py](../../../custom_components/activity_tracker/sensor.py) - creates selected sensors and calculates their values.
- [const.py](../../../custom_components/activity_tracker/const.py) - defines supported metrics and periods.
- [test_sensor.py](../../../tests/test_sensor.py) - verifies current, period, application, and availability values.

## Related

- [Decision: Home Assistant Config-Entry Integration](../../decisions/002-home-assistant-integration-architecture.md)
- [Feature: Activity Reporting](../../intent/feature-activity-reporting.md)
- [Decision: Period-Specific Report Sensor Selection](../../decisions/012-period-specific-report-sensor-selection.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active
