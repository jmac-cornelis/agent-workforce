# AI Agent System Implementation Roadmap

Author: John N. Macdonald (Concept Origin)  
Document Type: Standalone Implementation Roadmap  
Scope: 90-day delivery plan for the first operational version of the agent platform

---

# 1. Purpose

This document turns the agent concept into an execution plan.

The goal is not to build every agent at once. The goal is to establish the core event model, the first production-worthy agent workflows, and enough traceability that the system starts delivering value early.

This roadmap assumes a staged rollout with strong human oversight, clear ownership boundaries, and a bias toward shipping narrow slices that can be hardened in place.

---

# 2. Delivery Objectives

By the end of the first implementation cycle, the platform should be able to:

- react to GitHub development events
- run configuration-aware builds through Fuze
- run staged automated tests
- map internal build identities to releasable versions
- push traceability into Jira
- capture and summarize Teams transcripts
- establish the common event and schema foundation for later agents

The first cycle should **not** try to solve every workflow problem. It should establish the system spine.

---

# 3. Guiding Principles

## 3.1 Build the spine first

Before advanced planning, adaptive test generation, or rich release intelligence, the platform needs:

- canonical schemas
- event routing
- auditability
- identity consistency
- service boundaries

## 3.2 Start where signal is strongest

The highest-signal implementation path is:

- GitHub
- Fuze
- build records
- test records
- Jira traceability

Those systems have the clearest machine-driven triggers.

## 3.3 Keep humans in the loop

Agents can recommend, annotate, summarize, classify, and orchestrate.

Humans should retain control over:

- production release approval
- policy overrides
- major traceability exceptions
- external documentation publication

## 3.4 Make every result inspectable

Every agent action should be visible through records, logs, linked artifacts, and status history.

No black boxes.

---

# 4. Delivery Scope

## 4.1 In scope for the first 90 days

- shared event envelope
- canonical record schemas
- Josephine MVP
- Galileo MVP
- Curie MVP
- Faraday MVP
- Tesla MVP
- Mercator MVP
- Berners-Lee MVP
- Pliny MVP
- narrow GitHub integration
- narrow Jira integration
- Fuze integration for build orchestration
- one hardware/test environment integration path
- basic operational dashboards

## 4.2 Explicitly out of scope for the first 90 days

- full autonomous project planning
- deep Jira planning automation
- broad documentation automation at publication quality
- advanced release matrix optimization
- self-improving test generation loops
- multi-tenant customer release partitioning
- fully automated release promotion to production

---

# 5. Recommended Delivery Order

## Phase 0 — Architecture and Foundations

Build the shared platform pieces before building smart behavior.

Deliverables:

- system architecture baseline
- event taxonomy
- canonical schemas
- service ownership map
- repository structure
- environment and credential model
- audit logging approach

Primary output:

A foundation package that every agent can use.

## Phase 1 — Build and Test Spine

Stand up the operational core:

- Josephine
- Galileo
- Curie
- Faraday
- Tesla
- Fuze integration
- GitHub event handling
- artifact metadata capture

Primary output:

A build-and-test loop that reacts to GitHub events and produces durable machine-readable records.

## Phase 2 — Versioning and Traceability

Stand up the technical identity layer:

- Mercator
- Berners-Lee
- Jira linkage
- build-to-bug relationships
- release mapping records

Primary output:

Exact traceability from code and build to issue and release context.

## Phase 3 — Knowledge Capture

Stand up the first human-context workflow:

- Pliny
- Teams transcript ingestion
- summary extraction
- Jira follow-up creation or suggestion path

Primary output:

Meeting knowledge becomes structured and recoverable without manual copy/paste.

## Phase 4 — Operational Hardening

Harden what already exists:

- retries
- dead-letter handling
- idempotency
- metrics
- dashboards
- approval gates
- rollout discipline

Primary output:

A production-worthy internal platform, even if functionally narrow.

---

# 6. 90-Day Plan

# 6.1 Days 1–15 — Platform Design and Contract Freeze

## Objectives

Define the operating model and freeze the interfaces before implementation spreads.

## Workstreams

### A. Architecture
- finalize event-driven architecture
- choose transport layer for agent events
- define service boundaries
- define system-of-record ownership

### B. Schemas
- finalize:
  - Build Record
  - Test Execution Record
  - Release Record
  - Traceability Record
  - Meeting Summary Record
- define versioning strategy for schemas

