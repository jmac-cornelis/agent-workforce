# STL 12.2 Release Status Plan Comparison

> **Generated**: 2026-03-25
> **Documents compared**:
> - External plan: `/Users/johnmacdonald/tmp/agent-workforce/.sisyphus/plans/12.2-release-status-page.md`
> - Repo blueprint: `docs/12_2/STL_12_2_RELEASE_COCKPIT_BLUEPRINT.md`
> **Purpose**: Compare the two plans, highlight strengths and gaps, and recommend a single direction for the `12.2.0.x` CN5000/CN6000 release-status page

---

## Executive Summary

The two documents are **complementary**, not conflicting.

The external plan is stronger as a **tactical release-ops page plan**:

- clearer executive metrics
- better immediate remediation priorities
- stronger initial saved-filter/JQL set
- more pragmatic rollout choices

The repo blueprint is stronger as a **system-design and Jira-governance plan**:

- clearer information architecture for the page
- stronger separation of feature delivery vs bug readiness
- deeper Jira hierarchy repair strategy
- better long-term operating model for trustworthy reporting

The recommendation is to **merge them**, with this division of responsibility:

1. use the external plan as the **v1 operational page build**
2. use the repo blueprint as the **v2 structural correction and governance plan**
3. explicitly reconcile the scope and counting differences before presenting either as the single source of truth

---

## What Each Document Optimizes For

### External plan

Primary optimization:

- get a useful `12.2` release-status page live quickly

Strengths:

- concrete sections for leadership
- concrete JQL
- immediate remediation list
- explicit rollout options:
  - manual
  - semi-automated
  - fully automated
- emphasis on visible operational gaps such as:
  - unversioned CN6000 work
  - unversioned bugs
  - stale version dates
  - wrong release tracker fixVersions

Weakness:

- less explicit about how Jira itself must change to make the page trustworthy long-term

### Repo blueprint

Primary optimization:

- make the release cockpit structurally trustworthy over time

Strengths:

- clearer page information architecture
- explicit distinction between:
  - feature delivery
  - bug readiness
  - critical path
  - data confidence
- stronger canonical Jira model
- clearer hierarchy rules
- stronger ticket repair workstreams
- better ownership model

Weakness:

- less focused on fast operational adoption
- less explicit about near-term page setup tradeoffs and rollout economics

---

## Major Areas of Agreement

The two documents agree strongly on the following:

### 1. The page should be a Confluence page, not a Jira dashboard

Both documents prefer a Confluence page with embedded live Jira sections because dashboards are too constrained for the intended release view.

### 2. The page should be live where possible

Both documents favor:

- live Jira issue tables
- saved filters / JQL-backed sections
- limited generated narrative on top

### 3. Jira data quality is currently not good enough

Both documents identify Jira hygiene as part of the problem, not just page design.

Shared concerns include:

- stale release dates
- untrustworthy scope
- poor release visibility
- weak hygiene on core reporting fields

### 4. CN6000 is under-modeled in the current release view

Both documents conclude that CN6000 is not represented with the same maturity as CN5000.

### 5. A release page must include both status and cleanup actions

Both documents move beyond reporting into operational next steps.

---

## Major Differences

### 1. Scope philosophy

The biggest difference is **what each document treats as the canonical issue set**.

#### External plan

Treats the release page as a broad operational view of `12.2.0.x`, including:

- versioned work
- bug populations
- unversioned work that likely belongs in the release
- cross-release context
- release pipeline context

This is why its numbers are much larger:

- about `267` total tickets in its framing
- `154` bugs
- explicit inclusion of `319` unversioned CN6000 tickets as a key operational gap

#### Repo blueprint

Treats the cockpit as a **canonical in-scope release slice**, centered on:

- `fixVersion = "12.2.0.x"`
- `Product Family` / label scope for `CN5000` and `CN6000`
- strict feature vs bug separation

This is why its initial raw slice is smaller:

- `100` tickets in the canonical release slice used for structural analysis

#### Recommendation

Use both scopes, but name them explicitly:

- `Release Scope`
  - tickets explicitly in `12.2.0.x`
- `Release Risk Backlog`
  - unversioned or mis-versioned work that may still affect `12.2`

Do not mix those into one total without labeling the distinction.

### 2. Page structure emphasis

#### External plan

Optimizes for leadership consumption:

- executive summary
- bug summary
- P0/P1 tracker
- component health
- story completion
- release pipeline context
- hygiene dashboard

#### Repo blueprint

Optimizes for release governance and interpretability:

- scope/definitions
- feature delivery
- bug readiness
- release gates
- critical path
- data confidence
- action queue

#### Recommendation

Adopt the repo blueprint as the top-level structure, but pull these external-plan sections into it:

- `P0/P1 Stopper Tracker`
- `Component Health Matrix`
- `Release Pipeline Context`
- `Hygiene & Risk Dashboard`

### 3. Jira deficiencies emphasized

#### External plan emphasizes

- unversioned CN6000 work
- unversioned bugs
- stale release date
- wrong fixVersions on release tracker tickets
- missing release-phase/gate modeling

#### Repo blueprint emphasizes

- hierarchy defects
- inconsistent family scoping
- multi-release feature tickets
- asymmetric release roots
- undisciplined epic closure

#### Recommendation

Treat these as two layers:

- `Operational deficiencies`
  - external plan
- `Structural deficiencies`
  - repo blueprint

The merged plan should track both.

### 4. Recommended rollout

#### External plan

Gives an explicit recommendation:

- start with `Option B` (semi-automated)

This is very pragmatic and likely correct.

#### Repo blueprint

