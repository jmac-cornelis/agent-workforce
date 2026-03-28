# 12.2 Release Cockpit — Combined Execution Plan

**Date:** 2026-03-26
**Author:** John Macdonald
**Status:** Draft
**Sources:** `12.2-release-cockpit-recommendations.md`, `STL_12_2_RELEASE_COCKPIT_BLUEPRINT.md`, `opencode_12.2-release-cockpit-steps.md`, `codex_12.2-release-cockpit-steps.md`, `STL_12_2_RELEASE_STATUS_PLAN_COMPARISON.md`

---

## What This Plan Is

This is the single execution plan for the 12.2.0.x release cockpit.

It combines everything from the survey-based analysis, the structural blueprint, the two step-by-step plans, and both comparison documents into one place. This document is self-contained. You should not need to go back to the source documents to execute it.

The job:

1. Make the key decisions about what 12.2 is.
2. Fix the Jira data that makes reporting wrong.
3. Build a Confluence page people will actually use.
4. Keep it honest about what is clean data and what is not.
5. Make this repeatable for the next release.

---

## The Most Important Rule

**Separate "Release Scope" from "Release Risk Backlog" everywhere.**

- **Release Scope** means tickets with `fixVersion = 12.2.0.x`. These are clearly assigned to the release.
- **Release Risk Backlog** means tickets without a fixVersion that probably affect 12.2, but nobody has confirmed yet.

Never combine these into one number. The moment you mix clean data with messy data, the page becomes something people argue about instead of something people use.

This rule applies to every table, every chart, every summary on the page. If a section shows a count, it must say which bucket it comes from.

---

## What We Know Right Now

These are the live numbers from Jira as of 2026-03-25.

**12.2.0.x Release Scope (fixVersion assigned):**
- 267 total tickets (154 bugs, 84 stories, 16 epics, 13 other)
- 100 bugs open (30 Open, 22 Closed, 21 Verify, 17 In Progress)
- 19 P0-Stopper, 17 P1-Critical
- Top bug components: JKR Host Driver (23), CN5000 FM (16), Chassis GUI (14), OFI OPX (10)

**Release Risk Backlog (unversioned, likely affects 12.2):**
- 319 CN6000 tickets with no fixVersion at all
- 582 STL bugs with no fixVersion
- Unknown number of P0/P1 bugs hiding in the unversioned pool

**Known Jira problems:**
- `12.2.0.x` version date is 2025-10-31 — five months stale
- STL-75304 claims to be the 12.2.1 release tracker but points at fixVersion `12.1.1.x` (wrong)
- STL-75299 claims to be the 12.3.0 release tracker but points at fixVersion `12.1.0.x` (wrong)
- CN6000 has no release-tracking root parallel to CN5000's STL-75294
- 8 stories in 12.2.0.x have no parent epic
- 3 feature tickets are tagged with multiple fixVersions (scope confusion)
- 7 open epics may be ready to close or need re-scoping
- 15+ components prefixed "Obsolete -" are still active in the project

---

## Readiness Checks

Use these to know when you are ready for the next phase.

### Before building the page

All of these should be true:

- The team agrees what 12.2 means (joint CN5000+CN6000 or CN5000-primary)
- The Jira hierarchy shape is decided (umbrella + two Initiative children, or two parallel roots)
- The release date is updated
- Product Family is declared the canonical scope field
- The broken release tracker tickets are fixed

### Before calling the page trustworthy

Most of these should be true:

- P0/P1 unversioned bugs have been triaged and versioned
- Orphan stories have parents
- CN6000 participation level is no longer a mystery
- The page clearly separates Release Scope from Risk Backlog

### Before investing in heavy automation

All of these should be true:

- The Jira filters are stable (not changing every week)
- The page layout is accepted by stakeholders
- People are actually using the page in weekly reviews

---

## Phase 1 — Decisions and Anchors (today)

These are conversations and small Jira edits, not engineering work. Nothing else in this plan works until these are done.

### Task 1. Decide what 12.2 is

Answer this question:

- Is `12.2.0.x` a real joint CN5000 + CN6000 release?
- Or is it mostly CN5000, with some CN6000 work riding along?

