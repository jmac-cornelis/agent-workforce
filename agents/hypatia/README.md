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
