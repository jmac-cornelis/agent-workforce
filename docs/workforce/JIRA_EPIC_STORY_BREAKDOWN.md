# AI Agent Workforce — Jira Epic / Story Breakdown

> **Generated**: 2026-03-14
> **Source**: `ai_agents_spec_complete.md`, `ai_agent_implementation_roadmap.md`, per-agent `agents/*_PLAN.md` files
> **Story Points**: Fibonacci scale (1, 2, 3, 5, 8, 13)
> **Delivery Waves**: 6 waves aligned to 90-day roadmap + future agents

---

## How to Read This Document

- **Epic** = one agent or platform capability (top-level Jira Epic)
- **Story** = one deliverable unit of work (Jira Story under the Epic)
- **SP** = story points (Fibonacci)
- **Depends On** = blocking dependency (must be done first)
- **Sprint** = suggested sprint assignment (S1–S8)
- **AC** = acceptance criteria (definition of done)

---

## Wave 0 — Platform Foundation

### Epic: PLATFORM-FOUNDATION — Shared Infrastructure

All agents depend on this. Must be complete before any agent work begins.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| PF-1 | **Design and implement canonical event envelope** — Define standard envelope schema (`event_id`, `event_type`, `producer`, `occurred_at`, `correlation_id`, `subject_id`, `payload`). Implement serialization, validation, and versioning. | 5 | S1 | — | Envelope schema published; serialization library passes round-trip tests; versioning strategy documented |
| PF-2 | **Define canonical data schemas** — BuildRecord, TestExecutionRecord, ReleaseRecord, TraceabilityRecord, DocumentationRecord, MeetingSummaryRecord as JSON Schema with validation library. | 5 | S1 | — | All 6 schemas defined with JSON Schema; validation library with test coverage; example payloads for each |
| PF-3 | **Set up event transport** — Select and deploy event bus (e.g., NATS, RabbitMQ, or Kafka). Implement publish/subscribe with idempotency keys, retry, and dead-letter queue. | 8 | S1 | PF-1 | Event bus deployed; pub/sub working with idempotency; DLQ configured; retry policy documented |
| PF-4 | **Implement GitHub adapter** — Consume PR, push, merge, tag, workflow events. Produce status checks, comments, release notes, links. Webhook receiver + API client. | 5 | S1 | PF-1 | PR/merge/tag events consumed and published to event bus; status checks and PR comments working E2E |
| PF-5 | **Implement Jira adapter** — Consume bug/ticket/release/priority events. Produce build links, flags, comments, trace links. Webhook receiver + API client. | 5 | S2 | PF-1 | Jira issue events consumed; write-backs (comments, links, flags) working E2E |
| PF-6 | **Implement Teams adapter** — Consume meeting-ended, transcript-ready events. Produce summary posts, approval prompts, escalations. | 5 | S2 | PF-1 | Meeting-ended events detected; transcript payloads retrievable; summary posting working |
| PF-7 | **Implement Fuze adapter** — Interface with Fuze CLI for build config, build-ID extraction, policy, release metadata. Library wrapper around fuze.py/build.py. | 5 | S1 | PF-1 | Fuze config parsed; build requests submittable; build IDs extractable; release metadata readable |
| PF-8 | **Implement Environment Manager adapter** — Interface with ATF resource files for environment availability, capability, topology, reservation state. | 3 | S2 | PF-1 | ATF resource files parsed; environment catalog queryable; reservation state readable |
| PF-9 | **Security and governance framework** — Service principals per agent, approval gate framework for irreversible actions, audit log infrastructure. | 8 | S1 | — | Service principals provisioned; approval gate API working; audit log captures all agent actions with correlation IDs |
| PF-10 | **Observability and dashboards** — Per-agent metrics (latency, success, error, throughput), trace ID propagation, dashboard templates, alerting rules. | 5 | S2 | PF-3 | Metrics emitted by event bus; trace IDs propagated; dashboard template deployed; alert rules for DLQ depth |
| PF-11 | **Repository scaffolding and CI** — Monorepo or multi-repo layout, shared library packages, CI pipeline for build/test/lint, deployment model, environment configs. | 5 | S1 | — | Repo structure created; CI pipeline runs lint+test+build; deployment model documented; dev/staging environments provisioned |
| PF-12 | **Artifact metadata store** — Durable storage for build artifacts, test results, generated docs, meeting summaries. Queryable by build ID, correlation ID. | 5 | S1 | PF-2 | Store deployed; CRUD operations working; queryable by build_id and correlation_id; retention policy configured |

**Wave 0 Total: 64 SP**

---

## Wave 1 — Build & Test Spine

### Epic: JOSEPHINE — Build & Package Agent