Why this matters: if it is joint, then the 319 unversioned CN6000 tickets need triage now. If it is CN5000-primary, CN6000 triage can wait and the page focuses on CN5000 delivery.

Owner: PM / Release Lead

### Task 2. Decide the Jira hierarchy shape

Recommendation: one top SW Release umbrella ticket for `12.2.0.x`, with two Initiative children underneath — one for CN5000, one for CN6000.

Plain meaning: one release, two family work buckets.

The alternative is two parallel release roots (one per family). That works too, but it makes rollup reporting harder.

Owner: PM / Release Lead

### Task 3. Decide what the page totals mean

Agree on these two display buckets before anyone builds anything:

- **Release Scope** — tickets with `fixVersion = 12.2.0.x`
- **Release Risk Backlog** — tickets without a fixVersion that probably belong in 12.2

Every number on the page will be labeled as one or the other. No mixing.

Owner: PM / Release Lead

### Task 4. Make Product Family the canonical scope field

`Product Family` (`customfield_28382` in prod, `customfield_28434` in sandbox) is the real source of truth for CN5000 vs CN6000.

Labels can still exist, but they should not drive the page. Tell the teams.

Owner: PM / Engineering Leads

### Task 5. Set a real release date on 12.2.0.x

The Jira version date is 2025-10-31. That is five months stale. Every velocity and readiness calculation depends on this number being real.

Set the actual target date.

Owner: PM / Release Lead

### Task 6. Fix the broken release tracker tickets

Two tickets are pointing at the wrong fixVersion:

| Ticket | Claims to be | Currently points at | Fix |
|--------|-------------|--------------------|----|
| STL-75304 | 12.2.1 tracker | `12.1.1.x` | Change to `12.2.0.x` |
| STL-75299 | 12.3.0 tracker | `12.1.0.x` | Change to `12.3.0.x` |

Owner: PM / Jira Admin

### Task 7. Create the CN6000 release-tracking root

CN5000 has STL-75294 as its release anchor. CN6000 needs the same kind of top-level ticket so the page can show both families fairly.

Create an Initiative or SW Release ticket parallel to STL-75294, matching whatever hierarchy shape was decided in Task 2.

Owner: PM / Release Lead

---

## Phase 2 — Data Repair

These tasks can run in parallel once Phase 1 decisions are made. They do not need to be done sequentially. Hand them to the right people and let them work at the same time.

### Task 8. Triage P0/P1 unversioned bugs

This is the minimum. The P0/P1 counts on the page cannot be trusted until this is done.

Query:
```
project = STL AND issuetype = Bug AND fixVersion is EMPTY
  AND priority in ("P0-Stopper", "P1-Critical")
  AND status not in (Closed, Done)
```

For each ticket: assign to `12.2.0.x`, `12.3.0.x`, or explicitly mark as backlog.

Owner: PM + Engineering Leads

### Task 9. Triage CN6000 unversioned tickets

There are 319 CN6000 tickets with no fixVersion. That is the single largest gap in release visibility.

Query:
```
project = STL AND "Product Family" = CN6000
  AND fixVersion is EMPTY AND status not in (Closed, Done)
```

For each ticket: assign to `12.2.0.x`, `12.3.0.x`, or backlog.

Do not try to do all 319 in one sitting. Have component owners work through their own subsets in manageable batches.

Owner: Component Leads (batched by component)

### Task 10. Parent the 8 orphan stories

These stories are in 12.2.0.x but have no parent epic. That means they do not roll up into any feature delivery view.

| Ticket | Action |
|--------|--------|
| STL-77053 | Confirm family, parent to epic, resolve multi-release (also in 12.3.0.x) |
| STL-76985 | Confirm family, parent to epic |
| STL-76978 | Confirm family, parent to epic |
| STL-76933 | Confirm family, parent to epic |
| STL-76673 | Confirm family, parent to epic |
| STL-76597 | Confirm family, parent to epic |
| STL-76596 | Confirm family, parent to epic |
| STL-76455 | Confirm family, parent to epic |

