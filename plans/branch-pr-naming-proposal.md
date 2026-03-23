# Proposal: Branch and PR Naming Requirements for Jira Automation

**Author:** John Macdonald  
**Date:** March 23, 2026  
**Status:** Draft — for team review

---

## Problem Statement

Our Jira-GitHub automation relies on branch names containing a Jira ticket key
(e.g. `STL-76966`) to automatically link PRs to tickets and transition ticket
status on merge. Current adoption data shows:

- **31% of ticket transitions** are automated (via scm-bot); 69% are still manual
- **Only 29% of new feature branches** include a Jira ticket in the name
- Several repos have near-zero compliance (swvl at 6%, cn-forge-sw at 0%)

At the same time, the team has raised valid concerns about the current "put the
ticket in the branch name" approach:

1. **Multi-PR features** (Bob C.): Archana's dual-plane work is split across many
   small PRs under one Jira story. She shouldn't need the ticket in every sub-branch,
   and merging each sub-PR shouldn't transition the main ticket.

2. **Dev branches are free** (Mike B.): You can't stop people from making their own
   dev branches in git. The automation should only care about the branch that gets
   merged to main.

3. **Trivial fixes** (Ben L.): A typo in a log message or a one-line fix shouldn't
   require creating a Jira ticket first. That's overhead that discourages quick
   improvements.

All three points are valid. This proposal addresses them while improving
automation coverage.

---

## Proposed Rule

**The PR targeting `main` (or a release branch) must reference a Jira ticket in
its title.** Not the branch name. Not every branch. Just the PR that lands.

This is a shift from "branch naming requirement" to "PR title requirement" —
it's lighter, catches the right moment (merge to main), and accommodates all
three concerns above.

---

## How It Works

### Normal Feature Work

```
Branch:   STL-76966/dual-plane-part2
PR Title: STL-76966: Dual Plane Part 2 — fi_opx_addr and shm changes
Target:   main
Result:   ✅ Automation links PR to Jira, transitions ticket on merge
```

### Multi-PR Feature (Archana's Pattern)

```
Feature branch:  STL-76966/dual-plane
  ├── archana/dual-plane-shm      → PR to STL-76966/dual-plane  (ignored)
  ├── archana/dual-plane-reliab    → PR to STL-76966/dual-plane  (ignored)
  └── archana/dual-plane-stripe    → PR to STL-76966/dual-plane  (ignored)

Final PR: STL-76966/dual-plane     → PR to main
Result:   ✅ Only the final merge to main triggers automation
          Sub-PRs to the feature branch are invisible to the automation
```

### Dev / Scratch Branches (Mike's Point)

```
Branch:   bob/experiment-cq-perf
Result:   ❌ No PR to main → automation never sees it
          Developers can create unlimited personal branches freely
```

### Typo / One-Liner (Ben's Point)

```
Branch:   fix/typo-log-msg
PR Title: [NO-JIRA] Fix typo in error log message
Target:   main
Result:   ⚠️ Allowed — [NO-JIRA] prefix explicitly opts out
          PR merges, no Jira activity generated
```

---

## Bug Ticket Branch Requirement

**All bug fix branches MUST include the bug ticket key in the branch name.**
This is stricter than the general PR title rule because bug traceability is
non-negotiable — every bug fix must be traceable from Jira to the exact
branch, commits, and PR that resolved it.

### Format

```
STL-76942/fix-lustre-bufcount-zero
STL-76950/bulksvc-cleanup-crash
```

### Why Stricter Than Features?

- **Audit trail**: Customers and field support need to trace a fix back to the
  exact code change. Branch name → PR → commits → Jira ticket must be an
  unbroken chain.
- **Cherry-pick tracking**: Bug fixes are frequently cherry-picked across
  release branches (12.1.2.x, 12.2.0.x, etc.). The ticket in the branch name
  makes it immediately clear which fix is being picked.
- **Release notes automation**: Release notes are generated from merged PRs
  tagged with bug tickets. If the branch doesn't have the ticket, the fix
  may be missed in release notes.
- **`[NO-JIRA]` is NOT allowed for bug fixes.** If you're fixing a bug, there
  must be a ticket. No exceptions.

### Enforcement

The PR title check (Tier 1 below) catches this at merge time, but for bugs
we additionally recommend a branch name check on push. The GitHub Action
includes an optional strict mode for repos that want to enforce branch naming
for bug-type tickets.

---

## The Three Tiers

### Tier 1: Required (enforced by GitHub branch protection)

PRs targeting `main` or `release-*` branches **must** contain one of:

- A Jira ticket key: `STL-XXXXX` or `STLSW-XXXXX`
- An explicit opt-out: `[NO-JIRA]` (**not permitted for bug fixes**)

This is enforced by a lightweight GitHub Actions check on PR open/edit. If
neither pattern is present, the merge is blocked with a clear error message
explaining the requirement.

### Tier 2: Recommended for features / Required for bugs

- Branch name includes `STL-XXXXX` → automation auto-links the PR to Jira and
  transitions the ticket on merge to main
- Branch name doesn't include it, but PR title does → automation still links
  from the PR title
- Both work. Branch naming is convenient (auto-populates the PR title in
  GitHub), but not mandatory.

### Tier 3: Opt-Out (explicit and auditable)

- `[NO-JIRA]` in the PR title signals "this change doesn't need a ticket"
- Intended for: typo fixes, log message corrections, comment updates, trivial
  dependency bumps, formatting-only changes
