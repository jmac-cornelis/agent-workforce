# Hypatia — Documentation Agent

## Overview

Hypatia is the documentation agent for the Cornelis Networks platform. Named after Hypatia of Alexandria, it turns source changes, build and test facts, traceability context, release context, and meeting-derived clarifications into durable engineering and user-facing documentation.

Hypatia does not generate prose detached from implementation truth. It produces documentation from authoritative system records — code, builds, tests, releases, and meeting decisions.

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

## CLI Commands

### Workflow (via `pm_agent.py`)

| Workflow | Description | Example |
|----------|-------------|---------|
| `hypatia-generate` | Generate source-grounded documentation | `python pm_agent.py --workflow hypatia-generate --doc-title "CN5000 Build Guide" --docs src/build.md` |

#### Hypatia Workflow Options

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
| `--env FILE` | `.env` | Alternate environment file |

#### Hypatia Examples

```bash
# Generate documentation from source files (dry-run preview)
python pm_agent.py --workflow hypatia-generate \
  --doc-title "OPA PSM2 Architecture" --doc-type engineering_reference \
  --docs docs/architecture.md src/psm2_hal.c \
  --evidence build_log.json test_results.yaml

# Generate and publish to Confluence
python pm_agent.py --workflow hypatia-generate \
  --doc-title "CN5000 User Guide" --doc-type user_guide \
  --docs docs/user_guide.md \
  --confluence-space ENG --confluence-parent-id 12345 \
  --execute

# Generate with strict validation
python pm_agent.py --workflow hypatia-generate \
  --doc-title "Release Notes v2.4" --doc-type release_note_support \
  --docs CHANGELOG.md --doc-validation strict
```

## Directory Structure

```text
agents/hypatia/
├── README.md               # This file
├── __init__.py
├── agent.py                # HypatiaDocumentationAgent
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
