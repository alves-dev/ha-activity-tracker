# Learning: Initialize Template Rule Results

## Observation

The template preview correctly evaluated a constant start expression, but a
live monitor remained idle with its template result marked as pending. The
runtime subscribed to Home Assistant template updates without rendering the
initial value before the first session evaluation.

## Learning

Template trackers should be registered after an initial render populates the
runtime boolean cache. This preserves Home Assistant dependency tracking while
making constant and already-resolvable expressions effective immediately at
startup.

## Applies To

- Native template leaves in Activity Tracker rules.
- Future runtime features that cache asynchronous Home Assistant evaluations.

## Status

- **Created**: 2026-10-16
- **Status**: Active
