# Shannon Permanent Deployment Plan

## Status: Draft — awaiting network topology confirmation

## Context

Shannon is proven working end-to-end as of 2026-03-17:
- `@Shannon /stats` in Teams → Outgoing Webhook → cloudflared quick tunnel → Shannon on localhost:8200 → Adaptive Card reply in channel
- The current setup is ephemeral: cloudflared quick tunnel URL changes on restart, requiring a new Teams webhook each time

## Goal

Run Shannon permanently on `cn-ai-01.cornelisnetworks.com` so that `@Shannon` works 24/7 in the `#agent-shannon` channel without manual tunnel restarts or webhook recreation.

---

## Decision: Network Path

Teams Outgoing Webhooks require Microsoft servers to POST to a public HTTPS URL. There are two paths depending on whether `cn-ai-01` is internet-reachable.

### Path A — Named Cloudflare Tunnel (recommended if cn-ai-01 is behind firewall)

No inbound ports needed. Cloudflare Tunnel creates an outbound-only connection from cn-ai-01 to Cloudflare edge, which proxies Teams traffic in.

**Pros:**
- Zero firewall changes, zero IT networking tickets
- Free tier is sufficient
- Stable URL that survives restarts
- TLS handled by Cloudflare automatically

**Cons:**
- Dependency on Cloudflare infrastructure
- Requires a Cloudflare account (free)

### Path B — Direct hosting with reverse proxy and TLS

Open port 443 on cn-ai-01 (or a load balancer in front of it), get a DNS name like `shannon.cornelisnetworks.com`, and terminate TLS with nginx/caddy.

**Pros:**
- No third-party tunnel dependency
- Full control over the network path

**Cons:**
- Requires IT to open firewall ports
- Requires a public DNS record
- Requires TLS certificate management (Let's Encrypt or corporate CA)

### Recommendation

**Use Path A (Named Cloudflare Tunnel)** unless IT confirms cn-ai-01 is already internet-reachable. It requires zero firewall changes and gives a stable URL.

---

## Implementation Plan — Path A (Named Cloudflare Tunnel)

### Step 1: Create a Cloudflare account and named tunnel

```bash
# On cn-ai-01:
# 1. Install cloudflared
sudo curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared

# 2. Authenticate (opens browser, links to Cloudflare account)
cloudflared tunnel login

# 3. Create a named tunnel (stable ID, survives restarts)
cloudflared tunnel create shannon

# 4. Note the tunnel UUID and credentials file path
# Output: Created tunnel shannon with id <TUNNEL_UUID>
# Credentials: ~/.cloudflared/<TUNNEL_UUID>.json
```

### Step 2: Configure the tunnel

Create `/etc/cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL_UUID>
credentials-file: /etc/cloudflared/<TUNNEL_UUID>.json

ingress:
  - hostname: shannon.<your-domain>.com
    service: http://localhost:8200
  - service: http_status:404
```

If you do not have a domain on Cloudflare, you can use a `trycloudflare.com` subdomain with a named tunnel, but a custom domain is more professional and stable.

### Step 3: Add DNS record

```bash
# This creates a CNAME pointing shannon.<domain> to the tunnel
cloudflared tunnel route dns shannon shannon.<your-domain>.com
```

### Step 4: Deploy Shannon as a systemd service

Create `/etc/systemd/system/shannon.service`:

```ini
[Unit]
Description=Shannon Teams Bot Service
After=network.target

[Service]
Type=simple
User=agent
Group=agent
WorkingDirectory=/opt/jira-utilities
EnvironmentFile=/opt/jira-utilities/.env
ExecStart=/opt/jira-utilities/.venv/bin/python -m uvicorn shannon.app:app --host 127.0.0.1 --port 8200
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Step 5: Deploy cloudflared as a systemd service

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### Step 6: Update Teams webhook (one-time)

1. Delete the existing Shannon outgoing webhook in Teams
2. Create a new one with callback URL: `https://shannon.<your-domain>.com/v1/teams/outgoing-webhook`
3. Save the HMAC secret to `/opt/jira-utilities/.env`
4. Restart Shannon: `sudo systemctl restart shannon`

### Step 7: Verify

```bash
# Health check through the tunnel
curl https://shannon.<your-domain>.com/v1/bot/health

# Then @Shannon /stats in Teams
```

---

## Implementation Plan — Path B (Direct Hosting)

### Prerequisites from IT

1. Public DNS record: `shannon.cornelisnetworks.com` → cn-ai-01 public IP
2. Firewall rule: allow inbound TCP 443 from Microsoft Teams IP ranges
3. TLS certificate for `shannon.cornelisnetworks.com`

### Steps

1. Install nginx on cn-ai-01
2. Configure nginx as reverse proxy: `443 → localhost:8200` with TLS
3. Deploy Shannon as systemd service (same as Path A Step 4)
4. Update Teams webhook URL to `https://shannon.cornelisnetworks.com/v1/teams/outgoing-webhook`

---

## Repo Changes Needed (Both Paths)

### Files to create

| File | Purpose |
|------|---------|
| `deploy/shannon.service` | systemd unit file for Shannon |
| `deploy/cloudflared-config.yml.template` | cloudflared tunnel config template |
| `deploy/deploy-shannon.sh` | Deployment script for cn-ai-01 |

### Files to update

| File | Change |
|------|--------|
| `.env.example` | Document all Shannon env vars with comments |
| `docs/shannon-teams-setup.md` | Add permanent deployment section |
| `config/shannon/agent_registry.yaml` | Fill in team_id and channel_id from live activity |

### Capture team_id and channel_id from live traffic

The outgoing webhook activity payload includes `channelData.teamsTeamId` and `channelData.teamsChannelId`. We should log these from the next live request and populate `agent_registry.yaml`. This can be done by checking the audit log:

```bash
cat data/shannon/audit/*.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    r = json.loads(line)
    cd = r.get('channel_data', {})
    if cd.get('teamsTeamId'):
        print(f\"team_id: {cd['teamsTeamId']}\")
        print(f\"channel_id: {cd['teamsChannelId']}\")
        break
"
```

---

## Architecture Diagram

```mermaid
flowchart LR
    User[Teams User] -->|@Shannon /stats| Teams[Microsoft Teams]
    Teams -->|POST with HMAC| CF[Cloudflare Edge]
    CF -->|Tunnel| CFD[cloudflared on cn-ai-01]
    CFD -->|localhost:8200| Shannon[Shannon Service]
    Shannon -->|JSON response| CFD
    CFD --> CF
    CF --> Teams
    Teams -->|Adaptive Card| User
```

---

## Questions to Resolve

1. **Is cn-ai-01 internet-reachable?** → Determines Path A vs Path B
2. **Do you have a Cloudflare account?** → If not, create one (free tier is fine)
3. **Do you have a domain on Cloudflare?** → If not, can add one or use trycloudflare.com with named tunnel
4. **What user account runs services on cn-ai-01?** → For the systemd unit file
5. **Where is the repo cloned on cn-ai-01?** → For WorkingDirectory in systemd unit
