# 12.2 Release Cockpit — Codex vs Opencode Plan Review

**Date:** 2026-03-26
**Author:** Codex
**Status:** Draft
**Documents reviewed:**
- `codex_12.2-release-cockpit-steps.md`
- `opencode_12.2-release-cockpit-steps.md`

---

## Purpose

This document compares the two step-by-step plans and answers a simple question:

- should we combine them?
or
- is the Codex plan missing things that the Opencode plan already does better?

Short answer:

- the **Codex plan is easier to read**
- the **Opencode plan is better as a working execution checklist**
- the best result is a **combined plan**

If we must choose one as the main action plan today, I would use the **Opencode plan as the execution spine** and use the **Codex plan as the simpler reader-friendly version**.

---

## High-Level Comparison

### What the Codex plan does well

- uses plainer English
- explains why each step matters
- makes the `Release Scope` vs `Release Risk Backlog` split very clear
- is easier for a broad audience to read
- is better as a communication document

### What the Opencode plan does well

- is more concrete
- is better sequenced by week
- has a clearer dependency chain
- includes more exact actions
- includes more operational detail
- is better as a work plan

---

## Where the Codex Plan Is Weaker

These are the main weaknesses in the Codex version compared to the Opencode version.

### 1. The Codex plan is less precise about timing

The Codex plan has phases, which is fine, but the Opencode plan is better at telling people when to do things:

- `Week 1`
- `Week 1-2`
- `Week 2`
- `Week 3-4`

Why that matters:

- people can tell what needs to happen now
- it is easier to run in a release meeting
- it is easier to assign ownership

### 2. The Codex plan is less explicit about dependencies

The Opencode plan starts with a simple dependency chain:

- early decisions first
- then cleanup
- then filters
- then page build

The Codex plan implies that order, but does not make it as explicit.

Why that matters:

- a team may try to build the page before the release assumptions are fixed
- it is easier to lose the “what blocks what” logic

### 3. The Codex plan is weaker on exact operational tasks

The Opencode plan includes more exact details, for example:

- the two release tracker tickets to fix and how
- the count of `22` saved filters
- the split of filter groups
- the action-queue population step
- the exact weekly commands for Gantt

The Codex plan keeps those ideas, but in a more general way.

Why that matters:

- general plans are easier to agree with
- specific plans are easier to execute

### 4. The Codex plan is weaker on ownership cues

The Opencode plan more clearly hints at who should own certain work:

- PM / leadership for release decisions
- component owners for CN6000 triage

The Codex plan is more neutral and less explicit about who does what.

Why that matters:

- somebody needs to know who actually moves the tickets

### 5. The Codex plan does not include enough hard-edged cleanup detail

The Opencode plan explicitly keeps:

- the orphan-ticket table
- the multi-release ticket table
- the open epic review table

The Codex plan mentions those tasks, but does not preserve as much of the direct execution detail.

Why that matters:

- the detailed tables are immediately usable in a working session

### 6. The Codex plan is weaker on automation next steps

The Opencode plan is more specific about later automation:

- extend `gantt-release-monitor`
- automate epic-child closure analysis
- auto-publish to Confluence
- add trend charts
- add ASIC blocking links

The Codex plan has the same ideas, but is less exact about them.

### 7. The Codex plan drops some useful operational items

Compared to the Opencode plan, the Codex plan under-emphasizes:

- archiving obsolete components
- pipeline-context filters
- the exact number and grouping of filters
- the specific gate-tracking options

These are not the core of the strategy, but they are useful practical details.

---

## Where the Codex Plan Is Stronger

To be fair, the Codex plan improves on the Opencode plan in a few important ways.

### 1. It is clearer about the core idea

The Codex plan is better at saying:

- fix the Jira model
- build the page
- keep the page honest while the data is still messy

That is easier to understand than a purely task-driven list.

### 2. It is stronger on the scope split

The Codex plan does a better job emphasizing:

- `Release Scope`
- `Release Risk Backlog`

This is one of the most important ideas in the whole `12.2` effort, and it should not get buried.

### 3. It is easier to share with non-technical stakeholders

The Codex plan reads better for:

- managers
- project leads
- people who are not living in Jira and Confluence every day

### 4. It is better at stating readiness checks

The `Before building the page`, `Before calling the page trustworthy`, and `Before heavy automation` checks are simple and useful.

That should be kept.

---

## Recommendation

I do **not** recommend replacing one plan with the other.

I recommend a combined plan with this split:

### Use the Opencode plan for

- detailed execution order
- weekly rollout timing
- exact ticket cleanup tasks
- exact filter creation work
- exact page-build checklist
- exact automation backlog

### Use the Codex plan for

- the plain-English explanation
- the core reasoning
- the `Release Scope` vs `Release Risk Backlog` rule
- the simple readiness checks

---

## Best Combined Plan

If we merge the two properly, the result should look like this:

### 1. Keep the Opencode timing structure

Use:

- `Week 1`
- `Week 1-2`
- `Week 2`
- `Week 3-4`
- `Later`

This is the better execution shape.

### 2. Keep the Codex scope rule

Carry this forward clearly:

- `Release Scope`
- `Release Risk Backlog`

and never mix them into one total.

### 3. Keep the Opencode tables for cleanup work

Preserve the detailed tables for:

- orphan stories
- multi-release feature tickets
- open epics

These are better than a looser prose list.

### 4. Keep the Codex plain-English framing at the top

Start the merged plan with:

- what the job is
- why the order matters
- the basic rule: build early, but be honest

### 5. Keep the Opencode filter list, but add the Codex wording rule

The filter work should stay concrete, but the page should still clearly separate:

- clearly versioned release work
- likely release-impacting unversioned work

### 6. Keep the Codex readiness checks

These should stay at the end of the merged plan:

- before building the page
- before calling it trustworthy
- before automating heavily

---

## If We Do Not Merge Them

If for some reason we want to keep only one plan as the main working document, my recommendation is:

### Main working plan

Use:

- `opencode_12.2-release-cockpit-steps.md`

Because it is more concrete and easier to execute.

### Supporting summary plan

Keep:

- `codex_12.2-release-cockpit-steps.md`

Because it is easier to read and explain.

That is the better split than the other way around.

---

## Final Judgment on the Codex Plan

The Codex plan is **not wrong**.

Its problem is that it is a better **explainer** than it is an **execution checklist**.

The main weaknesses are:

- not enough timing detail
- not enough execution detail
- not enough ownership detail
- not enough exact cleanup detail
- not enough exact filter and automation detail

The main strengths are:

- clearer plain English
- better explanation of the main idea
- stronger emphasis on the scope split
- easier for a broad audience to read

So the right answer is:

- **keep the Codex plan**
- **do not use it alone as the only working plan**
- **merge it with the Opencode plan or use Opencode as the main execution plan**

---

## Recommended Next Step

The next best document to create would be:

- a single merged working plan

That merged plan should:

1. keep the Opencode execution detail
2. keep the Codex plain-English framing
3. keep the Codex `Release Scope` vs `Release Risk Backlog` split
4. become the one plan the team actually follows

