# AGENTS.md

## Setup Commands

- Install: `uv sync`
- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Validate integration structure: `python3 /path/to/home-assistant-integration-standards/scripts/validate_integration_structure.py .`
- Local smoke test: copy `custom_components/activity_tracker` into a Home Assistant configuration directory, restart Home Assistant, add a monitor through the UI, and change the source state from Developer Tools.

## Code Style

- Use Python 3.14 syntax and Home Assistant async conventions.
- Ruff uses an 88-character line length and enforces bugbear, isort, naming, pylint, pyupgrade, and related rules.
- Keep activity-rule classification, session accounting, storage, and entity presentation separated.
- Follow patterns from `@context/knowledge/patterns/`.

## Context Files to Load

Before starting work, load relevant context:

- `@context/intent/project-intent.md` (always)
- `@context/intent/feature-*.md` (for the affected feature)
- `@context/decisions/*.md` (relevant technical decisions)
- `@context/knowledge/patterns/*.md` (patterns to follow)
- `@context/.context-mesh-framework.md` (framework rules)
- `@context/evolution/*-implementation-plan.md` (an active proposed plan, when present)

## Project Structure

```text
root/
├── AGENTS.md
├── context/
│   ├── intent/
│   ├── decisions/
│   ├── knowledge/
│   ├── agents/
│   └── evolution/
├── custom_components/activity_tracker/
├── tests/
└── docs/
```

## AI Agent Rules

### Always

- Load relevant context before planning or implementing.
- Follow accepted decisions from `@context/decisions/`.
- Use patterns from `@context/knowledge/patterns/`.
- Apply the mandatory Plan, Approve, Execute workflow in the framework file.
- Update Context Mesh after changes.

### Never

- Ignore documented decisions without superseding them.
- Put technical implementation details in feature-intent files.
- Put code recipes in decision files.
- Leave context stale after changes.

### After Any Changes (Critical)

- Update affected feature intent when functionality changes.
- Create or update ADRs for technical choices and record outcomes when implementation differs.
- Update `context/evolution/changelog.md`.
- Create a learning file for significant, reusable insights.

## Definition of Done (Build Phase)

- [ ] ADR exists before implementation when a technical decision is involved.
- [ ] Code follows documented patterns.
- [ ] Accepted decisions are respected.
- [ ] Relevant tests and linting pass.
- [ ] Context reflects the completed change.
- [ ] Changelog is updated.
