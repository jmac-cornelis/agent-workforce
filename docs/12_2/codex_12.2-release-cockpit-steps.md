# 12.2 Release Cockpit — Codex Step-by-Step Plan

**Date:** 2026-03-26
**Author:** Codex
**Status:** Draft
**Main source:** `12.2-release-cockpit-recommendations.md`

---

## Purpose

This is the plain-English version of the plan.

The job is simple:

1. decide what really belongs in `12.2.0.x`
2. fix the Jira data that makes reporting unreliable
3. build a useful Confluence page
4. keep cleaning Jira until the page is something people can trust

---

## Basic Rule

Build the page early, but be honest about what is still messy.

That means:

- make a useful page now
- keep a visible cleanup list on the page
- do not pretend the numbers are perfect until the Jira cleanup is underway

---

## Step-by-Step Plan

## Phase 1 — Make the key decisions first

These decisions should happen first because they control everything else.

### Step 1. Decide what `12.2.0.x` really is

Answer this:

- is `12.2.0.x` a real `CN5000 + CN6000` release?
or
- is it mostly `CN5000`, with some `CN6000` work around it?

Why this matters:

- this decides how much CN6000 work must be cleaned up right away
- this also decides how the page should be laid out

### Step 2. Decide how the top of the Jira structure should look

My recommendation:

- one top `SW Release` ticket for `12.2.0.x`
- one `CN5000` delivery parent under it
- one `CN6000` delivery parent under it

Plain meaning:

- one release
- two family work buckets underneath it

### Step 3. Decide what the page totals mean

Use these two buckets on the page:

- `Release Scope`
  Meaning tickets clearly assigned to `12.2.0.x`
- `Release Risk Backlog`
  Meaning tickets that may affect `12.2`, but are not cleanly assigned to it yet

Do not mix those together into one total.

### Step 4. Make `Product Family` the main scope field

Use `Product Family` as the real source of truth for `CN5000` and `CN6000`.

Labels can still exist, but they should not drive the page.

---

## Phase 2 — Fix the Jira fields that make the page wrong

These are the first Jira cleanup tasks.

### Step 5. Fix the `12.2.0.x` release date

The Jira version date is stale.

Set the real target date so the page is not built on obviously bad timing data.

### Step 6. Fix the broken release tracker tickets

These need to point at the right release:

- `STL-75304`
- `STL-75299`

### Step 7. Create the missing CN6000 release parent

CN5000 has a clearer release-tracking anchor today.
CN6000 needs the same kind of top-level release parent so the page can show both sides fairly.

### Step 8. Clean up unversioned P0/P1 bugs first

Start here because this is what leadership will care about first.

Goal:

- if a serious bug belongs to `12.2`, it needs the right `fixVersion`

### Step 9. Start triaging unversioned CN6000 work

Go through the CN6000 tickets without a `fixVersion` and sort them into:

- `12.2.0.x`
- `12.3.0.x`
- backlog / later

Do not try to solve every CN6000 ticket in one sitting. Work through them in manageable batches.

---

## Phase 3 — Fix the way feature work is organized

This is the next big thing because the page cannot show real delivery status if the work does not roll up correctly.

### Step 10. Parent the open stories and tasks that have no epic

Use the orphan list from the recommendations doc.

For each ticket:

1. confirm the family
2. confirm whether it really belongs in `12.2`
3. pick the right epic
4. set the parent

### Step 11. Fix the feature tickets that point at more than one release

Priority tickets:

- `STL-77053`
- `STL-77014`
- `STL-76300`

For each one, choose one of these:

- keep it in `12.2`
- move it out of `12.2`
- split it into separate tickets for separate releases

### Step 12. Review the open epics one by one

Priority epics:

- `STL-68268`
- `STL-69162`
- `STL-76008`
- `STL-75423`
- `STL-76300`
- `STL-75118`
- `STL-70567`

For each epic, answer:

1. should it still be open?
2. is the remaining work really under this epic?
3. is the remaining work in the right release?
4. does this epic need to be closed, split, or cleaned up?

---

## Phase 4 — Create the Jira filters the page will use

Do this before building the final page so we are not relying on random one-off searches.

### Step 13. Create the main feature filters

At minimum:

- `12.2 Feature Dev - CN5000`
- `12.2 Feature Dev - CN6000`
- `12.2 Feature Dev - Shared`
- `12.2 Feature Dev - In Progress`
- `12.2 Feature Dev - Remaining`

