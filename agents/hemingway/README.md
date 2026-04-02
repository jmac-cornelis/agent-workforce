# Hemingway — Documentation Agent

## Overview

Hemingway is the documentation agent for the Cornelis Networks platform. Named for Ernest Hemingway, it turns source changes, build and test facts, traceability context, release context, and meeting-derived clarifications into durable engineering and user-facing documentation.

Hemingway does not generate prose detached from implementation truth. It produces documentation from authoritative system records — code, builds, tests, releases, and meeting decisions.

## Quick Start

```bash
# Docker
docker compose up hemingway

# Local
uvicorn agents.hemingway.api:app --host 0.0.0.0 --port 8203
```

## What Hemingway Does

- Generates and maintains repo-level as-built documentation
- Updates user and engineering documentation when code, build, test, release, or meeting knowledge changes
- Proposes documentation changes linked to their triggering events
- Publishes approved docs to internal documentation targets (Sphinx/ReadTheDocs)
- Keeps documentation linked to builds, versions, and traceability records

### What Hemingway Does Not Do

- Autonomously publish external customer-visible documentation
- Replace engineers as final approvers of normative docs
- Invent architecture or behavior not grounded in source or records
- Generate generic LLM-produced markdown dumps

## Data Sources

Hemingway draws from multiple agents to build documentation:

| Source | What It Provides |
|--------|-----------------|
| GitHub | Source and structural change signals |
| Josephine | Build and package facts |
| Faraday | Test execution evidence |
| Humphrey | Release readiness and release-state context |
| Berners-Lee | Traceability context |
| Pliny | Meeting-derived clarification and documentation suggestions |

## CLI Commands

### Standalone CLI (`hemingway-agent`)

Hemingway has its own standalone CLI for direct access without going through `agent-cli`:

```bash
hemingway-agent <command> [options]
```

| Command | Description | Example |
|---------|-------------|---------|
| `generate` | Generate source-grounded documentation | `hemingway-agent generate --doc-title "CN5000 Build Guide" --docs src/build.md` |
| `list` | List stored documentation records | `hemingway-agent list --project STL` |
| `get` | Load a stored documentation record | `hemingway-agent get --doc-id abc123` |

#### Standalone CLI Examples

```bash
# Generate documentation from source files (dry-run preview)
hemingway-agent generate \
  --doc-title "OPA PSM2 Architecture" --doc-type engineering_reference \
  --docs docs/architecture.md src/psm2_hal.c \
  --evidence build_log.json test_results.yaml

# Generate and publish to Confluence
hemingway-agent generate \
  --doc-title "CN5000 User Guide" --doc-type user_guide \
  --docs docs/user_guide.md \
  --confluence-space ENG --confluence-parent-id 12345 \
  --execute

# Generate with strict validation and JSON output
hemingway-agent generate \
  --doc-title "Release Notes v2.4" --doc-type release_note_support \
  --docs CHANGELOG.md --doc-validation strict --json

# List recent documentation records
hemingway-agent list --project STL --limit 10

# Export a stored record
hemingway-agent get --doc-id abc123 --output exported_record.json

# Use alternate env file
hemingway-agent generate --doc-title "Guide" --docs README.md --env /path/to/prod.env
```

### Via `agent-cli` (unified CLI)

The same functionality is also available through `agent-cli`:

```bash
agent-cli hemingway generate --doc-title "CN5000 Build Guide" --docs src/build.md
```

#### Options Reference

| Option | Default | Description |
|--------|---------|-------------|
| `--doc-title TEXT` | auto | Document title |
| `--doc-type TYPE` | engineering_reference | Document class (`as_built`, `engineering_reference`, `how_to`, `release_note_support`, `user_guide`) |
| `--doc-summary TEXT` | — | Purpose/scope summary |
| `--docs FILE...` | — | Source documents / datasheets |
| `--evidence FILE...` | — | Evidence files (JSON, YAML, Markdown) |
| `--target-file FILE` | auto | Repo-owned Markdown target |
| `--confluence-title TITLE` | — | Confluence page title |
| `--confluence-page PAGE` | — | Confluence page ID or title to update |
| `--confluence-space SPACE` | — | Confluence space key or ID |
| `--confluence-parent-id ID` | — | Parent page ID for new Confluence pages |
| `--version-message TEXT` | — | Confluence version message |
| `--doc-validation PROFILE` | default | Validation profile (`default`, `strict`, `sphinx`) |
| `--execute` | off | Actually publish approved changes (default: dry-run preview) |
| `--project` / `-p` | — | Jira project key (optional) |
| `--output FILE` | auto | Output filename |
| `--json` | off | Output as JSON instead of formatted text |
| `--env FILE` | `.env` | Alternate environment file |

## Directory Structure

```text
agents/hemingway/
├── README.md               # This file
├── __init__.py
├── agent.py                # HemingwayDocumentationAgent
├── cli.py                  # Standalone CLI (hemingway-agent command)
├── models.py               # Documentation models
├── tools.py                # Agent tool wrappers
├── prompts/
│   └── system.md           # Agent behavior prompt
├── state/
│   ├── __init__.py
│   └── record_store.py     # Documentation record persistence
└── docs/
    └── PLAN.md             # Full technical specification
```

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
