# Shannon — Communications Agent

## Overview

Shannon is the single Microsoft Teams bot that serves as the human interface for all domain agents in the Cornelis Networks Agent Workforce. Named after Claude Shannon, the father of information theory.

One deployment, all channels. Shannon receives messages from Teams channels, routes commands to the correct agent API, renders responses as Adaptive Cards, manages approval workflows, and logs every interaction for audit.

Shannon is not a dumb proxy. It owns command parsing, routing, response rendering, approval lifecycle management, conversation threading, rate limiting, error handling, and audit logging.

## Quick Start

```bash
# Docker
docker compose up shannon

# Local
uvicorn shannon.service:app --host 0.0.0.0 --port 8200
```

## How It Works

1. User sends `@Shannon /command args` in a Teams channel
2. Shannon looks up the agent registered for that channel via the agent registry
3. Dispatches to the agent's API (GET or POST based on the registry entry)
4. Renders the response as an Adaptive Card in the Teams thread

### Dry-Run Safety

For mutation commands (marked `mutation: true` in the registry), Shannon always sends `dry_run=true` first. You see a preview card showing what would happen. To execute for real, append `execute` to the command:

```text
@Shannon /some-mutation-command args          # Preview (dry run)
@Shannon /some-mutation-command args execute  # Execute for real
```

## Built-In Commands

These commands report on Shannon's own operational status:

| Command | Description |
|---------|-------------|
| `/stats` | Service status and message throughput |
| `/busy` | Current load summary |
| `/work-today` | Today's work summary |
| `/token-status` | Token execution summary |
| `/decision-tree` | Recent routing and posting decisions |
| `/why {record_id}` | Deep dive into a specific routing decision |

## Agent Registry

Shannon's routing is configured via `config/shannon/agent_registry.yaml`. Each agent entry specifies:

- `agent_id`, `display_name`, `role`
- `channel_name`, `channel_id` — which Teams channel maps to which agent
- `api_base_url` — where to forward commands (e.g., `http://localhost:8201`)
- `custom_commands` — list of commands with `command`, `description`, `api_method`, `api_path`, and `mutation` flag

Adding a new command is as simple as adding an entry to the YAML file. Shannon picks it up on restart.

### Currently Registered Agents

| Agent | Role | Port | Commands |
|-------|------|------|----------|
| Shannon | Communications | 8200 | 6 built-in |
| Drucker | Engineering Hygiene | 8201 | 15 commands (Jira + GitHub) |
| Gantt | Project Planning | 8202 | 8 commands |

## Approval Workflows

Shannon manages approval workflows end-to-end:

1. An agent requests approval via the Bot API (`POST /v1/bot/notify`)
2. Shannon posts an approval card in the appropriate Teams channel
3. The user responds (approve/reject) via card action buttons
4. Shannon tracks the response with timeout and escalation
5. The result is forwarded back to the requesting agent

## API Reference

Shannon exposes a REST API on port 8200:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/bot/notify` | POST | Receive proactive notifications from agents |
| `/v1/status/stats` | GET | Service statistics |
| `/v1/status/load` | GET | Current load summary |
| `/v1/status/work-summary` | GET | Today's work summary |
| `/v1/status/tokens` | GET | Token execution summary |
| `/v1/status/decisions` | GET | Recent routing decisions |
| `/v1/status/decisions/{record_id}` | GET | Specific decision details |

## Configuration

- `config/shannon/agent_registry.yaml` — Agent and command routing
- Environment variables: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, `TEAMS_WEBHOOK_URL`

## Directory Structure

```text
agents/shannon/
├── README.md               # This file
└── docs/
    ├── PLAN.md             # Full technical specification
    └── TEAMS_BOT_FRAMEWORK.md  # Bot Framework integration details

shannon/                    # Implementation (repo root)
├── service.py              # FastAPI application, command dispatch
├── cards.py                # Adaptive Card builders for all agents
└── poster.py               # Teams message posting (Workflows, Bot Framework)
```

> Note: Shannon's implementation lives in `shannon/` at the repo root (legacy FastAPI service), while agent metadata and documentation live in `agents/shannon/`.

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
