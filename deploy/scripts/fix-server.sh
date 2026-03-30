#!/usr/bin/env bash
# ==========================================================================
# fix-server.sh — Fix SSH rate limiting + switch to host networking
# ==========================================================================
# Run this once when SSH access is restored. It:
#   1. Increases SSH MaxStartups to prevent future lockouts
#   2. Recreates containers with --network host for cross-container comms
#   3. Restarts cloudflare tunnel
#   4. Verifies both services healthy
# ==========================================================================

set -euo pipefail

echo "=== Fix Server Configuration ==="
echo "Date: $(date)"
echo ""

# --- Step 1: Fix SSH rate limiting ---
echo "[1/5] Fixing SSH MaxStartups..."
if grep -q '^MaxStartups' /etc/ssh/sshd_config 2>/dev/null; then
    sudo sed -i 's/^MaxStartups.*/MaxStartups 30:50:100/' /etc/ssh/sshd_config
    echo "  Updated existing MaxStartups"
elif grep -q '^#MaxStartups' /etc/ssh/sshd_config 2>/dev/null; then
    sudo sed -i 's/^#MaxStartups.*/MaxStartups 30:50:100/' /etc/ssh/sshd_config
    echo "  Uncommented and set MaxStartups"
else
    echo 'MaxStartups 30:50:100' | sudo tee -a /etc/ssh/sshd_config > /dev/null
    echo "  Appended MaxStartups"
fi

# Check and disable fail2ban if it exists
if systemctl is-active --quiet fail2ban 2>/dev/null; then
    echo "  fail2ban is active — flushing bans..."
    sudo fail2ban-client unban --all 2>/dev/null || true
fi

sudo systemctl restart sshd
echo "  SSHD restarted with MaxStartups 30:50:100"

# --- Step 2: Stop existing containers ---
echo ""
echo "[2/5] Stopping existing containers..."
podman stop shannon drucker 2>/dev/null || true
podman rm -f shannon drucker 2>/dev/null || true
echo "  Containers removed"

# --- Step 3: Recreate with host networking ---
echo ""
echo "[3/5] Starting containers with --network host..."

podman run -d --name shannon --network host \
    --env-file /home/scm/agent-workforce/deploy/env/shared.env \
    --env-file /home/scm/agent-workforce/deploy/env/teams.env \
    -v /home/scm/agent-workforce/config:/app/config:ro,Z \
    -v /home/scm/agent-workforce/data/shannon:/data/shannon:Z \
    localhost/cornelis/agent-workforce:latest \
    uvicorn shannon.app:app --host 0.0.0.0 --port 8200
echo "  Shannon started on :8200 (host network)"

podman run -d --name drucker --network host \
    --env-file /home/scm/agent-workforce/deploy/env/shared.env \
    --env-file /home/scm/agent-workforce/deploy/env/jira.env \
    --env-file /home/scm/agent-workforce/deploy/env/github.env \
    -v /home/scm/agent-workforce/config:/app/config:ro,Z \
    -v /home/scm/agent-workforce/data/drucker:/data/drucker:Z \
    localhost/cornelis/agent-workforce:latest \
    uvicorn agents.drucker.api:app --host 0.0.0.0 --port 8201
echo "  Drucker started on :8201 (host network)"

# --- Step 4: Restart Cloudflare tunnel ---
echo ""
echo "[4/5] Restarting Cloudflare tunnel..."
pkill cloudflared 2>/dev/null || true
sleep 1
nohup cloudflared tunnel --url http://localhost:8200 > /tmp/cloudflared.log 2>&1 &
sleep 3
TUNNEL_URL=$(grep -o 'https://[^ ]*trycloudflare.com' /tmp/cloudflared.log 2>/dev/null | head -1)
if [ -n "$TUNNEL_URL" ]; then
    echo "  Tunnel URL: ${TUNNEL_URL}"
    echo "  *** UPDATE Teams outgoing webhook URL to: ${TUNNEL_URL}/v1/teams/outgoing-webhook ***"
else
    echo "  WARNING: Tunnel URL not found yet — check /tmp/cloudflared.log"
fi

# --- Step 5: Verify ---
echo ""
echo "[5/5] Verifying services..."
sleep 3

SHANNON_OK=$(curl -s http://localhost:8200/v1/bot/health | python3 -c "import json,sys; print(json.load(sys.stdin).get('ok','FAIL'))" 2>/dev/null || echo "FAIL")
DRUCKER_OK=$(curl -s http://localhost:8201/v1/health | python3 -c "import json,sys; print(json.load(sys.stdin).get('ok','FAIL'))" 2>/dev/null || echo "FAIL")

echo "  Shannon: ${SHANNON_OK}"
echo "  Drucker: ${DRUCKER_OK}"

# Test cross-container: Shannon calling Drucker at localhost:8201
CROSS_OK=$(curl -s -X POST http://localhost:8201/v1/activity/bugs \
    -H "Content-Type: application/json" \
    -d '{"project_key": "STL"}' | python3 -c "import json,sys; print(json.load(sys.stdin).get('ok','FAIL'))" 2>/dev/null || echo "FAIL")
echo "  Cross-container (Drucker API): ${CROSS_OK}"

echo ""
if [ "$SHANNON_OK" = "True" ] && [ "$DRUCKER_OK" = "True" ] && [ "$CROSS_OK" = "True" ]; then
    echo "=== ALL SERVICES HEALTHY ==="
    echo ""
    echo "Next steps:"
    echo "  1. Send '@Shannon /stats' in Teams to re-establish conversation reference"
    echo "  2. Test '@Shannon /bug-activity project STL' for full Shannon→Drucker flow"
else
    echo "=== SOME SERVICES UNHEALTHY — check logs ==="
    echo "  podman logs --tail 20 shannon"
    echo "  podman logs --tail 20 drucker"
fi
