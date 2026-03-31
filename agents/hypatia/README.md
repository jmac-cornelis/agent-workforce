# Hypatia - Documentation Agent

## Overview

Hypatia is the documentation agent for the Cornelis Networks platform. Named after Hypatia of Alexandria, it turns source changes, build and test facts, traceability context, release context, and meeting-derived clarifications into durable engineering and user-facing documentation.

Hypatia does not generate prose detached from implementation truth. It produces documentation from authoritative system records - code, builds, tests, releases, and meeting decisions.

## Quick Start

```bash
# Docker
docker compose up hypatia

# Local
uvicorn agents.hypatia.api:app --host 0.0.0.0 --port 8203
```

## What Hypatia Does

- Generates and maintains repo-level as-built documentation
- Updates user and engineering documentation when code, build, test, release, or meeting knowledge changes
- Proposes documentation changes linked to their triggering events
- Publishes approved docs to internal documentation targets (Sphinx/ReadTheDocs)
- Keeps documentation linked to builds, versions, and traceability records

### What Hypatia Does Not Do

- Autonomously publish external customer-visible documentation
- Replace engineers as final approvers of normative docs
- Invent architecture or behavior not grounded in source or records
- Generate generic LLM-produced markdown dumps

## Data Sources

Hypatia draws from multiple agents to build documentation:

| Source | What It Provides |
|--------|-----------------|
| GitHub | Source and structural change signals |
| Josephine | Build and package facts |
| Faraday | Test execution evidence |
| Hedy | Release readiness and release-state context |
| Linnaeus | Traceability context |
| Herodotus | Meeting-derived clarification and documentation suggestions |

## Shannon Teams Commands

Hypatia has 5 Shannon commands registered:

- `/generate-doc` - Generate source-grounded documentation (mutation: true, requires "execute" to proceed)
- `/impact-detect` - Detect documentation impact from changes (mutation: false)
- `/doc-records` - List stored documentation records (GET)
- `/doc-record` - Get specific documentation record (GET)
- `/publish-doc` - Publish approved documentation (mutation: true, requires "execute")

### Teams Usage Examples

```
@Shannon /generate-doc title "CN5000 Build Guide" doc_type engineering_reference
@Shannon /impact-detect project STL
@Shannon /doc-records project STL
@Shannon /doc-record doc_id abc123
@Shannon /publish-doc doc_id abc123
```

## REST API

Hypatia exposes a REST API on port 8203.

### Key Endpoints

- `GET /v1/health` - Health check
- `GET /v1/status/stats` - Session statistics (total sessions, total documents)
- `POST /v1/docs/generate` - Generate documentation (dry_run by default)
- `GET /v1/docs/records` - List documentation records
- `GET /v1/docs/record/{doc_id}` - Get specific record
- `POST /v1/docs/impact` - Detect documentation impact
- `POST /v1/docs/publish` - Publish approved docs (dry_run by default)

## Documentation Types

Hypatia supports 3 documentation types with corresponding prompt files:

| Type | Prompt File | Description |
|------|------------|-------------|
| `as_built` / `engineering_reference` | `prompts/as-built-design.md` | 3-pass methodology: structure discovery -> behavior tracing -> synthesis. Architecture diagrams via Mermaid. |
| `user_guide` / `how_to` | `prompts/user-guide.md` | MkDocs Material compatible, man-page style (NAME/SYNOPSIS/DESCRIPTION/SUBCOMMANDS/OPTIONS/EXAMPLES). |
| `release_note_support` / traceability | `prompts/traceability.md` | RTM format: requirements extraction -> implementation mapping -> test mapping -> coverage matrix -> gap analysis. |

## CLI Commands

### Standalone CLI (`hypatia-agent`)

Hypatia has its own standalone CLI for direct access without going through `agent-cli`:

```bash
hypatia-agent <command> [options]
```

| Command | Description | Example |
|---------|-------------|---------|
| `generate` | Generate source-grounded documentation | `hypatia-agent generate --doc-title "CN5000 Build Guide" --docs src/build.md` |
| `list` | List stored documentation records | `hypatia-agent list --project STL` |
| `get` | Load a stored documentation record | `hypatia-agent get --doc-id abc123` |

