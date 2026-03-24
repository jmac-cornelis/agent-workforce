# Shannon Deployment Plan — Company-Wide Rollout

## Overview

Shannon is the communications agent for the Cornelis AI agent workforce.
It provides a bidirectional interface between Microsoft Teams and the agent
platform using zero-cost Teams integration mechanisms (no Azure Bot Service
subscription required).

**Architecture summary:**

| Direction | Mechanism | Cost |
|---|---|---|
| Users → Shannon | Teams Outgoing Webhook (HMAC-verified) | Free |
| Shannon → Channel | Teams Workflows Incoming Webhook | Free |

Shannon runs as a single FastAPI service.  Users @mention Shannon in a
Teams channel to issue commands.  Shannon can proactively post Adaptive
Cards into channels via the Workflows webhook.

---

## Prerequisites

- A Linux server (physical or VM) with Python 3.9+ and network access
- A public HTTPS endpoint (via reverse proxy, Cloudflare Tunnel, or cloud load balancer)
- Microsoft Teams admin access to the target team
- Git clone of the `agent-workforce` repository

---

## Phase 1 — Infrastructure Setup

**Goal:** Shannon running on a stable server with a permanent HTTPS URL.

### 1.1 Provision the host

Pick one of these options based on what Cornelis has available:

| Option | Pros | Cons | Cost |
|---|---|---|---|
| Existing internal Linux server + Cloudflare Tunnel | No new infra, stable URL, auto-TLS | Requires `cloudflared` install | Free |
| Existing internal Linux server + nginx reverse proxy | Full control, standard ops | Requires public IP + TLS cert management | Free (if server exists) |
| AWS EC2 t3.micro / Azure B1s | Always on, isolated | Monthly cost | ~$8–13/month |
| Docker on existing container host | Standard deployment, easy restart | Needs existing Docker infra | Free (if host exists) |

**Recommendation:** Internal server + Cloudflare Tunnel is the simplest
zero-cost production path.  If Cornelis already has a public-facing server
with nginx, use that instead.

### 1.2 Install the application

```bash
# Clone the repo
git clone git@github.com:jmac-cornelis/agent-workforce.git
cd agent-workforce

# Create venv and install dependencies
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 1.3 Set up a stable public URL

**Option A — Cloudflare Tunnel (recommended for zero-cost):**

```bash
# Install cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

# Authenticate (one-time)
cloudflared tunnel login

# Create the tunnel
cloudflared tunnel create shannon

# Route a subdomain (e.g. shannon.cornelisnetworks.com)
cloudflared tunnel route dns shannon shannon.cornelisnetworks.com

