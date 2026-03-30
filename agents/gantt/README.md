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