#### Standalone CLI Examples

```bash
# Generate documentation from source files (dry-run preview)
hypatia-agent generate \
  --doc-title "OPA PSM2 Architecture" --doc-type engineering_reference \
  --docs docs/architecture.md src/psm2_hal.c \
  --evidence build_log.json test_results.yaml

# Generate and publish to Confluence
hypatia-agent generate \
  --doc-title "CN5000 User Guide" --doc-type user_guide \
  --docs docs/user_guide.md \
  --confluence-space ENG --confluence-parent-id 12345 \
  --execute

# Generate with strict validation and JSON output
hypatia-agent generate \
  --doc-title "Release Notes v2.4" --doc-type release_note_support \
  --docs CHANGELOG.md --doc-validation strict --json

# List recent documentation records
hypatia-agent list --project STL --limit 10

# Export a stored record
hypatia-agent get --doc-id abc123 --output exported_record.json

# Use alternate env file
hypatia-agent generate --doc-title "Guide" --docs README.md --env /path/to/prod.env
```

### Via `agent-cli` (unified CLI)

The same functionality is also available through `agent-cli`:

```bash
agent-cli hypatia generate --doc-title "CN5000 Build Guide" --docs src/build.md
```

#### Options Reference

| Option | Default | Description |
|--------|---------|-------------|
| `--doc-title TEXT` | auto | Document title |
| `--doc-type TYPE` | engineering_reference | Document class (`as_built`, `engineering_reference`, `how_to`, `release_note_support`, `user_guide`) |
| `--doc-summary TEXT` | - | Purpose/scope summary |
| `--docs FILE...` | - | Source documents / datasheets |
| `--evidence FILE...` | - | Evidence files (JSON, YAML, Markdown) |
| `--target-file FILE` | auto | Repo-owned Markdown target |
| `--confluence-title TITLE` | - | Confluence page title |
| `--confluence-page PAGE` | - | Confluence page ID or title to update |
| `--confluence-space SPACE` | - | Confluence space key or ID |
| `--confluence-parent-id ID` | - | Parent page ID for new Confluence pages |
| `--version-message TEXT` | - | Confluence version message |
| `--doc-validation PROFILE` | default | Validation profile (`default`, `strict`, `sphinx`) |
| `--execute` | off | Actually publish approved changes (default: dry-run preview) |
| `--project` / `-p` | - | Jira project key (optional) |
| `--output FILE` | auto | Output filename |
| `--json` | off | Output as JSON instead of formatted text |
| `--env FILE` | `.env` | Alternate environment file |

## Deployment

- **Prerequisites**: Shared container image built, LLM credentials in `deploy/env/llm.env`
- **Container run command**:

  ```bash
  podman run -d --name hypatia -p 8203:8203 \
    --env-file deploy/env/shared.env \
    --env-file deploy/env/llm.env \
    -v $(pwd)/config:/app/config:ro,Z \
    -v $(pwd)/data/hypatia:/data/hypatia:Z \
    localhost/cornelis/agent-workforce:latest \
    uvicorn agents.hypatia.api:app --host 0.0.0.0 --port 8203
  ```

- **Verify**: `curl http://localhost:8203/v1/health`
- **Systemd**: `deploy/systemd/hypatia.service`
- **Cross-container**: Shannon reaches Hypatia at `http://host.containers.internal:8203`

## Directory Structure

```text
agents/hypatia/
|-- README.md
|-- __init__.py
|-- agent.py                # HypatiaDocumentationAgent
|-- api.py                  # REST API (port 8203)
|-- cli.py                  # Standalone CLI (hypatia-agent command)
|-- models.py               # Documentation models
|-- tools.py                # Agent tool wrappers
|-- prompts/
|   |-- system.md           # Core agent behavior prompt
|   |-- as-built-design.md  # As-built/engineering reference prompt
|   |-- user-guide.md       # User guide/how-to prompt
|   `-- traceability.md     # Traceability/RTM prompt
|-- state/
|   |-- __init__.py
|   `-- record_store.py     # Documentation record persistence
`-- docs/
    `-- PLAN.md             # Full technical specification
```

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
