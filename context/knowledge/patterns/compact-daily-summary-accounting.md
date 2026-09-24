# Pattern: Compact Daily Summary Accounting

## Description

Account completed sessions into one aggregate per local calendar day while
keeping only the small active-session checkpoint and latest-session metadata
needed by the runtime.

## When to Use

Use this pattern when reports need durable calendar summaries but the product
must not retain a permanent detailed session archive.

## Pattern

Keep canonical duration in seconds. Convert a completed interval into one or
more local-date allocations according to the monitor's cross-midnight policy,
then update the corresponding `DailySummary`. Store timing aggregates as
circular sine/cosine components instead of averaging clock values directly.
Serialize the summary through an explicit versioned storage payload.

## Example

```python
for day, seconds in attribute_session(start, end, policy):
    summary = summaries.setdefault(day, DailySummary())
    summary.total_seconds += seconds
    summary.sessions_started += 1
    summary.add_start_time(start)
    summary.add_end_time(end)
```

## Files Using This Pattern

- [models.py](../../../custom_components/activity_tracker/models.py) - defines
  daily aggregates, local-midnight splitting, and circular time averages.
- [accounting.py](../../../custom_components/activity_tracker/accounting.py) -
  commits completed sessions into summaries.
- [storage.py](../../../custom_components/activity_tracker/storage.py) - stores
  the versioned compact payload.
- [runtime.py](../../../custom_components/activity_tracker/runtime.py) - owns
  lifecycle checkpoints and retention cleanup.

## Related

- [Decision: Compact Daily Summary Storage](../../decisions/004-compact-daily-summary-storage.md)
- [Decision: Session Day Attribution and Report Periods](../../decisions/015-session-day-attribution-and-report-periods.md)
- [Feature: Durable Activity History](../../intent/feature-durable-activity-history.md)
- [Feature: Activity Reporting](../../intent/feature-activity-reporting.md)

## Status

- **Created**: 2026-09-19
- **Status**: Active
