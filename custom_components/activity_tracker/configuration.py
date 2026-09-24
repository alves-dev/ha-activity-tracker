"""Validation helpers for unified-rule report selections."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import (
    CONF_ENABLED_METRICS,
    CONF_PERIOD_METRICS,
    METRICS,
    PERIOD_METRICS,
    PERIOD_PREVIOUS_DAY_PREFIX,
    PERIOD_ROLLING_WINDOW_PREFIX,
    PERIODS,
)


def period_metric_selections(data: Mapping[str, Any]) -> dict[str, list[str]]:
    """Return the selected period-aware metrics from the unified contract."""
    selected = data.get(CONF_PERIOD_METRICS)
    if isinstance(selected, Mapping):
        return {
            period: _selected_metrics(metrics, PERIOD_METRICS)
            for period, metrics in selected.items()
            if _valid_period(period) and _selected_metrics(metrics, PERIOD_METRICS)
        }

    return {}


def monitor_metric_selections(data: Mapping[str, Any]) -> list[str]:
    """Return selected monitor-wide metrics from the unified contract."""
    return _selected_metrics(
        data.get(CONF_ENABLED_METRICS), set(METRICS) - PERIOD_METRICS
    )


def _selected_metrics(value: object, allowed: set[str] | frozenset[str]) -> list[str]:
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(metric for metric in value if metric in allowed))


def _valid_period(value: object) -> bool:
    if value in PERIODS:
        return True
    if not isinstance(value, str):
        return False
    prefix = next(
        (
            candidate
            for candidate in (
                PERIOD_PREVIOUS_DAY_PREFIX,
                PERIOD_ROLLING_WINDOW_PREFIX,
            )
            if value.startswith(candidate)
        ),
        None,
    )
    if prefix is None:
        return False
    try:
        return int(value.removeprefix(prefix)) > 0
    except ValueError:
        return False