### C. Security
- define service principals
- define secret storage model
- define approval paths
- define audit requirements

### D. Delivery mechanics
- choose repo layout
- choose deployment model
- define environments:
  - dev
  - staging
  - internal production

## Exit criteria

- architecture doc approved
- event envelope frozen
- canonical schemas frozen
- ownership model assigned
- MVP scope frozen

---

# 6.2 Days 16–30 — Josephine MVP

## Objectives

Build the first agent that creates durable technical facts.

## Josephine MVP capabilities

- consume GitHub PR and merge events
- retrieve Fuze configuration
- request build execution
- record build metadata
- publish build completion and failure events
- attach artifact metadata

## Required integrations

- GitHub / GitHub Actions
- Fuze
- artifact storage
- event bus

## Exit criteria

- PR-triggered builds work
- merge-triggered builds work
- build IDs are durable and queryable
- artifact manifests are stored
- failed builds emit usable events

---

# 6.3 Days 31–45 — Test Spine MVP

## Objectives

Attach meaningful test execution to the build spine.

## Test spine MVP capabilities

- Galileo selects a test plan based on trigger type
- Curie materializes executable test inputs
- Tesla tracks environment reservations
- Faraday runs PR-level test plans
- Faraday runs merge-level test plans
- publish test execution records
- emit pass/fail and coverage summaries

## Testing levels for MVP

### PR path
- unit tests
- fast functional tests
- mocked or reduced HIL path
- runtime target: under 10 minutes

### Main merge path
- expanded functional tests
- HIL when available
- runtime target: around 30 minutes

### Nightly path
- extended suite
- longer HIL coverage
- artifact-rich output

## Exit criteria

- Galileo consumes Josephine events
- Curie and Faraday consume Galileo outputs
- tests run automatically by trigger class
- results are queryable by build ID
- environment reservations are tracked
- coverage summaries are available

---

# 6.4 Days 46–60 — Mercator and Berners-Lee MVP

## Objectives

Create exact technical traceability.

## Mercator MVP capabilities

- map internal Fuze build IDs to external versions
- expose lookup by internal build ID
- expose reverse lookup by external version
- emit version mapping events

## Berners-Lee MVP capabilities

- associate Jira issues to build IDs
- associate test runs to build IDs
- create traceability views
- push issue comments or metadata updates into Jira
- flag missing build association on bugs

## Recommended first Jira behavior

Keep it narrow:

- on new bug intake, detect missing build identity
- comment with request for missing build context
- attach build and test evidence when available
- show release relevance where available

## Exit criteria

- engineers can start from a Jira issue and reach build/test facts
- engineers can start from a build and reach associated bugs
- internal and external version mapping works
- missing-build bug reports are flagged

---

# 6.5 Days 61–75 — Pliny MVP

## Objectives

Automate transcript capture and structured summary generation.

## Pliny MVP capabilities

- detect transcript availability from Teams
- ingest transcript automatically
- generate:
  - summary
  - decisions
  - action items
- publish summary to a defined target
- optionally create Jira follow-up suggestions

## Recommended first publishing target

Start with one target only:

- internal meeting summary store or repo

Optionally mirror key items into Jira only when confidence is high.

## Exit criteria

- transcript ingestion is automatic
- no manual copy/paste required
- summaries are consistent
- action item extraction is usable
- links between summary and meeting metadata are preserved

---

# 6.6 Days 76–90 — Hardening and Internal Rollout

## Objectives

Make the initial platform reliable enough for sustained internal use.

## Hardening work

### Reliability
- idempotent event handling
- retry strategy
- dead-letter queue
- timeout policy
- failure classification

### Observability
- per-agent metrics
- event lag metrics
- build success rates
- test pass rates
- traceability completion rates
- transcript processing success rates

### Operations
- deployment runbooks
- rollback plan
- support ownership
- escalation paths
- incident triage process

### Governance
- human approval gates
- audit log review
- exception handling workflow
- data retention policy

## Exit criteria

- platform operates in internal production
- support ownership is clear
- dashboards exist
- failure handling is documented
- at least one team can use the platform end-to-end

---

# 7. Recommended Team Structure

A small cross-functional strike team is enough for the first cycle.

## Core roles

### 1. Platform lead
Owns architecture, contracts, and technical decisions.

### 2. Integration engineer
Owns GitHub, Jira, Teams, and Fuze integration wiring.

### 3. Build/test systems engineer
Owns Josephine, Galileo, Curie, Faraday, Tesla, and environment orchestration.