# Run the tunnel
cloudflared tunnel --url http://localhost:8200 run shannon
```

**Option B — nginx reverse proxy (if you have a public-facing server):**

```nginx
server {
    listen 443 ssl;
    server_name shannon.cornelisnetworks.com;

    ssl_certificate     /etc/letsencrypt/live/shannon.cornelisnetworks.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shannon.cornelisnetworks.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8200;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 1.4 Create the production environment file

Create `.env_prod` on the server (do NOT commit this file):

```bash
# Shannon core
SHANNON_AGENT_REGISTRY_PATH=./config/shannon/agent_registry.yaml
SHANNON_STATE_DIR=./data/shannon
SHANNON_TEAMS_BOT_NAME=Shannon
SHANNON_HOST=0.0.0.0
SHANNON_PORT=8200
SHANNON_SEND_WELCOME_ON_INSTALL=true

# Posting mode
SHANNON_TEAMS_POST_MODE=workflows

# Outgoing Webhook HMAC secret (from Teams — Step 2.2)
SHANNON_TEAMS_OUTGOING_WEBHOOK_SECRET=<to-be-filled>

# Workflows incoming webhook URL (from Teams — Step 2.3)
SHANNON_TEAMS_WORKFLOWS_WEBHOOK_URL=<to-be-filled>
```

### 1.5 Set up process management

**Option A — systemd (recommended for bare metal / VM):**

Create `/etc/systemd/system/shannon.service`:

```ini
[Unit]
Description=Shannon Communications Agent
After=network.target

[Service]
Type=simple
User=shannon
WorkingDirectory=/opt/agent-workforce
EnvironmentFile=/opt/agent-workforce/.env_prod
ExecStart=/opt/agent-workforce/.venv/bin/uvicorn shannon.app:app --host 0.0.0.0 --port 8200
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable shannon
sudo systemctl start shannon
```

**Option B — Docker:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8200
CMD ["uvicorn", "shannon.app:app", "--host", "0.0.0.0", "--port", "8200"]
```

```bash
docker build -t shannon .
docker run -d --name shannon --env-file .env_prod -p 8200:8200 --restart unless-stopped shannon
```

### 1.6 Verify the service is reachable

```bash
# Local health check
curl http://localhost:8200/v1/bot/health

# External health check (through public URL)
curl https://shannon.cornelisnetworks.com/v1/bot/health
```

Both should return `{"status": "ok", ...}`.

---

## Phase 2 — Teams Configuration

**Goal:** Teams connected bidirectionally to Shannon.

### 2.1 Create the team and channel

1. In Teams, create a team called **Agent Workforce** (or reuse an existing one).
2. Create a standard channel called **#agent-shannon**.

### 2.2 Create the Outgoing Webhook (users → Shannon)

1. Open the **Agent Workforce** team in Teams.
2. Click `...` next to the team name → **Manage team** → **Apps** tab.
3. Click **Create an outgoing webhook**.
4. Name: `Shannon`
5. Callback URL: `https://shannon.cornelisnetworks.com/v1/teams/outgoing-webhook`
6. Description: `Cornelis AI agent communications service`
7. Click **Create** and **copy the HMAC secret** (shown once — cannot be retrieved later).
8. Update `.env_prod`:
   ```
   SHANNON_TEAMS_OUTGOING_WEBHOOK_SECRET=<the-secret>
   ```

### 2.3 Create the Workflows Incoming Webhook (Shannon → channel)

1. In **#agent-shannon**, click `+` or the `...` menu.
2. Search for **Workflows**.
3. Select the template: **"Send webhook alerts to a channel"**.
4. Set **Team** to `Agent Workforce` and **Channel** to `agent-shannon`.
5. Click **Save**.
6. On the confirmation page, click **Copy webhook link**.
7. Update `.env_prod`:
   ```
   SHANNON_TEAMS_WORKFLOWS_WEBHOOK_URL=<the-url>
   ```

### 2.4 Restart Shannon to pick up new secrets

```bash
# systemd
sudo systemctl restart shannon

# or Docker
docker restart shannon
```

### 2.5 Verify the full round-trip

**Test inbound (user → Shannon):**

In `#agent-shannon`, type:
```
@Shannon /stats
```
Shannon should reply with a status card.

**Test outbound (Shannon → channel):**

```bash
curl -X POST https://shannon.cornelisnetworks.com/v1/bot/notify \
  -H 'Content-Type: application/json' \
  -d '{"agent_id": "shannon", "title": "Deployment Test", "text": "Shannon is live."}'
```
A card should appear in `#agent-shannon`.

---

## Phase 3 — Company-Wide Rollout

**Goal:** All Cornelis staff can interact with Shannon in Teams.

### 3.1 Ensure team membership

All employees who need Shannon access must be members of the **Agent
Workforce** team in Teams.  Work with IT to:

- Add the team to auto-membership for relevant groups, OR
- Distribute a join link / join code for the team

### 3.2 Communicate the rollout

Send an announcement (via Shannon itself, once live) with:

- What Shannon does and which commands are available
- Which channel to use (`#agent-shannon`)
- How to interact (type `@Shannon /help` to get started)

### 3.3 Available commands (v1)

| Command | Description |
|---|---|
| `/stats` | Service statistics |
| `/busy` | Current load status |
| `/work-today` | Work summary for today |
| `/token-status` | Token/cost status |
| `/decision-tree` | Recent decisions |
| `/why <id>` | Explain a specific decision |
| `/help` | List available commands |

### 3.4 Add agent channels (future)

As additional agents come online (Gantt, Drucker, Hypatia, etc.),
repeat Step 2.3 for each agent's channel and update the agent registry
(`config/shannon/agent_registry.yaml`) with the channel IDs.

---

## Phase 4 — Operational Readiness

### 4.1 Monitoring

- Shannon exposes `/v1/bot/health` for uptime monitoring.  Point your
  monitoring tool (Datadog, Uptime Robot, etc.) at the public URL.
- `/v1/status/load` returns load classification (idle / working / busy /
  overloaded) based on message volume.
- Audit logs are written to `$SHANNON_STATE_DIR/audit/` as JSONL files,
  one per day.

### 4.2 Log management

Shannon logs to stdout via Python `logging`.  With systemd, logs go to
the journal:

```bash
journalctl -u shannon -f
```

With Docker:

```bash
docker logs -f shannon
```

### 4.3 Updates

```bash
cd /opt/agent-workforce
git pull origin shannon-agent-dev
sudo systemctl restart shannon
```

### 4.4 Backup

The only stateful data is in `$SHANNON_STATE_DIR` (default `data/shannon/`):
- `conversation_references.json` — stored Teams conversation references
- `audit/` — daily JSONL audit logs

Include this directory in your backup routine.

---

## Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| 5-second outgoing webhook timeout | Long commands may time out | Shannon replies "working on it" and posts the full result via Workflows webhook |
| No threading on Workflows posts | Proactive messages appear as new messages, not replies | Cosmetic only — content is the same |
| Adaptive Card actions limited to `openURL` | No interactive approve/reject buttons | Use link-based approval workflows instead |
| Channel-only | No personal or group chat DMs | All interaction happens in the team channel |
| Proactive posts show as "Workflows" sender | Sender name is not "Shannon" | Cosmetic only — the card content identifies Shannon |

---

## Rollback

If something goes wrong:

1. **Turn off the Workflows webhook** in Teams (Workflows dialog → Turn off)
2. **Delete the outgoing webhook** in team settings → Apps
3. **Stop Shannon**: `sudo systemctl stop shannon` or `docker stop shannon`

No data is mutated in Jira or Confluence by Shannon — it is read-only
unless explicitly invoked through agent workflows.

---

## Summary Checklist

- [ ] Server provisioned and accessible
- [ ] Public HTTPS URL configured and verified
- [ ] `.env_prod` created with all secrets
- [ ] Shannon running under process manager (systemd / Docker)
- [ ] Health check passing at public URL
- [ ] Outgoing Webhook created in Teams with HMAC secret captured
- [ ] Workflows Incoming Webhook created and URL captured
- [ ] Shannon restarted with production secrets
- [ ] `@Shannon /stats` returns a card in Teams
- [ ] Proactive notify test posts a card to the channel
- [ ] Team membership opened to target employees
- [ ] Rollout announcement sent
- [ ] Monitoring configured on `/v1/bot/health`
