# Development

Install the pinned tooling with `uv sync`, then run:

```sh
uv run pytest
uv run ruff check .
python3 /path/to/home-assistant-integration-standards/scripts/validate_integration_structure.py .
```

The test suite enforces at least 80% coverage for `custom_components/activity_tracker`.

The final command is provided by the shared Home Assistant integration standards
repository. It validates release metadata, documentation, HACS configuration,
branding files, and the GitHub Actions flow.

For a local Home Assistant smoke test, run `sh dev/copy-to-core.sh` to stop the
local instance, deploy `custom_components/activity_tracker`, and start it again.
Then add a monitor through the UI and trigger source state changes from Developer
Tools.
