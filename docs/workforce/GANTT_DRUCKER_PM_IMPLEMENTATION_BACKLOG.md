# Gantt + Drucker PM Implementation Backlog

> **Generated**: 2026-03-25
> **Source branch evaluated**: `project-manager-agents`
> **Scope**: Planning & Delivery implementation backlog for `Gantt` and `Drucker`

---

## Purpose

This backlog turns the current evaluation into an execution plan for the Planning & Delivery slice of the agent workforce.

The governing decisions are:

1. We are building a full-fledged set of project management agents, not a collection of one-off utilities.
2. `Gantt` and `Drucker` are the enduring PM agent products. `release_tracker` and `ticket_monitor` are harvest sources, not permanent top-level agent identities.
3. Both agents must support two execution modes:
   - `one-shot`: explicit task execution from UI or API
   - `polling`: always-on service mode that periodically evaluates work and emits durable artifacts or notifications
4. The human-facing UI for each agent must be:
   - `Shannon` for Teams/channel operation
   - `pm_agent` for CLI operation
5. API, tool, MCP, Shannon, and CLI surfaces should stay aligned. No PM capability should exist in only one surface.

---

## Product Boundaries

### Gantt owns

- planning snapshots
- release-health snapshots
- milestone proposals
- dependency views
- backlog and release planning risk

### Drucker owns

- Jira intake hygiene
- issue metadata policy
- stale and misrouted work detection
- new-ticket evaluation
- review-gated Jira remediation actions

### Not in scope as standalone agents

- `ReleaseTrackerAgent`
- `TicketMonitorAgent`

These should be harvested into Gantt and Drucker respectively.

---

## Execution Model Contract

Both PM agents should implement the same service shape:

- `run_once(request)`: perform a specific one-shot task
- `tick(poller_spec)`: discover work for a scheduled cycle and run the appropriate one-shot tasks
- `run_poller(poller_spec)`: long-lived loop around `tick`
- `publish_result(...)`: send summaries to stores, APIs, Shannon, and CLI-friendly outputs

This keeps polling and one-shot behavior aligned and avoids separate code paths.

---

## Harvest Mapping

| Source branch artifact | Harvest target | Notes |
|---|---|---|
| `agents/release_tracker.py` | `agents/gantt_agent.py`, new `agents/gantt_api.py` | Keep release monitoring under Gantt |
| `config/release_tracker.yaml` | new `config/gantt_polling.yaml` or Gantt service config section | Rename around Gantt ownership |
| `state/learning.py` release snapshot and cycle-time pieces | new `state/gantt_release_monitor_store.py` | Do not keep mixed-use PM learning store |
| `agents/ticket_monitor.py` | `agents/drucker_agent.py`, `agents/drucker_api.py` | Fold intake and monitoring into Drucker |
| `core/monitoring.py` | `core/monitoring.py` | Deterministic policy engine is worth preserving |
| `state/monitor_state.py` | new `state/drucker_monitor_state.py` | Rename around Drucker ownership |
| `state/learning.py` intake-learning pieces | new `state/drucker_learning_store.py` | Split from Gantt release monitoring state |
| `notifications/jira_comments.py` | `notifications/jira_comments.py` | Keep, but route through Drucker policy gates |
| `ticket_monitor_cli.py` | `pm_agent.py` workflows | No separate top-level CLI |
| `release_tracker_cli.py` | `pm_agent.py` workflows | No separate top-level CLI |

---

## Wave 1 — Shared PM Runtime + Gantt Surface Parity

### Epic: PM-1 — Shared PM Agent Contract

