# Learning: Observation Timestamps Are Not Display Ticks

## Insight

A periodic entity-refresh tick must never update a monitor's last observed source
timestamp. Doing so converts the absence of an observation into apparent evidence
that an activity continued, which overcounts time after restarts or source loss.

## Application

The runtime keeps source observations, interruption deadlines, and presentation
refreshes separate. A checkpoint records only compact aggregate data for the
currently open logical session, allowing pauses and unknown time to be excluded
without creating a permanent session archive.

## Status

- **Created**: 2026-08-27
- **Status**: Active learning