> Wraps Fuze build/package into an API-driven service. First agent online.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| JOS-1 | **Extract Fuze core library** — Refactor fuze.py/build.py into importable library. Remove singleton/global state, replace interactive prompts with policy, replace plugin side effects with event sinks. Parity harness ensures CLI still works. | 8 | S2 | PF-7, PF-11 | Library entrypoint exists; CLI parity harness passes; no interactive prompts in library path; event sinks wired |
| JOS-2 | **Implement Josephine API service** — `POST /v1/build-jobs`, `GET /v1/build-jobs/{id}/status`, `GET /v1/build-jobs/{id}/events`, `GET /v1/build-jobs/{id}/artifacts`, cancel, retry, drain endpoints. | 5 | S2 | JOS-1, PF-9 | All API endpoints functional; OpenAPI spec published; auth via service principal; request validation working |
| JOS-3 | **Implement Josephine worker** — FIFO queue consumer, ephemeral Docker workspaces, one build per worker, lease/heartbeat model. Executes builds via Fuze core library. | 8 | S2 | JOS-1, PF-3 | Worker consumes queue; builds execute in Docker; heartbeats emitted; workspace cleaned on completion/failure |
| JOS-4 | **Build metadata and artifact recording** — Persist BuildRecord to metadata store. Record artifact manifests. Emit `build.completed`, `build.failed`, `artifact.published` events. | 5 | S2 | JOS-3, PF-2, PF-12 | BuildRecord persisted for every build; artifact manifest queryable; events emitted on bus; correlation IDs present |
| JOS-5 | **GitHub PR/merge trigger integration** — Consume GitHub PR and merge events via adapter. Auto-trigger builds. Post build status back to GitHub. | 5 | S2 | JOS-2, PF-4 | PR events trigger builds; merge events trigger builds; GitHub status checks updated; build links posted as PR comments |
| JOS-6 | **Prove on atf/build/atf.json** — End-to-end validation using ATF build config as first target. Parity checks against manual Fuze builds. Failure classification. | 5 | S3 | JOS-5 | ATF builds succeed via Josephine; output matches manual Fuze build; failure classes documented; logs sufficient for debugging |
| JOS-7 | **Harden security and operations** — Workspace isolation (no shared mutable state, restricted network), short-lived credentials via SecretProvider, alerts on stuck/failed builds, graceful teardown. | 5 | S3 | JOS-6, PF-9 | No raw creds in requests; workspace_profile_ref resolves via SecretProvider; alerts fire on stuck builds; teardown verified |

**Josephine Total: 41 SP**

---

### Epic: ADA — Test Planner Agent

> Turns build context + trigger type into durable TestPlans.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| ADA-1 | **Implement planning compatibility layer** — Durable TestPlan objects linked to build IDs. TestPlanRequest/TestPlan/CoverageSummary schemas. | 5 | S3 | PF-2, JOS-4 | TestPlan schema defined; plans persisted with build_id linkage; plans queryable by build_id |
| ADA-2 | **Implement trigger-to-plan selection** — PolicyResolver maps trigger class (PR/merge/nightly/release) to plan class. Respects Fuze Test suite selection precedence. | 5 | S3 | ADA-1 | PR→unit+fast, merge→expanded+HIL, nightly→extended, release→cert+policy-gated; policy decisions logged |
| ADA-3 | **Implement Galileo API** — `POST /v1/test-plans/select`, `GET /v1/test-plans/{id}`, `GET /v1/test-plans/{id}/events`. Emit `test.plan_selected`, `coverage_gap_detected`. | 3 | S3 | ADA-2, PF-3 | API endpoints functional; events emitted; plans queryable; OpenAPI spec published |
| ADA-4 | **Fuze Test dry-run planning mode** — Add dry-run mode to run-atf.py that outputs machine-readable plan without executing. Galileo consumes this for plan validation. | 5 | S3 | ADA-2 | Dry-run flag added to run-atf.py; machine-readable output parseable by Galileo; no side effects in dry-run |
| ADA-5 | **Coverage feedback loop** — CoverageAdvisor tracks coverage gaps across runs. Emits `coverage_gap_detected` when plan leaves known areas untested. | 5 | S4 | ADA-3 | Coverage gaps detected and emitted; gap records queryable; advisory signals sent to downstream consumers |

**Galileo Total: 23 SP**

---

### Epic: CURIE — Test Generator Agent

