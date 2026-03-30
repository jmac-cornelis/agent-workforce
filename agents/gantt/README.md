# Gantt: Project Planner Agent

## Overview

Gantt is the project planning agent for the Cornelis Networks platform. Its job is to provide clear, evidence-backed planning recommendations by analyzing your Jira work state alongside actual technical progress.

Rather than replacing human project managers, Gantt makes planning highly visible and data-driven. It connects work items to real-world evidence from builds, tests, and releases to produce milestone proposals, dependency maps, and risk signals.

Gantt treats Jira as the source of truth for work tracking. It reads your Jira epics, stories, bugs, priorities, and workflow states, then cross-references them with evidence from other agents across the platform to help you plan with confidence.

## Quick Start

Gantt runs as an on-demand planning service. You can interact with it through the Shannon Teams bot or via its REST API.

If you want to run Gantt locally for testing:
```bash
# Using Docker
docker compose up gantt

# Using Uvicorn directly
uvicorn agents.gantt.api:app --host 0.0.0.0 --port 8202
```

To run the polling worker:
```bash
python pm_agent.py --workflow gantt-poll --poll-interval 300
```

## Shannon Commands

You can interact with Gantt directly in Microsoft Teams using the Shannon bot. When you send a mutation command (like creating a snapshot), Shannon will first perform a "dry run" and show you a preview of what will happen. To actually execute the command, append `execute` to your message.

| Command | Description |
|---------|-------------|
| `/planning-snapshot` | Create a new planning snapshot based on current Jira state and technical evidence. |
| `/planning-snapshots` | List all stored planning snapshots for review. |
| `/release-monitor` | Create a new release monitor report to check the health and progress of an upcoming release. |
| `/release-reports` | List all stored release monitor reports. |
| `/release-report` | Get the details of a specific release monitor report. |
| `/release-survey` | Create a release execution survey to evaluate delivery performance. |
| `/release-survey-reports` | List all stored release surveys. |
| `/release-survey-report` | Get the details of a specific release survey. |

**Standard Commands:**
Like all agents, Gantt also supports the standard operational commands: `/stats`, `/busy`, `/work-today`, `/token-status`, `/decision-tree`, and `/why {decision-id}`.

### Command Examples

```text
@Shannon /planning-snapshot PROJ-123
@Shannon /planning-snapshots
@Shannon /release-monitor v2.4.0
@Shannon /release-monitor v2.4.0 execute
```

## CLI Commands

### Standalone CLI (`gantt-agent`)

Gantt has its own standalone CLI for direct access without going through `pm_agent.py`:

```bash
gantt-agent <command> [options]
```

| Command | Description | Example |
|---------|-------------|---------|
| `snapshot` | Create a planning snapshot | `gantt-agent snapshot --project STL` |
| `snapshot-get` | Load a stored snapshot | `gantt-agent snapshot-get --snapshot-id abc123` |
| `snapshot-list` | List stored snapshots | `gantt-agent snapshot-list --project STL` |
| `release-monitor` | Release health monitoring | `gantt-agent release-monitor --project STL --releases v2.4.0` |
| `release-monitor-get` | Load a stored release report | `gantt-agent release-monitor-get --report-id abc123` |
| `release-monitor-list` | List stored release reports | `gantt-agent release-monitor-list --project STL` |
| `release-survey` | Release execution survey | `gantt-agent release-survey --project STL --releases v2.4.0` |
| `release-survey-get` | Load a stored survey | `gantt-agent release-survey-get --survey-id abc123` |
| `release-survey-list` | List stored surveys | `gantt-agent release-survey-list --project STL` |
| `poll` | Scheduled planning and monitoring | `gantt-agent poll --project STL --poll-interval 300` |

#### Standalone CLI Examples

```bash
# Create a planning snapshot with JSON output
gantt-agent snapshot --project STL --planning-horizon 90 --json

# Release health check across two releases
gantt-agent release-monitor --project STL --releases v2.4.0,v2.5.0

# Continuous polling with release monitoring and Shannon notifications
gantt-agent poll --project STL \
  --releases v2.4.0 --run-release-monitor --run-release-survey \
  --poll-interval 600 --max-cycles 0 --notify-shannon

# Export a release monitor report with evidence
gantt-agent release-monitor --project STL \
  --releases v2.4.0 --evidence build_results.json test_summary.yaml \
  --output reports/release_health.json

# List recent snapshots
gantt-agent snapshot-list --project STL --limit 10

# Use alternate env file
gantt-agent snapshot --project STL --env /path/to/production.env
```

### Workflows (via `pm_agent.py`)

The same functionality is also available through `pm_agent.py`:

