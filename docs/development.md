# Development

Install the pinned tooling with `uv sync`, then run:

```sh
uv run pytest
uv run ruff check .
python3 /home/alves-dev/.codex/skills/home-assistant-integration-standards/scripts/validate_integration_structure.py .
```

The test suite enforces at least 80% coverage for `custom_components/activity_tracker`.

For a local Home Assistant smoke test, copy `custom_components/activity_tracker` to the local HA configuration's `custom_components` directory, restart Home Assistant, add a monitor through the UI, and trigger source state changes from Developer Tools.