> Materializes Galileo TestPlans into concrete Fuze Test runtime inputs.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| CUR-1 | **Implement deterministic materialization** — PlanMaterializer + SuiteResolver + RuntimeInputBuilder. Converts TestPlan into GeneratedTestInput with reproducible version hash. | 8 | S3 | ADA-3, PF-2 | TestPlan→GeneratedTestInput conversion working; version hash reproducible; generation manifest recorded |
| CUR-2 | **Implement Curie API** — `POST /v1/test-inputs/generate`, `GET /v1/test-inputs/{id}`, `GET /v1/test-inputs/{id}/artifacts`. | 3 | S3 | CUR-1 | API endpoints functional; generated inputs queryable; artifacts downloadable; OpenAPI spec published |
| CUR-3 | **Runtime overlay support** — Generate runtime overlay dirs/archives for environment-specific config without source edits. | 5 | S4 | CUR-2 | Overlays generated per environment class; overlays applied without source modification; overlay archives versioned |
| CUR-4 | **Fuze Test generated-input support** — Add first-class generated-input consumption to Fuze Test. Stable suite-resolution output. | 5 | S4 | CUR-2 | Fuze Test accepts generated inputs; suite resolution output machine-readable; no regression in manual test flows |

**Curie Total: 21 SP**

---

### Epic: TESLA — Test Environment Manager Agent

> Shared reservation service for HIL and mock environments.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| TES-1 | **Implement environment catalog** — Parse ATF resource files into EnvironmentCatalog. Track env_id, location, class, hardware_profile, topology_profile, DUT set, capabilities, status. | 5 | S3 | PF-8 | ATF resource files parsed; catalog queryable by capability/class/status; catalog refreshes on file change |
| TES-2 | **Implement reservation service** — Request→match→grant/reject→heartbeat→release/expire lifecycle. CapabilityMatcher for requirement-to-environment matching. | 8 | S3 | TES-1, PF-3 | Reservations grantable; heartbeat keeps reservation alive; expiry on missed heartbeat; conflict detection working |
| TES-3 | **Implement Tesla API** — `GET /v1/environments`, `POST /v1/reservations`, heartbeat, release, quarantine, maintenance endpoints. | 3 | S3 | TES-2 | All API endpoints functional; OpenAPI spec published; reservation lifecycle E2E working |
| TES-4 | **Health monitoring and operator controls** — EnvironmentHealthMonitor + MaintenanceAdapter. Quarantine/maintenance workflows. Degraded status detection. | 5 | S4 | TES-3 | Health probes running; quarantine/maintenance toggles working; degraded environments excluded from matching |
| TES-5 | **ATF reservation-aware execution guard** — ATF checks for valid reservation before test execution. Prevents uncoordinated environment access. | 3 | S4 | TES-3 | ATF rejects execution without valid reservation; reservation ID passed through execution context |

**Tesla Total: 24 SP**

---

### Epic: FARADAY — Test Executor Agent

> Wraps Fuze Test execution with structured state, results, and failure classification.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| FAR-1 | **Implement basic test execution wrapper** — TestRunDispatcher + FuzeTestInvoker. Launch ATF, link to build IDs, capture raw artifacts. Execution stages: accepted→running→completed/failed. | 8 | S3 | CUR-2, TES-3, JOS-4 | Test runs launchable via API; linked to build_id; raw artifacts captured; basic pass/fail status recorded |
| FAR-2 | **Implement structured execution state** — Full stage machine (accepted→waiting_for_env→env_reserved→staging→invoking→running→collecting→publishing→completed/failed/cancelled). ResultNormalizer + RunMonitor. | 5 | S3 | FAR-1 | All stages tracked; stage transitions emitted as events; results normalized into TestExecutionRecord |
| FAR-3 | **Implement Faraday API** — `POST /v1/test-runs`, cancel, `GET /v1/test-runs/{id}/status`, events, results. Emit `test.execution_completed`. | 3 | S3 | FAR-2, PF-3 | API endpoints functional; events emitted; results queryable by build_id and test_run_id; OpenAPI spec published |
| FAR-4 | **Failure classification** — Classify failures: bad_request, missing_artifacts, reservation_failure, atf_config_failure, pta_failure, dut_env_failure, timeout, infra_loss. Retry only transient infra failures before execution starts. | 5 | S4 | FAR-3 | All failure classes implemented; failure class recorded in TestFailureRecord; transient retries working; non-transient failures terminal |
| FAR-5 | **Tesla reservation integration hardening** — Reservation gating, heartbeats during execution, timeout handling, graceful release on completion/failure. | 5 | S4 | FAR-3, TES-3 | Execution blocked without reservation; heartbeats sent during run; reservation released on completion; timeout triggers graceful abort |
| FAR-6 | **Fuze Test integration improvements** — Machine-readable execution state, stable result envelope, structured failure classes, cancellation support, dry-run validation in Fuze Test. | 5 | S4 | FAR-3 | Fuze Test outputs machine-readable state; result envelope stable; cancellation supported; dry-run validates config without execution |

**Faraday Total: 31 SP**

---

**Wave 1 Total: 140 SP**

---

## Wave 2 — Versioning & Traceability

### Epic: BABBAGE — Version Mapping Agent

