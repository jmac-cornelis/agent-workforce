# Deploy

Server deployment configuration for the agent workforce.

## Structure

```
deploy/
├── caddy/
│   └── Caddyfile         # TLS reverse proxy (HTTPS termination)
├── env/
│   ├── shared.env        # Non-sensitive: log level, state backend, paths
│   └── teams.env         # Teams webhook credentials
├── scripts/
│   └── deploy-shannon.sh # One-shot deployment to bld-node-48
└── systemd/
    ├── shannon.service     # Podman container as systemd user service
    └── caddy-proxy.service # Caddy TLS proxy as systemd user service
```

## Quick Start

```bash
# 1. Edit credentials
vim deploy/env/teams.env

# 2. Deploy
./deploy/scripts/deploy-shannon.sh
```

## Target Server

| Property | Value |
|----------|-------|
| Host | bld-node-48.cornelisnetworks.com |
| User | scm |
| Runtime | Podman 5.6.0 (rootless) |
| OS | RHEL 10.1 |
| Port | 8200 (HTTP), 443 (HTTPS via Caddy) |

## Services

**Shannon** runs as a rootless Podman container managed by systemd user service.
Auto-restarts on failure, survives logout via `loginctl enable-linger`.

**Caddy** provides TLS termination. Teams webhooks require HTTPS.
For internal-only use, set `tls internal` in the Caddyfile (self-signed).
For public access, replace with the server's FQDN for automatic Let's Encrypt.
