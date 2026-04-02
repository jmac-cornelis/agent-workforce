# Agent Rename Execution Backlog

## Purpose

This document turns the approved agent rename slate into a concrete execution plan.
It covers:

- repo code and file changes
- CLI, API, MCP, and Teams surfaces
- deployment and runtime migration
- Confluence and published documentation
- compatibility handling for live agents

## Approved Rename Map

| Current | New | Internal Slug | Notes |
|---|---|---|---|
| Hypatia | Hemingway | `hemingway` | Implemented and deployed; highest-risk rename |
| Hedy | Humphrey | `humphrey` | Planned |
| Brandeis | Blackstone | `blackstone` | Planned |
| Babbage | Mercator | `mercator` | Planned |
| Linnaeus | Berners-Lee | `bernerslee` | Use hyphen only in display name |
| Herodotus | Pliny | `pliny` | Planned |
| Brooks | Shackleton | `shackleton` | Planned |
| Ada | Galileo | `galileo` | Planned |

## Rename Principles

1. New names become the canonical public names.
2. Old names remain as aliases for one transition cycle.
3. Ports stay the same.
4. Confluence pages should be renamed in place where possible.
5. Teams, CLI, and API should continue to recognize old names during the transition.
6. Internal slugs stay lowercase and punctuation-free.
7. `Berners-Lee` uses `bernerslee` internally and `Berners-Lee` in user-facing text.

## Workstreams

### 1. Naming Contract And Alias Layer

Goal: create one source of truth for agent identity and make old names work during migration.

Files and surfaces:

- `agents/README.md`
- `agent_cli.py`
- `mcp_server.py`
- `config/shannon/agent_registry.yaml`
- any central agent registries or exported symbol maps

Tasks:

1. Add a rename map and alias map in one shared location.
2. Update CLI parsing to accept both old and new names.
3. Update Shannon routing so both names resolve to the same agent.
4. Update any MCP or tool naming surfaces that expose these agents.
5. Add a standard deprecation message when an old name is used.

Acceptance criteria:

- `agent-cli hypatia ...` and `agent-cli hemingway ...` both work during transition
- old and new Shannon commands resolve correctly
- new names are shown in help text and cards

### 2. Repo File And Import Rename

Goal: rename the agent packages and direct imports.

Target directories:

- `agents/hypatia` -> `agents/hemingway`
- `agents/hedy` -> `agents/humphrey`
- `agents/brandeis` -> `agents/blackstone`
- `agents/babbage` -> `agents/mercator`
- `agents/linnaeus` -> `agents/bernerslee`
- `agents/herodotus` -> `agents/pliny`
- `agents/brooks` -> `agents/shackleton`
- `agents/ada` -> `agents/galileo`

Primary files to update:

- `agents/__init__.py`
- `mcp_server.py`
- `pyproject.toml`
- imports in tests
- prompt and state imports inside each renamed package

Tasks:

1. Rename package directories.
2. Rename module-level class names where they include the old agent name.
3. Update imports across the repo.
4. Keep lightweight compatibility shim modules if needed for one cycle.

Acceptance criteria:

- repo imports succeed under new names
- old imports either still work through a shim or fail only after the compatibility window
- smoke tests for renamed agents pass

### 3. Display Name And Documentation Update

Goal: replace old names in user-facing docs and plans.

High-priority docs:

- `agents/README.md`
- each renamed agent `README.md`
- each renamed agent `docs/PLAN.md`
- `docs/workflows.md`
- `docs/agent-usefulness-and-applications.md`
- `docs/workforce/README.md`
- `docs/workforce/*.md` that refer to these agents
- `plans/*.md` where these names are part of current architecture descriptions

Tasks:

1. Update headings, prose, and dependency tables.
2. Update examples and command names.
3. Update cross-agent references in other agents' docs.
4. Update diagrams and diagram labels where these names appear.

Acceptance criteria:

- no stale old names remain in primary docs except in migration notes
- all user-facing examples show the new names

### 4. CLI, API, MCP, And Entrypoints

Goal: make the runnable system speak the new names.

Files and surfaces:

- `agent_cli.py`
- `pyproject.toml`
- `mcp_server.py`
- each renamed agent's `api.py`
- any standalone CLI entrypoints

Tasks:

1. Rename standalone commands where they exist.
2. Update `agent-cli` subcommands and help text.
3. Update API titles/descriptions.
4. Update MCP tool descriptions and names where exposed.
5. Keep old CLI spellings as aliases during transition.

Acceptance criteria:

- `--help` surfaces show the new names
- old commands still work with deprecation warnings
- MCP shows new names

### 5. Teams And Shannon Migration

Goal: update human-facing collaboration surfaces.

Files and surfaces:

- `config/shannon/agent_registry.yaml`
- `shannon/service.py`
- `shannon/cards.py`
- docs for Teams setup and usage

Tasks:

1. Update `agent_id`, `display_name`, and channel-facing descriptions.
2. Add old-name aliases to command routing.
3. Update card titles and approval text.
4. Decide whether Teams channels are renamed immediately or after the code rollout.

Recommendation:

- rename displayed names immediately
- keep old channel references and command aliases for one transition cycle

Acceptance criteria:

- Shannon cards and responses display new names
- old commands still resolve

### 6. Deployment And Runtime Migration

Goal: update running services without breaking live systems.

Files and surfaces:

- `docker-compose.yml`
- `deploy/README.md`
- `deploy/scripts/*`
- systemd service references if present
- env var references like `AGENT_ID`

Tasks:

