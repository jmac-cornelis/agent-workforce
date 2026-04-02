# Deployment Guide

[Back to AI Agent Workforce](README.md) | [Infrastructure Architecture](INFRASTRUCTURE_ARCHITECTURE.md)

## Overview

This guide covers the deployment architecture for the Cornelis Networks AI Agent Workforce. It describes the single-image, multi-entrypoint pattern where all agents run from the same foundational container image but execute different entrypoint commands.

For information on the underlying platform components, event transport, and security architecture, see the [Infrastructure Architecture](INFRASTRUCTURE_ARCHITECTURE.md) document.

## Current Production Deployment

Shannon and Drucker are deployed on `bld-node-48.cornelisnetworks.com` using rootless Podman containers. Teams connectivity is provided by a Cloudflare named tunnel at `shannon.cn-agents.com` (domain: `cn-agents.com`).

| Property | Value |
|----------|-------|
| Server | `bld-node-48.cornelisnetworks.com` (RHEL 10.1, 88 CPUs, 62 GB RAM) |
| Runtime | Podman 5.6.0 (rootless) |
| Shannon | Port 8200, `https://shannon.cn-agents.com` |
| Drucker | Port 8201, internal only via `host.containers.internal` |
| Tunnel | Cloudflare named tunnel `agent-workforce` |
| Teams callback | `https://shannon.cn-agents.com/api/webhook` |