For each ticket: confirm the product family, pick the right epic, confirm it belongs in 12.2.0.x, set the parent.

Owner: Engineering Leads (per component)

### Task 11. Resolve the 3 multi-release feature tickets

These tickets are tagged with more than one fixVersion. That means they show up in multiple release views, which confuses scope counts.

| Ticket | Current fixVersions | Decision needed |
|--------|--------------------|-----------------| 
| STL-77053 | 12.2.0.x + 12.3.0.x | Keep in one release, move to the other, or split into two tickets |
| STL-77014 | 12.2.0.x + 14.0.0.x | Keep in one release, move to the other, or split into two tickets |
| STL-76300 | 12.2.0.x + 14.0.0.x | Keep in one release, move to the other, or split into two tickets |

Owner: PM

### Task 12. Review 7 open epics for closure or re-scoping

These epics are open in 12.2.0.x and may need attention.

| Epic | Current situation | Action |
|------|-------------------|--------|
| STL-68268 | Children appear closed | Review for closure |
| STL-69162 | Held open by STL-70348 only | Confirm whether there is real remaining work |
| STL-76008 | In Progress | Confirm remaining child work |
| STL-75423 | In Progress | Confirm remaining child work |
| STL-76300 | In Progress, also tagged 14.0.0.x | Resolve release intent |
| STL-75118 | Open | Confirm remaining child work |
| STL-70567 | In Progress | Confirm remaining child work |

For each epic: should it still be open? Is the remaining work really under this epic? Is the remaining work in the right release? Does this epic need to be closed, split, or cleaned up?

Owner: Engineering Leads

### Task 13. Archive obsolete components and normalize scope fields

- Archive 15+ components prefixed "Obsolete -" in the STL project.
- Communicate to all teams that `Product Family` is the canonical scope field (from Task 4).

Owner: Jira Admin / DevOps

---

## Phase 3 — Build the Cockpit

This can overlap with Phase 2. You do not need to wait for all data repair to finish before building the page. The page should be useful even while cleanup is ongoing — that is the whole point of the Release Scope vs Risk Backlog separation.

### Task 14. Create 22 saved JQL filters in Jira

All JQL definitions are in `12.2-release-cockpit-recommendations.md`, Section 7. Create them as shared filters visible to the release team.

**Feature delivery filters (5):**
- `12.2 Feature Dev - CN5000`
- `12.2 Feature Dev - CN6000`
- `12.2 Feature Dev - Shared`
- `12.2 Feature Dev - In Progress`
- `12.2 Feature Dev - Remaining`

**Bug readiness filters (6):**
- `12.2 Bugs - CN5000`
- `12.2 Bugs - CN6000`
- `12.2 Bugs - P0 P1 Open`
- `12.2 Bugs - Verify Queue`
- `12.2 Bugs - Multi Release`
- `12.2 Bugs - Stale`

**Hierarchy and critical path filters (3):**
- `12.2 Open Epics - CN5000`
- `12.2 Open Epics - CN6000`
- `12.2 Epic Closure Blockers`

**Data confidence filters (4):**
- `12.2 Orphan Stories`
- `12.2 Multi FixVersion Exceptions`
- `12.2 Missing Product Family`
- `12.2 No Assignee`

**Pipeline context filters (4):**
- `STL Active Releases`
- `CN6000 Unversioned`
- `STL Unversioned Bugs`
- `ASIC Dependencies`

Owner: DevOps

### Task 15. Build the Confluence page

Build the page with these 12 sections. Use Confluence Jira macros for the live sections. Write the narrative sections by hand for now.

