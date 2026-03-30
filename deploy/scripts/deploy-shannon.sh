#!/usr/bin/env bash
# ==========================================================================
# deploy-shannon.sh — One-shot Shannon deployment to bld-node-48
# ==========================================================================
# Usage:
#   ./deploy/scripts/deploy-shannon.sh
#
# Prerequisites:
#   - SSH access to scm@bld-node-48.cornelisnetworks.com
#   - Podman image already built (localhost/cornelis/agent-workforce:latest)
#   - deploy/env/*.env files configured with real credentials
#
# What this does:
#   1. Syncs deploy/ directory to server
#   2. Stops any existing Shannon container
#   3. Starts Shannon via systemd user service
#   4. Installs Caddy TLS proxy (if not present)
#   5. Verifies health endpoint
# ==========================================================================

set -euo pipefail

HOST="scm@bld-node-48.cornelisnetworks.com"
REMOTE_DIR="/home/scm/agent-workforce"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=== Shannon Deployment ==="
echo "Host: ${HOST}"
echo "Local: ${SCRIPT_DIR}"
echo ""

# --- Step 1: Sync deploy config to server ---
echo "[1/6] Syncing deploy configuration..."
rsync -avz --progress \
    "${SCRIPT_DIR}/deploy/" \
    "${HOST}:${REMOTE_DIR}/deploy/" \
    --exclude '*.example' \
    --exclude '.DS_Store'

# --- Step 2: Sync config (agent registry, etc.) ---
echo "[2/6] Syncing config directory..."
rsync -avz --progress \
    "${SCRIPT_DIR}/config/" \
    "${HOST}:${REMOTE_DIR}/config/" \
    --exclude 'env/'

# --- Step 3: Ensure data directories exist ---
echo "[3/6] Setting up data directories and systemd..."
ssh "${HOST}" bash -s <<'REMOTE_SETUP'
set -euo pipefail

mkdir -p ~/agent-workforce/data/shannon
mkdir -p ~/.config/systemd/user
mkdir -p /var/log/caddy 2>/dev/null || true

# Install systemd units
cp ~/agent-workforce/deploy/systemd/shannon.service ~/.config/systemd/user/
cp ~/agent-workforce/deploy/systemd/caddy-proxy.service ~/.config/systemd/user/
systemctl --user daemon-reload

# Enable linger so services survive logout
loginctl enable-linger "$(whoami)" 2>/dev/null || echo "linger already enabled or requires sudo"

echo "Setup complete."
REMOTE_SETUP

# --- Step 4: Stop old container, start via systemd ---
echo "[4/6] Starting Shannon service..."
ssh "${HOST}" bash -s <<'REMOTE_START'
set -euo pipefail

# Stop any manually-started container
podman stop shannon 2>/dev/null || true
podman rm -f shannon 2>/dev/null || true

# Start via systemd
systemctl --user restart shannon

# Wait for startup
echo "Waiting for Shannon to start..."
for i in $(seq 1 15); do
    if curl -sf http://localhost:8200/v1/bot/health >/dev/null 2>&1; then
        echo "Shannon is up after ${i}s"
        break
    fi
    sleep 1
done
REMOTE_START

# --- Step 5: Check if Caddy is installed ---
echo "[5/6] Checking Caddy installation..."
ssh "${HOST}" bash -s <<'REMOTE_CADDY'
if command -v caddy >/dev/null 2>&1; then
    echo "Caddy is installed: $(caddy version)"
    systemctl --user restart caddy-proxy 2>/dev/null || echo "Caddy service not running yet"
else
    echo "Caddy NOT installed. Install with:"
    echo "  sudo dnf install 'dnf-command(copr)'"
    echo "  sudo dnf copr enable @caddy/caddy"
    echo "  sudo dnf install caddy"
    echo "  sudo setcap cap_net_bind_service=+ep \$(which caddy)"
    echo ""
    echo "Shannon is running on HTTP :8200 without TLS."
fi
REMOTE_CADDY

# --- Step 6: Verify ---
echo "[6/6] Verifying deployment..."
ssh "${HOST}" bash -s <<'REMOTE_VERIFY'
echo "=== Container Status ==="
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== Health Check ==="
curl -s http://localhost:8200/v1/bot/health | python3 -m json.tool 2>/dev/null || echo "Health check failed"

echo ""
echo "=== Systemd Status ==="
systemctl --user is-active shannon 2>/dev/null || echo "Shannon service: inactive"

echo ""
echo "=== Memory ==="
free -h | head -2
REMOTE_VERIFY

echo ""
echo "=== Deployment Complete ==="
echo "Shannon HTTP:  http://bld-node-48.cornelisnetworks.com:8200/v1/bot/health"
echo "Shannon HTTPS: https://bld-node-48.cornelisnetworks.com/v1/bot/health (requires Caddy)"
echo ""
echo "Next steps:"
echo "  1. Configure Teams webhook in deploy/env/teams.env"
echo "  2. Re-run this script to apply webhook config"
echo "  3. Set up outgoing webhook in Teams channel"
