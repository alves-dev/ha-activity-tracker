# Pattern: Calendar-Day Session Aggregation

## Description

Convert a completed activity interval into durable daily aggregates by splitting it at local midnight, then update per-day totals and session statistics.

## When to Use

Use this pattern when committing a live session, importing a historical session, or adding a report that relies on daily retained activity.

## Pattern

First split the interval by local date. Add each fragment's duration to its date's summary. Record the session start only on the first fragment and mark later fragments as continuations. Store the full session duration for longest and shortest session statistics so a cross-midnight session remains one logical session.

## Example

```python
for index, (date, part_start, part_end) in enumerate(
    split_interval(session.started_at, ended_at)
):
    summary = DailySummary.from_dict(summaries.get(date))
    seconds = (part_end - part_start).total_seconds()
    summary.total_seconds += seconds
    if index == 0:
        summary.sessions_started += 1
    else:
        summary.continued_sessions += 1
    summary.longest_session_seconds = max(summary.longest_session_seconds, duration)
    summaries[date] = summary.as_dict()
```

## Files Using This Pattern

- [models.py](../../../custom_components/activity_tracker/models.py) - supplies `split_interval` and the serializable `DailySummary` model.
- [runtime.py](../../../custom_components/activity_tracker/runtime.py) - commits live and imported sessions into summaries.
- [test_runtime.py](../../../tests/test_runtime.py) - verifies a session crossing midnight and application aggregation.
- [test_models.py](../../../tests/test_models.py) - verifies midnight splitting.

## Related

- [Decision: Compact Daily Summary Storage](../../decisions/004-compact-daily-summary-storage.md)
- [Decision: Real-Time Session Accounting](../../decisions/003-real-time-session-accounting.md)
- [Feature: Durable Activity History](../../intent/feature-durable-activity-history.md)

## Status

- **Created**: 2026-08-27
- **Status**: Active
