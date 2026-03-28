# Proposal: GitHub PR Hygiene Scans via the Drucker Agent

Date: 2026-03-28
Status: Draft proposal
Audience: Development, PM, release engineering

## Problem Statement

Pull requests on our GitHub repositories have no automated lifecycle hygiene.
PRs go stale without notification, review requests languish, and there is no
systematic way to nudge PR originators when their work sits idle.

Today the only GitHub-Jira integration is the branch-naming automation (see
`plans/branch-pr-naming-proposal.md`), which handles forward linking from Git
to Jira. There is nothing that looks backward at PR state and flags problems.

Meanwhile, Drucker already runs scheduled hygiene scans against Jira and
delivers findings through Shannon. Extending Drucker to scan GitHub PRs is
the lowest-friction path to coverage because the polling infrastructure,
notification pipeline, and review-gated action model are already in place.

## Goals

1. Notify PR originators when their PRs are older than a configurable
   threshold (default: 5 days with no update).
2. Deliver notifications through Shannon (Teams), matching the existing
   Drucker notification pattern.
3. Follow the existing `drucker-poll` / `gantt-poll` scheduling model so
   GitHub scans run on the same cadence infrastructure.
4. Keep Drucker's Jira hygiene and GitHub hygiene loosely coupled so each
   can be enabled or disabled independently.
5. Establish an extensible scan framework so additional GitHub hygiene
   checks can be added incrementally.

## Current State

### Drucker Infrastructure (Ready)

| Component | Path | Status |
|---|---|---|
| Polling config | `config/drucker_polling.yaml` | Production — 2 Jira job types |
| Polling loop | `agents/drucker_agent.py` `tick()` / `run_poller()` | Production |
| Shannon notify | `agents/pm_runtime.py` `notify_shannon()` | Production |
| Report store | `state/drucker_report_store.py` | Production |
| Monitor state | `state/drucker_monitor_state.py` | Production |

### GitHub Infrastructure (Skeleton)

| Component | Path | Status |
|---|---|---|
| Adapter ABC | `adapters/github/adapter.py` | Skeleton — 4 abstract methods |
| REST adapter | `adapters/github/adapter.py` `GitHubRESTAdapter` | Stub — all `NotImplementedError` |
| Webhook receiver | `adapters/github/webhook.py` | Partial — HMAC verification works, event bus TODO |
| PR event model | `adapters/github/adapter.py` `PREvent` | Complete |

### What Needs to Be Built

1. **`list_open_pull_requests()`** on `GitHubAdapter` / `GitHubRESTAdapter` — new
   abstract + concrete method to fetch open PRs for a given repo with age and
   review-state metadata.
2. **GitHub scan job type** in `config/drucker_polling.yaml` — a new job entry
   alongside the existing `hygiene-scan` and `recent-ticket-intake` jobs.
3. **`analyze_github_pr_hygiene()`** on `DruckerCoordinatorAgent` — scan method
   that follows the same pattern as `analyze_project_hygiene()` but targets
   GitHub PRs instead of Jira tickets.
4. **GitHub-specific finding categories and actions** in the Drucker models.
5. **Shannon notification payload builder** for PR hygiene findings.

## Design

### Scan Architecture

The GitHub PR hygiene scan follows the same three-layer pattern as Jira scans:

```
config/drucker_polling.yaml     ← job definition
    │
    ▼
DruckerCoordinatorAgent.tick()  ← dispatches by job type
    │
    ├── Jira jobs → analyze_project_hygiene() / analyze_recent_ticket_intake()
    │
    └── GitHub jobs → analyze_github_pr_hygiene()   [NEW]
                          │
                          ▼
                      GitHubRESTAdapter.list_open_pull_requests()  [NEW]
                          │
                          ▼
                      _build_pr_findings() → _build_pr_actions()  [NEW]
                          │
                          ▼
                      notify_shannon()   ← existing path
```

### Polling Configuration

New job type in `config/drucker_polling.yaml`:

```yaml
jobs:
  - job_id: hygiene-scan
    description: Full-project hygiene scan for active work.
    recent_only: false

  - job_id: recent-ticket-intake
    description: Recent-ticket intake scan using Drucker checkpoint state.
    recent_only: true

  - job_id: github-pr-hygiene                          # NEW
    description: Scan open PRs for staleness and missing reviews.
    scan_type: github                                   # distinguishes from Jira jobs
    repos:                                              # list of org/repo targets
      - cornelisnetworks/opa-psm2
      - cornelisnetworks/opa-ff
    stale_pr_days: 5                                    # days with no update
    enabled: true
```

The `scan_type: github` field tells `tick()` to dispatch to the GitHub scan
path instead of the Jira path. Repos are listed explicitly rather than
discovered, matching the explicit `project_key` pattern for Jira jobs.

### GitHub Adapter Extension

Add to `GitHubAdapter` ABC and `GitHubRESTAdapter`:

```python
@abstractmethod
async def list_open_pull_requests(
    self,
    repo: str,
    *,
    state: str = 'open',
    sort: str = 'updated',
    direction: str = 'asc',
    per_page: int = 100,
) -> list[dict]:
    '''Return open PRs with metadata needed for hygiene analysis.'''
    ...
```

Each returned dict should include:
- `number`, `title`, `author` (login), `created_at`, `updated_at`
- `requested_reviewers` (list of logins)
- `review_state` (approved, changes_requested, pending, none)
- `draft` (bool)
- `head_branch`, `base_branch`
- `mergeable_state` (clean, dirty, unknown)
- `labels` (list of label names)
- `html_url`

### Finding Categories

