# Shannon — Communications Agent

## Overview

Shannon is the single Microsoft Teams bot that serves as the human interface for all domain agents in the Cornelis Networks Agent Workforce. Named after Claude Shannon, the father of information theory.

One deployment, all channels. Shannon receives messages from Teams channels, routes commands to the correct agent API, renders responses as Adaptive Cards, manages approval workflows, and logs every interaction for audit.

Shannon is not a dumb proxy. It owns command parsing, routing, response rendering, approval lifecycle management, conversation threading, rate limiting, error handling, and audit logging.

## Quick Start

```bash
# Podman (production)
podman run -d --name shannon -p 8200:8200 \
    --env-file deploy/env/shared.env \
    --env-file deploy/env/teams.env \
    -v $(pwd)/config:/app/config:ro,Z \
    -v $(pwd)/data/shannon:/data/shannon:Z \
    localhost/cornelis/agent-workforce:latest \
    uvicorn shannon.app:app --host 0.0.0.0 --port 8200

# Local development
uvicorn shannon.app:app --host 0.0.0.0 --port 8200
```

## Deployment

### Prerequisites

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| OS | RHEL 9+ / Ubuntu 22.04+ | Tested on RHEL 10.1 |
| Container runtime | Podman 5.x (rootless) | Docker also works |
| Python | 3.11+ (inside container) | Host Python not required |
| RAM | 2 GB | Shannon is lightweight |
| Ports | 8200 (HTTP) | HTTPS handled by tunnel or reverse proxy |

### Current Production Server

| Property | Value |
|----------|-------|
| Host | `bld-node-48.cornelisnetworks.com` |
| User | `scm` |
| IP (internal) | `10.228.209.81` |
| OS | RHEL 10.1, kernel 6.12, 88 CPUs, 62 GB RAM |
| Runtime | Podman 5.6.0 (rootless) |
| Data dir | `/home/scm/agent-workforce/data/shannon/` |
| Config dir | `/home/scm/agent-workforce/config/` (mounted read-only) |
| Env files | `/home/scm/agent-workforce/deploy/env/` |

### Step 1: Build the Image

```bash
# Clone repo on the server
git clone https://github.com/jmac-cornelis/agent-workforce.git
cd agent-workforce

# Build (takes ~5 minutes first time)
podman build -t localhost/cornelis/agent-workforce:latest .
```

> **Rootless Podman note:** If you get UID mapping errors, ensure subuid/subgid are configured:
> ```bash
> echo "$USER:100000:65536" | sudo tee -a /etc/subuid
> echo "$USER:100000:65536" | sudo tee -a /etc/subgid
> ```

### Step 2: Configure Environment Files

Create `deploy/env/` on the server with real credentials:

**`deploy/env/shared.env`** — Non-sensitive config shared by all agents:
```bash
LOG_LEVEL=INFO
STATE_BACKEND=json
PERSISTENCE_DIR=/data/state
SHANNON_STATE_DIR=/data/shannon
DRY_RUN=true
```

