"""Compatibility helpers for monitor report selections."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import (
    CONF_ENABLED_METRICS,
    CONF_PERIOD_METRICS,
    CONF_PERIODS,
    METRICS,
    PERIOD_METRICS,
    PERIODS,
)


def period_metric_selections(data: Mapping[str, Any]) -> dict[str, list[str]]:
    """Return the selected period-aware metrics, including legacy entries."""
    selected = data.get(CONF_PERIOD_METRICS)
    if isinstance(selected, Mapping):
        return {
            period: _selected_metrics(metrics, PERIOD_METRICS)
            for period, metrics in selected.items()
            if _valid_period(period) and _selected_metrics(metrics, PERIOD_METRICS)
        }

    metrics = _selected_metrics(data.get(CONF_ENABLED_METRICS), PERIOD_METRICS)
    return {
        period: metrics
        for period in _selected_periods(data.get(CONF_PERIODS))
        if metrics
    }


def monitor_metric_selections(data: Mapping[str, Any]) -> list[str]:
    """Return selected monitor-wide metrics from either configuration shape."""
    return _selected_metrics(
        data.get(CONF_ENABLED_METRICS), set(METRICS) - PERIOD_METRICS
    )


def migrate_monitor_data(data: Mapping[str, Any]) -> dict[str, Any]:
    """Convert legacy Cartesian report selections to explicit period selections."""
    if isinstance(data.get(CONF_PERIOD_METRICS), Mapping):
        return dict(data)
    migrated = dict(data)
    migrated[CONF_PERIOD_METRICS] = period_metric_selections(data)
    migrated[CONF_ENABLED_METRICS] = monitor_metric_selections(data)
    migrated.pop(CONF_PERIODS, None)
    return migrated


def _selected_periods(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(period for period in value if _valid_period(period)))


def _selected_metrics(value: object, allowed: set[str] | frozenset[str]) -> list[str]:
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(metric for metric in value if metric in allowed))


def _valid_period(value: object) -> bool:
    if value in PERIODS:
        return True
    if not isinstance(value, str) or not value.startswith("rolling_days:"):
        return False
    try:
        return int(value.split(":", 1)[1]) > 0
    except ValueError:
        return False