| ID | Story | SP | Depends On | Write Scope | AC |
|---|---|---:|---|---|---|
| PM-1 | Define a shared PM agent execution contract for one-shot and polling modes. | 3 | — | `docs/workforce/GANTT_PROJECT_PLANNER_PLAN.md`, `docs/workforce/DRUCKER_JIRA_COORDINATOR_PLAN.md`, `docs/workforce/GANTT_DRUCKER_PM_IMPLEMENTATION_BACKLOG.md` | Both plans describe `run_once`, `tick`, and `run_poller`; one-shot and polling are explicitly supported for both agents |
| PM-2 | Add common CLI semantics for PM one-shot and polling-oriented workflows. | 5 | PM-1 | `pm_agent.py`, `README.md`, `docs/workflows.md` | `pm_agent` documents explicit one-shot workflows for Gantt and Drucker; operator-facing flags are consistent across both agents |
| PM-3 | Define Shannon command and notification conventions for PM agents. | 3 | PM-1 | `config/shannon/agent_registry.yaml`, `shannon/service.py`, `shannon/cards.py`, `docs/shannon-teams-setup.md` | Both agents have dedicated command families and proactive notification conventions documented and routable through Shannon |

### Epic: GAN-1 — Gantt Service Grade API

| ID | Story | SP | Depends On | Write Scope | AC |
|---|---|---:|---|---|---|
| GAN-1 | Create a dedicated Gantt API service instead of relying only on direct calls from tools and `pm_agent`. | 5 | PM-1 | new `agents/gantt_api.py`, `README.md`, `docs/workflows.md` | FastAPI service exists with planning and release-monitor endpoints; OpenAPI available; service can be run independently |
| GAN-2 | Expose release monitoring as a first-class Gantt tool and MCP surface. | 3 | GAN-1 | `tools/gantt_tools.py`, `tools/__init__.py`, `mcp_server.py`, `tests/test_mcp_server_gantt_char.py` | `create_release_monitor` is exported through tools and MCP and covered by characterization tests |
| GAN-3 | Separate Gantt release-monitor persistence from roadmap snapshot storage. | 5 | GAN-1 | new `state/gantt_release_monitor_store.py`, `tools/gantt_tools.py`, `agents/gantt_api.py`, `tests/test_gantt_tools_char.py` | Release-monitor artifacts are stored in a Gantt-specific store; no roadmap store reuse remains |
| GAN-4 | Add `pm_agent` workflows for release monitoring and report retrieval/listing. | 5 | GAN-2 | `pm_agent.py`, `README.md`, `docs/workflows.md` | CLI supports `gantt-release-monitor`, `gantt-release-monitor-get`, and `gantt-release-monitor-list` with output and persist options |

### Epic: GAN-2 — Gantt Release Monitoring Harvest

| ID | Story | SP | Depends On | Write Scope | AC |
|---|---|---:|---|---|---|
| GAN-5 | Harvest prior-snapshot delta comparison and historical release snapshot loading from the PM branch. | 5 | GAN-3 | `agents/gantt_agent.py`, `core/release_tracking.py`, new `state/gantt_release_monitor_store.py`, `tests/test_gantt_agent_char.py`, `tests/test_release_tracking.py` | Gantt release monitor compares against persisted prior snapshots for the same release scope and reports meaningful deltas |
| GAN-6 | Harvest cycle-time and readiness-support logic without preserving a generic PM learning store. | 8 | GAN-5 | `agents/gantt_agent.py`, `core/release_tracking.py`, new `state/gantt_release_monitor_store.py`, `tests/test_release_tracking.py` | Gantt readiness reports can consume stored cycle-time stats and produce richer readiness outputs than the current empty-cycle-time path |
| GAN-7 | Preserve export/report formatting from the release tracker where it improves operator usability. | 3 | GAN-5 | `agents/gantt_agent.py`, `tools/gantt_tools.py`, `pm_agent.py`, `tests/test_gantt_agent_char.py` | Gantt can return readable summary, JSON, and file-based report outputs without reviving a separate release-tracker CLI |

### Epic: GAN-3 — Gantt Polling + Shannon UI

