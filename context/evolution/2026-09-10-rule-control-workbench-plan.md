# Plan: Activity Rule Control Workbench

## Purpose

Give users a calm, visual way to inspect and change rules when the compact
Home Assistant options flow becomes too narrow for multi-condition activities.

## Proposed Experience

The sidebar page, titled **Activity Rules**, is a three-area workspace:

```text
Monitors                 Rule canvas                         Inspector
──────────               ───────────                         ─────────
Sleep       Active       Start:  ALL                         selected condition
Washer      Waiting        ├─ Bed = on        ✓              entity + state
Office temp Warning        └─ Person = home   ✕              duration / grouping
                         Stop:   ANY                         live result / reason
                           ├─ Bed = off       ✕              remove / duplicate
                           └─ Sensor stale    ✓
```

1. The monitor list shows the active state, source-health warning, and a short
   rule summary. It filters by monitor name and status.
2. The rule canvas renders start and stop as visible AND/OR trees. Each leaf
   shows its current result, observed value, and pending deadline. The user can
   select, insert, move, duplicate, or remove a leaf without losing context.
3. The inspector edits only the selected leaf or group. It includes a safe
   template editor with preview output for template-rule monitors.
4. Saving shows a precise diff and invokes the existing server-side retained
   history confirmation whenever the rule or midnight policy changed.

## Architecture Boundaries

- This is a future custom sidebar panel, with a bundled local frontend module
  and a permission-checked websocket API for read-only snapshots and draft
  validation.
- The browser never writes config-entry data directly. The backend validates
  the full rule and performs the existing history-clear confirmation.
- Live status is pushed from the runtime; saved rules, draft previews, and
  active-session data remain separated.
- The panel must use Home Assistant-supported APIs and responsive layout, and
  retain full functionality in the native options flow.

## Delivery Slices

1. Read-only monitor list and live expression canvas.
2. Draft editor with condition/group operations and server validation.
3. Save/review/history-confirmation integration.
4. Template preview, accessibility review, translations, and local HA smoke
   testing.

## Status

- **Created**: 2026-09-10
- **Status**: Proposed product plan; no sidebar implementation is authorized by
  this document alone.
