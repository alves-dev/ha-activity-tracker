"""Tests for the unified-rule configuration journeys."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from homeassistant.util import dt as dt_util

from custom_components.activity_tracker.config_flow import (
    ActivityTrackerConfigFlow,
    ActivityTrackerOptionsFlow,
    _condition_choices,
    _conditions_status,
    _expression,
    _previous_day_periods,
)
from custom_components.activity_tracker.const import (
    CONF_ENABLED_METRICS,
    CONF_PERIOD_METRICS,
    CONF_RULE,
    OPT_CROSS_MIDNIGHT_POLICY,
)


def _flow() -> ActivityTrackerConfigFlow:
    flow = ActivityTrackerConfigFlow()
    flow.hass = SimpleNamespace(states=SimpleNamespace(get=lambda _: None))
    flow.async_show_form = lambda **kwargs: kwargs
    flow.async_create_entry = lambda **kwargs: kwargs
    return flow


async def test_custom_flow_finishes_without_an_extra_condition() -> None:
    flow = _flow()

    assert (await flow.async_step_user({"template": "custom"}))["step_id"] == "source"
    assert (await flow.async_step_source({"name": "Sleep"}))[
        "step_id"
    ] == "start_condition"
    assert (await flow.async_step_start_condition({"editor_action": "add"}))[
        "step_id"
    ] == "condition"
    assert (
        await flow.async_step_condition(
            {
                "entity_id": "binary_sensor.bed",
                "condition_type": "state",
                "states": "on",
                "operator": "equals",
                "for_seconds": 0,
                "next_action": "and",
            }
        )
    )["description_placeholders"]["conditions"] == "(binary_sensor.bed is on)"
    await flow.async_step_start_condition({"editor_action": "add"})
    assert (
        await flow.async_step_condition(
            {
                "entity_id": "person.igor",
                "condition_type": "state",
                "states": "home",
                "operator": "equals",
                "for_seconds": 0,
                "next_action": "or",
            }
        )
    )["description_placeholders"][
        "conditions"
    ] == "(binary_sensor.bed is on AND person.igor is home)"
    await flow.async_step_start_condition({"editor_action": "add"})
    assert (
        await flow.async_step_condition(
            {
                "entity_id": "person.jade",
                "condition_type": "state",
                "states": "home",
                "operator": "equals",
                "for_seconds": 0,
                "next_action": "finish",
            }
        )
    )["step_id"] == "stop_condition"
    assert (await flow.async_step_stop_condition({"editor_action": "add"}))[
        "step_id"
    ] == "condition"
    behavior = await flow.async_step_condition(
        {
            "entity_id": "binary_sensor.bed",
            "condition_type": "state",
            "states": "off",
            "operator": "equals",
            "for_seconds": 30,
            "next_action": "finish",
        }
    )
    assert behavior["step_id"] == "behavior"
    assert flow._data[CONF_RULE]["start_when"] == _expression(
        [
            [
                {
                    "type": "state",
                    "entity_id": "binary_sensor.bed",
                    "states": ["on"],
                    "operator": "equals",
                    "for_seconds": 0,
                },
                {
                    "type": "state",
                    "entity_id": "person.igor",
                    "states": ["home"],
                    "operator": "equals",
                    "for_seconds": 0,
                },
            ],
            [
                {
                    "type": "state",
                    "entity_id": "person.jade",
                    "states": ["home"],
                    "operator": "equals",
                    "for_seconds": 0,
                }
            ],
        ]
    )


async def test_flow_collects_closed_day_periods_and_metric_pairs() -> None:
    flow = _flow()
    await flow.async_step_user({"template": "zone_presence"})
    await flow.async_step_source(
        {"name": "Home", "entity_id": "person.igor", "zone_entity_id": "zone.home"}
    )
    await flow.async_step_behavior(
        {
            "duration_unit": "h",
            "retention_days": 30,
            "minimum_session_seconds": 0,
            "cross_midnight_policy": "split_at_midnight",
        }
    )
    assert (
        await flow.async_step_periods(
            {"periods": ["current_day"], "previous_days": "1, 2"}
        )
    )["step_id"] == "period_metrics"
    await flow.async_step_period_metrics({CONF_PERIOD_METRICS: ["total_duration"]})
    await flow.async_step_period_metrics({CONF_PERIOD_METRICS: ["session_count"]})
    assert (
        await flow.async_step_period_metrics(
            {CONF_PERIOD_METRICS: ["average_start_time"]}
        )
    )["step_id"] == "metrics"
    review = await flow.async_step_metrics(
        {CONF_ENABLED_METRICS: ["time_since_last_session"]}
    )
    created = await flow.async_step_review({})

    assert review["step_id"] == "review"
    assert created["data"][CONF_PERIOD_METRICS] == {
        "current_day": ["total_duration"],
        "previous_day:1": ["session_count"],
        "previous_day:2": ["average_start_time"],
    }
    assert _previous_day_periods("1, 2") == ["previous_day:1", "previous_day:2"]


async def test_template_rule_flow_collects_start_and_stop_templates() -> None:
    flow = _flow()

    assert (
        await flow.async_step_user({"template": "template_rule"})
    )["step_id"] == "source"
    assert (await flow.async_step_source({"name": "High battery"}))[
        "step_id"
    ] == "template_rule"
    behavior = await flow.async_step_template_rule(
        {"start_template": "true", "stop_template": "false"}
    )

    assert behavior["step_id"] == "behavior"
    assert flow._data[CONF_RULE] == {
        "start_when": {"type": "template", "value_template": "true"},
        "stop_when": {"type": "template", "value_template": "false"},
    }


async def test_options_rule_change_requires_history_clear_confirmation() -> None:
    entry = SimpleNamespace(
        entry_id="monitor",
        title="Old",
        data={"template": "custom", "name": "Old", CONF_RULE: {}},
        options={OPT_CROSS_MIDNIGHT_POLICY: "split_at_midnight"},
    )
    runtime = SimpleNamespace(async_clear_history=AsyncMock())
    updates = []

    class Entries:
        def async_get_known_entry(self, _entry_id):
            return entry

        def async_update_entry(self, _entry, **kwargs):
            updates.append(kwargs)

    flow = ActivityTrackerOptionsFlow()
    flow.hass = SimpleNamespace(
        config_entries=Entries(),
        data={"activity_tracker": {"monitor": runtime}},
        states=SimpleNamespace(get=lambda _: None),
    )
    flow.handler = "monitor"
    flow.async_show_form = lambda **kwargs: kwargs
    flow.async_create_entry = lambda **kwargs: kwargs
    flow._start_editor(
        {
            "template": "custom",
            "name": "New",
            CONF_RULE: {"new": True},
            CONF_PERIOD_METRICS: {"current_day": ["total_duration"]},
            CONF_ENABLED_METRICS: [],
        },
        {OPT_CROSS_MIDNIGHT_POLICY: "ended_day"},
    )
    result = await flow._async_save_monitor()
    assert result["step_id"] == "confirm_history"
    assert (await flow.async_step_confirm_history({"confirm_history_action": False}))[
        "errors"
    ] == {"confirm_history_action": "confirmation_required"}
    await flow.async_step_confirm_history({"confirm_history_action": True})
    runtime.async_clear_history.assert_awaited_once()
    assert updates[0]["title"] == "New"


async def test_options_preserves_conditions_and_shows_current_snapshot() -> None:
    """Editing an activity must begin with its saved rule, not a blank editor."""
    rule = {
        "start_when": _expression(
            [
                [
                    {
                        "type": "state",
                        "entity_id": "binary_sensor.bed",
                        "states": ["on"],
                        "operator": "equals",
                        "for_seconds": 0,
                    }
                ]
            ]
        ),
        "stop_when": _expression(
            [
                [
                    {
                        "type": "state",
                        "entity_id": "binary_sensor.bed",
                        "states": ["off"],
                        "operator": "equals",
                        "for_seconds": 0,
                    }
                ]
            ]
        ),
    }
    state = SimpleNamespace(state="on", last_changed=dt_util.utcnow())
    flow = ActivityTrackerOptionsFlow()
    flow.hass = SimpleNamespace(states=SimpleNamespace(get=lambda _: state))
    flow.async_show_form = lambda **kwargs: kwargs
    flow._start_editor(
        {
            "template": "custom",
            "name": "Sleep",
            CONF_RULE: rule,
            CONF_PERIOD_METRICS: {"current_day": ["total_duration"]},
            CONF_ENABLED_METRICS: [],
        }
    )

    form = await flow.async_step_source({"name": "Sleep"})

    assert form["description_placeholders"]["conditions"] == (
        "(binary_sensor.bed is on)"
    )
    assert "Start: ✓ matched" in form["description_placeholders"]["status"]
    assert "current on" in form["description_placeholders"]["status"]

    removing = await flow.async_step_start_condition({"editor_action": "remove"})
    assert removing["step_id"] == "remove_condition"
    removed = await flow.async_step_remove_condition(
        {"condition_id": _condition_choices(flow._conditions["start"])[0]}
    )

    assert removed["description_placeholders"]["conditions"] == "No conditions yet."


def test_condition_snapshot_shows_a_pending_report_silence_deadline() -> None:
    state = SimpleNamespace(
        state="on",
        last_changed=dt_util.utcnow(),
        last_reported=dt_util.utcnow(),
    )

    status = _conditions_status(
        SimpleNamespace(states=SimpleNamespace(get=lambda _: state)),
        [
            [
                {
                    "type": "report_silence",
                    "entity_id": "sensor.phone",
                    "for_seconds": 300,
                }
            ]
        ],
        "stop",
    )

    assert "Stop: ✕ not matched" in status
    assert "sensor.phone: current on" in status
    assert "remaining" in status