- These PRs merge without generating any Jira activity
- A weekly report flags `[NO-JIRA]` PR volume per repo so PMs can audit if
  the escape hatch is being overused

---

## Transition Rules

| Event | Automation Action |
|---|---|
| PR opened targeting `main` with `STL-XXXXX` | Link PR to Jira ticket |
| PR merged to `main` with `STL-XXXXX` | Transition ticket (e.g. Open → In Progress, or In Progress → Verify) |
| PR opened targeting a feature branch | **No action** — sub-PRs are invisible |
| PR merged to a feature branch | **No action** |
| PR with `[NO-JIRA]` merged to `main` | **No action** — logged for audit only |

This means Archana can merge 10 sub-PRs into her feature branch without
triggering 10 Jira transitions. Only the final merge to main moves the ticket.

---

## What Changes for Developers

| Today | After This Proposal |
|---|---|
| "Put the ticket in the branch name" (unenforced) | "Put the ticket in the PR title" (enforced on merge) |
| Branch name is the only way automation finds the ticket | PR title works too — branch name is optional convenience |
| Typo fix → create a Jira ticket or skip automation | Typo fix → use `[NO-JIRA]` prefix, no ticket needed |
| Sub-PRs to feature branches may trigger automation | Sub-PRs are completely ignored |
| No enforcement → 29% compliance | Merge gate → 100% compliance (with explicit opt-out) |
| No visibility into opt-outs | Weekly `[NO-JIRA]` audit report |

---

## Implementation Plan

### Phase 1: PR Title Validation (GitHub Action)

Add a shared GitHub Action to all monitored repos that runs on
`pull_request: [opened, edited, synchronize]`:

```yaml
name: PR Title Check
on:
  pull_request:
    types: [opened, edited, synchronize]
    branches: [main, 'release-*']

jobs:
  check-title:
    runs-on: ubuntu-latest
    steps:
      - name: Validate PR title contains Jira ticket or NO-JIRA
        run: |
          TITLE="${{ github.event.pull_request.title }}"
          if echo "$TITLE" | grep -qEi '(STL|STLSW)-[0-9]+|\[NO-JIRA\]'; then
            echo "✅ PR title is compliant: $TITLE"
          else
            echo "❌ PR title must contain a Jira ticket (STL-XXXXX) or [NO-JIRA]"
            echo "   Got: $TITLE"
            echo ""
            echo "Examples:"
            echo "  STL-76966: Dual Plane Part 2 — fi_opx_addr changes"
            echo "  [NO-JIRA] Fix typo in error log message"
            exit 1
          fi
```

This is ~20 lines of YAML, deployed via the scm-jenkins-shared-library or
directly to each repo's `.github/workflows/`.

### Phase 2: Extend Webhook Automation

Update the existing Jira-GitHub webhook to also parse the PR title (not just
the branch name) for the ticket key. This is a fallback for cases where the
developer puts the ticket in the PR title but not the branch name.

### Phase 3: Transition Scope Filter

Configure the automation to **only fire transitions on merges to `main` or
`release-*` branches**. Merges to feature branches (e.g. `STL-76966/dual-plane`)
produce no Jira activity.

### Phase 4: Weekly NO-JIRA Audit

Add a weekly report (via the existing daily_report infrastructure) that lists:

- Count of `[NO-JIRA]` PRs per repo
- Count of `[NO-JIRA]` PRs per author
- Flagging if any single author or repo exceeds a threshold (e.g. >5/week)

---

## Rollout

| Week | Action |
|---|---|
| 1 | Deploy PR title check in **warning mode** (posts comment but doesn't block) to all 22 monitored repos |
| 2 | Announce policy to the team, address questions |
| 3 | Switch to **enforced mode** (blocks merge without ticket or `[NO-JIRA]`) |
| 4 | Deploy transition scope filter (main/release only) and NO-JIRA audit report |

---

## FAQ

**Q: Do I need to change my branch naming?**  
A: No. If you already put `STL-XXXXX` in your branch name, nothing changes for
you. The PR title gets auto-populated from the branch name in GitHub, so the
check passes automatically.

**Q: What if I forget the ticket in the PR title?**  
A: The check runs immediately on PR open. You'll see a clear error message with
examples. Just edit the PR title to add the ticket key — the check re-runs
automatically.

**Q: Can I still make personal dev branches without tickets?**  
A: Yes. Branch creation is completely unrestricted. The check only runs when
you open a PR targeting `main` or a release branch.

**Q: What about hotfix / bug fix branches?**  
A: Bug fixes have a stricter rule — the branch name MUST include the bug ticket
key (e.g. `STL-76942/fix-lustre-bufcount`). `[NO-JIRA]` is not allowed for
bug fixes. If you're fixing a bug, there must be a ticket — no exceptions.

**Q: Will sub-PRs to my feature branch be blocked?**  
A: No. The check only runs on PRs targeting `main` or `release-*`. PRs
between feature branches have no restrictions.

**Q: What if multiple PRs reference the same Jira ticket?**  
A: That's fine and expected (Archana's pattern). The ticket transitions on
the **final merge to main**, not on every PR that references it.

**Q: What if I'm working on something exploratory with no ticket yet?**  
A: Work on your branch freely. When you're ready to PR to main, either create
a ticket at that point or use `[NO-JIRA]` if it's trivial. The gate is at
merge time, not at branch creation time.
