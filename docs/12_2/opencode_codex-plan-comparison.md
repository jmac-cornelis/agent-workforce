# Codex vs OpenCode Plan Comparison — 12.2 Release Cockpit

**Date:** 2026-03-26
**Author:** John Macdonald
**Purpose:** Compare the two step-by-step execution plans and produce a combined recommendation

---

## 1. Overview

Two AI agents independently produced step-by-step execution plans from the same source material (`12.2-release-cockpit-recommendations.md` and `STL_12_2_RELEASE_COCKPIT_BLUEPRINT.md`). Both plans agree on the fundamental sequence — decisions → data repair → filters → page → operationalize → automate — but differ meaningfully in structure, specificity, and what they emphasize.

| Aspect | Codex Plan | OpenCode Plan |
|--------|-----------|---------------|
| Length | 413 lines, 27 steps, 7 phases | 219 lines, 23 steps, 4 phases + "Later" |
| Tone | Plain-English, accessible to non-engineers | Engineering-oriented, dense, actionable |
| Timeline | No week structure | Week 1 / Week 1-2 / Week 2 / Week 3-4 |
| Dependencies | Implicit (phase ordering) | Explicit chain stated upfront |
| JQL queries | None — references source doc | Included inline for key steps |
| Ticket specifics | References "the list" | Tables with ticket IDs and per-ticket actions |
| CLI commands | None | Included for gantt-release-monitor |
| Novel concepts | "Release Scope vs Risk Backlog" separation, readiness checks, "End Goal" framing | Milestone discipline, drucker-hygiene scheduling, dependency chain |

---

## 2. What Codex Got Right That OpenCode Missed

### 2a. "Release Scope" vs "Release Risk Backlog" (Codex Step 3)

This is the single best idea in the Codex plan. It names a problem that both analyses identified but neither solved cleanly: **the 267-vs-100 count discrepancy means different people will see different numbers and argue about what's "in" the release.**

Codex proposes showing two explicit buckets on the page:

- **Release Scope** — tickets clearly assigned to `12.2.0.x` via fixVersion
- **Release Risk Backlog** — tickets that may affect 12.2 but are not cleanly assigned yet

This prevents the most common failure mode of release pages: mixing clean data with messy data into one number that nobody trusts.

OpenCode's plan doesn't address this. It assumes data repair happens before the page is built, but in practice the repair will take weeks and the page needs to be useful before the data is perfect.

**Verdict: Adopt this. Add to page Section 2 (Scope & Definitions) and enforce in all aggregate counts.**

### 2b. Readiness checks as phase gates (Codex "Simple Readiness Checks")

Codex defines three explicit gates:

1. **Before building the page** — team agrees what 12.2 means, date is fixed, structure decided
2. **Before calling the page trustworthy** — orphans parented, bugs versioned, CN6000 participation clear, scope/risk separated
3. **Before investing in automation** — filters stable, layout accepted, people actually using the page

OpenCode has no equivalent. It has a dependency chain, but no explicit "you are not ready for the next phase" criteria.

**Verdict: Adopt this. Add as exit criteria to each phase.**

### 2c. "End Goal" framing

Codex ends with a clear statement that the goal is not just a page — it's:
- a release page people trust
- Jira tickets that roll up cleanly
- a repeatable process for the next release

OpenCode treats this as a one-time project. Codex correctly frames it as establishing a pattern.

**Verdict: Adopt this framing in the introduction.**

### 2d. "Decide what the page totals mean" as a distinct decision (Codex Step 3)

This forces the team to agree on display semantics before building anything. OpenCode skips this and jumps straight to "build the page with 12 sections." But if the team hasn't agreed what "total bug count" means (is it fixVersion-only? fixVersion + unversioned P0/P1? all bugs that might affect the release?), the page will generate arguments instead of resolving them.

**Verdict: Adopt this as a new decision step, before page construction.**

---

## 3. What OpenCode Got Right That Codex Missed

### 3a. Explicit dependency chain

OpenCode opens with: "Steps 1-3 → Step 6 → Step 12 → Step 13. Everything else is parallel improvement."

This is immediately useful for scheduling. Codex's phases imply an order but don't state which steps are truly blocking vs. parallelizable.

**Verdict: Adopt. State the critical path explicitly.**

### 3b. Inline JQL queries

OpenCode includes the actual JQL for Steps 6 and 7. Codex says "use the orphan list from the recommendations doc" — which means someone has to go find the right section of a different document, locate the query, and come back.

For a plan that will be handed to component leads and PMs who need to execute triage sessions, the queries must be inline.

**Verdict: Adopt. Every triage step must include its JQL.**

### 3c. Specific ticket tables with per-ticket actions

OpenCode provides tables for orphan stories (8 tickets), multi-release tickets (3 tickets), and epic review (7 tickets) — each with the specific action needed.