Phase 1 (this proposal):

| Category | Severity | Trigger |
|---|---|---|
| `stale_pr` | medium (high if >10 days) | PR has no update in `stale_pr_days` |
| `missing_review` | medium | PR has no requested reviewers and no approvals |

Phase 2 (future, listed for design foresight):

| Category | Severity | Trigger |
|---|---|---|
| `review_request_stale` | medium | Review requested but no response in N days |
| `pr_naming_noncompliant` | low | PR title/branch doesn't match naming policy |
| `draft_pr_stale` | low | Draft PR with no update in 2x `stale_pr_days` |
| `merge_conflict` | high | PR has merge conflicts with base branch |
| `stale_branch` | low | Branch with no PR, no commits in 30+ days |
| `pr_too_large` | medium | PR diff exceeds configurable line threshold |
| `ci_failure_unresolved` | high | CI failing for >2 days with no commits |

### Notification Format

Shannon notification for stale PR findings:

```
Title: Drucker GitHub PR Hygiene — cornelisnetworks/opa-psm2
Text: 3 findings across 2 PRs
Body:
  - PR #1234 (alice): "Add dual-plane SHM support" — no update in 8 days
  - PR #1267 (bob): "Fix OFI endpoint cleanup" — no update in 6 days, no reviewers assigned
  - Scan covered 12 open PRs across 1 repo
```

### Jira Cross-Reference (Optional Enhancement)

When the PR branch name contains a Jira ticket key (per the naming convention),
the finding can be enriched with Jira ticket metadata. This links the GitHub
hygiene finding to the Jira work item, enabling Drucker to:

- Flag Jira tickets whose linked PRs are stale
- Include PR staleness in Jira hygiene reports
- Suggest Jira comments noting the stale PR

This cross-referencing is not required for Phase 1 but the finding model
should include an optional `jira_ticket_key` field to support it later.

## Implementation Phases

### Phase 1 — Stale PR Notifications (This Proposal)

Scope:
1. Implement `list_open_pull_requests()` on `GitHubRESTAdapter`
2. Add `github-pr-hygiene` job type to polling config
3. Add `analyze_github_pr_hygiene()` to `DruckerCoordinatorAgent`
4. Add `stale_pr` and `missing_review` finding categories
5. Wire Shannon notification for GitHub findings
6. Add config knobs: `stale_pr_days`, `repos`, `enabled`
7. Unit tests following the `_char` pattern

Deliverables:
- Working stale-PR scan in the Drucker polling loop
- Shannon notifications for stale PRs
- Config-driven repo list and staleness threshold

### Phase 2 — Extended GitHub Scans

Add the remaining scan types from the finding categories table above,
prioritized by team feedback. Each new scan type follows the same pattern:
new category constant, finding builder, action builder, test.

### Phase 3 — Extraction Decision Point

If GitHub scan types reach 4+, evaluate extracting GitHub hygiene into a
dedicated agent (working name: "Torvalds" or similar). The extraction would:
- Move GitHub-specific scan logic to `agents/workforce/torvalds/`
- Keep Drucker as the Jira-only coordinator
- Both agents share the Shannon notification pipeline
- Polling config splits into `drucker_polling.yaml` (Jira) and
  `torvalds_polling.yaml` (GitHub)

This extraction is not needed until the GitHub scan surface grows large enough
to warrant its own agent identity, prompt, and configuration namespace.

## Authentication

The `GitHubRESTAdapter` requires a GitHub token. Configuration follows the
existing pattern for external service credentials:

- Environment variable: `GITHUB_TOKEN`
- The adapter reads this at construction time
- For GitHub App authentication (future), the adapter would accept app ID
  and private key instead, but PAT is sufficient for Phase 1

## Testing Strategy

Follow the existing characterization test pattern (`tests/test_drucker_agent_char.py`):

- Mock `GitHubRESTAdapter.list_open_pull_requests()` to return canned PR data
- Verify finding generation: stale PRs produce `stale_pr` findings, PRs with
  no reviewers produce `missing_review` findings
- Verify notification payload format matches Shannon expectations
- Verify polling config parsing handles `scan_type: github` correctly
- No live GitHub API calls in tests

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| GitHub API rate limiting | Use conditional requests (If-Modified-Since), paginate conservatively, cache PR state between polls |
| Token permission scope | Document minimum required scopes (repo read, PR read) |
| Large repo PR volume | Config `per_page` limit, scan only explicitly listed repos |
| Notification fatigue | Configurable threshold, suppress repeat notifications for same PR within N hours |
| Drucker scope creep | Phase 3 extraction gate ensures Drucker doesn't grow unbounded |

## Relationship to Existing Plans

- **`plans/branch-pr-naming-proposal.md`**: The PR naming enforcement described
  there becomes a natural Phase 2 scan type (`pr_naming_noncompliant`). The
  audit report proposed in that document could be generated by Drucker's GitHub
  scan infrastructure rather than a standalone GitHub Action.

- **Linus code review agent**: Linus remains scoped to code quality review.
  GitHub lifecycle hygiene (staleness, review coverage) stays in Drucker.
  Linus may consume Drucker's PR metadata in the future but does not own it.

## Open Questions

1. Should stale-PR notifications tag the PR author directly in Teams, or just
   post to a channel? (Recommendation: channel first, direct tagging Phase 2.)
2. Should the scan cover all repos in the org, or only an explicit allowlist?
   (Recommendation: explicit allowlist via config, matching Jira's explicit
   `project_key` pattern.)
3. What is the right polling interval for GitHub scans? (Recommendation: once
   daily, separate from Jira's more frequent polling.)
