# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Build & Test

- **Venv**: `.venv/bin/python` / `.venv/bin/pytest` — always use the venv, no global installs.
- **Install**: `pip install -e ".[agents,test]"` — core deps are minimal; agent pipeline and test deps are optional extras.
- **Run all tests**: `.venv/bin/pytest -q`
- **Run single test**: `.venv/bin/pytest tests/test_drucker_agent_char.py::test_drucker_agent_builds_hygiene_report_and_actions -q`
- **Syntax check**: `python -m py_compile <module.py>` on touched files before committing.
- No linter/formatter config exists (no ruff, flake8, black, mypy). Rely on existing code style.

## Code Style (Discovered)

- **Module header**: Every `.py` file starts with a `##########` banner containing `Module:`, `Description:`, `Author:`.
- **Logging**: `log = logging.getLogger(os.path.basename(sys.argv[0]))` everywhere except [`core/reporting.py`](core/reporting.py:33) which uses `logging.getLogger(__name__)` and [`mcp_server.py`](mcp_server.py:49) which uses a hardcoded name.
- **Strings**: Single quotes for all Python strings (not double quotes).
- **Docstrings**: Single-quoted triple-quote `'''` style, not `"""`.
- **Types**: Uses `typing` module (`Dict`, `List`, `Optional`, `Any`) — not Python 3.10+ built-in generics, except in newer `core/` modules which use `list[str]` style.
- **Data models**: `@dataclass` from stdlib, not Pydantic. See [`agents/base.py`](agents/base.py:31), [`tools/base.py`](tools/base.py:34).
- **Env loading**: `from dotenv import load_dotenv; load_dotenv()` at module top in any module that reads env vars.

## Agent Interface Requirements

Every implemented agent MUST expose all three user-facing surfaces:

1. **CLI** (`agents/<name>/cli.py`) — Standalone argparse-based CLI with subcommands. Registered as a console entry point in `pyproject.toml` (e.g., `drucker-agent = "agents.drucker.cli:main"`). Pattern: `build_parser()` → `main()` → `args.func(args)` dispatch. See `agents/shannon/cli.py` or `agents/gantt/cli.py` for reference.
2. **Shannon Teams interface** — Commands registered in `config/shannon/agent_registry.yaml` under the agent's entry. Each command needs: `command`, `description`, `api_method`, `api_path`, `mutation` flag. Card builders in `shannon/cards.py` render responses as Adaptive Cards.
3. **REST API** (`agents/<name>/api.py`) — FastAPI app created via `create_agent_app()` from `framework/api/app.py`. Pydantic request models, JSON responses. Endpoints must match the `api_path` values in the Shannon registry.

All three surfaces must stay aligned — same capabilities, same parameters, same behavior. When adding a new feature to an agent, wire it through all three.

**Mutation safety**: All mutation endpoints use `dry_run: Optional[bool] = None` resolved via `config.env_loader.resolve_dry_run()` (explicit param > `DRY_RUN` env var > `True` default). Shannon enforces a two-step flow for commands marked `mutation: true` — preview first, user must say "execute" to proceed.

## Architecture (Non-Obvious)

- **Per-agent directories**: Each agent lives in `agents/<name>/` with `agent.py`, `api.py`, `models.py`, `cli.py`, `tools.py`, `prompts/system.md`, `config/`, `state/`, `docs/`. See [`agents/README.md`](agents/README.md) for the full TOC.
- **Two-layer tool pattern**: Standalone CLIs (`jira_utils.py`, `github_utils.py`, `confluence_utils.py`) contain all business logic. `tools/*.py` and `agents/<name>/tools.py` are thin wrappers that return [`ToolResult`](tools/base.py:34) objects for agent consumption. [`mcp_server.py`](mcp_server.py) wraps the same utilities for MCP. All three surfaces must stay aligned.
- **Prompt files**: Agent prompts live in `agents/<name>/prompts/system.md`. Loaded via `_load_prompt_file()` using path relative to the agent module's `__file__`.
- **Shannon dual location**: `shannon/` is the legacy FastAPI Teams service; `agents/shannon/` is the newer agent-framework version with Graph API client.
- **State stores**: `agents/<name>/state/*.py` — each agent domain has its own store class. Persistence backends in [`state/persistence.py`](state/persistence.py) support JSON files and SQLite. Backward-compat re-exports in `state/__init__.py`.
- **`core/` is pure logic**: No print statements, no CLI concerns. Returns structured dicts for any consumer. See [`core/reporting.py`](core/reporting.py:7) header.
- **Framework API factory**: [`framework/api/app.py`](framework/api/app.py:20) `create_agent_app()` gives every agent a FastAPI instance with standard middleware (correlation ID, request logging, metrics) and health/status routes.
- **Environment loading**: `config/env_loader.py` provides `load_env()` (three-tier: explicit path → `config/env/` directory → root `.env`) and `resolve_dry_run()`. Agent APIs and `config/settings.py` use `load_env()`; standalone CLIs keep their own `load_dotenv()` for independent operation.

## Safety

- Default to dry-run/analysis-only. Jira and Confluence writes require explicit user request.
- Validate identifiers, scope, and destination before any mutation.
- Always use this repo's local Confluence publishing tools for Confluence writes and updates. Prefer the existing publisher scripts and `confluence_utils.py` over ad hoc API calls or one-off publish code.
- Never commit `.env`, `*.log`, or scratch files listed in `.gitignore`.

## Testing Patterns

- Tests use `_char` suffix convention (e.g., `test_drucker_agent_char.py`) for characterization tests.
- [`tests/conftest.py`](tests/conftest.py) provides shared fixtures: `issue_factory`, `mock_jira`, `fake_response_factory`, `fake_issue_resource_factory`. Jira custom fields are mapped (e.g., `customfield_17504` = customer IDs, `customfield_28434` = product family).
- Tests heavily use `monkeypatch` to stub tool functions and agent internals — no live API calls.
- `pytest-asyncio` is installed for async test support.