Pushes toward:

- define model
- repair Jira
- then build and operationalize

This is architecturally cleaner but slower.

#### Recommendation

Use the external rollout model, but constrain it with the repo blueprint:

1. build a useful page now
2. do not claim it is fully authoritative yet
3. use its `Data Confidence` section to drive the Jira cleanup backlog
4. progressively tighten the Jira model until the page becomes authoritative

---

## Strengths of the External Plan

The external plan adds several things the repo blueprint should absorb.

### 1. Better executive reporting shape

Its `Executive Summary`, `P0/P1 Stopper Tracker`, and `Component Health Matrix` are strong leadership-facing constructs.

These are especially useful because:

- leadership often asks about blockers first
- component hotspots often matter more than raw ticket totals
- a clear stopper tracker creates operational focus

### 2. Better immediate remediation framing

The following are excellent immediate actions from the external plan:

- triage CN6000 fixVersions
- update the `12.2.0.x` release date
- fix wrong release tracker fixVersions
- triage unversioned open bugs

These are better prioritized as first-week actions than the repo blueprint currently states.

### 3. Better adoption path

Its `Option A / B / C` framing is strong because it acknowledges operational reality.

The recommendation to start with `Option B` is sound:

- manual page structure
- live JQL sections
- semi-automated agent refresh
- low maintenance burden

---

## Strengths of the Repo Blueprint

The repo blueprint adds several things the external plan should absorb.

### 1. Better long-term page architecture

The repo blueprint’s separation into:

- feature delivery
- bug readiness
- release gates
- critical path
- data confidence
- action queue

is structurally stronger than a mostly metric-centric page.

### 2. Better Jira operating model

The external plan identifies data problems, but the repo blueprint better explains the desired target model:

- `Product Family` as source of truth
- one release hierarchy
- bugs separated from feature completion
- explicit family delivery roots

### 3. Better hierarchy repair plan

The repo blueprint is much stronger on:

- orphan story cleanup
- epic closure discipline
- feature-ticket release targeting
- family tagging normalization

This is what will make the page trustworthy rather than merely useful.

---

## Gaps in the External Plan

These are the most important things the external plan under-specifies.

### 1. It does not define a target Jira hierarchy strongly enough

It highlights release tracker and fixVersion defects, but it does not define a canonical family/epic/story model in the same depth as the repo blueprint.

### 2. It risks mixing in-scope and at-risk work

Its inclusion of unversioned work is useful, but without clear separation it can blur:

- actual release scope
- likely release risk
- generic backlog debt

### 3. It is more bug-centric than delivery-centric

That is useful for release readiness, but the page still needs a true feature-delivery spine.

---

## Gaps in the Repo Blueprint

These are the most important things the repo blueprint under-specifies.

### 1. It does not foreground blocker and component reporting enough

Leadership will want:

- P0/P1 view
- verify backlog
- component hotspots

Those deserve first-class presence.

### 2. It does not prioritize unversioned-work triage strongly enough

The external plan is right that unversioned CN6000 work and unversioned bugs are probably the biggest immediate truth gap.

### 3. It does not give a practical build sequence for the page itself

The external plan’s `Option B` is a better operational rollout recommendation.

---

## Recommended Merged Blueprint

The best path is to merge the two documents into a single implementation direction.

### Recommended page structure

1. `Header`
- release
- owner
- health
- refresh timestamp

2. `Executive Summary`
- one paragraph on release health
- top risks
- top decisions needed

3. `P0/P1 Stopper Tracker`
- external-plan strength

4. `Feature Delivery`
- `CN5000`
- `CN6000`
- `Shared`

5. `Bug Readiness`
- per family
- verify backlog
- multi-release backports

6. `Component Health`
- external-plan strength

7. `Critical Path`
- repo-blueprint strength

8. `Release Gates`
- merged concept

9. `Data Confidence`
- orphan stories
- unversioned CN6000 work
- unversioned bugs
- multi-fixVersion feature tickets
- bad release anchors

10. `Action Queue`
- concrete cleanup and delivery actions

### Recommended Jira cleanup priority

#### Immediate priority

1. fix `12.2.0.x` release date
2. fix release tracker fixVersions
3. triage CN6000 unversioned work
4. triage P0/P1 unversioned bugs

#### Next priority

5. parent open orphan feature stories
6. clean multi-release feature tickets
7. normalize CN6000 release roots
8. review open epics for closure correctness

#### After that

9. add release-gate model
10. add cross-project ASIC dependency visibility
11. automate page refresh

---

## Final Recommendation

Do **not** choose one document over the other.

Instead:

1. adopt the external plan as the `v1 page-construction and immediate remediation plan`
2. adopt the repo blueprint as the `v2 Jira-governance and trustworthiness plan`
3. explicitly split the page into:
   - `In-Scope 12.2 Work`
   - `12.2 Risk / Unversioned Work`
4. start with the external plan’s `Option B`
5. use the repo blueprint’s `Data Confidence` and `Ticket and Hierarchy Repair Plan` as the weekly cleanup program

### Practical recommendation

If only one execution path is chosen this week, it should be:

- build the Confluence page now
- keep it semi-automated
- clearly label what is in release scope vs at-risk but unversioned
- begin the hierarchy and fixVersion cleanup immediately in parallel

That gives the team a useful page quickly without pretending the underlying Jira model is already healthy.

---

## Recommended Next Deliverable

The next document should be a merged implementation spec that includes:

- final Confluence page sections
- final saved filters / JQL
- exact ownership for each cleanup workstream
- weekly operating cadence for page refresh and Jira cleanup
