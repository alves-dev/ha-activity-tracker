"""Tests for config-flow input helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from custom_components.activity_tracker.config_flow import (
    ActivityTrackerConfigFlow,
    ActivityTrackerOptionsFlow,
    _is_rule_changing,
    _rolling_periods,
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


def test_rule_change_classification_excludes_presentation_options() -> None:
    data = {
        CONF_MONITOR_TYPE: TYPE_ENTITY_STATE,
        CONF_ENTITY_ID: "input_boolean.activity",
        CONF_ACTIVE_STATES: ["on"],
        CONF_NAME: "Activity",
        CONF_PERIODS: ["current_day"],
        CONF_ENABLED_METRICS: ["total_duration"],
    }
    options = {"retention_days": 90, "minimum_session_seconds": 0}

    assert not _is_rule_changing(
        data,
        options,
        {**data, CONF_NAME: "Renamed", CONF_PERIODS: ["current_week"]},
        {**options, "retention_days": 30},
    )
    assert _is_rule_changing(
        data,
        options,
        {**data, CONF_ACTIVE_STATES: ["on", "playing"]},
        options,
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


async def test_options_flow_edits_a_complete_monitor() -> None:
    entry = SimpleNamespace(
        entry_id="monitor-1",
        title="Old monitor",
        data={
            CONF_MONITOR_TYPE: TYPE_ENTITY_STATE,
            CONF_NAME: "Old monitor",
            CONF_ENTITY_ID: "input_boolean.old",
            CONF_ACTIVE_STATES: ["on"],
            CONF_PERIODS: ["current_day"],
            CONF_ENABLED_METRICS: ["total_duration"],
        },
        options={"retention_days": 90, "minimum_session_seconds": 0},
    )
    updates: list[dict[str, object]] = []

    class Entries:
        def async_get_known_entry(self, entry_id: str):
            assert entry_id == entry.entry_id
            return entry

        def async_update_entry(self, updated_entry, **kwargs):
            assert updated_entry is entry
            updates.append(kwargs)

    flow = ActivityTrackerOptionsFlow()
    flow.hass = SimpleNamespace(config_entries=Entries(), data={})
    flow.handler = entry.entry_id
    flow.async_show_form = lambda **kwargs: kwargs
    flow.async_create_entry = lambda **kwargs: kwargs

    assert (await flow.async_step_init())["step_id"] == "init"
    assert (await flow.async_step_init({CONF_MONITOR_TYPE: TYPE_ENTITY_STATE}))[
        "step_id"
    ] == "source"
    assert (
        await flow.async_step_source(
            {
                CONF_NAME: "New monitor",
                CONF_ENTITY_ID: "input_boolean.new",
                CONF_ACTIVE_STATES: "on, playing",
            }
        )
    )["step_id"] == "behavior"
    assert (await flow.async_step_behavior({"retention_days": 30}))[
        "step_id"
    ] == "periods"
    assert (
        await flow.async_step_periods(
            {CONF_PERIODS: ["current_week"], "rolling_days": "7"}
        )
    )["step_id"] == "metrics"
    assert (await flow.async_step_metrics({CONF_ENABLED_METRICS: ["session_count"]}))[
        "step_id"
    ] == "history"
    created = await flow.async_step_history({"history_action": "keep"})

    assert created["data"]["retention_days"] == 30
    assert updates[0]["title"] == "New monitor"
    assert updates[0]["data"][CONF_PERIODS] == ["current_week", "rolling_days:7"]


async def test_options_flow_confirms_destructive_history_actions() -> None:
    entry = SimpleNamespace(
        entry_id="monitor-1",
        title="Monitor",
        data={
            CONF_MONITOR_TYPE: TYPE_ENTITY_STATE,
            CONF_NAME: "Monitor",
            CONF_ENTITY_ID: "input_boolean.activity",
            CONF_ACTIVE_STATES: ["on"],
            CONF_PERIODS: ["current_day"],
            CONF_ENABLED_METRICS: ["total_duration"],
        },
        options={"retention_days": 90, "minimum_session_seconds": 0},
    )
    updates: list[dict[str, object]] = []
    runtime = SimpleNamespace(async_clear_history=AsyncMock())

    class Entries:
        def async_get_known_entry(self, entry_id: str):
            return entry

        def async_update_entry(self, updated_entry, **kwargs):
            updates.append(kwargs)

    flow = ActivityTrackerOptionsFlow()
    flow.hass = SimpleNamespace(
        config_entries=Entries(), data={"activity_tracker": {entry.entry_id: runtime}}
    )
    flow.handler = entry.entry_id
    flow.async_show_form = lambda **kwargs: kwargs
    flow.async_create_entry = lambda **kwargs: kwargs

    await flow.async_step_init({CONF_MONITOR_TYPE: TYPE_ENTITY_STATE})
    await flow.async_step_source(
        {
            CONF_NAME: "Monitor",
            CONF_ENTITY_ID: "input_boolean.activity",
            CONF_ACTIVE_STATES: "on, playing",
        }
    )
    await flow.async_step_behavior({"retention_days": 90})
    await flow.async_step_periods({CONF_PERIODS: ["current_day"], "rolling_days": ""})
    assert (
        await flow.async_step_metrics({CONF_ENABLED_METRICS: ["total_duration"]})
    )["step_id"] == "history"
    assert (
        await flow.async_step_history({"history_action": "clear"})
    )["step_id"] == "confirm_history"
    rejected = await flow.async_step_confirm_history({"confirm_history_action": False})
    assert rejected["errors"] == {"confirm_history_action": "confirmation_required"}
    assert not updates
    created = await flow.async_step_confirm_history({"confirm_history_action": True})

    assert created["data"]["retention_days"] == 90
    runtime.async_clear_history.assert_awaited_once()


async def test_options_flow_skips_history_step_for_presentation_only_edit() -> None:
    entry = SimpleNamespace(
        entry_id="monitor-1",
        data={
            CONF_MONITOR_TYPE: TYPE_ENTITY_STATE,
            CONF_NAME: "Monitor",
            CONF_ENTITY_ID: "input_boolean.activity",
            CONF_ACTIVE_STATES: ["on"],
            CONF_PERIODS: ["current_day"],
            CONF_ENABLED_METRICS: ["total_duration"],
        },
        options={"retention_days": 90, "minimum_session_seconds": 0},
    )

    class Entries:
        def async_get_known_entry(self, entry_id: str):
            return entry

        def async_update_entry(self, updated_entry, **kwargs):
            return None

    flow = ActivityTrackerOptionsFlow()
    flow.hass = SimpleNamespace(config_entries=Entries(), data={})
    flow.handler = entry.entry_id
    flow.async_show_form = lambda **kwargs: kwargs
    flow.async_create_entry = lambda **kwargs: kwargs
    flow._monitor = {**entry.data, CONF_NAME: "Renamed"}
    flow._options = {**entry.options, "retention_days": 30}

    result = await flow.async_step_metrics(
        {CONF_ENABLED_METRICS: ["total_duration", "session_count"]}
    )

    assert result["data"]["retention_days"] == 30