| ID | Story | SP | Depends On | Write Scope | AC |
|---|---|---:|---|---|---|
| GAN-8 | Add scheduled refresh mode for planning snapshots and release-health snapshots. | 5 | GAN-5 | `agents/gantt_agent.py`, `agents/gantt_api.py`, new `config/gantt_polling.yaml`, `docs/workforce/GANTT_PROJECT_PLANNER_PLAN.md` | Gantt supports configured polling jobs for named project/release scopes and persists the outputs |
| GAN-9 | Add Shannon routing and cards for Gantt one-shot and proactive release/planning updates. | 5 | GAN-1 | `config/shannon/agent_registry.yaml`, `shannon/service.py`, `shannon/cards.py`, `tests/test_shannon_service_char.py` | Shannon can invoke Gantt commands and render planning/release-monitor cards; scheduled Gantt runs can post summaries to Teams |

---

## Wave 2 — Drucker Intake + Policy Convergence

### Epic: DRU-1 — Deterministic Intake Engine Harvest

| ID | Story | SP | Depends On | Write Scope | AC |
|---|---|---:|---|---|---|
| DRU-1 | Harvest deterministic field-validation rules and action recommendation logic from the PM branch. | 5 | PM-1 | new `core/monitoring.py`, `agents/drucker_agent.py`, `tests/test_drucker_agent_char.py`, new `tests/test_monitoring.py` | Drucker can evaluate individual issues for required/warn fields using deterministic policy rules |
| DRU-2 | Split PM-branch monitoring state into Drucker-owned persistent stores. | 5 | DRU-1 | new `state/drucker_monitor_state.py`, new `state/drucker_learning_store.py`, `agents/drucker_agent.py`, `tests/test_monitor_state.py`, `tests/test_learning.py` | Drucker stores checkpoints, validation history, and learning records in Drucker-specific state modules |
| DRU-3 | Add issue-level one-shot evaluation to Drucker API and CLI. | 5 | DRU-1 | `agents/drucker_api.py`, `agents/drucker_agent.py`, `pm_agent.py`, `docs/workflows.md` | Operators can run one-shot issue evaluation from API, Shannon, and `pm_agent` without invoking a project-wide hygiene report |
| DRU-4 | Fold daily/report modes into Drucker instead of preserving `ticket_monitor_cli.py`. | 5 | DRU-1 | `agents/drucker_agent.py`, `agents/drucker_api.py`, `pm_agent.py`, `shannon/cards.py`, `tests/test_drucker_agent_char.py` | Drucker exposes bug activity, intake report, and hygiene-report outputs as first-class Drucker capabilities |

### Epic: DRU-2 — Review-Gated Jira Writeback Policy

| ID | Story | SP | Depends On | Write Scope | AC |
|---|---|---:|---|---|---|
| DRU-5 | Adopt Jira comment notification helpers under Drucker policy control. | 3 | DRU-1 | new `notifications/base.py`, new `notifications/jira_comments.py`, `agents/drucker_agent.py`, `tests/test_notifications.py` | Drucker can emit safe comments and suggestions without duplicating comment logic; duplicate-post protection is covered by tests |
| DRU-6 | Convert Ticket Monitor direct field mutation into review-gated Drucker actions. | 8 | DRU-2, DRU-5 | `agents/drucker_agent.py`, `agents/drucker_models.py`, `agents/review_agent.py`, `tools/drucker_tools.py`, `tests/test_drucker_agent_char.py` | Suggested or learned field changes become proposed Drucker actions by default; auto-apply requires explicit policy and is auditable |
| DRU-7 | Add evidence-aware routing and likely-owner suggestions without crossing into Gantt planning behavior. | 5 | DRU-3 | `agents/drucker_agent.py`, `config/prompts/drucker_agent.md`, `tests/test_drucker_agent_char.py` | Drucker can recommend owners/components using org knowledge while staying focused on hygiene and routing rather than planning |

### Epic: DRU-3 — Drucker Polling + Shannon UI

