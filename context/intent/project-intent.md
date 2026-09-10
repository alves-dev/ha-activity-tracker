# Project Intent: Activity Tracker

## What

Activity Tracker lets Home Assistant users measure how long a chosen activity is
active and how often it occurs. A user creates an independent monitor with
generic start and stop rules, then views the measurements they choose.

## Why

It gives users durable, understandable activity reports without relying on
Recorder history. This helps answer everyday questions expressed by one or more
Home Assistant entities.

## Current State

The custom integration is active at version 2026.9.0 and supports UI-only
monitor setup, persistent daily summaries, configurable report periods and
metrics, and complete monitor editing. It has a zone-presence template and a
generic rule editor with state, state-duration, and report-silence conditions.

The integration is localized in English and Brazilian Portuguese. It is distributed as a HACS custom integration and requires Home Assistant 2026.8 or newer.

## Current Features

- [Flexible activity monitoring](feature-flexible-activity-monitoring.md)
- [Guided monitor management](feature-guided-monitor-management.md)
- [Activity reporting](feature-activity-reporting.md)
- [Durable activity history](feature-durable-activity-history.md)

## Scope Boundaries

The current product does not provide a custom dashboard, permanent detailed
session history, manual correction of completed sessions, cross-monitor
rankings, numeric conditions, background-application tracking, automatic
application classification, or automatic interpretation of activity duration.
Those areas remain outside the documented MVP or are future evolution candidates.

For the full traceability of the retired implementation specification—including requirements that are only partial or not yet implemented—see [Legacy Specification Traceability](../evolution/legacy-specification-traceability.md).

## Status

- **Created**: 2026-08-27 (Phase: Intent)
- **Status**: Active
- **Note**: Generated from existing codebase analysis
