# 12.2 Release Cockpit — Step-by-Step Execution Plan

**Date:** 2026-03-26
**Author:** John Macdonald
**Status:** Draft
**Source:** `12.2-release-cockpit-recommendations.md`
**Scope:** Concrete task sequence to deliver a trustworthy `12.2.0.x` release cockpit for CN5000 and CN6000

---

## Dependency Chain

Steps 1-3 → Step 6 → Step 12 → Step 13. Everything else is parallel improvement. A usable (if imperfect) cockpit is achievable by end of Week 2 if PM makes the decisions in Week 1.

---

## Week 1: Decisions & Anchors

These are PM/leadership conversations, not engineering tasks.

### Step 1. Decide: Is 12.2 a joint CN5000+CN6000 release or CN5000-primary?

This determines whether the 319 CN6000 unversioned tickets need triage now or can wait.

### Step 2. Decide: Single SW Release umbrella with two Initiative children, or two parallel release roots?

Recommendation: single umbrella + two Initiative sub-roots.

### Step 3. Set a real release date on the `12.2.0.x` Jira version

Currently 2025-10-31 — 5 months stale. Every velocity/readiness calculation depends on this.

### Step 4. Fix the two broken SW Release tracker tickets

- STL-75304: Change fixVersion from `12.1.1.x` → `12.2.0.x`
- STL-75299: Change fixVersion from `12.1.0.x` → `12.3.0.x`

### Step 5. Create the CN6000 release-tracking root

Create an Initiative or SW Release ticket parallel to STL-75294, matching whatever structure was agreed in Step 2.

---

## Week 1-2: Data Repair (parallel workstreams)

These can run simultaneously once Steps 1-5 are done.

### Step 6. Triage P0/P1 unversioned bugs

Query:
```
project=STL AND issuetype=Bug AND fixVersion is EMPTY
  AND priority in ("P0-Stopper","P1-Critical")
  AND status not in (Closed,Done)
```

Per ticket: assign to 12.2.0.x, 12.3.0.x, or explicitly mark backlog.

This is the minimum — P0/P1 counts cannot be trusted until this is done.

### Step 7. Triage CN6000 unversioned tickets (319)

Query:
```
project=STL AND "Product Family"=CN6000
  AND fixVersion is EMPTY AND status not in (Closed,Done)
```

Per ticket: assign to 12.2.0.x, 12.3.0.x, or backlog. Component owners should own their subset. Do not try to do all 319 in one session.

### Step 8. Parent the 8 orphan stories under epics

| Ticket | Action |
|--------|--------|
| STL-77053 | Confirm family, parent to epic, resolve multi-release (12.2 + 12.3) |
| STL-76985 | Confirm family, parent to epic |
| STL-76978 | Confirm family, parent to epic |
| STL-76933 | Confirm family, parent to epic |
| STL-76673 | Confirm family, parent to epic |
| STL-76597 | Confirm family, parent to epic |
| STL-76596 | Confirm family, parent to epic |
| STL-76455 | Confirm family, parent to epic |

For each: confirm family, confirm epic, confirm it belongs in 12.2.0.x, set parent.

### Step 9. Resolve the 3 multi-release feature tickets

| Ticket | Current fixVersions | Decision needed |
|--------|-------------------|-----------------|
| STL-77053 | 12.2.0.x + 12.3.0.x | Keep in one, move, or split |
| STL-77014 | 12.2.0.x + 14.0.0.x | Keep in one, move, or split |
| STL-76300 | 12.2.0.x + 14.0.0.x | Keep in one, move, or split |

### Step 10. Review 7 open epics for closure or re-scoping

| Epic | Issue | Action |
|------|-------|--------|
| STL-68268 | Children appear closed | Review for closure |
| STL-69162 | Held open by STL-70348 only | Confirm real remaining work |
| STL-76008 | In Progress | Confirm remaining child work |
| STL-75423 | In Progress | Confirm remaining child work |
| STL-76300 | In Progress, also tagged 14.0.0.x | Resolve release intent |
| STL-75118 | Open | Confirm remaining child work |
| STL-70567 | In Progress | Confirm remaining child work |

### Step 11. Normalize scope fields and archive obsolete components

- Communicate that `Product Family` is the canonical scope field (not labels)
- Archive 15+ "Obsolete -" prefixed components in STL project

---

## Week 2: Build the Cockpit (can overlap with data repair)

### Step 12. Create 22 saved JQL filters in Jira

All JQL is defined in `12.2-release-cockpit-recommendations.md` Section 7. Share filters with the release team.

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

### Step 13. Build the Confluence page with all 12 sections

| # | Section | Source | Type |
|---|---------|--------|------|
| 1 | Header | Generated + manual | Health, risks, decisions needed |
| 2 | Scope & Definitions | Static template | What the page means |
| 3 | Executive Summary | Generated or manual | Narrative for management |
| 4 | Feature Delivery | Live Jira macros | Per-family feature breakdown |
| 5 | Bug Readiness | Live Jira macros | Per-family bug breakdown |
| 6 | P0/P1 Stopper Tracker | Live Jira macro | First thing leadership reads |
| 7 | Component Health Matrix | Live Jira macro or generated | Bug distribution by component |
| 8 | Release Gates | Manual table | Ship readiness beyond ticket counts |
| 9 | Critical Path | Generated epic-child analysis | What must close before ship |
| 10 | Release Pipeline Context | Manual or generated | Where 12.2 sits vs other releases |
| 11 | Data Confidence | Generated hygiene analysis | Can the page be trusted? |
| 12 | Action Queue | Manual, maintained weekly | Operational cleanup actions |

### Step 14. Populate the Action Queue

Add remaining cleanup items from Steps 6-11 that are not yet done.

---

## Week 3-4: Operationalize

### Step 15. Schedule weekly gantt-release-monitor runs

```bash
pm_agent --workflow gantt-release-monitor --project-key STL --releases "12.2.0.x" --scope-label CN5000
pm_agent --workflow gantt-release-monitor --project-key STL --releases "12.2.0.x" --scope-label CN6000
```

### Step 16. Schedule weekly drucker-hygiene run

Refreshes the Data Confidence section automatically.

### Step 17. Add milestone discipline

Pick one gate-tracking mechanism:

- **Option A:** Label convention — `gate:feature-complete`, `gate:validation`, `gate:rc`, `gate:ga`
- **Option B:** Custom field — "Release Phase" dropdown
- **Option C:** Formalize existing labels — `sw_debugging`, `sw_critical_debugging` + add `sw_verification`, `sw_rc`

Apply to release umbrellas and critical-path epics.

### Step 18. Make the cockpit the weekly release review source of truth

Use the Data Confidence section as the standing cleanup queue.

---

## Later: Full Automation (only if cockpit proves valuable)

### Step 19. Extend gantt-release-monitor for cross-product comparison

### Step 20. Add epic-child closure analysis automation

Powers the Critical Path section.

### Step 21. Add Confluence API auto-publish

### Step 22. Add trend charts

Bug open/close trend, P0/P1 count over time, story completion burndown. Matplotlib or Confluence chart macro.

### Step 23. Create cross-project ASIC blocking links

CN5AW and CYRAW → STL blocking links to make ASIC dependencies visible in release health.
