# Agent Workforce

The Cornelis Networks Agent Workforce is a coordinated system of AI-powered agents that automate engineering operations — from Jira ticket hygiene and GitHub PR lifecycle management to project planning, documentation generation, and Teams-based collaboration.

## Implemented Agents

| Agent | Role | Port | Description |
|-------|------|------|-------------|
| [Drucker](agents/drucker.md) | Engineering Hygiene | 8201 | Jira ticket quality analysis + GitHub PR lifecycle scanning |
| [Gantt](agents/gantt.md) | Project Planning | 8202 | Planning snapshots, release monitoring, dependency review |
| [Hypatia](agents/hypatia.md) | Documentation | 8203 | Source-grounded documentation generation and publication |
| [Shannon](agents/shannon.md) | Communications | 8200 | Microsoft Teams bot — routing surface for all agents |

## Three Access Surfaces

Every agent exposes the same three interfaces:

1. **Shannon Teams** — `@Shannon /command args` in Microsoft Teams
2. **CLI** — `agent-cli <agent> <subcommand>` or standalone `drucker-agent`, `gantt-agent`, etc.
3. **REST API** — FastAPI on per-agent ports with OpenAPI docs at `/docs`

## Quick Start

```bash
pip install -e ".[agents]"

# Run Drucker hygiene scan via CLI
drucker-agent hygiene --project-key STL --stale-days 30

# Run Gantt planning snapshot
gantt-agent snapshot --project-key STL --planning-horizon 90

# Generate documentation with Hypatia
hypatia-agent generate --doc-title "Module Overview" --docs src/module/

# Start Shannon API server
uvicorn shannon.app:app --host 0.0.0.0 --port 8200
```

## Deployment

See the [Deployment Guide](deployment/index.md) for Docker/Podman container setup on Cornelis internal servers.

Current production: `bld-node-48.cornelisnetworks.com` with Shannon accessible at `shannon.cn-agents.com`.