### Step 14. Create the main bug filters

At minimum:

- `12.2 Bugs - CN5000`
- `12.2 Bugs - CN6000`
- `12.2 Bugs - P0 P1 Open`
- `12.2 Bugs - Verify Queue`

### Step 15. Create the cleanup filters

At minimum:

- `12.2 Orphan Stories`
- `12.2 Multi FixVersion Exceptions`
- `12.2 Missing Product Family`
- `12.2 No Assignee`
- `CN6000 Unversioned`
- `STL Unversioned Bugs`

### Step 16. Create the critical-path filters

At minimum:

- `12.2 Open Epics - CN5000`
- `12.2 Open Epics - CN6000`
- `12.2 Epic Closure Blockers`

Result of this phase:

- one shared set of Jira filters everyone can use

---

## Phase 5 — Build the first useful Confluence page

Now build the page, but keep it honest.

### Step 17. Build the page with these sections

Recommended sections:

1. Header
2. Scope and Definitions
3. Executive Summary
4. Feature Delivery
5. Bug Readiness
6. P0/P1 Stopper Tracker
7. Component Health
8. Release Gates
9. Critical Path
10. Release Pipeline Context
11. Data Confidence
12. Action Queue

### Step 18. Make the tables live where possible

Use Confluence Jira macros for:

- feature tables
- bug tables
- P0/P1 tracker
- open epics
- cleanup lists

Keep these as generated or manually written sections:

- executive summary
- release gates
- critical path explanation
- data confidence summary
- action queue

### Step 19. Keep `Release Scope` and `Release Risk Backlog` separate on the page

This is the most important display rule.

Never let these get folded into one unclear total:

- work clearly in `12.2`
- work that probably affects `12.2`
- general backlog

Result of this phase:

- a useful first version of the page

---

## Phase 6 — Make it part of the weekly routine

Once the page exists, use it every week.

### Step 20. Refresh it every week

Each weekly review should include:

- update the summary text
- review P0/P1 changes
- review open epics
- review the cleanup findings
- update the action queue

### Step 21. Use the tools we already have

Use:

- `Gantt` to refresh release surveys and release status views
- `Drucker` to refresh Jira cleanup findings

### Step 22. Keep the `Data Confidence` section alive

That section should always answer:

- what still makes this page less trustworthy than we want?

### Step 23. Make this page the actual weekly release page

Do not let it become an extra page no one uses.

Result of this phase:

- the page becomes part of the real release process

---

## Phase 7 — Automate more later

Do this only after the page and filters settle down.

### Step 24. Add automatic side-by-side comparisons

Use Gantt or related tools to build consistent CN5000 vs CN6000 comparison output.

### Step 25. Automate Confluence publishing

Do this only after the page structure stops changing every week.

### Step 26. Add trend charts

Examples:

- bugs opened vs closed
- P0/P1 trend over time
- feature completion trend

### Step 27. Add outside blockers if they matter

Especially:

- `CN5AW`
- `CYRAW`

if those projects are actually blocking `12.2`

---

## If I Had To Start Today

This is the exact order I would follow first:

1. decide if `12.2` is joint or CN5000-primary
2. set the real `12.2.0.x` release date
3. fix the broken release tracker tickets
4. create the CN6000 release parent
5. clean up unversioned P0/P1 bugs
6. start triaging CN6000 unversioned work
7. parent the orphan stories
8. create the saved Jira filters
9. build the Confluence page
10. continue epic cleanup and multi-release cleanup in parallel

That gets a useful page in place quickly without hard-coding bad Jira data into it.

---

## Simple Readiness Checks

### Before building the page

These should be true:

- the team agrees what `12.2` means
- the release date is fixed
- the top-level release structure is decided

### Before calling the page trustworthy

These should mostly be true:

- open orphan feature work has parents
- serious bugs are versioned correctly
- CN6000 participation is no longer a mystery
- the page clearly separates in-scope work from risk backlog

### Before spending time on heavy automation

These should be true:

- the Jira filters are stable
- the page layout is accepted
- people are actually using the page every week

---

## End Goal

The goal is not just to publish a page.

The goal is to end up with:

- a release page people trust
- Jira tickets that roll up cleanly
- a repeatable way to do this again for the next release

So the real plan is:

- **page early**
- **cleanup in parallel**
- **trust comes after cleanup**
- **automation comes after stability**

