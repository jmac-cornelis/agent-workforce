# Deployment Guide

Server deployment configuration for the Cornelis Networks Agent Workforce.

## Architecture

All agents share a single Docker/Podman image (`localhost/cornelis/agent-workforce:latest`). Each agent runs as a separate container with its own entrypoint, environment files, and data volume. Containers use `--network host` so they can communicate via `localhost:PORT`.

```text
┌─────────────────────────────────────────────────────────┐
│  bld-node-48.cornelisnetworks.com (RHEL 10.1, Podman)  │
│                                                         │
│  ┌─────────────────┐  ┌──────────────────┐              │
│  │  Shannon :8200   │  │  Drucker :8201   │              │
│  │  (Teams bot)     │──│  (Jira/GitHub)   │              │
│  │  teams.env       │  │  jira.env        │              │
│  │  shared.env      │  │  github.env      │              │
│  └────────┬────────┘  │  shared.env      │              │
│           │            └──────────────────┘              │
│  ┌────────┴────────┐                                    │
│  │ Cloudflare Tunnel│  HTTPS → localhost:8200            │
│  │ (ephemeral URL)  │                                   │
│  └─────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
```

## Directory Layout

```text
deploy/
├── README.md                  # This file
├── caddy/
│   └── Caddyfile              # TLS reverse proxy (alternative to Cloudflare)
├── env/
│   ├── shared.env             # Non-sensitive: log level, state backend, paths
│   ├── teams.env              # Teams webhook credentials (Shannon)
│   ├── jira.env               # Jira service account (Drucker)
│   └── github.env             # GitHub PAT (Drucker, optional)
├── scripts/
│   ├── deploy-shannon.sh      # One-shot Shannon deployment
│   └── fix-server.sh          # Fix SSH lockouts + host networking
└── systemd/
    ├── shannon.service         # Shannon Podman systemd user unit
    ├── drucker.service         # Drucker Podman systemd user unit
    └── caddy-proxy.service     # Caddy TLS proxy systemd user unit
```

## Target Server

| Property | Value |
|----------|-------|
| Host | `bld-node-48.cornelisnetworks.com` |
| User | `scm` |
| Internal IP | `10.228.209.81` |
| External IP | `208.255.156.42` (NAT) |
| OS | RHEL 10.1, kernel 6.12 |
| Hardware | 88 CPUs, 62 GB RAM, 428 GB disk |
| Runtime | Podman 5.6.0 (rootless) |
| SSH | `sshpass -p 'Beatles=2021' ssh scm@bld-node-48.cornelisnetworks.com` |

## Quick Start (Full Stack)

```bash
# 1. SSH to server
ssh scm@bld-node-48.cornelisnetworks.com

# 2. Clone repo (if not already done)
git clone https://github.com/jmac-cornelis/agent-workforce.git
cd agent-workforce

# 3. Build image (~5 minutes first time)
podman build -t localhost/cornelis/agent-workforce:latest .

# 4. Create data directories
mkdir -p data/shannon data/drucker

# 5. Configure environment files (edit with real credentials)
vim deploy/env/teams.env   # Teams webhook secrets
vim deploy/env/jira.env    # Jira service account
vim deploy/env/github.env  # GitHub PAT (optional)

# 6. Start both agents
podman run -d --name shannon --network host \
    --env-file deploy/env/shared.env \
    --env-file deploy/env/teams.env \
    -v $(pwd)/config:/app/config:ro,Z \
    -v $(pwd)/data/shannon:/data/shannon:Z \
    localhost/cornelis/agent-workforce:latest \
    uvicorn shannon.app:app --host 0.0.0.0 --port 8200

podman run -d --name drucker --network host \
    --env-file deploy/env/shared.env \
    --env-file deploy/env/jira.env \
    --env-file deploy/env/github.env \
    -v $(pwd)/config:/app/config:ro,Z \
    -v $(pwd)/data/drucker:/data/state:Z \
    localhost/cornelis/agent-workforce:latest \
    uvicorn agents.drucker.api:app --host 0.0.0.0 --port 8201

# 7. Verify
curl -s http://localhost:8200/v1/bot/health | python3 -m json.tool
curl -s http://localhost:8201/v1/health | python3 -m json.tool

# 8. Install systemd services (auto-restart, survive logout)
mkdir -p ~/.config/systemd/user
cp deploy/systemd/shannon.service ~/.config/systemd/user/
cp deploy/systemd/drucker.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now shannon drucker
loginctl enable-linger $(whoami)

# 9. Set up HTTPS for Teams (Cloudflare Tunnel)
sudo dnf install -y https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm
nohup cloudflared tunnel --url http://localhost:8200 > /tmp/cloudflared.log 2>&1 &
grep -o 'https://[^ ]*trycloudflare.com' /tmp/cloudflared.log | head -1
# → Use this URL as the Teams outgoing webhook callback

# 10. In Teams: @Shannon /stats  (establishes conversation reference)
```

## Environment Files

### `shared.env` — All agents

```bash
LOG_LEVEL=INFO
STATE_BACKEND=json
PERSISTENCE_DIR=/data/state
SHANNON_STATE_DIR=/data/shannon
DRY_RUN=true                     # Safe default — set to false for production execution
```

### `teams.env` — Shannon only

```bash
SHANNON_TEAMS_POST_MODE=workflows                    # memory | workflows | botframework
SHANNON_TEAMS_OUTGOING_WEBHOOK_SECRET=<hmac-secret>  # From Teams outgoing webhook setup
SHANNON_TEAMS_WORKFLOWS_WEBHOOK_URL=<url>            # From Teams Workflows incoming webhook
SHANNON_TEAMS_BOT_NAME=Shannon
```