| ID | Story | SP | Depends On | Write Scope | AC |
|---|---|---:|---|---|---|
| DRU-8 | Add always-on polling mode for new-ticket intake and scheduled hygiene scans. | 8 | DRU-2 | `agents/drucker_agent.py`, `agents/drucker_api.py`, new `config/drucker_polling.yaml`, `docs/workforce/DRUCKER_JIRA_COORDINATOR_PLAN.md` | Drucker supports polling jobs for new-ticket scans and stale/incomplete-work scans with checkpointing and durable records |
| DRU-9 | Extend Shannon command coverage for issue-check, hygiene, and bug-activity workflows. | 5 | DRU-3, DRU-4 | `config/shannon/agent_registry.yaml`, `shannon/service.py`, `shannon/cards.py`, `tests/test_shannon_service_char.py` | Teams users can invoke Drucker one-shot checks and receive proactive hygiene summaries through Shannon |

---

## Wave 3 — Unified PM UX, Tests, and Cleanup

### Epic: PM-2 — Surface Parity and Migration

| ID | Story | SP | Depends On | Write Scope | AC |
|---|---|---:|---|---|---|
| PM-4 | Align API, `tools/`, MCP, Shannon, and CLI surface naming for Gantt and Drucker. | 5 | GAN-9, DRU-9 | `README.md`, `docs/workflows.md`, `tools/__init__.py`, `mcp_server.py`, `config/shannon/agent_registry.yaml` | The same core capabilities are reachable from all supported surfaces with consistent names |
| PM-5 | Add migration guidance showing that `release_tracker` and `ticket_monitor` were harvested rather than productized. | 3 | PM-4 | `README.md`, `docs/agent-usefulness-and-applications.md`, `docs/workforce/README.md`, `docs/workforce/GANTT_DRUCKER_PM_IMPLEMENTATION_BACKLOG.md` | Docs explain the harvest path, enduring ownership, and why no separate top-level PM tracker/monitor agents remain |
| PM-6 | Consolidate and retarget PM-branch tests under Gantt and Drucker identities. | 8 | GAN-7, DRU-9 | `tests/test_gantt_agent_char.py`, `tests/test_drucker_agent_char.py`, new `tests/test_release_tracking.py`, new `tests/test_monitoring.py`, new `tests/test_learning.py`, new `tests/test_monitor_state.py`, `tests/test_cli_entry_points.py` | Test coverage exists for one-shot mode, polling mode, Shannon routing, CLI workflows, and persistence behavior |
| PM-7 | Remove or archive branch-specific standalone identities from user-facing docs once parity is complete. | 2 | PM-5, PM-6 | `README.md`, `docs/workflows.md`, `docs/agent-usefulness-and-applications.md` | No user-facing doc presents `ticket_monitor` or `release_tracker` as enduring top-level PM agents |

---

## Recommended Delivery Order

1. `PM-1`, `PM-2`, `PM-3`
2. `GAN-1`, `GAN-2`, `GAN-3`, `GAN-4`
3. `GAN-5`, `GAN-6`, `GAN-7`
4. `DRU-1`, `DRU-2`, `DRU-3`, `DRU-4`
5. `DRU-5`, `DRU-6`, `DRU-7`
6. `GAN-8`, `GAN-9`, `DRU-8`, `DRU-9`
7. `PM-4`, `PM-5`, `PM-6`, `PM-7`

This order gets Gantt service parity first, then folds the more mutation-sensitive Ticket Monitor logic into Drucker with policy boundaries intact.

---

## Exit Criteria

This backlog is complete when all of the following are true:

- Gantt and Drucker are the only public PM agent identities for this slice
- both agents support one-shot and polling execution modes
- both agents are operable from Shannon and `pm_agent`
- both agents have aligned API, tool, and MCP surfaces
- both agents persist durable outputs and polling history
- review-gated write-back remains explicit for non-trivial Jira mutations
- user-facing docs no longer describe `release_tracker` or `ticket_monitor` as standalone PM agent products
