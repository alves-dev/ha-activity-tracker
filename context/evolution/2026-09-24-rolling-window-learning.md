# Learning: Explicit Historical-Day and Rolling-Window Contracts

## Discovery

Users can reasonably read “Last 10” as either the date ten days ago or the
last ten completed days. Reusing one identifier for both meanings would make
existing entity IDs silently change meaning.

## Outcome

The implementation keeps `previous_day:N` stable and adds
`rolling_window:N`. The panel describes the distinction next to the inputs,
and sensors expose the selected offset/window size in their attributes. Report
boundaries use timezone-aware half-open local-day instants, so the window does
not need a synthetic `23:59:59` endpoint.

## Reusable Insight

When a historical report can be interpreted as either an anchor date or a
duration, encode the distinction in the persisted period key and explain both
semantics at the point of configuration.

## Status

- **Created**: 2026-09-24
- **Status**: Applied
