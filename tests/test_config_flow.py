"""Tests for config-flow input helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock

from custom_components.activity_tracker.config_flow import (
    ActivityTrackerConfigFlow,
    _rolling_periods,
    _select_options,
    _split_states,
)
from custom_components.activity_tracker.const import (
    CONF_ACTIVE_STATES,
    CONF_ENABLED_METRICS,
    CONF_ENTITY_ID,
    CONF_MONITOR_TYPE,
    CONF_NAME,
    CONF_PERIODS,
    TYPE_ENTITY_STATE,
)


def test_split_states_normalizes_comma_separated_values() -> None:
    assert _split_states(" on, playing ,,paused ") == ["on", "playing", "paused"]


def test_rolling_periods_accepts_only_positive_whole_days() -> None:
    assert _rolling_periods("7, 35, 0, no") == (
        ["rolling_days:7", "rolling_days:35"],
        True,
    )


async def test_config_flow_runs_the_complete_entity_monitor_journey() -> None:
    flow = ActivityTrackerConfigFlow()
    flow.async_show_form = lambda **kwargs: kwargs
    flow.async_create_entry = lambda **kwargs: kwargs
    flow.async_set_unique_id = AsyncMock()

    first = await flow.async_step_user()
    assert first["step_id"] == "user"
    source = await flow.async_step_user({CONF_MONITOR_TYPE: TYPE_ENTITY_STATE})
    assert source["step_id"] == "source"
    behavior = await flow.async_step_source(
        {
            CONF_NAME: "Television",
            CONF_ENTITY_ID: "media_player.tv",
            CONF_ACTIVE_STATES: "on, playing",
        }
    )
    assert behavior["step_id"] == "behavior"
    periods = await flow.async_step_behavior({"retention_days": 90})
    assert periods["step_id"] == "periods"
    invalid = await flow.async_step_periods({CONF_PERIODS: [], "rolling_days": "zero"})
    assert invalid["errors"] == {CONF_PERIODS: "required"}
    metrics = await flow.async_step_periods(
        {CONF_PERIODS: ["current_day"], "rolling_days": "7, 35"}
    )
    assert metrics["step_id"] == "metrics"
    missing = await flow.async_step_metrics({CONF_ENABLED_METRICS: []})
    assert missing["errors"] == {CONF_ENABLED_METRICS: "required"}
    review = await flow.async_step_metrics({CONF_ENABLED_METRICS: ["total_duration"]})
    assert review["step_id"] == "review"
    created = await flow.async_step_review({})
    assert created["title"] == "Television"
    assert created["data"][CONF_ACTIVE_STATES] == ["on", "playing"]


async def test_config_flow_reports_attribute_and_rolling_input_errors() -> None:
    flow = ActivityTrackerConfigFlow()
    flow.async_show_form = lambda **kwargs: kwargs
    flow._monitor = {CONF_MONITOR_TYPE: "foreground_application"}
    result = await flow.async_step_source(
        {
            CONF_NAME: "Phone",
            CONF_ENTITY_ID: "sensor.phone",
            "value_source": "attribute",
        }
    )
    assert result["errors"] == {"value_attribute": "required"}
    flow._monitor = {CONF_MONITOR_TYPE: TYPE_ENTITY_STATE}
    result = await flow.async_step_periods(
        {CONF_PERIODS: ["current_day"], "rolling_days": "7, no"}
    )
    assert result["errors"] == {"rolling_days": "invalid_rolling_days"}


def test_select_options_keep_values_and_show_human_labels() -> None:
    options = _select_options(("entity_state", "total_duration", "unknown"))
    assert options == [
        {"value": "entity_state", "label": "Entity is in one of several active states"},
        {"value": "total_duration", "label": "Total activity duration"},
        {"value": "unknown", "label": "Mark the interval as unknown"},
    ]
