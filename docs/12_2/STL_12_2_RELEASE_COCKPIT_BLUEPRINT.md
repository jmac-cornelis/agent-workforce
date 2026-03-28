# STL 12.2 Release Cockpit Blueprint

> **Generated**: 2026-03-25
> **Scope**: `12.2.0.x` release view for `CN5000` and `CN6000`
> **Purpose**: Define the Confluence page structure, Jira model, cleanup work, and governance needed to provide a trustworthy view of `12.2.0.x` development and release status

---

## Executive Summary

The `12.2.0.x` view should be treated as a **release cockpit**, not a single report or dashboard gadget.

The central problem is not only presentation. The current Jira data model makes it difficult to produce a clean status page because:

- feature delivery and bug readiness are mixed together in the same release slice
- scope is modeled through both `labels` and `Product Family`
- open feature work exists without consistent hierarchy
- many tickets carry multiple `fixVersion` values
- release-tracking structure is asymmetric between `CN5000` and `CN6000`
- version metadata and milestone data are incomplete

The right solution is:

1. define a clear page structure
2. define canonical Jira-backed issue sets for the page
3. repair Jira hierarchy and release-targeting hygiene
4. keep the page mostly live through Jira filters/macros
5. add generated analysis only where Jira cannot express the needed reasoning

---

## Objectives

This cockpit should answer six questions quickly:

1. What is the overall status of `12.2.0.x`?
2. What is the feature-delivery status for `CN5000`?
3. What is the feature-delivery status for `CN6000`?
4. What is the bug-readiness status for each family?
5. What exact work is blocking completion?
6. How trustworthy is the underlying Jira data?

---

## Current-State Findings

The recommendations in this document are grounded in a live survey of the `12.2.0.x` Jira slice on 2026-03-25.

### Raw release slice

Using:

- `project = STL`
- `fixVersion = "12.2.0.x"`
- `labels in (CN5000, CN6000) OR "Product Family" in (CN5000, CN6000)`

Observed:

- `100` total tickets in the raw slice
- `73` bugs
- `27` non-bug items in the raw slice previously used for high-level feature views, but the broader feature slice is much larger once initiatives and epics are considered
- `23` tickets with more than one `fixVersion`
- `99` of `100` tickets without `due date`
- `8` open story-like tickets with no parent

### Field model findings

- Live Jira shows `Product Family` as `customfield_28382`
- Scope is still effectively discoverable through both `labels` and `Product Family`
- `Product Family` should become the authoritative scope field

### Release-tracking findings

