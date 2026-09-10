"""Tests for native-template unified activity rules."""

from __future__ import annotations

from datetime import datetime

from custom_components.activity_tracker.rules import (
    CONDITION_TEMPLATE,
    expression_matches,
    template_values,
)
from custom_components.activity_tracker.session_engine import UnifiedSessionEngine


def test_template_expression_uses_current_tracked_boolean_result() -> None:
    now = datetime.now().astimezone()
    expression = {
        "type": CONDITION_TEMPLATE,
        "value_template": "{{ state_attr('sensor.battery', 'level') | int > 80 }}",
    }

    assert template_values(expression) == {expression["value_template"]}
    assert not expression_matches(
        expression, {}, now, {expression["value_template"]: False}
    )
    assert expression_matches(expression, {}, now, {expression["value_template"]: True})


def test_session_engine_transitions_from_template_results() -> None:
    now = datetime.now().astimezone()
    start_template = "{{ state_attr('sensor.battery', 'level') | int > 80 }}"
    stop_template = "{{ state_attr('sensor.battery', 'level') | int <= 80 }}"
    engine = UnifiedSessionEngine(
        {
            "start_when": {
                "type": CONDITION_TEMPLATE,
                "value_template": start_template,
            },
            "stop_when": {
                "type": CONDITION_TEMPLATE,
                "value_template": stop_template,
            },
        }
    )

    assert (
        engine.process({}, now, {start_template: True, stop_template: False}).action
        == "started"
    )
    assert (
        engine.process({}, now, {start_template: False, stop_template: True}).action
        == "stopped"
    )
