# Decision: Activity Image Presentation and Missing-Image Repair

## Context

Activities can be easier to identify during a workout when they have an
associated image or animated GIF. Existing activities do not have this
metadata, and opening an image from the activity workspace should not take the
user away from Home Assistant.

## Decision

Store an optional `image_url` alongside the activity's persisted configuration.
Expose it in the server-owned Activity Rules draft editor and the native setup
flow. Create a non-blocking Home Assistant issue for each configured activity
that has no image URL; remove that issue as soon as the activity is saved with
one. Render the URL as an image in the Activity Rules panel and open it in an
in-panel modal when clicked. The modal uses the image URL directly so animated
GIFs remain animated and no browser navigation occurs.

The URL is validated as HTTP(S) input at the integration boundary. Existing
entries remain valid without an image so this is an adoption aid, not a
required migration.

## Rationale

The config entry is the authoritative owner of activity presentation metadata,
and the existing server-owned draft editor already centralizes validation and
persistence. The issue registry gives administrators a discoverable repair
without making historical activities unusable. A local modal keeps the user in
the workout context and supports both static images and GIFs.

## Status

- **Created**: 2026-09-19
- **Status**: Accepted

## Related

- [Feature: Guided Monitor Management](../intent/feature-guided-monitor-management.md)
- [Pattern: Server-Owned Sidebar Draft Editor](../knowledge/patterns/server-owned-sidebar-draft-editor.md)