For step-by-step deployment instructions, see [`deploy/README.md`](../../deploy/README.md). For per-agent guides, see [`agents/shannon/README.md`](../../agents/shannon/README.md#deployment) and [`agents/drucker/README.md`](../../agents/drucker/README.md#deployment).

## Planned Multi-Host Architecture

The long-term vision targets deployment across the `cn-ai-[01:04]` host cluster using Docker Compose.

## Container Architecture

The system uses a single Docker image built from the repository root. Each agent starts via a different entrypoint command, leveraging the FastAPI framework app factory (`framework/api/app.py` `create_agent_app()`).

```mermaid
graph TD
    subgraph Docker Image
        Base[Python 3.11 Base Layer]
        Deps[pip dependencies from pyproject.toml]
        Code[Source Code: agents/, tools/, framework/, etc.]
        Base --> Deps --> Code
    end

    Code --> Agent1[Entrypoint: shannon.app:app]
    Code --> Agent2[Entrypoint: agents.drucker.api:app]
    Code --> AgentN[Entrypoint: agents.*.api:app]

    subgraph Volumes
        Config[/app/config/]
        State[/data/state/]
    end

    Agent1 -.-> Config
    Agent1 -.-> State
    Agent2 -.-> Config
    Agent2 -.-> State
    AgentN -.-> Config
    AgentN -.-> State
```

## Docker Image

The single `Dockerfile` at the repository root uses a multi-stage build:

1.  **Builder Stage**: Installs both core dependencies and `[agents]` optional dependencies using `pip`.
2.  **Runtime Stage**: A slim Python 3.11 base image that copies the installed dependencies and all necessary source code.

Copied source directories include: `*.py`, `agents/`, `tools/`, `adapters/`, `config/`, `framework/`, `core/`, `state/`, `llm/`, `data/`.

The entrypoint is configurable via environment variable or command override.

**Example execution:**
```bash
CMD ["uvicorn", "agents.drucker.api:app", "--host", "0.0.0.0", "--port", "8201"]
```

## Environment File Architecture

The deployment uses a segregated environment file architecture to ensure each container only receives the credentials it needs (least-privilege). Container isolation provides the security boundary.

```mermaid
graph LR
    subgraph config/env/
        Shared[shared.env<br>LOG_LEVEL, STATE_BACKEND]
        Jira[jira.env<br>JIRA_API_TOKEN, etc.]
        LLM[llm.env<br>CORNELIS_LLM_BASE_URL, etc.]
        GitHub[github.env<br>GITHUB_TOKEN, etc.]
        Teams[teams.env<br>AZURE_CLIENT_SECRET, etc.]
    end

    Shannon((Shannon))
    Drucker((Drucker))
    Gantt((Gantt))

    Shared --> Shannon
    Shared --> Drucker
    Shared --> Gantt

    LLM --> Shannon
    Teams --> Shannon

    Jira --> Drucker
    LLM --> Drucker
    GitHub --> Drucker

    Jira --> Gantt
    LLM --> Gantt
```

### Agent Environment Mapping

| Agent | shared.env | jira.env | llm.env | github.env | teams.env |
|-------|------------|----------|---------|------------|-----------|
| Shannon | ✓ | | ✓ | | ✓ |
| Drucker | ✓ | ✓ | ✓ | ✓ | |
| Gantt | ✓ | ✓ | ✓ | | |
| Hemingway | ✓ | | ✓ | | |
| Josephine | ✓ | | | ✓ | |
| Galileo | ✓ | | ✓ | | |
| Curie | ✓ | | ✓ | | |
| Faraday | ✓ | | | | |
| Tesla | ✓ | | | | |
| Humphrey | ✓ | ✓ | ✓ | ✓ | |
| Linus | ✓ | | ✓ | ✓ | |
| Mercator | ✓ | ✓ | | | |
| Berners-Lee | ✓ | ✓ | | | |
| Pliny | ✓ | | ✓ | | ✓ |
| Nightingale | ✓ | ✓ | ✓ | ✓ | |
| Shackleton | ✓ | ✓ | ✓ | | |
| Blackstone | ✓ | | | ✓ | |

## Docker Compose Service Topology

The services are distributed across four hosts (`cn-ai-01` through `cn-ai-04`). Each service definition in the Compose files includes specific configurations for the agent.

```mermaid
graph TB
    subgraph cn-ai-01 [cn-ai-01: Core & Planning]
        PG[(PostgreSQL)]
        Redis[(Redis)]
        Nginx[Nginx Proxy]
        Shannon[Shannon:8200]
        Drucker[Drucker:8201]
        Gantt[Gantt:8202]
        Hemingway[Hemingway:8203]
    end

    subgraph cn-ai-02 [cn-ai-02: Engineering & Test]
        Josephine[Josephine:8210]
        Galileo[Galileo:8211]
        Curie[Curie:8212]
        Faraday[Faraday:8213]
        Tesla[Tesla:8214]
    end

    subgraph cn-ai-03 [cn-ai-03: Management & Delivery]
        Humphrey[Humphrey:8220]
        Linus[Linus:8221]
        Mercator[Mercator:8222]
        Berners-Lee[Berners-Lee:8223]
        Pliny[Pliny:8224]
        Nightingale[Nightingale:8225]
        Shackleton[Shackleton:8226]
        Blackstone[Blackstone:8227]
    end

    subgraph cn-ai-04 [cn-ai-04: Observability]
        Grafana[Grafana]
        Loki[Loki]
        Prometheus[Prometheus]
    end
```

### Service Definition Structure
Each service definition includes:
- `image`: The shared workforce image
- `command`: The specific uvicorn entrypoint for the agent
- `ports`: The mapped port (see allocation below)
- `env_file`: The list of environment files based on the mapping table
- `volumes`: Required persistent storage
- `restart`: `unless-stopped`
- `healthcheck`: HTTP GET to `/health`
- `depends_on`: Core services like Redis/Postgres if applicable

## Port Allocation

| Agent | Port | Host |
|-------|------|------|
| Shannon | 8200 | cn-ai-01 |
| Drucker | 8201 | cn-ai-01 |
| Gantt | 8202 | cn-ai-01 |
| Hemingway | 8203 | cn-ai-01 |
| Josephine | 8210 | cn-ai-02 |
| Galileo | 8211 | cn-ai-02 |
| Curie | 8212 | cn-ai-02 |
| Faraday | 8213 | cn-ai-02 |
| Tesla | 8214 | cn-ai-02 |
| Humphrey | 8220 | cn-ai-03 |
| Linus | 8221 | cn-ai-03 |
| Mercator | 8222 | cn-ai-03 |
| Berners-Lee | 8223 | cn-ai-03 |
| Pliny | 8224 | cn-ai-03 |
| Nightingale | 8225 | cn-ai-03 |
| Shackleton | 8226 | cn-ai-03 |
| Blackstone | 8227 | cn-ai-03 |

## Volume Mounts

Containers require persistent storage for specific functions:

- **State files**: `/data/state/` → Used by the `state/` module for local persistence.
- **Config**: `/app/config/` → Agent YAML configurations and markdown prompt files.
- **Logs**: `/data/logs/` → Agent log files (though stdout is preferred for Docker).
- **Artifacts**: `/data/artifacts/` → Build outputs and test results (primarily used by Josephine and Faraday).

## Deployment Workflow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as GitHub (main)
    participant CI as CI Pipeline
    participant Reg as Registry
    participant Ans as Ansible
    participant Host as cn-ai-[01:04]

    Dev->>Git: Push to main
    Git->>CI: Trigger build
    CI->>CI: Build Docker image
    CI->>CI: Tag image (git SHA)
    CI->>Reg: Push image
    CI->>Ans: Trigger deployment playbook
    Ans->>Host: Pull new image
    Ans->>Host: docker-compose up -d
    Host->>Host: Start containers
    Host-->>Ans: Health checks pass
```

## Health Checks & Monitoring

- **Health Endpoints**: Each agent exposes a `GET /health` endpoint automatically provided by the framework app factory (`create_agent_app()`).
- **Reverse Proxy**: Nginx uses these health checks to manage upstream availability.
- **Metrics**: Prometheus scrapes `/metrics` endpoints provided by the framework.
- **Dashboards**: Grafana provides per-agent dashboards visualizing the scraped metrics.

## Local Development

For local development, the segregated `config/env/` split is not strictly required. Developers typically use `python-dotenv` with a single `.env` file at the repository root. The split environment file architecture is specifically designed for the production Docker Compose deployment to enforce least-privilege.

To run agents locally:
```bash
uvicorn agents.drucker.api:app --reload --port 8201
# OR
uvicorn shannon.app:app --reload --port 8200
```

## Secrets Management Roadmap

- **Phase 1 (Current)**: `.env` files located in `config/env/`, mounted into containers, and ignored by `.gitignore`.
- **Phase 2 (Planned)**: Docker Swarm secrets (if the deployment topology migrates from plain Compose to Swarm).
- **Phase 3 (Future)**: HashiCorp Vault integration with short-lived credentials for ultimate security.
