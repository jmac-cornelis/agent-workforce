# Drucker Engineering Hygiene Agent

## Overview

The Drucker Engineering Hygiene Agent is the most feature-rich implemented agent. It automates Jira ticket hygiene and GitHub pull request lifecycle management, ensuring compliance and visibility across engineering workflows.

## Quick Start

The Drucker Agent monitors Jira and GitHub to ensure tickets and pull requests adhere to engineering standards. It operates in a safe, dry-run mode by default, allowing you to preview changes before execution.

You can interact with Drucker through Teams chat (via `@Shannon`), REST API endpoints, or CLI commands.

## Dry-Run Safety

**All mutation operations default to dry-run mode.** This means Drucker will report on findings but will not modify Jira tickets or GitHub PRs unless explicitly instructed.

To override dry-run mode and execute changes:

*   **Shannon:** Append `execute` to the command.
*   **API:** Pass `dry_run=false` in the request parameters.
*   **Environment:** Set `DRY_RUN=false` in your environment variables.

## Shannon Commands

Interact with Drucker directly in Teams by mentioning `@Shannon`.

### Jira Hygiene Commands

| Command | Action | Example |
| :--- | :--- | :--- |
| `/issue-check` | Run intake validation for one Jira ticket | `@Shannon /issue-check STLSW-1234` |
| `/intake-report` | Run a recent-ticket intake report | `@Shannon /intake-report` |
| `/hygiene-run` | Run hygiene analysis | `@Shannon /hygiene-run` |
| `/hygiene-report` | Get a stored report | `@Shannon /hygiene-report 12345` |
| `/hygiene-list` | List stored reports | `@Shannon /hygiene-list` |
| `/bug-activity` | Show bug ticket activity for today | `@Shannon /bug-activity` |

### GitHub PR Hygiene Commands

| Command | Action | Example |
| :--- | :--- | :--- |
| `/pr-hygiene` | Full PR hygiene scan (stale PRs + missing reviews) | `@Shannon /pr-hygiene cornelisnetworks/ifs-all` |
| `/pr-stale` | Find stale PRs with no activity | `@Shannon /pr-stale cornelisnetworks/ifs-all` |
| `/pr-reviews` | Find PRs missing code review | `@Shannon /pr-reviews cornelisnetworks/ifs-all` |
| `/pr-list` | List open PRs for a repository | `@Shannon /pr-list cornelisnetworks/ifs-all` |

### GitHub Extended Hygiene Commands

| Command | Action | Example |
| :--- | :--- | :--- |
| `/naming-compliance` | Check branch/PR naming compliance | `@Shannon /naming-compliance cornelisnetworks/ifs-all` |
| `/merge-conflicts` | Find open PRs with merge conflicts | `@Shannon /merge-conflicts cornelisnetworks/ifs-all` |
| `/ci-failures` | Find open PRs with failing CI checks | `@Shannon /ci-failures cornelisnetworks/ifs-all` |
| `/stale-branches` | Find stale branches with no activity | `@Shannon /stale-branches cornelisnetworks/ifs-all` |
| `/extended-hygiene`| Run comprehensive extended analysis (all scan types) | `@Shannon /extended-hygiene cornelisnetworks/ifs-all` |

## API Reference

The Drucker Agent exposes REST endpoints, typically on port 8201.

### Jira Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/v1/hygiene/issue` | POST | Single ticket validation |
| `/v1/hygiene/intake` | POST | Recent ticket intake report |
| `/v1/hygiene/run` | POST | Full hygiene analysis |
| `/v1/hygiene/report/{report_id}` | GET | Get stored report |
| `/v1/hygiene/reports` | GET | List reports |
| `/v1/activity/bugs` | POST | Bug activity |

### GitHub Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/v1/github/pr-hygiene` | POST | Full PR hygiene scan |
| `/v1/github/pr-stale` | POST | Stale PR scan |
| `/v1/github/pr-reviews` | POST | Missing reviews scan |
| `/v1/github/prs/{owner}/{repo}` | GET | List open PRs |
| `/v1/github/naming-compliance` | POST | Naming compliance |
| `/v1/github/merge-conflicts` | POST | Merge conflicts |
| `/v1/github/ci-failures` | POST | CI failures |
| `/v1/github/stale-branches` | POST | Stale branches |
| `/v1/github/extended-hygiene` | POST | Extended hygiene (all scans) |

