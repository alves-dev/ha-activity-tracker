"""Tests for the read-only Activity Rules sidebar data model."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from custom_components.activity_tracker.panel import _monitor_snapshots
from custom_components.activity_tracker.panel_editor import (
    DraftValidationError,
    draft_preview,
    normalize_draft,
)


def test_rule_panel_snapshot_exposes_live_condition_results() -> None:
    now = datetime.now().astimezone()
    rule = {
        "start_when": {
            "type": "state",
            "entity_id": "binary_sensor.bed",
            "states": ["on"],
        },
        "stop_when": {
            "type": "template",
            "value_template": "{{ state_attr('sensor.phone', 'charging') }}",
        },
    }
    entry = SimpleNamespace(
        entry_id="sleep",
        title="Sleep",
        data={"rule": rule, "template": "custom"},
    )
    state = SimpleNamespace(state="on", last_changed=now, last_reported=now)
    runtime = SimpleNamespace(
        session=SimpleNamespace(),
        _template_results={rule["stop_when"]["value_template"]: False},
    )
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda _: [entry]),
        data={"activity_tracker": {"sleep": runtime}},
        states=SimpleNamespace(get=lambda _: state),
    )

    with patch(
        "custom_components.activity_tracker.panel.dt_util.now", return_value=now
    ):
        snapshots = _monitor_snapshots(hass)

    assert snapshots[0]["active"]
    assert snapshots[0]["start"]["matched"]
    assert snapshots[0]["start"]["current_state"] == "on"
    assert not snapshots[0]["stop"]["matched"]
    assert snapshots[0]["stop"]["template_result"] is False


def test_draft_preview_supports_nested_conditions_templates_and_history_gate() -> None:
    now = datetime.now().astimezone()
    entry = SimpleNamespace(
        entry_id="sleep",
        title="Sleep",
        data={
            "name": "Sleep",
            "template": "custom",
            "rule": {
                "start_when": {
                    "type": "state",
                    "entity_id": "binary_sensor.bed",
                    "states": ["on"],
                },
                "stop_when": {
                    "type": "state",
                    "entity_id": "binary_sensor.bed",
                    "states": ["off"],
                },
            },
            "period_metrics": {"current_day": ["total_duration"]},
            "enabled_metrics": [],
        },
        options={"cross_midnight_policy": "split_at_midnight"},
    )
    hass = SimpleNamespace(
        config=SimpleNamespace(legacy_templates=False),
        states=SimpleNamespace(
            get=lambda entity_id: (
                SimpleNamespace(state="on", last_changed=now, last_reported=now)
                if entity_id == "binary_sensor.bed"
                else None
            )
        ),
    )
    draft = {
        "name": "Sleep",
        "template": "custom",
        "rule": {
            "start_when": {
                "operator": "all",
                "conditions": [
                    {
                        "type": "state",
                        "entity_id": "binary_sensor.bed",
                        "states": ["on"],
                        "operator": "equals",
                        "for_seconds": 0,
                    },
                    {"type": "template", "value_template": "true"},
                ],
            },
            "stop_when": {
                "type": "state",
                "entity_id": "binary_sensor.bed",
                "states": ["off"],
                "operator": "equals",
                "for_seconds": 0,
            },
        },
        "options": {
            "duration_unit": "h",
            "retention_days": 90,
            "minimum_session_seconds": 0,
            "cross_midnight_policy": "split_at_midnight",
        },
        "period_metrics": {"current_day": ["total_duration"]},
        "enabled_metrics": [],
    }

    preview = draft_preview(hass, draft, entry)

    assert preview["requires_history_clear"]
    assert preview["draft"]["rule"]["start_when"]["operator"] == "all"
    assert preview["preview"]["start"]["matched"]
    assert preview["preview"]["start"]["conditions"][1]["template_result"] is True


def test_draft_validation_rejects_an_empty_or_invalid_expression() -> None:
    hass = SimpleNamespace(states=SimpleNamespace(get=lambda _: None))
    draft = {
        "name": "Broken",
        "template": "custom",
        "rule": {"start_when": {"operator": "all", "conditions": []}},
        "options": {},
        "period_metrics": {"current_day": ["total_duration"]},
        "enabled_metrics": [],
    }

    try:
        normalize_draft(hass, draft)
    except DraftValidationError as error:
        assert "start" in error.errors
    else:
        msg = "The panel backend must reject incomplete drafts."
        raise AssertionError(msg)


def test_draft_validation_accepts_numeric_state_comparison() -> None:
    hass = SimpleNamespace(states=SimpleNamespace(get=lambda _: None))
    draft = {
        "name": "Warm room",
        "template": "custom",
        "rule": {
            "start_when": {
                "operator": "all",
                "conditions": [
                    {
                        "type": "numeric_state",
                        "entity_id": "sensor.temperature",
                        "attribute": None,
                        "operator": "greater_or_equal",
                        "value": "25.0",
                        "for_seconds": 30,
                    }
                ],
            },
            "stop_when": {
                "operator": "all",
                "conditions": [
                    {
                        "type": "numeric_state",
                        "entity_id": "sensor.temperature",
                        "operator": "less_than",
                        "value": "24",
                        "for_seconds": 0,
                    }
                ],
            },
        },
        "options": {},
        "period_metrics": {"current_day": ["total_duration"]},
        "enabled_metrics": [],
    }

    data, _options = normalize_draft(hass, draft)

    assert data["rule"]["start_when"]["conditions"][0]["value"] == "25.0"


def test_panel_review_action_is_not_shadowed_by_the_review_renderer() -> None:
    source = Path(
        "custom_components/activity_tracker/frontend/activity-rules-panel.js"
    ).read_text()

    assert source.count("async _review()") == 1
    assert source.count("_renderReview()") >= 2