> Maps Fuze internal build IDs to external customer-facing release versions.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| BAB-1 | **Implement basic version mapping** — VersionMapper + VersionMappingRequest/Record schemas. `POST /v1/version-mappings`, `GET` by mapping_id, build_id, external_version. | 5 | S4 | JOS-4, PF-2 | Mappings creatable; queryable forward (build→version) and reverse (version→build); records persisted |
| BAB-2 | **Conflict detection and handling** — ConflictDetector for: already_assigned, incompatible_mapping, scope_mismatch, non_eligible_build, ambiguous_hint. No silent re-pointing. | 5 | S4 | BAB-1 | All conflict types detected; conflicts block mapping creation; conflict records queryable; no silent overwrites |
| BAB-3 | **Lineage and supersession tracking** — LineageRecorder tracks version lineage chains. Explicit supersession records. CompatibilityRecorder for cross-version compatibility. | 5 | S5 | BAB-2 | Lineage chains queryable; supersession explicit; compatibility records maintained; version.mapped events emitted |
| BAB-4 | **Fuze release integration** — Stable release-version extraction from Fuze. Stable release record lookup. Explicit replacement metadata. Emit `version.mapped`, `mapping_conflict_detected`. | 5 | S5 | BAB-3, PF-7 | Fuze release versions extracted reliably; release records queryable; events emitted on mapping and conflict |
| BAB-5 | **Confirmation workflow** — `POST /v1/version-mappings/{id}/confirm` for human approval of ambiguous or high-risk mappings. | 3 | S5 | BAB-2 | Confirmation endpoint working; unconfirmed mappings flagged; confirmed mappings promoted to authoritative |

**Mercator Total: 23 SP**

---

### Epic: LINNAEUS — Traceability Agent

> Maintains queryable relationships between requirements, issues, commits, builds, tests, releases, versions.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| LIN-1 | **Implement build-issue linkage** — RelationshipResolver + TraceStore. Assert `issue_affects_build`, `issue_fixed_in_build` relationships. `POST /v1/trace/assert`, `GET /v1/trace/builds/{id}/issues`. | 5 | S4 | JOS-4, PF-5 | Build↔issue links assertable; queryable in both directions; trace records persisted with correlation IDs |
| LIN-2 | **Implement test-build linkage** — Assert `build_validated_by_test_run` relationships. `GET /v1/trace/builds/{id}/test-runs`. | 3 | S4 | LIN-1, FAR-3 | Test run↔build links assertable; queryable; linked to TestExecutionRecord |
| LIN-3 | **Implement release-version lineage** — Assert `build_promoted_to_release`, `build_mapped_to_external_version`. Integrate with Mercator version records. | 5 | S5 | LIN-2, BAB-1 | Release↔build↔version links queryable; lineage navigable end-to-end |
| LIN-4 | **Implement requirement coverage** — Assert `requirement_implemented_by_commit`, `requirement_verified_by_test_run`. CoverageGapDetector flags unverified requirements. | 5 | S5 | LIN-3 | Requirement↔commit↔test links assertable; coverage gaps detected and emitted; gap records queryable |
| LIN-5 | **Implement trace query service** — `GET /v1/trace/issues/{id}`, `/releases/{id}`, `/requirements/{id}`, `/gaps`. Full trace view from any anchor. | 5 | S5 | LIN-4 | Full trace navigable from any identity anchor; trace views return complete relationship graph |
| LIN-6 | **Jira write-back integration** — JiraTracePublisher pushes traceability comments, evidence links, missing-build flags, trace view links to Jira issues. | 5 | S5 | LIN-5, PF-5 | Jira issues receive trace comments; evidence links clickable; missing-build flags visible; no duplicate write-backs |

**Berners-Lee Total: 28 SP**

---

**Wave 2 Total: 51 SP**

---

## Wave 3 — Human Context

### Epic: HERODOTUS — Knowledge Capture Agent

> Ingests Teams meeting transcripts and produces structured summaries, decisions, and action items.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| HER-1 | **Implement transcript ingestion** — TranscriptIngestor + MeetingNormalizer. Detect meeting-ended events, retrieve transcript payloads, normalize into MeetingRecord + TranscriptRecord. | 5 | S5 | PF-6, PF-2 | Meeting-ended events trigger ingestion; transcripts normalized; MeetingRecord persisted; no manual copy/paste required |
| HER-2 | **Implement summary engine** — SummaryEngine generates MeetingSummaryRecord from transcript. Distinguishes fact/decision/action/unresolved. Minimal quotes, uncertain attribution marked. | 8 | S5 | HER-1 | Summaries generated; fact/decision/action/unresolved classified; attribution uncertainty marked; summaries queryable |
| HER-3 | **Implement action extraction** — ActionExtractor produces ActionItemDraft records. Actions are drafts until accepted. DecisionRecord for explicit decisions. | 5 | S5 | HER-2 | Action items extracted as drafts; decisions recorded separately; draft→accepted workflow working |
| HER-4 | **Implement Pliny API** — `POST /v1/meetings/ingest`, `/summarize`, `/publish`. `GET /v1/meetings/{id}`, `/summary`. | 3 | S5 | HER-3 | API endpoints functional; summaries queryable; publication triggerable; OpenAPI spec published |
| HER-5 | **Controlled publication** — PublicationCoordinator publishes to internal meeting-summary store. Optional Jira follow-up suggestions (for Drucker). Doc suggestions (for Hemingway). | 5 | S6 | HER-4, PF-5 | Summaries published to knowledge store; Jira follow-up suggestions emitted; doc suggestions emitted; review gate before external publish |