### `jira.env` — Drucker (and any Jira-accessing agent)

```bash
JIRA_EMAIL=scm@cornelisnetworks.com
JIRA_API_TOKEN=<api-token>
JIRA_URL=https://cornelisnetworks.atlassian.net
JIRA_DEFAULT_PROJECT=ONECLI
```

### `github.env` — Drucker (optional, for PR hygiene)

```bash
GITHUB_TOKEN=<personal-access-token>    # Scopes: repo, read:org
GITHUB_API_URL=https://api.github.com
GITHUB_ORG=cornelisnetworks
```

## Services

### Shannon (port 8200)

Teams bot gateway. Routes commands to agent APIs, renders Adaptive Cards.

- Entrypoint: `uvicorn shannon.app:app --host 0.0.0.0 --port 8200`
- Env files: `shared.env`, `teams.env`
- Data volume: `data/shannon` → `/data/shannon` (conversation references)
- Systemd unit: `deploy/systemd/shannon.service`

### Drucker (port 8201)

Engineering hygiene agent. Jira ticket validation + GitHub PR lifecycle scanning.

- Entrypoint: `uvicorn agents.drucker.api:app --host 0.0.0.0 --port 8201`
- Env files: `shared.env`, `jira.env`, `github.env`
- Data volume: `data/drucker` → `/data/state` (reports, monitor state)
- Systemd unit: `deploy/systemd/drucker.service`

## Port Allocation

| Port | Agent | Status |
|------|-------|--------|
| 8200 | Shannon | ✅ Deployed |
| 8201 | Drucker | ✅ Deployed |
| 8202 | Gantt | Planned |
| 8203 | Hypatia | Planned |
| 8210-8227 | Future agents | Reserved |

## Networking

All containers use **`--network host`**. This is critical:

- Shannon calls Drucker at `http://localhost:8201` (per `config/shannon/agent_registry.yaml`)
- Bridge networking isolates each container's `localhost` — Shannon can't reach Drucker
- Host networking puts all containers on the same network namespace
- The `:Z` volume suffix is required for SELinux on RHEL

To override agent API URLs without editing YAML (e.g., multi-host deployment):

```bash
# In shared.env:
DRUCKER_API_URL=http://cn-ai-03:8201
GANTT_API_URL=http://cn-ai-03:8202
```

Shannon's registry loader checks `{AGENT_ID}_API_URL` env vars at startup.

## HTTPS for Teams

Teams outgoing webhooks require HTTPS. Current approach: **Cloudflare Tunnel** (quick, no DNS config).

```bash
# Start ephemeral tunnel
nohup cloudflared tunnel --url http://localhost:8200 > /tmp/cloudflared.log 2>&1 &
grep -o 'https://[^ ]*trycloudflare.com' /tmp/cloudflared.log | head -1
```

**Limitation:** URL changes on every restart. Update the Teams outgoing webhook callback URL accordingly.

For persistent HTTPS, use Caddy (`deploy/caddy/Caddyfile`) with a public DNS record.

## Updating

```bash
cd ~/agent-workforce
git pull
podman build -t localhost/cornelis/agent-workforce:latest .
systemctl --user restart shannon drucker
```

For config-only changes (env files, agent registry YAML), just restart:

```bash
systemctl --user restart shannon drucker
```

## Maintenance

### Logs

```bash
journalctl --user -u shannon -f         # Shannon logs
journalctl --user -u drucker -f         # Drucker logs
podman logs --tail 50 shannon           # Container stdout
podman logs --tail 50 drucker           # Container stdout
```

### Container Management

```bash
podman ps                                # List running containers
podman stats                             # Resource usage
systemctl --user status shannon drucker  # Service status
```

### SSH Rate Limiting

The server's SSH daemon has aggressive rate limiting. Rapid automated commands (e.g., during image builds) can trigger lockouts lasting 5-10 minutes. If locked out:

1. Wait 5-10 minutes for the rate limiter to cool down
2. When access recovers, run `deploy/scripts/fix-server.sh` to increase `MaxStartups` to `30:50:100`
3. HTTP ports (8200, 8201) continue working during SSH lockouts

### Conversation Reference Reset

After container restart, Shannon loses conversation references. Send `@Shannon /stats` in the Teams channel to re-establish. Required before Shannon can route commands to other agents.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| SSH connection drops during key exchange | SSH MaxStartups rate limit | Wait 5-10 min; run `fix-server.sh` when recovered |
| `podman restart` fails | Port conflict race condition | `podman stop && podman rm -f` then re-run |
| Shannon 500 on agent commands | Agent not reachable | Verify both containers use `--network host` |
| `LLMError: litellm package required` | Image missing litellm | `podman build --no-cache` |
| Teams commands get no response | Lost conversation reference | Send `@Shannon /stats` in Teams |
| `poster_mode: MemoryPoster` | Wrong `SHANNON_TEAMS_POST_MODE` | Fix `teams.env`, restart shannon |
| `JiraConnectionError` | Bad Jira creds | Test: `curl -u email:token https://cornelisnetworks.atlassian.net/rest/api/2/myself` |
| Cloudflare tunnel URL changed | Ephemeral tunnel restarted | Update Teams webhook callback URL |

## Detailed Agent Deployment Guides

- [Shannon deployment](../agents/shannon/README.md#deployment)
- [Drucker deployment](../agents/drucker/README.md#deployment)
- [Deployment architecture](docs/workforce/DEPLOYMENT_GUIDE.md) (diagrams + full topology)