| # | Section | What it shows | Live or manual |
|---|---------|---------------|----------------|
| 1 | Header | Release name, owner, health status, last refresh | Manual |
| 2 | Scope & Definitions | What "Release Scope" and "Risk Backlog" mean, what Product Family means | Static template |
| 3 | Executive Summary | One paragraph on release health, top risks, decisions needed | Manual narrative |
| 4 | Feature Delivery | Per-family feature breakdown (CN5000, CN6000, Shared) | Live Jira macros |
| 5 | Bug Readiness | Per-family bug breakdown, separate from features | Live Jira macros |
| 6 | P0/P1 Stopper Tracker | Open P0 and P1 bugs — first thing leadership reads | Live Jira macro |
| 7 | Component Health Matrix | Bug distribution by component — shows where the problems cluster | Live Jira macro or generated |
| 8 | Release Gates | Ship readiness beyond ticket counts (code freeze, test cycles, partner validation) | Manual table |
| 9 | Critical Path | Open epics and their remaining child work — what must close before ship | Generated epic-child analysis |
| 10 | Release Pipeline Context | Where 12.2 sits relative to 12.1.2.x, 12.3.0.x, etc. | Manual or generated |
| 11 | Data Confidence | Can the page be trusted? Orphan count, unversioned count, hygiene score | Generated from filters |
| 12 | Action Queue | Concrete cleanup actions, maintained weekly | Manual |

**Display rule:** every aggregate count on the page must clearly indicate whether it represents Release Scope or includes Risk Backlog. Apply this during page construction, not after.

Owner: DevOps / PM

### Task 16. Populate the Action Queue

Add the remaining cleanup items from Phase 2 that are not yet done. This becomes the standing weekly to-do list.

Owner: PM

---

## Phase 4 — Operationalize

Do this once the page exists and people are looking at it.

### Task 17. Schedule weekly gantt-release-monitor runs

```bash
pm_agent --workflow gantt-release-monitor --project-key STL --releases "12.2.0.x" --scope-label CN5000
pm_agent --workflow gantt-release-monitor --project-key STL --releases "12.2.0.x" --scope-label CN6000
```

This gives you side-by-side CN5000 vs CN6000 snapshots every week.

Owner: DevOps

### Task 18. Schedule weekly drucker-hygiene run

This automatically refreshes the Data Confidence section by identifying orphan tickets, hygiene issues, and stale data.

Owner: DevOps

### Task 19. Add milestone discipline

Pick one gate-tracking mechanism. Any of these will work:

- **Option A:** Label convention — `gate:feature-complete`, `gate:validation`, `gate:rc`, `gate:ga`
- **Option B:** Custom field — "Release Phase" dropdown
- **Option C:** Formalize existing labels — `sw_debugging`, `sw_critical_debugging` + add `sw_verification`, `sw_rc`

Apply the chosen mechanism to release umbrella tickets and critical-path epics.

Owner: PM / Release Lead

### Task 20. Make the cockpit the weekly release review source of truth

Each weekly review should include:

- Update the executive summary narrative
- Review P0/P1 changes since last week
- Review open epics and critical path
- Review Data Confidence findings
- Update the Action Queue

Do not let this become an extra page no one uses. It replaces whatever the team was using before.

Owner: PM / Release Lead

---

## Phase 5 — Automate (only after the page proves valuable)

Do not invest in this until the page layout is stable and people are actually using it every week.

| Task | What it does | What it powers |
|------|-------------|----------------|
| 21. Cross-product comparison | Extend gantt-release-monitor for CN5000 vs CN6000 diffs | Side-by-side family comparison |
| 22. Epic-child closure analysis | Automate "what blocks this epic from closing" | Critical Path section |
| 23. Confluence auto-publish | Use Confluence API to push generated sections | Zero-touch page refresh |
| 24. Trend charts | Bug open/close trend, P0/P1 over time, story burndown | Visual history |
| 25. Cross-project ASIC links | Create CN5AW/CYRAW → STL blocking links | ASIC dependency visibility |

---

## Critical Path

The minimum path to a useful cockpit:

**Tasks 1-5 → Task 8 → Task 14 → Task 15**

Everything else improves accuracy and trust in parallel.

Plain meaning: make the decisions, triage the worst bugs, create the filters, build the page. The rest is making it better over time.

---

## End Goal

The goal is not just to publish a page for 12.2.

The goal is to end up with:

- A release page people trust
- Jira tickets that roll up cleanly
- A clear separation between what is in the release and what is a risk
- A repeatable structure that works for 12.3, 14.0, and beyond
- Automation that maintains itself once the manual process stabilizes

**Page early. Cleanup in parallel. Trust comes after cleanup. Automation comes after stability.**