| Workflow | Example |
|----------|---------|
| `gantt-snapshot` | `python pm_agent.py --workflow gantt-snapshot -p STL` |
| `gantt-snapshot-get` | `python pm_agent.py --workflow gantt-snapshot-get --snapshot-id abc123` |
| `gantt-snapshot-list` | `python pm_agent.py --workflow gantt-snapshot-list -p STL` |
| `gantt-release-monitor` | `python pm_agent.py --workflow gantt-release-monitor -p STL --releases v2.4.0` |
| `gantt-release-monitor-get` | `python pm_agent.py --workflow gantt-release-monitor-get --report-id abc123` |
| `gantt-release-monitor-list` | `python pm_agent.py --workflow gantt-release-monitor-list -p STL` |
| `gantt-release-survey` | `python pm_agent.py --workflow gantt-release-survey -p STL --releases v2.4.0` |
| `gantt-release-survey-get` | `python pm_agent.py --workflow gantt-release-survey-get --survey-id abc123` |
| `gantt-release-survey-list` | `python pm_agent.py --workflow gantt-release-survey-list -p STL` |
| `gantt-poll` | `python pm_agent.py --workflow gantt-poll -p STL --poll-interval 300` |

#### Options Reference

| Option | Default | Description |
|--------|---------|-------------|
| `--project` / `-p` | — | Jira project key (required for most commands) |
| `--planning-horizon DAYS` | 90 | Planning horizon in days for snapshots |
| `--releases CSV` | — | Comma-separated release names |
| `--scope-label LABEL` | — | Jira scope label filter |
| `--survey-mode MODE` | feature-dev | Survey mode (`feature-dev` or `bug`) |
| `--run-release-monitor` | off | Include release monitoring in polling |
| `--run-release-survey` | off | Include release surveys in polling |
| `--include-done` | off | Include done/closed issues |
| `--no-gap-analysis` | off | Disable roadmap gap analysis |
| `--no-bug-report` | off | Disable bug status/priority summary |
| `--no-velocity` | off | Disable velocity metrics |
| `--no-readiness` | off | Disable readiness assessment |
| `--no-compare-previous` | off | Disable previous-report delta comparison |
| `--snapshot-id ID` | — | Stored snapshot ID |
| `--report-id ID` | — | Stored report ID |
| `--survey-id ID` | — | Stored survey ID |
| `--evidence FILE...` | — | Evidence files (JSON, YAML, Markdown) |
| `--poll-interval SECS` | 300 | Polling interval in seconds |
| `--max-cycles N` | 1 | Number of polling cycles (`0` = continuous) |
| `--notify-shannon` | off | Post summaries through Shannon |
| `--shannon-url URL` | localhost:8200 | Shannon service base URL |
| `--output FILE` | auto | Output filename |
| `--limit N` | 200 | Maximum issues or snapshots to return |
| `--json` | off | Output as JSON instead of formatted text |
| `--env FILE` | `.env` | Alternate environment file |

## What Gantt Does

Gantt analyzes several sources of truth to build its recommendations:

*   **Jira State:** Epics, stories, bugs, priorities, assignees, and workflow status.
*   **Technical Evidence:** Build records, test outcomes, release readiness, and traceability data from other agents.
*   **Decisions:** Action items and choices captured from meeting summaries.

Using this data, Gantt produces:

1.  **Planning Snapshots:** A durable record of project state at a specific point in time, linking planned work to technical evidence.
2.  **Dependency Views:** Maps of explicit and inferred dependencies between work items, highlighting missing predecessors or blocked work.
3.  **Milestone Proposals:** Recommendations for grouping work into milestones or release trains based on readiness and dependencies.
4.  **Risk Signals:** Alerts about stale work, blocked dependencies, or schedule drift.

**Planning Rules:**
Gantt follows strict rules when making recommendations. It will always cite the evidence it used. Technical work that lacks linked build or test evidence is treated with lower confidence. Blocked dependencies are flagged before any schedule promises are made.

## API Reference

Gantt exposes a REST API on port 8202 for programmatic access.

*   `POST /v1/planning/snapshot` — Create a planning snapshot
*   `GET /v1/planning/snapshots` — List snapshots
*   `GET /v1/planning/snapshot/{snapshot_id}` — Get a specific snapshot
*   `POST /v1/release-monitor/run` — Run the release monitor
*   `GET /v1/release-monitor/reports` — List release reports
*   `GET /v1/release-monitor/report/{report_id}` — Get a specific report
*   `POST /v1/release-survey/run` — Run a release survey
*   `GET /v1/release-survey/reports` — List surveys
*   `GET /v1/release-survey/report/{report_id}` — Get a specific survey

## Directory Structure

```text
agents/gantt/
├── README.md               # This file
├── __init__.py
├── agent.py                # Core GanttProjectPlannerAgent logic
├── api.py                  # FastAPI endpoints (port 8202)
├── cli.py                  # Standalone CLI (gantt-agent command)
├── components.py           # Interpreters, Mappers, and Planners
├── models.py               # Data models (PlanningRequest, etc.)
├── tools.py                # Agent tool wrappers
├── prompts/
│   └── system.md           # LLM instructions
├── state/                  # Storage backends
│   ├── __init__.py
│   ├── dependency_review_store.py
│   ├── release_monitor_store.py
│   ├── release_survey_store.py
│   └── snapshot_store.py
└── docs/
    ├── PLAN.md             # Technical roadmap and architecture
    └── PM_IMPLEMENTATION_BACKLOG.md
```