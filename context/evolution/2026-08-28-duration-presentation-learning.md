# Learning: Preserve Canonical Durations When Changing Display Units

## Observation

Duration reports can become far easier to scan by using hours or minutes, but
their accounting and retained summaries must remain independent of that choice.

## Reusable Insight

Store and calculate elapsed time in one precise canonical unit, then convert
only at the entity presentation boundary. A user-selected unit must remain
stable for every numeric duration sensor on a monitor; an automatic per-value
unit would make states, historical charts, and automations ambiguous.

## Status

- **Created**: 2026-08-28
- **Status**: Active
- **Source**: [Per-Monitor Duration Presentation Unit](../decisions/011-duration-presentation-unit.md)