Codex lists the same tickets but without structured tables, making it harder to track completion.

**Verdict: Adopt. Tables with ticket ID + action + owner + status.**

### 3d. Timeline with week structure

OpenCode maps steps to Week 1, Week 1-2, Week 2, Week 3-4. Codex has no timeline — just phase ordering.

A plan without dates is a wish list.

**Verdict: Adopt. Map phases to weeks.**

### 3e. Milestone discipline (OpenCode Step 17)

OpenCode includes a step to pick and implement a gate-tracking mechanism (labels, custom field, or formalize existing labels). Codex mentions gates in the page structure but never includes a step to actually implement them in Jira.

**Verdict: Adopt.**

### 3f. drucker-hygiene scheduling (OpenCode Step 16)

OpenCode includes scheduling the drucker-hygiene workflow to auto-refresh the Data Confidence section. Codex mentions Drucker generally ("use Drucker to refresh Jira cleanup findings") but doesn't make it a concrete step.

**Verdict: Adopt as explicit step.**

### 3g. CLI commands for automation

OpenCode includes the actual `pm_agent --workflow gantt-release-monitor` commands. Codex says "use Gantt" without specifying how.

**Verdict: Adopt. Automation steps need executable commands.**

---

## 4. Weaknesses in the Codex Plan

### 4a. Not self-contained

The plan repeatedly says "use the list from the recommendations doc" or "use the orphan list." A step-by-step execution plan should be executable on its own without requiring cross-referencing a 500-line source document. Anyone handed this plan will immediately have to go find the other document.

### 4b. No JQL anywhere

For a plan centered on Jira triage, the absence of any JQL is a significant gap. Steps 8 and 9 (triage P0/P1 bugs, triage CN6000 work) cannot be executed without the queries. The person executing the plan has to construct them from scratch or find them elsewhere.

### 4c. Filter section lists names but not JQL

Steps 13-16 list filter names (correct) but not the JQL behind them (missing). The whole point of naming the filters in the plan is so someone can go create them. Without the JQL, this section is a checklist of names to create, not a specification of what to create.

### 4d. "If I Had To Start Today" partially duplicates the main plan

The 10-item summary at the end restates Steps 1-17 in compressed form. This creates ambiguity — is the "real" plan the 27 steps or the 10-item summary? A reader might skip the detailed steps and use the summary, missing important context.

### 4e. Step 19 is a design principle buried as a step

"Keep Release Scope and Release Risk Backlog separate on the page" is the most important display rule in the plan, but it's presented as Step 19 of 27 — after filter creation and page building have already started. If someone builds the page in Step 17 without having read ahead to Step 19, they'll build it wrong and have to redo it.

This should be a principle stated upfront (Phase 1), not a late-stage step.

### 4f. No owner assignments

Neither plan assigns owners to steps, but Codex makes this harder because it doesn't even indicate which steps are PM/leadership vs engineering vs DevOps. OpenCode at least says "These are PM/leadership conversations, not engineering tasks" for the decision phase.

### 4g. Phase separation may slow execution

Codex splits filter creation (Phase 4) and page building (Phase 5) into separate sequential phases. OpenCode groups them in the same week. In practice, you create a filter and immediately embed it in the Confluence page — separating these into distinct phases adds unnecessary wait time between them.

---

## 5. Weaknesses in the OpenCode Plan

### 5a. No "Release Scope vs Risk Backlog" concept

The plan assumes data will be clean before the page is useful. In reality, data repair takes weeks and the page needs to be valuable immediately. Without the scope/risk separation, the page will show misleading totals during the repair period.

### 5b. No readiness checks / exit criteria

There's no explicit "you are ready to proceed to the next phase" test. The week-based timeline implies everything flows smoothly, but in practice decisions slip, triage gets delayed, and someone needs to know "am I ready to build the page yet?"

### 5c. No repeatable-process framing

The plan reads as a one-time project. It doesn't call out that the structure being built should be reusable for 12.3, 14.0, etc. This matters because it affects design decisions (generic filter names vs release-specific, template page vs one-off, etc.).

### 5d. Step 11 underweights the scope-field decision

"Communicate that Product Family is the canonical scope field" is treated as a minor cleanup step. In practice, this is a governance decision that requires buy-in from every team — it's closer to a Phase 1 decision than a parallel data-repair task.

---

## 6. Combined Recommendation

The following merges the best of both plans into a single execution sequence.

### Core Principles (state upfront, do not bury as steps)

1. **Model first, page second.** The page is a rendering layer. Trustworthy data is the real deliverable.
2. **Separate Release Scope from Release Risk Backlog.** Never combine clean-data counts with messy-data estimates in one number.
3. **Build early, be honest.** Ship the page before data is perfect, but clearly label what is reliable and what is not.
4. **Build for reuse.** The structure must work for 12.3, 14.0, and beyond — not just 12.2.

