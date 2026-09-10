# Learning: Native Configuration Flows in a Custom Sidebar (Superseded)

## Insight

A locally served Home Assistant custom panel can host the platform's serialized
configuration and options flows with `hass.callApi` and `ha-form`. This keeps
entity selectors, template selectors, validation responses, review steps, and
permission enforcement aligned with the integration's existing UI.

## Application

The Activity Rules panel starts a configuration flow for adding a monitor and
an options flow for editing the selected monitor. It does not expose a custom
write websocket endpoint or config-entry mutation path. On successful flow
completion it recreates its live snapshot subscription, which also includes a
newly created monitor.

The panel must also include Home Assistant's `HA-Frontend-Base` header when it
creates or continues either flow. This mirrors the platform frontend's
config-flow client and gives the API the frontend origin it requires.

Each flow step validates its input against that step's exact schema. Retain
only values whose field names are present in the currently returned schema;
carrying a value such as `template` into the following source step is rejected
as an extra key.

The locally served panel module needs an explicit asset revision in its URL.
Home Assistant can otherwise keep a prior ES module in the browser after an
integration restart, even when the static-path response is configured without
cache headers.

The `ha-form` Shadow DOM becomes available asynchronously after insertion.
Attach a listener for its internal field events on the next animation frame so
the panel receives the complete schema-aware value changes.

## Reuse Guidance

Prefer hosting an established Home Assistant flow when a custom panel needs a
write journey already modeled by that flow. Use a bespoke mutation API only
when the panel requires a genuinely different contract, and then preserve all
destructive-action confirmations server-side.

## Status

- **Created**: 2026-09-10
- **Status**: Superseded on 2026-09-10 by
  [Sidebar Draft Editor](2026-09-10-sidebar-draft-editor-learning.md)