1. Update service names, container names, and `AGENT_ID` values.
2. Keep ports unchanged.
3. Update health check and deployment docs.
4. Ensure compatibility for any automation that still references old service names.

Acceptance criteria:

- deployment config uses new names
- ports are unchanged
- operators can still identify which old service maps to which new one

### 7. Data And State Migration

Goal: handle persisted data paths for implemented agents safely.

Highest-risk case:

- `Hypatia` -> `Hemingway`

Known current state path:

- `data/hypatia_docs`

Tasks:

1. Update the record store to prefer `data/hemingway_docs`.
2. Add read fallback from `data/hypatia_docs`.
3. Optionally add a one-time migration helper to move historical records.
4. Document the migration clearly.

Acceptance criteria:

- existing stored docs remain readable
- new records write to the new location

### 8. Confluence And Published Workforce Docs

Goal: align deployed documentation with the new names.

Files and surfaces:

- `scripts/workforce/publish_all.py`
- `scripts/workforce/publish_teams_bot_confluence.py`
- any page-title or page-body generation logic
- workforce diagrams and generated screenshots

Tasks:

1. Update page titles and body content to the new names.
2. Rename Confluence pages in place where possible.
3. Republish workforce docs after repo docs are updated.
4. Verify backlinks, TOC, and child-page relationships still work.

Acceptance criteria:

- published Confluence pages show the new names
- page URLs and IDs are preserved where possible
- no duplicate shadow pages are created unnecessarily

### 9. Tests And Validation

Goal: prove both the rename and the compatibility layer work.

Test areas:

- import/smoke tests
- CLI tests
- Shannon routing tests
- MCP tests
- implemented-agent tests for Hemingway

Tasks:

1. Update existing tests to use new canonical names.
2. Add compatibility tests for old-name aliases.
3. Add migration-path tests for Hemingway state store fallback.
4. Run full repo suite before merge.

Acceptance criteria:

- full suite passes
- alias behavior is covered by tests

## Execution Order

### Wave 1. Foundations

1. Add central rename/alias map.
2. Add CLI and Shannon alias handling.
3. Add migration notes to docs.

### Wave 2. High-Risk Live Rename

1. Rename `Hypatia` to `Hemingway`.
2. Add state-store fallback from old data path.
3. Update API, CLI, MCP, docs, Shannon, and deployment references for Hemingway.
4. Validate locally and republish Confluence workforce docs.

### Wave 3. Planned-Agent Renames

1. Rename `Hedy` to `Humphrey`
2. Rename `Brandeis` to `Blackstone`
3. Rename `Babbage` to `Mercator`
4. Rename `Linnaeus` to `Berners-Lee`
5. Rename `Herodotus` to `Pliny`
6. Rename `Brooks` to `Shackleton`
7. Rename `Ada` to `Galileo`

### Wave 4. Deployment Surfaces

1. Update compose and deploy surfaces.
2. Update service names and `AGENT_ID` values.
3. Validate that deployed implemented agents still work.

### Wave 5. Publish And Cutover

1. Republish workforce docs to Confluence.
2. Update Teams-facing registry and cards.
3. Announce old-to-new mapping.
4. Keep aliases for one release cycle.

### Wave 6. Cleanup

1. Remove old-name aliases after the transition window.
2. Remove compatibility shims.
3. Remove old migration notes once no longer needed.

## Concrete File Groups

### Repo Identity And Exports

- `agents/__init__.py`
- `agent_cli.py`
- `mcp_server.py`
- `pyproject.toml`
- `framework/events/envelope.py`

### Agent Package Trees

- `agents/hypatia/**`
- `agents/hedy/**`
- `agents/brandeis/**`
- `agents/babbage/**`
- `agents/linnaeus/**`
- `agents/herodotus/**`
- `agents/brooks/**`
- `agents/ada/**`

### Runtime And Deploy

- `docker-compose.yml`
- `deploy/README.md`
- `deploy/scripts/*`
- any service/unit files that refer to these agent IDs

### Teams And Registry

- `config/shannon/agent_registry.yaml`
- `shannon/service.py`
- `shannon/cards.py`

### Confluence Publishers

- `scripts/workforce/publish_all.py`
- `scripts/workforce/publish_teams_bot_confluence.py`

### Docs

- `agents/README.md`
- `docs/workflows.md`
- `docs/agent-usefulness-and-applications.md`
- `docs/workforce/**`
- `plans/**` where these names appear in current architecture plans

### Tests

- `tests/test_smoke.py`
- agent-specific characterization tests
- Shannon and MCP tests

## Risks

1. `Hypatia` is implemented and already deployed.
   A hard rename without aliasing could break CLI, MCP, Shannon, or state loading.

2. Confluence page duplication.
   If page titles are changed without updating publisher logic, duplicate pages may be created.

3. Teams routing drift.
   If registry IDs change before aliases are in place, commands may stop resolving.

4. Old data path breakage.
   If Hemingway does not read old Hypatia state, prior doc history may disappear from the service.

## Recommended Success Criteria

The rename is complete when:

1. New names are canonical in repo code, docs, CLI, API, MCP, Teams cards, and Confluence.
2. Old names still work as aliases for one transition cycle.
3. Hemingway can still read old Hypatia records.
4. Deploy config and docs use the new names.
5. Full test suite passes.

## Immediate Next Step

Start with Wave 1 and Wave 2 only:

1. implement the shared rename/alias layer
2. rename Hypatia to Hemingway end-to-end
3. validate the live surfaces before touching the remaining seven planned agents

