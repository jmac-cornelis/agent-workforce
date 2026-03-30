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
*   `JIRA_EMAIL`: Email address for Jira authentication.
*   `JIRA_API_TOKEN`: Jira API token.
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
JIRA_EMAIL=scm@cornelisnetworks.com
JIRA_API_TOKEN=<your-jira-api-token>
JIRA_URL=https://cornelisnetworks.atlassian.net
JIRA_DEFAULT_PROJECT=ONECLI
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
podman run -d --name drucker --network host \
    --env-file deploy/env/shared.env \
    --env-file deploy/env/jira.env \
    --env-file deploy/env/github.env \
    -v $(pwd)/config:/app/config:ro,Z \
    -v $(pwd)/data/drucker:/data/state:Z \
    localhost/cornelis/agent-workforce:latest \
    uvicorn agents.drucker.api:app --host 0.0.0.0 --port 8201
```

> **`--network host` is required** — Shannon routes commands to Drucker at `http://localhost:8201`. Both must share the host network namespace.

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
1. Both containers use `--network host`
2. Drucker is healthy on port 8201
3. Shannon's conversation reference is established (send `@Shannon /stats` first)

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `LLMError: litellm package required` | Image missing litellm | Rebuild with `podman build --no-cache` (Dockerfile includes litellm) |
| `JiraConnectionError` | Bad credentials in jira.env | Verify `JIRA_EMAIL` and `JIRA_API_TOKEN` — test with `curl -u email:token https://cornelisnetworks.atlassian.net/rest/api/2/myself` |
| `GitHubConnectionError` | Missing or expired PAT | Generate new token at github.com/settings/tokens with `repo` + `read:org` scopes |
| Shannon commands return 500 | Drucker not reachable at localhost:8201 | Verify `--network host` on both containers |
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

The preferred way to run Drucker from the command line:

```bash
drucker-agent <subcommand> [options]
```

| Subcommand | Description | Example |
|------------|-------------|---------|
| `hygiene` | Full Jira hygiene analysis | `drucker-agent hygiene -p STL` |
| `issue-check` | Single ticket intake validation | `drucker-agent issue-check -p STL -t STLSW-1234` |
| `intake-report` | Recent ticket intake report | `drucker-agent intake-report -p STL --since "2026-03-01"` |
| `bug-activity` | Daily bug activity summary | `drucker-agent bug-activity -p STL --target-date 2026-03-30` |
| `github-hygiene` | GitHub PR hygiene scan | `drucker-agent github-hygiene cornelisnetworks/ifs-all` |
| `poll` | Scheduled hygiene polling loop | `drucker-agent poll -p STL --max-cycles 0` |

### Via `agent-cli` (unified CLI)

All Drucker subcommands are also available through the unified agent CLI:

```bash
agent-cli drucker hygiene -p STL
agent-cli drucker poll -p STL --poll-interval 300 --max-cycles 0
```

### Drucker CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--stale-days DAYS` | 14 | Stale ticket threshold in days |
| `--ticket-key KEY` / `-t` | — | Specific Jira ticket for `issue-check` |
| `--target-date YYYY-MM-DD` | today | Target date for `bug-activity` |
| `--since DATE` | — | Checkpoint override (YYYY-MM-DD) |
| `--recent-only` | off | Use recent-ticket intake scanning in `poll` |
| `--poll-config FILE` | — | YAML config for polling jobs |
| `--poll-job NAME` | — | Specific job ID from `--poll-config` |
| `--poll-interval SECS` | 300 | Polling interval in seconds |
| `--max-cycles N` | 1 | Number of polling cycles (`0` = continuous) |
| `--github-repos REPO...` | — | GitHub repos for PR hygiene (format: `owner/repo`) |
| `--github-stale-days DAYS` | 5 | Stale PR threshold in days |
| `--branch-stale-days DAYS` | 30 | Branch staleness threshold for `github-hygiene` |
| `--extended` | off | Run all 6 GitHub checks in `github-hygiene` |
| `--notify-shannon` | off | Post summaries through Shannon |
| `--shannon-url URL` | localhost:8200 | Shannon service base URL |
| `--include-done` | off | Include done/closed issues |
| `--output FILE` | auto | Output filename |
| `--limit N` | 200 | Maximum tickets per scan |
| `--json` | off | Output as JSON |
| `--env FILE` | `.env` | Alternate environment file |