### Phase 1: Decisions (Week 1)

Owner: PM / Release Lead

| Step | Action | Why it blocks everything |
|------|--------|--------------------------|
| 1 | Decide: Is 12.2 joint CN5000+CN6000 or CN5000-primary? | Controls CN6000 triage scope |
| 2 | Decide: One SW Release umbrella + two Initiative children, or two parallel roots? | Controls Jira hierarchy |
| 3 | Decide: What do page totals mean? Define "Release Scope" (fixVersion assigned) vs "Release Risk Backlog" (unversioned but potentially in-scope). | Controls page display semantics |
| 4 | Make `Product Family` the canonical scope field. Communicate to all teams. | Controls every filter and report |
| 5 | Set a real release date on `12.2.0.x` Jira version | Controls velocity/readiness calculations |

**Exit criteria (all must be true before proceeding):**
- Team agrees what 12.2 means (joint or CN5000-primary)
- Hierarchy shape decided
- Release date updated
- Product Family declared canonical

### Phase 2: Anchor Repairs (Week 1, can start as Steps 1-5 are answered)

Owner: PM / Release Lead

| Step | Action |
|------|--------|
| 6 | Fix STL-75304: fixVersion `12.1.1.x` → `12.2.0.x` |
| 7 | Fix STL-75299: fixVersion `12.1.0.x` → `12.3.0.x` |
| 8 | Create CN6000 release-tracking root parallel to STL-75294 |

### Phase 3: Data Repair (Week 1-2, parallel workstreams)

These run simultaneously once Phase 1 decisions are made.

**Step 9. Triage P0/P1 unversioned bugs**

Owner: PM + Engineering Leads

```
project=STL AND issuetype=Bug AND fixVersion is EMPTY
  AND priority in ("P0-Stopper","P1-Critical")
  AND status not in (Closed,Done)
```

Per ticket: assign to 12.2.0.x, 12.3.0.x, or explicitly mark backlog.

**Step 10. Triage CN6000 unversioned tickets (319)**

Owner: Component Leads (batch by component)

```
project=STL AND "Product Family"=CN6000
  AND fixVersion is EMPTY AND status not in (Closed,Done)
```

Per ticket: assign to 12.2.0.x, 12.3.0.x, or backlog. Work in batches by component — do not attempt all 319 in one session.

**Step 11. Parent 8 orphan stories under epics**

Owner: Engineering Leads (per component)

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

**Step 12. Resolve 3 multi-release feature tickets**

Owner: PM

| Ticket | Current fixVersions | Decision: keep in one, move, or split |
|--------|-------------------|---------------------------------------|
| STL-77053 | 12.2.0.x + 12.3.0.x | |
| STL-77014 | 12.2.0.x + 14.0.0.x | |
| STL-76300 | 12.2.0.x + 14.0.0.x | |

**Step 13. Review 7 open epics for closure or re-scoping**

Owner: Engineering Leads

| Epic | Issue | Action |
|------|-------|--------|
| STL-68268 | Children appear closed | Review for closure |
| STL-69162 | Held open by STL-70348 only | Confirm real remaining work |
| STL-76008 | In Progress | Confirm remaining child work |
| STL-75423 | In Progress | Confirm remaining child work |
| STL-76300 | In Progress, also 14.0.0.x | Resolve release intent |
| STL-75118 | Open | Confirm remaining child work |
| STL-70567 | In Progress | Confirm remaining child work |

**Step 14. Archive 15+ "Obsolete -" prefixed components**

Owner: Jira Admin / DevOps

**Exit criteria (before building the page):**
- P0/P1 unversioned bugs have been triaged
- Orphan stories have parents
- Multi-release feature tickets resolved
- CN6000 release root exists

### Phase 4: Build the Cockpit (Week 2, can overlap with Phase 3)

**Step 15. Create 22 saved JQL filters**

Owner: DevOps

All JQL is defined in `12.2-release-cockpit-recommendations.md` Section 7. Create as shared filters visible to the release team.

Feature delivery (5):
- `12.2 Feature Dev - CN5000`
- `12.2 Feature Dev - CN6000`
- `12.2 Feature Dev - Shared`
- `12.2 Feature Dev - In Progress`
- `12.2 Feature Dev - Remaining`

Bug readiness (6):
- `12.2 Bugs - CN5000`
- `12.2 Bugs - CN6000`
- `12.2 Bugs - P0 P1 Open`
- `12.2 Bugs - Verify Queue`
- `12.2 Bugs - Multi Release`
- `12.2 Bugs - Stale`

Hierarchy and critical path (3):
- `12.2 Open Epics - CN5000`
- `12.2 Open Epics - CN6000`
- `12.2 Epic Closure Blockers`