### Polling Endpoint

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/v1/poller/tick` | POST | Trigger one polling cycle |

### Example POST Body

For scanning a repository via API:

```json
{
  "owner": "cornelisnetworks",
  "repo": "ifs-all",
  "dry_run": true
}
```

For checking a single Jira issue via API:

```json
{
  "issue_key": "STLSW-1234",
  "dry_run": true
}
```

## Scan Types

Drucker performs several types of hygiene scans:

1.  **Stale PRs**: Identifies PRs with no activity beyond the configured threshold (default 5 days, with a 2x grace period for drafts).
2.  **Missing Reviews**: Highlights PRs without assigned reviewers or those with pending reviews.
3.  **Naming Compliance**: Verifies that branch and PR titles conform to Jira ticket patterns (e.g., `STLSW-12345` or `[NO-JIRA]`).
4.  **Merge Conflicts**: Detects PRs with a dirty merge state.
5.  **CI Failures**: Flags PRs with failing check runs.
6.  **Stale Branches**: Finds branches with no commits beyond the configured threshold and no open PRs.

## Polling and Automated Reports

Drucker's polling system can automatically run hygiene scans on a schedule and generate aggregated reports.

### GitHub PR Hygiene Polling

When the `github-hygiene-scan` polling job is enabled, Drucker:

1.  Scans all configured repositories for PR hygiene issues
2.  Aggregates findings across all repositories into a single report
3.  Saves the report to `/data/state/github_reports/{timestamp}/` with both JSON and Markdown formats
4.  Optionally sends a notification to Shannon with summary statistics

The aggregated report includes:

*   Overall statistics (total open PRs, stale PRs, missing reviews)
*   Per-repository breakdowns with detailed findings
*   Comparison with the previous scan (if available)
*   Markdown-formatted output for easy sharing

Reports are persisted to disk and can be retrieved later for historical analysis.

## Configuration

Drucker is configured via YAML files and environment variables.

### Configuration Files

*   `agents/drucker/config/polling.yaml`: Defines polling jobs, intervals, and thresholds.
    *   **Jobs**:
        *   `hygiene-scan` - Jira hygiene (scan_type: jira)
        *   `recent-ticket-intake` - New ticket intake (scan_type: jira)
        *   `github-hygiene-scan` - GitHub PR hygiene (scan_type: github, disabled by default)
        *   `github-extended-scan` - Extended GitHub scans (scan_type: github-extended, disabled by default)
*   `agents/drucker/config/monitor.yaml`: Defines validation rules per issue type.
*   `agents/drucker/prompts/system.md`: Sets the agent behavior prompt.

### Environment Variables

Required environment variables for full functionality:

*   `GITHUB_TOKEN`: GitHub personal access token.
*   `GITHUB_API_URL`: (Optional) URL for GitHub Enterprise.
*   `JIRA_SERVICE_EMAIL`: Jira service account email for deployed/shared execution.
*   `JIRA_SERVICE_API_TOKEN`: Jira service account API token.
*   `JIRA_URL`: Base URL for the Jira instance.
*   `DRY_RUN`: Controls mutation safety (defaults to `true`).

## Deployment

### Prerequisites

Drucker runs as a Podman container alongside Shannon. Shannon is **required** — it handles Teams command routing to Drucker's API.

| Requirement | Value |
|-------------|-------|
| Shannon | Must be running on the same host (port 8200) |
| Jira credentials | Service account email + API token |
| GitHub token | (Optional) PAT with `repo` + `read:org` scopes |
| Port | 8201 |

### Current Production Server

| Property | Value |
|----------|-------|
| Host | `bld-node-48.cornelisnetworks.com` |
| Data dir | `/home/scm/agent-workforce/data/drucker/` |
| Env files | `deploy/env/shared.env`, `deploy/env/jira.env`, `deploy/env/github.env` |

### Step 1: Build the Image

Uses the same shared image as Shannon (see [Shannon deployment](../shannon/README.md#deployment)):

```bash
podman build -t localhost/cornelis/agent-workforce:latest .
```

### Step 2: Configure Environment Files

Drucker needs Jira credentials and optionally GitHub:

**`deploy/env/jira.env`** — Jira authentication (required):
```bash
JIRA_URL=https://cornelisnetworks.atlassian.net
JIRA_DEFAULT_PROJECT=STL
JIRA_SERVICE_EMAIL=scm@cornelisnetworks.com
JIRA_SERVICE_API_TOKEN=<your-jira-api-token>
JIRA_ENABLE_LEGACY_FALLBACK=false

