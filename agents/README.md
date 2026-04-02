# Agent Workforce

The Cornelis Networks Agent Workforce is a system of 17 specialized agents that automate and coordinate the full software development lifecycle. Each agent owns a distinct responsibility — from build orchestration and test generation to release management and project planning — and communicates through well-defined interfaces.

Agents are organized into operational zones. Four agents are currently implemented and running; the remaining thirteen are planned with full technical specifications.

## Agents by Zone

### Execution Spine

Core build-test-release pipeline agents.

| Agent | Role | Status | Port | Description |
|-------|------|--------|------|-------------|
| [Josephine](josephine/README.md) | Build & Package | Planned | 8210 | Build orchestration and artifact production via Fuze |
| [Galileo](galileo/README.md) | Test Planning | Planned | 8211 | Determines what to test based on trigger class, coverage, and environment |
| [Curie](curie/README.md) | Test Generation | Planned | 8212 | Materializes test plans into concrete Fuze Test inputs |
| [Faraday](faraday/README.md) | Test Execution | Planned | 8213 | Runs ATF/Fuze Test cycles and produces execution records |
| [Tesla](tesla/README.md) | Environment Mgmt | Planned | 8214 | Shared reservation service for HIL and mock environments |
| [Humphrey](humphrey/README.md) | Release Mgmt | Planned | 8220 | Release decisions with stage promotion and approval gates |
| [Linus](linus/README.md) | Code Review | Planned | 8221 | PR evaluation against policy profiles with cross-agent signals |
| [Blackstone](blackstone/README.md) | Legal Compliance | Planned | 8227 | License compliance scanning and policy violation detection |

### Intelligence & Knowledge

Context, traceability, and institutional knowledge agents.

| Agent | Role | Status | Port | Description |
|-------|------|--------|------|-------------|
| [Mercator](mercator/README.md) | Version Mapping | Planned | 8222 | Maps internal Fuze build IDs to external release versions |
| [Berners-Lee](bernerslee/README.md) | Traceability | Planned | 8223 | Relationships between requirements, issues, commits, builds, tests, releases |
| [Pliny](pliny/README.md) | Knowledge Capture | Planned | 8224 | Meeting transcript ingestion, structured summaries, action items |
| [Hemingway](hemingway/README.md) | Documentation | **Implemented** | 8203 | As-built and user documentation from authoritative system records |
| [Nightingale](nightingale/README.md) | Bug Investigation | Planned | 8225 | Bug report qualification, context assembly, reproduction coordination |

### Engineering Hygiene

| Agent | Role | Status | Port | Description |
|-------|------|--------|------|-------------|
| [Drucker](drucker/README.md) | Engineering Hygiene | **Implemented** | 8201 | Jira ticket quality and GitHub PR lifecycle management |

### Planning & Delivery

| Agent | Role | Status | Port | Description |
|-------|------|--------|------|-------------|
| [Gantt](gantt/README.md) | Project Planning | **Implemented** | 8202 | Planning snapshots, dependency views, release health monitoring |
| [Shackleton](shackleton/README.md) | Delivery Mgmt | Planned | 8226 | Execution monitoring, schedule risk detection, delivery summaries |

### Service Infrastructure

| Agent | Role | Status | Port | Description |
|-------|------|--------|------|-------------|
| [Shannon](shannon/README.md) | Communications | **Implemented** | 8200 | Single Teams bot interface for all agents — routing, cards, approvals |

## Implementation Status

| Status | Count | Agents |
|--------|-------|--------|
| Implemented | 4 | Drucker, Gantt, Hemingway, Shannon |
| Planned | 13 | Berners-Lee, Blackstone, Curie, Faraday, Galileo, Humphrey, Josephine, Linus, Mercator, Nightingale, Pliny, Shackleton, Tesla |

## Getting Started

- **Teams users**: Interact with any implemented agent via `@Shannon /command` in the appropriate Teams channel
- **API users**: Each agent exposes a REST API on its assigned port
- **Operators**: See [DEPLOYMENT_GUIDE.md](../docs/workforce/DEPLOYMENT_GUIDE.md) for Docker Compose deployment
- **Architecture**: See [docs/workforce/README.md](../docs/workforce/README.md) for the full workforce vision
