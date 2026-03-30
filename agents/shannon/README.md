# Shannon — Communications Agent

## Overview

Shannon is the single Microsoft Teams bot that serves as the human interface for all domain agents in the Cornelis Networks Agent Workforce. Named after Claude Shannon, the father of information theory.

One deployment, all channels. Shannon receives messages from Teams channels, routes commands to the correct agent API, renders responses as Adaptive Cards, manages approval workflows, and logs every interaction for audit.

Shannon is not a dumb proxy. It owns command parsing, routing, response rendering, approval lifecycle management, conversation threading, rate limiting, error handling, and audit logging.

## Quick Start

```bash
# Podman (production)
podman run -d --name shannon --network host \
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
podman run -d --name shannon --network host \
    --env-file deploy/env/shared.env \
    --env-file deploy/env/teams.env \
    -v $(pwd)/config:/app/config:ro,Z \
    -v $(pwd)/data/shannon:/data/shannon:Z \
    localhost/cornelis/agent-workforce:latest \
    uvicorn shannon.app:app --host 0.0.0.0 --port 8200
```

> **`--network host` is required** — Shannon calls agent APIs at `localhost:8201`, `localhost:8202`, etc. Bridge networking isolates containers so `localhost` inside Shannon's container can't reach Drucker. Host networking puts all containers on the same network namespace.

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

**Option A: Cloudflare Tunnel (quick, ephemeral URL)**

```bash
# Install cloudflared
sudo dnf install -y https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm

# Start tunnel (URL changes on each restart)
nohup cloudflared tunnel --url http://localhost:8200 > /tmp/cloudflared.log 2>&1 &

# Get the URL
grep -o 'https://[^ ]*trycloudflare.com' /tmp/cloudflared.log | head -1
```

The tunnel URL (e.g., `https://category-mentor-columnists-serve.trycloudflare.com`) must be set as the outgoing webhook endpoint in Teams: `<tunnel-url>/v1/teams/outgoing-webhook`.

> **Limitation:** The URL changes every time `cloudflared` restarts. Update the Teams webhook accordingly.

**Option B: Caddy Reverse Proxy (persistent, requires DNS)**

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
2. Name: `Shannon`, Callback URL: `<https-url>/v1/teams/outgoing-webhook`
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

#### Re-establishing Conversation References

After a container restart, Shannon loses its in-memory conversation references. Send **`@Shannon /stats`** in the Teams channel to re-establish the reference. This is required before Shannon can route commands to other agents.

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection closed by remote host` on SSH | SSH rate limiting (MaxStartups) | Wait 5-10 min, or run `deploy/scripts/fix-server.sh` when access recovers |
| `podman restart` fails with port conflict | Race condition in rootless Podman | `podman stop -t 10 shannon && podman rm -f shannon` then re-run |
| Shannon returns 500 on agent commands | Agent container not reachable at localhost:PORT | Verify both containers use `--network host` |
| Teams commands get no response | Conversation reference lost after restart | Send `@Shannon /stats` to re-establish |
| `poster_mode: MemoryPoster` in /stats | `SHANNON_TEAMS_POST_MODE` not set or wrong | Check `deploy/env/teams.env`, restart container |
| Cloudflare tunnel URL changed | Ephemeral tunnel restarted | Update Teams outgoing webhook callback URL |

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