# Optional compatibility bridge for older callers:
# JIRA_EMAIL=scm@cornelisnetworks.com
# JIRA_API_TOKEN=<same-service-token>
```

**`deploy/env/github.env`** — GitHub authentication (optional, for PR hygiene):
```bash
GITHUB_TOKEN=<your-github-pat>
GITHUB_API_URL=https://api.github.com
GITHUB_ORG=cornelisnetworks
```

The PAT needs `repo` and `read:org` scopes. Generate at: https://github.com/settings/tokens

**`deploy/env/shared.env`** — Shared config (same file Shannon uses):
```bash
LOG_LEVEL=INFO
STATE_BACKEND=json
PERSISTENCE_DIR=/data/state
DRY_RUN=true
```

### Step 3: Create Data Directory

```bash
mkdir -p data/drucker
```

### Step 4: Start Drucker

```bash
podman run -d --name drucker -p 8201:8201 \
    --env-file deploy/env/shared.env \
    --env-file deploy/env/jira.env \
    --env-file deploy/env/github.env \
    -v $(pwd)/config:/app/config:ro,Z \
    -v $(pwd)/data/drucker:/data/state:Z \
    localhost/cornelis/agent-workforce:latest \
    uvicorn agents.drucker.api:app --host 0.0.0.0 --port 8201
```

> **Cross-container networking:** Shannon reaches Drucker via `http://host.containers.internal:8201` (configured in `config/shannon/agent_registry.yaml`). `host.containers.internal` resolves to the host's loopback from inside Podman containers.

### Step 5: Verify

```bash
# Health check
curl -s http://localhost:8201/v1/health | python3 -m json.tool
# Expected: {"ok": true}

# Test Jira connectivity (real API call)
curl -s -X POST http://localhost:8201/v1/activity/bugs \
    -H "Content-Type: application/json" \
    -d '{"project_key": "STL"}' | python3 -m json.tool

# Test Shannon → Drucker routing (in Teams)
# @Shannon /bug-activity project STL
```

### Step 6: Install Systemd Service

```bash
cp deploy/systemd/drucker.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now drucker

# Check status
systemctl --user status drucker
journalctl --user -u drucker -f  # tail logs
```

### Step 7: Verify Shannon Integration

In the Teams channel where Shannon is configured:

```text
@Shannon /bug-activity project STL        # Jira bug activity
@Shannon /issue-check STLSW-1234          # Single ticket check
@Shannon /pr-hygiene cornelisnetworks/ifs-all  # GitHub PR scan (requires GITHUB_TOKEN)
```

If Shannon returns an error, check:
1. Drucker is healthy on port 8201: `curl http://localhost:8201/v1/health`
2. Shannon can reach Drucker: `podman exec shannon python3 -c "import urllib.request; print(urllib.request.urlopen('http://host.containers.internal:8201/v1/health').read())"`
3. Shannon's conversation reference is established (send `@Shannon /stats` first)

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `LLMError: litellm package required` | Image missing litellm | Rebuild with `podman build --no-cache` (Dockerfile includes litellm) |
| `JiraConnectionError` | Bad credentials in jira.env | Verify `JIRA_EMAIL` and `JIRA_API_TOKEN` — test with `curl -u email:token https://cornelisnetworks.atlassian.net/rest/api/2/myself` |
| `GitHubConnectionError` | Missing or expired PAT | Generate new token at github.com/settings/tokens with `repo` + `read:org` scopes |
| Shannon commands return 500 | Drucker not reachable | Verify `api_base_url` in registry uses `host.containers.internal:8201` |
| `dry_run: true` in all responses | `DRY_RUN=true` in shared.env | Set `DRY_RUN=false` in `shared.env` or pass `dry_run=false` per request |

### Running Locally (Development)

```bash
# API server
uvicorn agents.drucker.api:app --host 0.0.0.0 --port 8201

# Docker Compose
docker compose up drucker
```

## CLI Commands

### Standalone CLI (`drucker-agent`)

The preferred way to run drucker-agent is:

```bash
agent-cli drucker <subcommand> [options]
```