**Pliny Total: 26 SP**

---

**Wave 3 Total: 26 SP**

---

## Wave 4 — Quality, Release, Docs & Bugs

### Epic: LINUS — Code Review Agent

> Evaluates PRs against code-quality and review-policy rules.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| LIN-R-1 | **Implement structured PR review** — DiffAnalyzer + PolicyProfileResolver + FindingEngine. Review categories: correctness_risk, safety_risk, concurrency_risk, maintainability_risk, policy_violation, documentation_impact, test_attention_needed. | 8 | S6 | PF-4, PF-2 | PR diffs analyzed; findings categorized; policy profiles (kernel, embedded_cpp, python_utility) applied; findings structured |
| LIN-R-2 | **Implement Linus API** — `POST /v1/reviews/pr`, `GET /v1/reviews/{id}`, `/findings`, `POST /v1/reviews/{id}/publish`. | 3 | S6 | LIN-R-1 | API endpoints functional; reviews queryable; findings filterable by category; OpenAPI spec published |
| LIN-R-3 | **GitHub review integration** — ReviewPublisher posts inline comments, PR summary, advisory status checks to GitHub. | 5 | S6 | LIN-R-2, PF-4 | Inline comments posted on PR; summary comment posted; advisory status check set; no duplicate comments on re-review |
| LIN-R-4 | **Cross-agent impact signals** — ImpactSignalEmitter sends doc impact→Hemingway, test attention→Galileo, build risk→Josephine. Emit `review.completed`, `review.policy_failed`, `documentation_impact_detected`. | 5 | S7 | LIN-R-3 | Impact signals emitted; downstream agents receive and can act on signals; events on bus with correlation IDs |
| LIN-R-5 | **Repository-specific tuning** — Per-repo policy profile configuration. Override rules. Audit trail for policy exceptions. | 3 | S7 | LIN-R-4 | Per-repo profiles configurable; overrides audited; exception trail queryable |

**Linus Total: 24 SP**

---

### Epic: HEDY — Release Orchestrator Agent

> Orchestrates release decisions using the Fuze release model.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| HED-1 | **Implement release evaluation** — ReleaseEvaluator + ReadinessSummarizer. Evaluate build eligibility, test evidence, blocking defects, version mapping, branch policy. Produce ReleaseReadinessSummary. | 8 | S6 | JOS-4, FAR-3, BAB-1, LIN-5 | Release candidates evaluated; readiness summary includes build/test/defect/version/branch status; non-eligible builds rejected |
| HED-2 | **Implement Humphrey API** — `POST /v1/releases/evaluate`, `/promote`, `/block`, `/deprecate`. `GET /v1/releases/{id}`, `/summary`. Emit `release.candidate_created`, `approval_requested`. | 3 | S6 | HED-1, PF-3 | API endpoints functional; events emitted; release state queryable; OpenAPI spec published |
| HED-3 | **Promotion orchestration** — StagePromoter manages sit→qa→release→deprecated transitions. ApprovalCoordinator enforces human approval for production promotion. | 8 | S7 | HED-2, PF-9 | Stage transitions enforced; human approval required for release promotion; approval audit trail; emit `release.promoted`, `release.blocked` |
| HED-4 | **Release matrix support** — ReleaseMatrixResolver handles 3D version matrix: time × hardware targets × customer targets. | 5 | S7 | HED-3 | Matrix-aware release candidates; per-HW and per-customer targeting; matrix queryable |
| HED-5 | **Fuze release integration** — Non-interactive release API in Fuze. Machine-readable release evaluation. Stable release-state output. Explicit automation hooks. | 5 | S7 | HED-3, PF-7 | Fuze release operations callable without prompts; release state machine-readable; automation hooks documented |

**Humphrey Total: 29 SP**

---

### Epic: HYPATIA — Documentation Agent

