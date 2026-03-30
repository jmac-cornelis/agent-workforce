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

## Running the Agent

You can run Drucker in several ways depending on your needs.

### Docker

Run via Docker Compose (exposes port 8201):

```bash
docker compose up drucker
```

### Local API Server

Run the FastAPI application locally:

```bash
uvicorn agents.drucker.api:app --host 0.0.0.0 --port 8201
```

### Polling Job

Start the polling loop for automated monitoring:

```bash
python pm_agent.py --workflow drucker-poll --poll-interval 300 --max-cycles 0 --github-repos cornelisnetworks/ifs-all
```

### CLI Execution

Execute specific scans directly from the command line:

```bash
python github_utils.py --extended-hygiene cornelisnetworks/ifs-all
```

## Directory Structure

```text
agents/drucker/
├── README.md              # This file
├── __init__.py
├── agent.py               # Core DruckerCoordinatorAgent (tick, polling, analysis)
├── api.py                 # FastAPI endpoints (port 8201)
├── models.py              # DruckerRequest, DruckerFinding, DruckerAction, DruckerHygieneReport
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