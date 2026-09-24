"""Tests for Activity Tracker repair issues."""

from types import SimpleNamespace
from unittest.mock import patch

from custom_components.activity_tracker.repairs import async_update_image_issue


def test_missing_image_creates_warning_issue() -> None:
    hass = SimpleNamespace()
    entry = SimpleNamespace(entry_id="workout", title="Workout", data={})

    with patch(
        "custom_components.activity_tracker.repairs.ir.async_create_issue"
    ) as create_issue:
        async_update_image_issue(hass, entry)

    assert create_issue.call_args.kwargs["translation_key"] == "missing_image"
    assert create_issue.call_args.args[2] == "missing_image_workout"


def test_image_issue_is_removed_when_url_exists() -> None:
    hass = SimpleNamespace()
    entry = SimpleNamespace(
        entry_id="workout",
        title="Workout",
        data={"image_url": "https://example.com/workout.gif"},
    )

    with patch(
        "custom_components.activity_tracker.repairs.ir.async_delete_issue"
    ) as delete_issue:
        async_update_image_issue(hass, entry)

    delete_issue.assert_called_once_with(
        hass, "activity_tracker", "missing_image_workout"
    )
