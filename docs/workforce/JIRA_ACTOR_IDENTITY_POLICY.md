# Jira Actor Identity Policy

## Purpose

This document defines when an automation agent should act in Jira as:

- the **service account**
- the **requesting human**
- **draft only** with no Jira mutation

The goal is simple:

- machine-owned actions should look like machine-owned actions
- human decisions should look like human decisions
- audit trails should always show who requested, approved, and executed the change

This policy applies to Jira-writing agents such as Drucker, Gantt, Hedy, and any
future agent that creates, updates, comments on, assigns, links, or transitions
Jira issues.

---

## Core Rule

**The Jira actor should match who owns the intent of the change.**

- Use the **service account** when the action is primarily a system action.
- Use the **requesting human** when the action is primarily a human decision.
- Use **draft only** when the agent is still analyzing, proposing, or waiting for approval.

---

## Actor Types

### 1. `draft_only`

The agent produces a recommendation, plan, or preview but does not write to Jira.

Use this when:

- the agent is still analyzing
- the change is non-trivial and has not been approved
- the action could affect priority, schedule, ownership, or customer commitments
- the user asked for a dry run

### 2. `service_account`

The action is executed by the shared Jira automation identity.

Use this when:

- the action came from polling, background automation, or a scheduled job
- the action is deterministic or policy-driven
- the action is repetitive or bulk-oriented
- the action records system evidence or hygiene state
- the action remains a system action even after human approval

### 3. `requester`

The action is executed as the human who initiated or approved it.

Use this when:

- the action expresses a human judgment call
- the action implies commitment, intent, priority, or ownership
- the action should read as if the human performed it directly in Jira

If requester credentials are not available, do not fake requester identity.
Execute as the service account and record `requested_by` and `approved_by`.

---

## Decision Matrix

| Action Type | Default Actor | Why |
|-------------|---------------|-----|
| Polling scan, monitoring pass, hygiene scan | `service_account` | The system owns the action |
| Add a machine-generated evidence comment | `service_account` | This is an automated observation |
| Add labels from policy or metadata hygiene rules | `service_account` | Deterministic, low-risk write |
| Add links to builds, PRs, dashboards, or evidence | `service_account` | Mechanical system write |
| Bulk create Jira tickets from an approved plan | `service_account` | The system is applying an approved batch |
| Bulk update non-sensitive metadata | `service_account` | Repetitive and auditable system action |
| Change priority | `requester` | Human judgment and tradeoff |
| Change fixVersion / release target | `requester` | Planning commitment |
| Change assignee based on management or delivery judgment | `requester` | Human ownership decision |
| Transition across meaningful workflow states | `requester` by default | Status changes often imply human intent |
| Close or reopen a ticket based on review | `requester` by default | This reads as a human decision |
| Comment that says what "we" decided or committed to | `requester` | Human statement, not a machine statement |
| Suggest a change without applying it | `draft_only` | Analysis only |

---

## What Counts As A System Action

These are strong service-account candidates:

- hygiene comments
- stale ticket notices
- missing metadata comments
- label cleanup
- evidence links
- build or PR linkage
- low-risk approved field synchronization
- audit or provenance comments
- agent-created ticket trees from an already approved plan

These should generally be written in machine voice, for example:

- `Drucker detected missing component metadata.`
- `Automation applied approved metadata update.`
- `Approved by John Macdonald on 2026-04-01.`

They should not sound like a human speaking personally.

Bad examples:

- `I moved this to Ready.`
- `We decided to take this in 14.1.`

---

## What Counts As A Human Decision

These are strong requester candidates:

- priority changes
- release-target changes
- schedule commitments
- customer-facing commitment comments
- ownership assignment based on management choice
- close / reopen decisions
- transitions such as `Open -> In Progress`, `Ready -> Closed`, or `Closed -> Reopened`
- comments that explain a judgment call rather than reporting machine evidence

These should read like the human actually made the decision.

---

## Review-Gated Hybrid Cases

Some actions begin as machine suggestions but become valid system writes after
human approval.

Examples:

- Drucker proposes component, label, or priority cleanup
- Gantt proposes a ticket tree
- Hedy proposes release-linking updates

Use this rule:

- if the approved action is still fundamentally a **system application of a rule**, use `service_account`
- if the approved action is now clearly a **human decision**, use `requester`

Examples:

| Scenario | Actor |
|----------|-------|
| Human approves label cleanup suggested by Drucker | `service_account` |
| Human approves bulk ticket creation from a Gantt plan | `service_account` |
| Human decides to move a ticket to `Closed` | `requester` |
| Human decides to change fixVersion to a different release | `requester` |

If requester credentials are not available:

- execute as `service_account`
- store `requested_by`
- store `approved_by`
- include the human identity in the audit record or comment body when appropriate

---

## Recommended Defaults By Agent

### Drucker

- polling hygiene scans: `service_account`
- metadata suggestions: `draft_only`
- approved low-risk hygiene updates: `service_account`
- priority or workflow-state changes: `requester`

### Gantt

- release/project analysis: `draft_only`
- approved bulk ticket creation from a plan: `service_account`
- release-scope or fixVersion decisions: `requester`

### Hedy

- release analysis and release-readiness reporting: `draft_only`
- non-sensitive release linkage or version bookkeeping: `service_account`
- stage transitions, promotion, or release-signoff actions: `requester` by default

### Hypatia

- Jira-facing documentation bookkeeping or doc-link comments: `service_account`
- human-authored commitment or approval comments: `requester`

---

## Sensitive Actions

The following should default to `requester` unless there is a strong explicit
policy exception:

- close / reopen
- priority changes
- fixVersion changes
- assignee changes with organizational implications
- status transitions across major workflow boundaries
- comments that make customer or release commitments

If these are ever allowed through the service account, the policy should be
explicit, narrow, and audited.

---

## Audit Requirements

Every Jira write should carry enough audit context to answer:

- who requested it
- who approved it
- which agent executed it
- which policy rule allowed it
- whether it was service-account or requester mode

Minimum audit fields:

- `actor_mode`
- `requested_by`
- `approved_by`
- `executed_by`
- `policy_rule`
- `correlation_id`
- `timestamp`

---

## Practical Execution Model

Agents should support three write modes:

- `draft_only`
- `service_account`
- `requester`

Recommended default behavior:

- background jobs start in `service_account`
- interactive commands start in `draft_only`
- non-trivial writes require explicit selection or policy resolution before execution

If identity cannot be resolved safely, fall back to:

- `draft_only` for sensitive actions
- `service_account` for low-risk deterministic actions

---

## Implementation Guidance

1. Do not fake human identity.
2. Do not let the service account write comments that sound like a person.
3. Separate low-risk hygiene writes from judgment-heavy planning and workflow writes.
4. Keep bulk and repetitive operations under the service account.
5. Keep planning commitments and workflow intent under the requester whenever possible.

---

## Short Policy Summary

- **System fact, system rule, system cleanup** -> `service_account`
- **Human judgment, commitment, ownership, or workflow intent** -> `requester`
- **Not approved yet** -> `draft_only`
