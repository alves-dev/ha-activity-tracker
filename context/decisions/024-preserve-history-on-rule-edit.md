# Decision: Preserve History on Rule Edits

## Context

Activity Tracker stores completed sessions as compact daily aggregates. Editing
start or stop rules changes how future events are classified, but does not make
already completed aggregates invalid. Clearing them on every rule edit loses
valid user data.

## Decision

Rule and midnight-policy edits preserve retained summaries. The existing active
session is restored across the config-entry reload caused by an update and is
left open. Subsequent state/template events and scheduled deadlines evaluate it
against the new rules; a matching new stop rule closes it normally. No browser
confirmation or automatic history clear is required.

## Outcome

Implemented on 2026-09-10. Explicit history deletion remains an administrative
operation, separate from editing an activity.

## Status

- **Status**: Accepted