### Polling Examples

```bash
# Single Jira hygiene cycle
drucker-agent poll -p STL --max-cycles 1

# Continuous polling with GitHub PR scanning
drucker-agent poll -p STL \
  --poll-interval 300 --max-cycles 0 \
  --github-repos cornelisnetworks/ifs-all cornelisnetworks/opa-psm2 \
  --github-stale-days 7 --notify-shannon

# Poll with custom config file
drucker-agent poll -p STL \
  --poll-config agents/drucker/config/polling.yaml

# GitHub-only: scan a single repo
drucker-agent github-hygiene cornelisnetworks/ifs-all --extended
```

### GitHub Utilities (via `github_utils.py`)

Standalone CLI for GitHub operations. Requires `GITHUB_TOKEN` in the environment.

| Command | Description | Example |
|---------|-------------|---------|
| `--list-repos ORG` | List repositories in a GitHub org | `python github_utils.py --list-repos cornelisnetworks` |
| `--repo-info REPO` | Get metadata for a repository | `python github_utils.py --repo-info cornelisnetworks/ifs-all` |
| `--list-prs REPO` | List pull requests | `python github_utils.py --list-prs cornelisnetworks/ifs-all --state open` |
| `--get-pr REPO N` | Get details for a specific PR | `python github_utils.py --get-pr cornelisnetworks/ifs-all 623` |
| `--pr-reviews REPO N` | Get reviews for a specific PR | `python github_utils.py --pr-reviews cornelisnetworks/ifs-all 623` |
| `--stale-prs REPO` | Find stale PRs | `python github_utils.py --stale-prs cornelisnetworks/ifs-all --days 7` |
| `--missing-reviews REPO` | Find PRs missing reviews | `python github_utils.py --missing-reviews cornelisnetworks/ifs-all` |
| `--pr-hygiene REPO` | Full PR hygiene report | `python github_utils.py --pr-hygiene cornelisnetworks/ifs-all --days 5` |
| `--naming-compliance REPO` | Branch/PR naming compliance | `python github_utils.py --naming-compliance cornelisnetworks/ifs-all` |
| `--merge-conflicts REPO` | Find PRs with merge conflicts | `python github_utils.py --merge-conflicts cornelisnetworks/ifs-all` |
| `--ci-failures REPO` | Find PRs with failing CI | `python github_utils.py --ci-failures cornelisnetworks/ifs-all` |
| `--stale-branches REPO` | Find stale branches | `python github_utils.py --stale-branches cornelisnetworks/ifs-all --branch-stale-days 60` |
| `--extended-hygiene REPO` | Full extended report (all scans) | `python github_utils.py --extended-hygiene cornelisnetworks/ifs-all` |
| `--rate-limit` | Show API rate limit status | `python github_utils.py --rate-limit` |

#### GitHub CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--state STATE` | open | PR state filter (`open`, `closed`, `all`) |
| `--limit N` | 100 | Maximum number of results |
| `--days N` | 5 | Staleness threshold in days |
| `--branch-stale-days N` | 30 | Branch staleness threshold in days |
| `--env FILE` | — | Alternate `.env` file |
| `--quiet` / `-q` | off | Suppress stdout (log file still written) |
| `--json` | off | Output as JSON instead of tables |
| `--verbose` / `-v` | off | Enable verbose console logging |

## Directory Structure

```text
agents/drucker/
├── README.md              # This file
├── __init__.py
├── agent.py               # Core DruckerCoordinatorAgent (tick, polling, analysis)
├── api.py                 # FastAPI endpoints (port 8201)
├── models.py              # DruckerRequest, DruckerFinding, DruckerAction, DruckerHygieneReport
├── cli.py                 # Standalone CLI (drucker-agent entry point)
├── tools.py               # Agent tool wrappers
├── config/
│   ├── polling.yaml       # Polling job definitions
│   └── monitor.yaml       # Validation rules
├── prompts/
│   └── system.md          # Agent behavior prompt
├── state/
│   ├── __init__.py
│   ├── report_store.py    # Hygiene report persistence
│   ├── monitor_state.py   # Monitor state tracking
│   └── learning_store.py  # Learning from past findings
└── docs/
    └── PLAN.md            # Detailed technical plan
```