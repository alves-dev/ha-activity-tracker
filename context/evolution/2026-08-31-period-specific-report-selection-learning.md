# Learning: Store Report Selections as Intentional Pairs

## Insight

When a metric has a reporting range, the selection is a metric-and-period pair,
not two independent preferences. Persisting the pair avoids creating irrelevant
entities while retaining one monitor and one activity history.

## Application

The configuration flow now collects period-aware metrics per selected report
period. A compatibility normalization translates older Cartesian selections
before sensor creation and during config-entry migration, preserving established
entity identities.

## Status

- **Created**: 2026-08-31
- **Status**: Active