> Generates documentation from authoritative system records.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| HYP-1 | **Implement doc impact analysis** — DocImpactAnalyzer consumes source changes, review findings, build metadata, test outcomes. Produces DocumentationImpactRecord. | 5 | S6 | LIN-R-4, JOS-4, FAR-3 | Impact records generated from source/review/build/test signals; impact severity classified; records queryable |
| HYP-2 | **Implement internal doc generation** — SourceSynthesizer + DocGenerator. Generate as-built docs from build metadata + source. Grounded in fuze/docs/source Sphinx tree. | 8 | S7 | HYP-1, PF-2 | As-built docs generated; grounded in Sphinx source; docs linked to build_id; generation manifest recorded |
| HYP-3 | **Implement Hemingway API** — `POST /v1/docs/impact`, `/generate`, `/publish`. `GET /v1/docs/{id}`, `/patch`. | 3 | S7 | HYP-2 | API endpoints functional; docs queryable; patches reviewable; OpenAPI spec published |
| HYP-4 | **Engineering and user doc support** — Generate engineering_reference and user_guide doc classes. DocValidator checks factual grounding. | 5 | S7 | HYP-3 | Engineering and user docs generated; validator catches ungrounded claims; doc classes correctly classified |
| HYP-5 | **Controlled publication** — PublicationCoordinator manages review gate before external publish. Sphinx/ReadTheDocs integration. Emit `docs.published`. | 5 | S8 | HYP-4, PF-9 | Review gate enforced; docs publishable to ReadTheDocs; publication audit trail; events emitted |

**Hemingway Total: 26 SP**

---

### Epic: NIGHTINGALE — Bug Investigation Agent

> Reacts to Jira bugs, qualifies reports, assembles context, drives reproduction.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| NIG-1 | **Implement bug intake and context assembly** — BugIntakeNormalizer + ContextAssembler + MissingDataDetector. Consume Jira bug events, pull trace/build/test/release evidence. | 8 | S6 | PF-5, LIN-5, JOS-4, FAR-3 | Bug events trigger intake; context assembled from trace/build/test/release; missing data identified and flagged |
| NIG-2 | **Implement Nightingale API** — `POST /v1/bugs/investigate`, `/reproduce`, `/summarize`. `GET /v1/bugs/{id}`, `/attempts`. | 3 | S6 | NIG-1 | API endpoints functional; investigations queryable; reproduction attempts tracked; OpenAPI spec published |
| NIG-3 | **Targeted reproduction workflow** — ReproductionPlanner + ReproductionCoordinator. Request reproduction via Galileo/Curie/Faraday/Tesla. Track ReproductionAttempt records. | 8 | S7 | NIG-2, ADA-3, CUR-2, FAR-3, TES-3 | Reproduction requests dispatched; attempts tracked with durable records; repro results linked to bug; no repro claim without evidence |
| NIG-4 | **Failure signatures and clustering** — FailureSignatureRecord for recurring patterns. Cluster similar failures across bugs. | 5 | S7 | NIG-3 | Failure signatures extracted; similar failures clustered; signature records queryable |
| NIG-5 | **Investigation summary and decision support** — InvestigationSummarizer produces structured summary separating facts/hypotheses/recommendations. Emit `bug.investigation_summarized`. | 5 | S8 | NIG-4 | Summaries generated; facts/hypotheses/recommendations separated; summaries queryable; events emitted |

**Nightingale Total: 29 SP**

---

**Wave 4 Total: 108 SP**

---

## Wave 5 — Project Management (Future Agents)

### Epic: DRUCKER — Jira Coordinator Agent

> Keeps Jira operationally coherent — triage, hygiene, routing, evidence-backed nudges.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| DRU-1 | **Implement issue triage engine** — IssueTriageEngine + WorkflowPolicyEngine. Evaluate new/updated issues for completeness, routing, priority. Grounded in jirafuze.py and _jira.py patterns. | 8 | S7 | PF-5, LIN-5 | New issues triaged; missing metadata flagged; routing suggestions generated; policy decisions logged |
| DRU-2 | **Implement Drucker API** — `POST /v1/jira/evaluate`, `/recommend`, `/apply`. `GET /v1/jira/coordination/{id}`, `/hygiene`. | 3 | S7 | DRU-1 | API endpoints functional; coordination records queryable; hygiene reports generated; OpenAPI spec published |
| DRU-3 | **Evidence-backed workflow coordination** — EvidenceCorrelator links Jira issues to build/test/trace evidence. WorkflowRecommendation with justification. RoutingDecision records. | 5 | S8 | DRU-2, LIN-5, JOS-4, FAR-3 | Recommendations backed by evidence; routing decisions auditable; stale issue detection working |
| DRU-4 | **Controlled Jira write-back** — JiraWritebackCoordinator applies recommendations. Rule-aware write-back mode (suggest vs. auto-apply). IssueAuditRecord for all changes. | 5 | S8 | DRU-3, PF-9 | Write-backs applied with audit trail; suggest mode shows recommendations without applying; auto-apply mode for low-risk actions only |
| DRU-5 | **Hygiene reporting** — Periodic hygiene reports: stale issues, missing metadata, blocked work, routing anomalies. | 3 | S8 | DRU-4 | Hygiene reports generated on schedule; reports queryable; anomalies classified |