Data confidence (4):
- `12.2 Orphan Stories`
- `12.2 Multi FixVersion Exceptions`
- `12.2 Missing Product Family`
- `12.2 No Assignee`

Pipeline context (4):
- `STL Active Releases`
- `CN6000 Unversioned`
- `STL Unversioned Bugs`
- `ASIC Dependencies`

**Step 16. Build the Confluence page**

Owner: DevOps / PM

| # | Section | Source | Live or Generated |
|---|---------|--------|-------------------|
| 1 | Header | Generated + manual | Health, risks, decisions |
| 2 | Scope & Definitions | Static template | **Must include Release Scope vs Risk Backlog definition** |
| 3 | Executive Summary | Generated or manual | Narrative for management |
| 4 | Feature Delivery | Live Jira macros | Per-family (CN5000, CN6000, Shared) |
| 5 | Bug Readiness | Live Jira macros | Per-family — **separate from features** |
| 6 | P0/P1 Stopper Tracker | Live Jira macro | First thing leadership reads |
| 7 | Component Health Matrix | Live Jira macro or generated | Bug distribution by component |
| 8 | Release Gates | Manual table | Ship readiness beyond counts |
| 9 | Critical Path | Generated epic-child analysis | What must close before ship |
| 10 | Release Pipeline Context | Manual or generated | Where 12.2 sits vs other releases |
| 11 | Data Confidence | Generated hygiene | Can the page be trusted? |
| 12 | Action Queue | Manual, weekly | Operational cleanup |

**Display rule (from Codex — apply during page construction, not after):** Every aggregate count on the page must clearly indicate whether it represents Release Scope (fixVersion-assigned tickets only) or includes Risk Backlog (unversioned tickets that may belong to this release).

**Step 17. Populate the Action Queue**

Add remaining cleanup items from Phase 3 that are not yet done.

**Exit criteria (before calling the page trustworthy):**
- Orphan feature work has parents
- P0/P1 bugs are versioned
- CN6000 participation is no longer a mystery
- Page clearly separates Release Scope from Risk Backlog

### Phase 5: Operationalize (Week 3-4)

**Step 18. Schedule weekly gantt-release-monitor runs**

Owner: DevOps

```bash
pm_agent --workflow gantt-release-monitor --project-key STL --releases "12.2.0.x" --scope-label CN5000
pm_agent --workflow gantt-release-monitor --project-key STL --releases "12.2.0.x" --scope-label CN6000
```

**Step 19. Schedule weekly drucker-hygiene run**

Refreshes Data Confidence section.

**Step 20. Add milestone discipline**

Owner: PM / Release Lead

Pick one gate-tracking mechanism:
- **Option A:** Label convention — `gate:feature-complete`, `gate:validation`, `gate:rc`, `gate:ga`
- **Option B:** Custom field — "Release Phase" dropdown
- **Option C:** Formalize existing labels — `sw_debugging`, `sw_critical_debugging` + add `sw_verification`, `sw_rc`

Apply to release umbrellas and critical-path epics.

**Step 21. Make the cockpit the weekly release review source of truth**

Each weekly review should:
- Update the summary narrative
- Review P0/P1 changes
- Review open epics
- Review Data Confidence findings
- Update the Action Queue

Use the Data Confidence section as the standing cleanup queue.

**Exit criteria (before investing in heavy automation):**
- Jira filters are stable (not changing weekly)
- Page layout is accepted by stakeholders
- People are actually using the page every week

### Phase 6: Full Automation (only if cockpit proves valuable)

| Step | Action | What it powers |
|------|--------|----------------|
| 22 | Extend gantt-release-monitor for cross-product comparison | Side-by-side CN5000 vs CN6000 |
| 23 | Add epic-child closure analysis | Critical Path section |
| 24 | Add Confluence API auto-publish | Zero-touch page refresh |
| 25 | Add trend charts (matplotlib or Confluence chart macro) | Bug trends, P0/P1 trends, burndown |
| 26 | Create cross-project ASIC blocking links (CN5AW/CYRAW → STL) | ASIC dependency visibility |

---

## 7. Critical Path Through the Combined Plan

**Minimum viable cockpit:** Steps 1-5 → Step 9 → Step 15 → Step 16

Everything else improves accuracy and trust in parallel. A usable page is achievable by end of Week 2 if PM makes decisions in Week 1.

---

## 8. End Goal

The goal is not just to publish a page for 12.2.

The goal is to end up with:

- A release page people trust
- Jira tickets that roll up cleanly
- A clear separation between what's in the release and what's a risk
- A repeatable structure that works for 12.3, 14.0, and beyond
- Automation that maintains itself once the manual process stabilizes

**Page early → cleanup in parallel → trust comes after cleanup → automation comes after stability.**
