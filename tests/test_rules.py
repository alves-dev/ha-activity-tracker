"""Tests for pure unified-rule expression evaluation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from types import SimpleNamespace

from custom_components.activity_tracker.rules import (
    CONDITION_NUMERIC_STATE,
    CONDITION_REPORT_SILENCE,
    CONDITION_STATE,
    GROUP_ALL,
    GROUP_ANY,
    expression_matches,
    expression_next_deadline,
    referenced_entity_ids,
)
from custom_components.activity_tracker.session_engine import UnifiedSessionEngine


def _state(value: str, changed_at: datetime, reported_at: datetime | None = None):
    return SimpleNamespace(
        state=value,
        last_changed=changed_at,
        last_reported=reported_at or changed_at,
    )


def test_nested_all_any_state_expression() -> None:
    now = datetime(2026, 9, 9, 12, tzinfo=datetime.now().astimezone().tzinfo)
    expression = {
        "operator": GROUP_ALL,
        "conditions": [
            {
                "type": CONDITION_STATE,
                "entity_id": "binary_sensor.bed",
                "states": ["on"],
            },
            {
                "operator": GROUP_ANY,
                "conditions": [
                    {
                        "type": CONDITION_STATE,
                        "entity_id": "person.igor",
                        "states": ["home"],
                    },
                    {
                        "type": CONDITION_STATE,
                        "entity_id": "person.jade",
                        "states": ["home"],
                    },
                ],
            },
        ],
    }
    states = {
        "binary_sensor.bed": _state("on", now),
        "person.igor": _state("not_home", now),
        "person.jade": _state("home", now),
    }

    assert expression_matches(expression, states, now)
    assert referenced_entity_ids(expression) == {
        "binary_sensor.bed",
        "person.igor",
        "person.jade",
    }


def test_state_duration_matches_only_at_deadline() -> None:
    now = datetime(2026, 9, 9, 12, tzinfo=datetime.now().astimezone().tzinfo)
    expression = {
        "type": CONDITION_STATE,
        "entity_id": "sensor.phone",
        "states": ["unavailable"],
        "for_seconds": 60,
    }
    states = {"sensor.phone": _state("unavailable", now)}

    assert not expression_matches(expression, states, now)
    assert expression_next_deadline(expression, states, now) == now + timedelta(
        seconds=60
    )
    assert expression_matches(expression, states, now + timedelta(seconds=60))


def test_numeric_state_supports_comparators_and_attributes() -> None:
    now = datetime(2026, 9, 9, 12, tzinfo=datetime.now().astimezone().tzinfo)
    state = SimpleNamespace(
        state="23.50",
        attributes={"battery_level": 81},
        last_changed=now,
        last_reported=now,
    )
    states = {"sensor.room": state}

    assert expression_matches(
        {
            "type": CONDITION_NUMERIC_STATE,
            "entity_id": "sensor.room",
            "operator": "greater_or_equal",
            "value": "23.5",
        },
        states,
        now,
    )
    assert expression_matches(
        {
            "type": CONDITION_NUMERIC_STATE,
            "entity_id": "sensor.room",
            "attribute": "battery_level",
            "operator": "greater_than",
            "value": "80",
        },
        states,
        now,
    )
    assert not expression_matches(
        {
            "type": CONDITION_NUMERIC_STATE,
            "entity_id": "sensor.room",
            "operator": "less_than",
            "value": "20",
        },
        states,
        now,
    )


def test_numeric_state_duration_uses_state_change_deadline() -> None:
    now = datetime(2026, 9, 9, 12, tzinfo=datetime.now().astimezone().tzinfo)
    expression = {
        "type": CONDITION_NUMERIC_STATE,
        "entity_id": "sensor.temperature",
        "operator": "greater_than",
        "value": "25",
        "for_seconds": 60,
    }
    states = {"sensor.temperature": _state("26", now)}

    assert not expression_matches(expression, states, now)
    assert expression_next_deadline(expression, states, now) == now + timedelta(
        seconds=60
    )


def test_report_silence_uses_unchanged_report_timestamp() -> None:
    now = datetime(2026, 9, 9, 12, tzinfo=datetime.now().astimezone().tzinfo)
    expression = {
        "type": CONDITION_REPORT_SILENCE,
        "entity_id": "sensor.phone_last_update",
        "for_seconds": 300,
    }
    states = {
        "sensor.phone_last_update": _state(
            "2026-09-09T11:50:00", now - timedelta(hours=1), now
        )
    }

    assert not expression_matches(expression, states, now)
    assert expression_next_deadline(expression, states, now) == now + timedelta(
        minutes=5
    )
    assert expression_matches(expression, states, now + timedelta(minutes=5))


def test_not_equals_condition_does_not_mature_when_state_changes_back() -> None:
    now = datetime(2026, 9, 9, 12, tzinfo=datetime.now().astimezone().tzinfo)
    expression = {
        "type": CONDITION_STATE,
        "entity_id": "binary_sensor.screen",
        "states": ["on"],
        "operator": "not_equals",
        "for_seconds": 30,
    }
    states = {"binary_sensor.screen": _state("off", now - timedelta(seconds=20))}

    assert expression_next_deadline(expression, states, now) == now + timedelta(
        seconds=10
    )
    states["binary_sensor.screen"] = _state("on", now + timedelta(seconds=5))
    assert not expression_matches(expression, states, now + timedelta(seconds=30))
    assert (
        expression_next_deadline(expression, states, now + timedelta(seconds=30))
        is None
    )


def test_engine_ends_confirmed_unavailability_at_first_observation() -> None:
    now = datetime(2026, 9, 9, 12, tzinfo=datetime.now().astimezone().tzinfo)
    engine = UnifiedSessionEngine(
        {
            "start_when": {
                "type": CONDITION_STATE,
                "entity_id": "binary_sensor.use",
                "states": ["on"],
            },
            "stop_when": {
                "type": CONDITION_STATE,
                "entity_id": "sensor.health",
                "states": ["unavailable"],
                "for_seconds": 60,
            },
        }
    )
    states = {
        "binary_sensor.use": _state("on", now),
        "sensor.health": _state("ok", now),
    }

    assert engine.process(states, now).action == "started"
    states["sensor.health"] = _state("unavailable", now + timedelta(seconds=10))
    assert engine.next_deadline(states, now + timedelta(seconds=10)) == now + timedelta(
        seconds=70
    )
    transition = engine.process(states, now + timedelta(seconds=70))

    assert transition.action == "stopped"
    assert transition.accounting_ended_at == now + timedelta(seconds=10)


def test_engine_closes_normal_delayed_stop_at_its_deadline() -> None:
    now = datetime(2026, 9, 9, 12, tzinfo=datetime.now().astimezone().tzinfo)
    engine = UnifiedSessionEngine(
        {
            "start_when": {
                "type": CONDITION_STATE,
                "entity_id": "binary_sensor.use",
                "states": ["on"],
            },
            "stop_when": {
                "type": CONDITION_STATE,
                "entity_id": "binary_sensor.use",
                "states": ["off"],
                "for_seconds": 30,
            },
        }
    )
    states = {"binary_sensor.use": _state("on", now)}
    engine.process(states, now)
    states["binary_sensor.use"] = _state("off", now + timedelta(seconds=10))

    transition = engine.process(states, now + timedelta(seconds=40))

    assert transition.action == "stopped"
    assert transition.accounting_ended_at == now + timedelta(seconds=40)


def test_unavailability_anchor_is_converted_to_the_rule_local_timezone() -> None:
    local = timezone(timedelta(hours=-3))
    now = datetime(2026, 9, 9, 20, tzinfo=local)
    engine = UnifiedSessionEngine(
        {
            "start_when": {
                "type": CONDITION_STATE,
                "entity_id": "binary_sensor.use",
                "states": ["on"],
            },
            "stop_when": {
                "type": CONDITION_STATE,
                "entity_id": "sensor.source",
                "states": ["unavailable"],
                "for_seconds": 60,
            },
        }
    )
    states = {
        "binary_sensor.use": _state("on", now),
        "sensor.source": _state("ok", now),
    }
    engine.process(states, now)
    states["sensor.source"] = _state(
        "unavailable", (now + timedelta(seconds=10)).astimezone(UTC)
    )

    transition = engine.process(states, now + timedelta(seconds=70))

    assert transition.accounting_ended_at == now + timedelta(seconds=10)