**Drucker Total: 24 SP**

---

### Epic: GANTT — Project Planner Agent

> Converts Jira work state + technical evidence + meeting decisions into planning outputs.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| GAN-1 | **Implement planning snapshots** — BacklogInterpreter + PlanningSummarizer. Consume Jira issues/epics, priorities, release targets. Produce PlanningSnapshot. | 8 | S7 | PF-5, DRU-1 | Planning snapshots generated from Jira state; snapshots queryable; scope summary included |
| GAN-2 | **Implement Gantt API** — `POST /v1/planning/snapshot`. `GET /v1/planning/snapshots/{id}`, `/milestones`, `/dependencies`. | 3 | S7 | GAN-1 | API endpoints functional; snapshots queryable; OpenAPI spec published |
| GAN-3 | **Dependency mapping** — DependencyMapper builds dependency graphs from Jira links + technical evidence (build/test/trace). | 5 | S8 | GAN-2, LIN-5, JOS-4 | Dependency graphs generated; critical path identified; blocked work highlighted |
| GAN-4 | **Milestone proposals** — MilestonePlanner generates MilestoneProposal records based on scope, dependencies, release targets. | 5 | S8 | GAN-3 | Milestone proposals generated; proposals linked to dependency graph; scope risk flagged |
| GAN-5 | **Risk projection and Jira feedback** — RiskProjector identifies scope drift, stale work, blocked handoffs. Optional Jira comment suggestions. | 5 | S8 | GAN-4 | Risk records generated; drift signals emitted; Jira feedback suggestions produced (not auto-applied) |

**Gantt Total: 26 SP**

---

### Epic: BROOKS — Delivery Manager Agent

> Monitors execution against plan, detects schedule risk and coordination failure.

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| BRO-1 | **Implement delivery snapshots** — StatusAggregator consumes Gantt snapshots, Jira state, build/test/release evidence. Produce DeliverySnapshot. | 5 | S8 | GAN-2, JOS-4, FAR-3, HED-2 | Delivery snapshots generated; aggregated from planning + execution evidence; snapshots queryable |
| BRO-2 | **Implement Shackleton API** — `POST /v1/delivery/snapshot`. `GET /v1/delivery/snapshots/{id}`, `/status`, `/risks`. | 3 | S8 | BRO-1 | API endpoints functional; delivery status queryable; OpenAPI spec published |
| BRO-3 | **Risk detection** — DeliveryRiskDetector classifies schedule risk, blocked handoffs, resource contention. DeliveryRiskRecord with severity and evidence. | 5 | S8 | BRO-2 | Risks detected and classified; risk records include evidence links; severity levels assigned |
| BRO-4 | **Forecasting** — ForecastEngine produces ForecastRecord with confidence intervals based on historical velocity and current state. | 5 | S8 | BRO-3 | Forecasts generated; confidence intervals included; forecasts linked to delivery snapshots |
| BRO-5 | **Human reporting and escalation** — StatusPublisher + EscalationCoordinator. StatusSummary for stakeholders. EscalationRecord for blocked/at-risk items. | 5 | S8 | BRO-4 | Status summaries generated; escalation records created for at-risk items; escalation prompts sent (not auto-resolved) |

**Shackleton Total: 23 SP**

---

**Wave 5 Total: 73 SP**

---

## Wave 6 — Hardening & Pilot

### Epic: HARDENING — Production Readiness

| ID | Story | SP | Sprint | Depends On | AC |
|----|-------|----|--------|------------|----|
| HAR-1 | **Idempotent event handling audit** — Verify all agents handle duplicate events correctly. Fix any non-idempotent handlers. | 5 | S6 | All Wave 1–3 agents | All agents pass duplicate-event tests; no side effects on replay; DLQ empty after replay |
| HAR-2 | **Retry and dead-letter queue hardening** — Verify retry policies, DLQ routing, failure classification across all agents. Runbooks for DLQ drain. | 5 | S6 | HAR-1 | Retry policies documented per agent; DLQ routing verified; drain runbooks written and tested |
| HAR-3 | **End-to-end flow validation** — PR→build→test→trace→Jira flow. Merge→build→test→version→trace flow. Bug→investigate→repro flow. Meeting→summary→actions flow. | 8 | S7 | All Wave 1–4 agents | All 4 flows pass E2E; correlation IDs traceable across full flow; no orphaned records |
| HAR-4 | **Dashboard and alerting deployment** — Per-agent dashboards (latency, success, error, throughput). Cross-agent flow dashboards. Alert rules for SLO violations. | 5 | S7 | PF-10 | Dashboards deployed; per-agent and cross-agent views working; alerts fire on SLO breach |
| HAR-5 | **Approval gate validation** — Verify human approval required for: release promotion, review policy override, traceability exception, external doc publish. | 3 | S7 | PF-9 | All 4 approval gates enforced; bypass attempts blocked; approval audit trail complete |
| HAR-6 | **Data retention and cleanup** — Retention policies for build records, test results, meeting summaries, trace records. Automated cleanup jobs. | 3 | S8 | PF-12 | Retention policies configured; cleanup jobs running; no data loss within retention window |
| HAR-7 | **Runbooks and operational documentation** — Per-agent runbooks (startup, shutdown, failure recovery, scaling). Incident response playbook. | 5 | S8 | All agents | Runbooks written for all 15 agents; incident playbook covers top 10 failure scenarios; reviewed by ops |
| HAR-8 | **Internal pilot rollout** — Deploy to production with limited scope (1-2 repos, 1 team). Monitor for 2 weeks. Collect feedback. | 8 | S8 | HAR-1 through HAR-7 | Pilot deployed; 2-week monitoring clean; feedback collected; go/no-go decision documented |