### 4. Backend/data engineer
Owns event transport, record persistence, query layer, and auditability.

### 5. Product/program owner
Owns scope control, rollout, approvals, and user feedback.

In a smaller team, several of these can be combined.

---

# 8. Suggested Technical Architecture

## Core platform components

- event bus
- shared schema package
- agent services
- artifact metadata store
- traceability query service
- audit log
- operational dashboard layer

## Suggested service cut

### Shared platform
- event transport
- schemas
- auth
- audit
- storage abstractions

### Agent services
- josephine-service
- galileo-service
- curie-service
- faraday-service
- tesla-service
- mercator-service
- bernerslee-service
- pliny-service

### Integration adapters
- github-adapter
- jira-adapter
- teams-adapter
- fuze-adapter
- environment-manager-adapter

This keeps the system modular and lets you replace pieces without rewriting everything.

---

# 9. Dependency Map

## Josephine depends on
- GitHub integration
- Fuze integration
- artifact store
- event transport

## Galileo depends on
- Josephine events
- Curie
- Faraday
- Tesla
- artifact/result storage

## Mercator depends on
- Josephine build IDs
- release/version policy

## Berners-Lee depends on
- Jira integration
- Josephine records
- Galileo planning records
- Faraday execution records
- Mercator mappings

## Pliny depends on
- Teams integration
- transcript access
- summary storage target

---

# 10. MVP Success Metrics

The first cycle should be judged by concrete operational outcomes.

## Delivery metrics
- percent of PRs that produce valid build records
- percent of merge events that produce valid test records
- percent of Jira bugs linked to exact build IDs
- percent of build IDs that map to external versions
- percent of eligible meetings automatically summarized

## Quality metrics
- build record completeness
- test record completeness
- traceability completeness
- false-positive rate for Jira bug metadata flags
- usefulness rating for meeting summaries

## Reliability metrics
- event processing success rate
- retry success rate
- mean processing latency by agent
- failed event backlog count

---

# 11. Key Risks

## Risk 1 — Too much scope too early

If the team tries to build every agent at once, the platform will sprawl before the event and schema model stabilizes.

### Mitigation
Ship the spine first.

## Risk 2 — Weak identity discipline

If build IDs, issue keys, and test IDs are not treated as authoritative, traceability will collapse fast.

### Mitigation
Make identity enforcement a non-negotiable rule from day 1.

## Risk 3 — Test environment bottlenecks

HIL infrastructure can become the constraint long before agent logic does.

### Mitigation
Start with reservation-aware scheduling and tiered test plans.

## Risk 4 — Over-automation of human decisions

Releases, policy exceptions, and externally visible docs should not be fully automated early.

### Mitigation
Keep approval gates explicit.

## Risk 5 — Poor observability

A distributed agent platform fails in confusing ways if metrics and audit trails are weak.

### Mitigation
Treat observability as part of MVP, not post-MVP cleanup.

---

# 12. Recommended Backlog for Sprint Planning

## Sprint 1
- define event envelope
- define canonical schemas
- choose event transport
- create shared schema package
- create service scaffolding
- stand up audit logging skeleton

## Sprint 2
- implement GitHub adapter
- implement Fuze adapter
- implement Josephine happy path
- store build records
- emit build events

## Sprint 3
- implement Galileo test-plan selection
- implement Curie test-input generation
- integrate Tesla environment reservation
- execute PR tests through Faraday
- store test execution records
- emit coverage summaries

## Sprint 4
- implement Mercator mapping logic
- implement Jira adapter
- implement Berners-Lee happy path
- link bugs to builds and tests
- push traceability comments to Jira

## Sprint 5
- implement Teams transcript ingestion
- implement Pliny summarization pipeline
- publish summary records
- generate action item drafts

## Sprint 6
- harden retries
- add dashboards
- add dead-letter handling
- document operations
- pilot with one internal team

---

# 13. Final Recommendation

Do not treat this as an AI project first.

Treat it as an engineering systems project with AI-enabled services inside it.

That framing matters.

If the event model, identity model, and traceability model are sound, the agents become practical and trustworthy.

If those foundations are weak, smarter models will only make the confusion happen faster.

The right first move is to build the narrow operational spine:

- Josephine
- Galileo
- Curie
- Faraday
- Tesla
- Mercator
- Berners-Lee
- Pliny

Then harden it.

Then expand.