**`deploy/env/teams.env`** — Teams integration (see [Teams Webhook Setup](#teams-webhook-setup)):
```bash
SHANNON_TEAMS_POST_MODE=workflows
SHANNON_TEAMS_OUTGOING_WEBHOOK_SECRET=<paste-from-teams-channel-config>
SHANNON_TEAMS_WORKFLOWS_WEBHOOK_URL=<paste-incoming-webhook-url>
SHANNON_TEAMS_BOT_NAME=Shannon
```

Post modes:
- `memory` — Dry-run/testing. No Teams interaction.
- `workflows` — Uses Power Automate Workflows webhook for proactive messages. Recommended for production.
- `botframework` — Azure Bot Framework with OAuth. Requires `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`.

### Step 3: Create Data Directories

```bash
mkdir -p data/shannon
```

### Step 4: Start Shannon

```bash
podman run -d --name shannon -p 8200:8200 \
    --env-file deploy/env/shared.env \
    --env-file deploy/env/teams.env \
    -v $(pwd)/config:/app/config:ro,Z \
    -v $(pwd)/data/shannon:/data/shannon:Z \
    localhost/cornelis/agent-workforce:latest \
    uvicorn shannon.app:app --host 0.0.0.0 --port 8200
```

> **Cross-container communication:** Shannon calls agent APIs via `host.containers.internal` (e.g., `http://host.containers.internal:8201`), which resolves to the host's loopback from inside any Podman container. This is configured in `config/shannon/agent_registry.yaml`.

> **`:Z` suffix on volumes** — Required for SELinux on RHEL. Tells Podman to relabel the volume for the container's SELinux context.

### Step 5: Verify

```bash
# Health check
curl -s http://localhost:8200/v1/bot/health | python3 -m json.tool

# Expected: {"ok": true, ...}

# Check poster mode
curl -s http://localhost:8200/v1/status/stats | python3 -m json.tool
# Look for: "poster_mode": "WorkflowsPoster"
```

### Step 6: Install Systemd Service

```bash
mkdir -p ~/.config/systemd/user
cp deploy/systemd/shannon.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now shannon

# Keep running after logout
loginctl enable-linger $(whoami)

# Check status
systemctl --user status shannon
journalctl --user -u shannon -f  # tail logs
```

### Step 7: HTTPS for Teams

Teams outgoing webhooks require HTTPS. Two options:

**Option A: Cloudflare Named Tunnel (production — permanent URL)**

The production deployment uses a Cloudflare named tunnel with the domain `cn-agents.com`:

| Property | Value |
|----------|-------|
| Domain | `cn-agents.com` (Cloudflare-managed) |
| Shannon URL | `https://shannon.cn-agents.com` |
| Tunnel name | `agent-workforce` |
| Teams webhook callback | `https://shannon.cn-agents.com/api/webhook` |

```bash
# Install cloudflared
sudo dnf install -y https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm

# Start the named tunnel (stable URL, survives restarts)
cloudflared tunnel run --token <TUNNEL_TOKEN>
```

The named tunnel maintains a permanent URL — no need to update webhook URLs on restart. Configure the route in Cloudflare Zero Trust dashboard: **Networks → Tunnels → Public Hostname** → `shannon.cn-agents.com` → `http://localhost:8200`.

**Option B: Caddy Reverse Proxy (alternative, requires DNS)**

See `deploy/caddy/Caddyfile`. Requires the server hostname to be resolvable and port 443 reachable.

```bash
sudo dnf install caddy
sudo setcap cap_net_bind_service=+ep $(which caddy)
caddy start --config deploy/caddy/Caddyfile
```

### Teams Webhook Setup

Shannon uses two webhook directions:

#### Outgoing Webhook (User → Shannon)

This lets users send `@Shannon /command` in Teams and have it reach Shannon's API.

1. In Microsoft Teams, go to the target channel → **Manage channel** → **Apps** → **Outgoing Webhook**
2. Name: `Shannon`, Callback URL: `https://shannon.cn-agents.com/api/webhook`
3. Copy the **HMAC secret** Teams generates
4. Paste it into `deploy/env/teams.env` as `SHANNON_TEAMS_OUTGOING_WEBHOOK_SECRET`
5. Restart Shannon: `systemctl --user restart shannon`

#### Incoming Webhook (Shannon → Channel)

This lets Shannon proactively post messages (e.g., polling results, notifications).

1. In Teams, go to the target channel → **Workflows** → search **"Send webhook alerts to a channel"**
2. Follow the wizard to create a Workflows automation
3. Copy the generated webhook URL
4. Paste into `deploy/env/teams.env` as `SHANNON_TEAMS_WORKFLOWS_WEBHOOK_URL`
5. Set `SHANNON_TEAMS_POST_MODE=workflows`
6. Restart Shannon: `systemctl --user restart shannon`

#### Per-Agent Notification Channels

Each domain agent can have its own Teams channel with a dedicated Workflows incoming webhook. When configured, proactive notifications (polling results, alerts) are posted directly to the agent's channel — not the default Shannon channel.

To set up a per-agent channel:

1. Create a dedicated Teams channel (e.g., `agent-drucker`)
2. Add a "Send webhook alerts to a channel" Workflow in that channel
3. Add the webhook URL to the agent's entry in `config/shannon/agent_registry.yaml`:

```yaml
agents:
  drucker:
    channel_name: agent-drucker
    notifications_webhook_url: "https://...powerautomate.com/..."
```

4. Restart Shannon: `systemctl --user restart shannon`
5. Test: `curl -X POST http://localhost:8200/v1/bot/notify -H 'Content-Type: application/json' -d '{"agent_id": "drucker", "title": "Test", "text": "Hello from Drucker"}'`

#### Re-establishing Conversation References

After a container restart, Shannon loses its in-memory conversation references. Send **`@Shannon /stats`** in the Teams channel to re-establish the reference. This is required before Shannon can route commands to other agents.

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection closed by remote host` on SSH | SSH rate limiting (MaxStartups) | Wait 5-10 min, or run `deploy/scripts/fix-server.sh` when access recovers |
| `podman restart` fails with port conflict | Race condition in rootless Podman | `podman stop -t 10 shannon && podman rm -f shannon` then re-run |
| Shannon returns 500 on agent commands | Agent container not reachable | Verify `api_base_url` in registry uses `host.containers.internal:PORT` |
| Teams commands get no response | Conversation reference lost after restart | Send `@Shannon /stats` to re-establish |
| `poster_mode: MemoryPoster` in /stats | `SHANNON_TEAMS_POST_MODE` not set or wrong | Check `deploy/env/teams.env`, restart container |
| Cloudflare tunnel down | `cloudflared` process died | Restart: `cloudflared tunnel run --token <TOKEN>` |

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
- `api_base_url` — where to forward commands (e.g., `http://host.containers.internal:8201`)
- `notifications_webhook_url` — optional per-agent Workflows webhook for proactive notifications
- `custom_commands` — list of commands with `command`, `description`, `api_method`, `api_path`, and `mutation` flag

Adding a new command is as simple as adding an entry to the YAML file. Shannon picks it up on restart.

### Typed Parameters

POST commands support typed parameters with automatic coercion. Each command's `params` in the YAML defines:

- `name` — Parameter key
- `type` — `str`, `int`, `list`, or `bool`
- `required` — Whether the parameter is mandatory
- `label` — Human-readable description shown in `/help`

When a user types `@Shannon /pr-hygiene repo cornelisnetworks/ifs-all stale_days 7`, Shannon:
1. Parses `repo` as `str` → `"cornelisnetworks/ifs-all"`
2. Parses `stale_days` as `int` → `7`
3. Sends `{"repo": "cornelisnetworks/ifs-all", "stale_days": 7}` to the agent API

List parameters use comma-separation: `source_paths src/a.c,src/b.c` → `["src/a.c", "src/b.c"]`

Use `/help` in any agent channel to see the full parameter syntax for all commands.

### Currently Registered Agents

| Agent | Role | Port | Commands |
|-------|------|------|----------|
| Shannon | Communications | 8200 | 6 built-in |
| Drucker | Engineering Hygiene | 8201 | 15 commands (Jira + GitHub) |
| Gantt | Project Planning | 8202 | 8 commands |
| Hypatia | Documentation | 8203 | 7 commands (generate, search, publish) |

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
├── cli.py                  # Standalone CLI for card testing
└── docs/
    ├── PLAN.md             # Full technical specification
    └── TEAMS_BOT_FRAMEWORK.md  # Bot Framework integration details

shannon/                    # Implementation (repo root)
├── app.py                  # FastAPI application factory (create_app)
├── service.py              # Command dispatch, agent routing
├── cards.py                # Adaptive Card builders for all agents
├── poster.py               # Teams message posting (Workflows, Bot Framework)
└── registry.py             # Agent registry loader (YAML + env overrides)

deploy/                     # Server deployment configuration
├── env/                    # Environment files (credentials)
│   ├── shared.env          # Non-sensitive: log level, paths
│   └── teams.env           # Teams webhook secrets
├── systemd/
│   └── shannon.service     # Podman systemd user unit
├── caddy/
│   └── Caddyfile           # TLS reverse proxy
└── scripts/
    ├── deploy-shannon.sh   # One-shot deployment script
    └── fix-server.sh       # SSH rate-limit + host networking fix
```

> Note: Shannon's implementation lives in `shannon/` at the repo root (legacy FastAPI service), while agent metadata and documentation live in `agents/shannon/`.

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