**Hardening Total: 42 SP**

---

**Wave 6 Total: 42 SP**

---

## Summary

| Wave | Focus | Epics | Stories | Total SP |
|------|-------|-------|---------|----------|
| 0 | Platform Foundation | 1 | 12 | 64 |
| 1 | Build & Test Spine | 5 (Josephine, Galileo, Curie, Tesla, Faraday) | 28 | 140 |
| 2 | Versioning & Traceability | 2 (Mercator, Berners-Lee) | 11 | 51 |
| 3 | Human Context | 1 (Pliny) | 5 | 26 |
| 4 | Quality, Release, Docs, Bugs | 4 (Linus, Humphrey, Hemingway, Nightingale) | 20 | 108 |
| 5 | Project Management (Future) | 3 (Drucker, Gantt, Shackleton) | 15 | 73 |
| 6 | Hardening & Pilot | 1 | 8 | 42 |
| **Total** | | **17 Epics** | **99 Stories** | **504 SP** |

---

## Dependency Graph (Critical Path)

```
PF-1/PF-2/PF-9/PF-11 (S1)
    └── PF-3/PF-4/PF-7/PF-12 (S1)
        └── JOS-1→JOS-5 (S2)
            ├── ADA-1→ADA-3 (S3)
            │   └── CUR-1→CUR-2 (S3)
            ├── TES-1→TES-3 (S3)
            │   └── FAR-1→FAR-3 (S3)
            ├── BAB-1→BAB-2 (S4)
            │   └── LIN-3 (S5)
            └── LIN-1→LIN-2 (S4)
                └── LIN-5→LIN-6 (S5)
                    ├── HED-1 (S6)
                    ├── NIG-1 (S6)
                    └── DRU-1 (S7)
                        └── GAN-1 (S7)
                            └── BRO-1 (S8)

PF-6 (S2)
    └── HER-1→HER-5 (S5-S6)

PF-4 (S1)
    └── LIN-R-1→LIN-R-4 (S6-S7)
        └── HYP-1→HYP-5 (S6-S8)
```

---

## Sprint Loading (Approximate)

| Sprint | SP Load | Key Deliverables |
|--------|---------|------------------|
| S1 | ~48 | Event envelope, schemas, transport, GitHub/Fuze adapters, security, repo scaffolding, artifact store |
| S2 | ~59 | Jira/Teams/Env adapters, observability, Josephine full MVP |
| S3 | ~68 | Galileo, Curie, Tesla, Faraday MVPs (test spine online) |
| S4 | ~46 | Mercator MVP, Berners-Lee build/test linkage, Faraday hardening, Galileo coverage |
| S5 | ~51 | Mercator lineage, Berners-Lee full trace + Jira write-back, Pliny MVP |
| S6 | ~56 | Linus, Humphrey, Hemingway, Nightingale MVPs, hardening audit |
| S7 | ~56 | Linus/Humphrey/Hemingway/Nightingale hardening, Drucker, Gantt, E2E validation |
| S8 | ~54 | Shackleton, Gantt/Drucker completion, hardening, pilot rollout |

---

## Notes

1. **Story IDs are placeholders** — replace with actual Jira keys when importing
2. **SP estimates assume** a team of 5 (platform lead, integration eng, build/test eng, backend/data eng, product owner) with 2-week sprints
3. **Wave 5 agents (Drucker, Gantt, Shackleton)** are marked as future in the spec but included per request — they can be deferred without blocking Waves 0–4
4. **Fuze changes** (JOS-1, ADA-4, CUR-4, FAR-6, TES-5, BAB-4, HED-5) are cross-cutting and may require coordination with the Fuze team
5. **Hardening stories (Wave 6)** should run in parallel with later waves, not strictly after — HAR-1/HAR-2 can start as soon as Wave 1 agents are online