- A release-tracking umbrella exists for `CN5000`:
  - [STL-75294](https://cornelisnetworks.atlassian.net/browse/STL-75294)
- A parallel `CN6000` release-tracking umbrella was not found in the same shape

### Open epic findings

Open `CN5000` epics in the `12.2.0.x` slice include:

- [STL-76008](https://cornelisnetworks.atlassian.net/browse/STL-76008)
- [STL-75423](https://cornelisnetworks.atlassian.net/browse/STL-75423)
- [STL-69162](https://cornelisnetworks.atlassian.net/browse/STL-69162)
- [STL-68268](https://cornelisnetworks.atlassian.net/browse/STL-68268)

Open `CN6000` epics in the `12.2.0.x` slice include:

- [STL-76300](https://cornelisnetworks.atlassian.net/browse/STL-76300)
- [STL-75118](https://cornelisnetworks.atlassian.net/browse/STL-75118)
- [STL-70567](https://cornelisnetworks.atlassian.net/browse/STL-70567)

Specific hierarchy smells:

- [STL-68268](https://cornelisnetworks.atlassian.net/browse/STL-68268) is still open even though known children appear closed
- [STL-69162](https://cornelisnetworks.atlassian.net/browse/STL-69162) appears to remain open primarily because of [STL-70348](https://cornelisnetworks.atlassian.net/browse/STL-70348)

### Open feature work without parent

The following open story-like items should be treated as hierarchy defects until parented:

- [STL-77053](https://cornelisnetworks.atlassian.net/browse/STL-77053)
- [STL-76985](https://cornelisnetworks.atlassian.net/browse/STL-76985)
- [STL-76978](https://cornelisnetworks.atlassian.net/browse/STL-76978)
- [STL-76933](https://cornelisnetworks.atlassian.net/browse/STL-76933)
- [STL-76673](https://cornelisnetworks.atlassian.net/browse/STL-76673)
- [STL-76597](https://cornelisnetworks.atlassian.net/browse/STL-76597)
- [STL-76596](https://cornelisnetworks.atlassian.net/browse/STL-76596)
- [STL-76455](https://cornelisnetworks.atlassian.net/browse/STL-76455)

### Multi-release feature smells

These tickets demonstrate why release-targeting policy needs to tighten:

- [STL-77053](https://cornelisnetworks.atlassian.net/browse/STL-77053) carries `12.3.0.x` and `12.2.0.x`
- [STL-77014](https://cornelisnetworks.atlassian.net/browse/STL-77014) carries `14.0.0.x` and `12.2.0.x`
- [STL-76300](https://cornelisnetworks.atlassian.net/browse/STL-76300) carries `14.0.0.x` and `12.2.0.x`

For bugs, multiple `fixVersion` values may reflect real backports. For feature work, they usually indicate blurred release intent.

---

## Page Blueprint

The page should be a single Confluence page with live Jira-backed sections and a small amount of generated analysis.

### 1. Header

Purpose: establish the release context immediately.

Should contain:

- release name: `12.2.0.x`
- covered families: `CN5000`, `CN6000`
- refresh timestamp
- release owner
- overall health: `On Track`, `At Risk`, or `Off Track`
- top three release risks
- top three decisions needed this week

Source:

- generated summary text
- Jira release metadata where available
- manually maintained owner field if Jira version metadata is incomplete

### 2. Scope and Definitions

Purpose: prevent confusion over what the page means.

Should define:

- `Feature Delivery = non-Bug issues`
- `Bug Readiness = Bug issues only`
- `Shared Work = tickets spanning more than one product family`
- `Done / In Progress / Remaining / Blocked` status mapping
- exact scope fields used: `fixVersion` and `Product Family`

Source:

- static explanation maintained in the page template

### 3. Executive Summary

Purpose: give management a short status answer without reading tables.

Should contain:

- release summary paragraph
- `CN5000` status summary
- `CN6000` status summary
- one-paragraph bug-readiness summary
- one-paragraph data-quality summary

Source:

- generated narrative from Gantt or a similar PM analysis path

### 4. Feature Delivery

Purpose: answer what has been built, what is active, and what remains.

Structure:

- `CN5000` feature summary
- `CN6000` feature summary
- `Shared / Cross-Family Feature Work`

For each family, include:

- total feature items
- done / in progress / remaining counts
- manager rollup
- open epics
- open story/task work
- highest-priority remaining work

Source:

- live Jira filters/macros

### 5. Bug Readiness

Purpose: answer whether the release is shippable from a quality standpoint.

For each family, include:

- open P0 / P1 / P2 counts
- bug status mix
- open verification queue
- old bugs or stale bugs
- multi-release backport list

Source:

- live Jira filters/macros
- optional bug-trend chart

### 6. Release Gates

Purpose: express ship readiness beyond ticket counts.

Recommended gates:

- feature complete
- release-blocking bugs at target threshold
- validation complete
- release notes complete
- manufacturing/support readiness
- final approval

Source:

- mostly manual or generated summary blocks
- not purely Jira-driven

### 7. Critical Path

Purpose: show what actually has to close before `12.2.0.x` is done.

Should contain:

- open epics blocking completion
- the open child work preventing closure
- any child work that is in the wrong release or wrong family
- a short “must move this week” list

Source:

- generated epic-child analysis
- selective live Jira filters for follow-up

### 8. Data Confidence

Purpose: tell the reader whether the page can be trusted.

Should contain:

- orphaned stories/tasks
- multi-fixVersion feature tickets
- missing `Product Family`
- missing parent hierarchy
- missing release-tracking anchors
- version metadata concerns

Source:

- generated hygiene analysis

### 9. Action Queue

Purpose: turn the page into an operational tool.

Should contain:

- 5 to 10 cleanup or delivery actions
- owner
- target date
- status

Source:

- manual or generated action list

---

## What Should Be Live vs Generated

### Live Jira sections

These should be Confluence Jira macros:

- feature-delivery tables
- bug-readiness tables
- open epics
- in-progress items
- remaining items
- manager-facing work queues
- cleanup queues such as orphaned work and multi-fixVersion work

### Generated sections

These should remain narrative or computed:

- executive summary
- critical-path interpretation
- epic child closure analysis
- data-confidence findings
- top risks and top decisions needed

---

## Canonical Jira Model

The page will only be trustworthy if Jira follows one consistent structure.

### Source-of-truth fields

- `fixVersion`: release dimension
- `Product Family`: scope dimension
- `parent`: hierarchy dimension
- `status`: workflow state
- `priority`: urgency

### Issue-type roles

- `SW Release`: release-operations umbrella
- `Initiative`: family-level delivery root
- `Epic`: meaningful deliverable bucket
- `Story` / `Task`: execution work
- `Bug`: release-readiness work

### Recommended hierarchy

1. One `SW Release` umbrella for `12.2.0.x`
2. Two family delivery roots:
   - `12.2.0.x CN5000 Feature Delivery`
   - `12.2.0.x CN6000 Feature Delivery`
3. Epics under the family delivery roots
4. Stories/tasks under those epics
5. Bugs linked to feature work only when they truly block it

### Important modeling rule

Feature progress must not be inferred from bug counts.

That means:

- do not mix bugs into feature-completion rollups
- do not require all bugs to live under epics
- use links such as `blocks` when a bug blocks a feature epic or story

---

## Required Jira Data Rules

### Every in-scope feature ticket must have

- exactly one intended release target unless explicitly split by policy
- `Product Family`
- assignee or explicit owner
- a parent epic if it is a `Story` or `Task`

### Every epic must have

- one family root
- one clear release intent
- a short delivery-oriented summary
- children that represent the actual remaining work

### Every release umbrella must have

- owner
- target date
- release status
- manual gate state or links to gate owners

### Due-date policy

Do not require due dates on every ticket.

Given current data quality, due dates should be required first on:

- `SW Release`
- family delivery roots / initiatives
- epics on the critical path

---

## Recommended Saved Filters

The page should be built around canonical saved filters instead of ad hoc JQL in gadgets.

### Feature delivery

- `12.2 Feature Dev - CN5000`
- `12.2 Feature Dev - CN6000`
- `12.2 Feature Dev - Shared`
- `12.2 Feature Dev - In Progress`
- `12.2 Feature Dev - Remaining`

### Bug readiness

- `12.2 Bugs - CN5000`
- `12.2 Bugs - CN6000`
- `12.2 Bugs - P0 P1`
- `12.2 Bugs - Verify Queue`
- `12.2 Bugs - Multi Release`

### Hierarchy and critical path

- `12.2 Open Epics - CN5000`
- `12.2 Open Epics - CN6000`
- `12.2 Epic Closure Blockers`

### Data confidence

- `12.2 Orphan Stories`
- `12.2 Multi FixVersion Exceptions`
- `12.2 Missing Product Family`

---

## Jira Deficiencies

### 1. Scope is modeled inconsistently

Current problem:

- both `labels` and `Product Family` are being used for release-family scope

Impact:

- filters drift
- dashboards disagree
- generated analysis becomes harder to trust

Fix:

- make `Product Family` authoritative
- use labels only for convenience, not as a primary reporting field

### 2. Feature hierarchy is incomplete

Current problem:

- open feature work exists without parent epics

Impact:

- epics understate remaining work
- family delivery views are incomplete
- critical path is hard to compute

Fix:

- parent every open story/task under a family-appropriate epic
- create missing epics where needed

### 3. Release targeting is muddy

Current problem:

- too many tickets carry multiple `fixVersion` values

Impact:

- status rollups overstate or double-count release scope
- release completion becomes ambiguous

Fix:

- feature tickets should normally target one release only
- bugs can carry multiple releases only when explicitly backported

### 4. Release-tracking structure is asymmetric

Current problem:

- `CN5000` has a visible release-tracking umbrella, `CN6000` does not appear to have the same structure

Impact:

- one family looks operationally mature and the other does not
- the release page cannot present parallel management views cleanly

Fix:

- create symmetric release-tracking roots for both families, or one umbrella with two family sub-roots

### 5. Epic closure is not disciplined

Current problem:

- open epics remain open even when remaining child work is unclear, moved, or effectively done

Impact:

- leadership cannot trust epic status
- critical path gets distorted

Fix:

- close epics based on actual child state
- rehome child work that belongs to a different release

### 6. Milestone metadata is weak

Current problem:

- due dates and version metadata are not reliable enough to serve as the primary schedule signal

Impact:

- timing risk cannot be read directly from Jira

Fix:

- require milestone discipline at release and epic level

---

## Ticket and Hierarchy Repair Plan

### Workstream 1: Establish release roots

Goal: create one canonical structure for the page to anchor on.

Actions:

1. Decide whether to use:
   - one `SW Release` umbrella with two family roots
   - or two explicit family release umbrellas under one release program structure
2. Normalize around `12.2.0.x`
3. Create a `CN6000` release-tracking root parallel to [STL-75294](https://cornelisnetworks.atlassian.net/browse/STL-75294), or replace `STL-75294` with a shared top umbrella and two family roots

### Workstream 2: Repair orphan feature work

Goal: ensure all open feature execution work rolls up to an epic.

Repair queue:

- [STL-77053](https://cornelisnetworks.atlassian.net/browse/STL-77053)
- [STL-76985](https://cornelisnetworks.atlassian.net/browse/STL-76985)
- [STL-76978](https://cornelisnetworks.atlassian.net/browse/STL-76978)
- [STL-76933](https://cornelisnetworks.atlassian.net/browse/STL-76933)
- [STL-76673](https://cornelisnetworks.atlassian.net/browse/STL-76673)
- [STL-76597](https://cornelisnetworks.atlassian.net/browse/STL-76597)
- [STL-76596](https://cornelisnetworks.atlassian.net/browse/STL-76596)
- [STL-76455](https://cornelisnetworks.atlassian.net/browse/STL-76455)

For each ticket:

1. confirm intended family
2. confirm intended epic
3. confirm whether it truly belongs in `12.2.0.x`
4. parent it appropriately

### Workstream 3: Tighten fixVersion policy

Goal: stop feature work from straddling releases by default.

Priority queue:

- [STL-77053](https://cornelisnetworks.atlassian.net/browse/STL-77053)
- [STL-77014](https://cornelisnetworks.atlassian.net/browse/STL-77014)
- [STL-76300](https://cornelisnetworks.atlassian.net/browse/STL-76300)

Decision options per ticket:

- keep in `12.2.0.x`
- move to later release
- split into separate per-release implementation tickets

### Workstream 4: Normalize epic closure

Goal: ensure open epics mean real incomplete delivery.

Priority review:

- [STL-68268](https://cornelisnetworks.atlassian.net/browse/STL-68268)
- [STL-69162](https://cornelisnetworks.atlassian.net/browse/STL-69162)
- [STL-76008](https://cornelisnetworks.atlassian.net/browse/STL-76008)
- [STL-75423](https://cornelisnetworks.atlassian.net/browse/STL-75423)
- [STL-76300](https://cornelisnetworks.atlassian.net/browse/STL-76300)
- [STL-75118](https://cornelisnetworks.atlassian.net/browse/STL-75118)
- [STL-70567](https://cornelisnetworks.atlassian.net/browse/STL-70567)

Specific observations:

- [STL-68268](https://cornelisnetworks.atlassian.net/browse/STL-68268) should be reviewed for closure or child re-scoping
- [STL-69162](https://cornelisnetworks.atlassian.net/browse/STL-69162) appears to be held open mainly by [STL-70348](https://cornelisnetworks.atlassian.net/browse/STL-70348)

### Workstream 5: Normalize family tagging

Goal: ensure every in-scope ticket is reportable by family.

Actions:

1. use `Product Family` as the canonical source for family reporting
2. review mixed-family tickets such as:
   - [STL-75284](https://cornelisnetworks.atlassian.net/browse/STL-75284)
3. decide whether mixed-family tickets should be:
   - split
   - treated as shared
   - assigned to one primary family

### Workstream 6: Add minimal milestone discipline

Goal: make the page schedulable without forcing due dates everywhere.

Actions:

1. require owner and target date on release umbrellas
2. require target date on critical-path epics
3. optionally add milestone labels or fields for:
   - feature complete
   - validation complete
   - release candidate ready

---

## Proposed Operating Rules

### Feature rules

- feature tickets belong to one target release
- every story/task belongs to an epic
- every epic belongs to one family delivery root

### Bug rules

- bugs are tracked separately from feature completion
- bugs may carry multiple releases only for intentional backports
- bugs should link to blocked feature work when relevant, but should not automatically define feature progress

### Reporting rules

- feature views use non-bug filters only
- bug views use bug filters only
- shared work is shown separately instead of silently duplicated in totals
- executive summaries must state whether the page is showing snapshot counts or live Jira results

---

## Ownership Model

### Release lead / PM

Owns:

- release umbrellas
- overall page health
- release gates
- action queue

### Engineering managers

Own:

- epics and their closure readiness
- hierarchy hygiene for their team’s work
- manager rollups and work movement

### Developers / leads

Own:

- parent correctness
- release targeting correctness
- status correctness on execution tickets

### Drucker / Gantt automation

Should own:

- detection of hierarchy defects
- detection of multi-release feature tickets
- survey generation
- manager rollups
- critical-path analysis

Should not own:

- unilateral Jira restructuring without review

---

## Recommended Rollout

### Phase 1: Define the canonical release model

- agree on the `12.2.0.x` release-root structure
- agree that `Product Family` is canonical
- agree on feature vs bug filter boundaries

### Phase 2: Repair the Jira model

- parent open orphan stories
- fix multi-release feature tickets
- normalize open epics
- add CN6000 release root symmetry

### Phase 3: Build the page

- create the canonical saved filters
- build Confluence sections from those filters
- add generated executive summary and critical-path analysis

### Phase 4: Operationalize

- make the page the weekly release source of truth
- use the `Data Confidence` section as a standing cleanup queue

---

## Exit Criteria

This blueprint is considered implemented when:

- `12.2.0.x` has a clear release-root structure covering both `CN5000` and `CN6000`
- feature delivery and bug readiness are reported separately
- all open feature stories/tasks have parents
- feature tickets no longer casually span multiple releases
- the Confluence page can be built from stable live Jira filters
- the page includes a data-confidence section so readers can trust the rollups
