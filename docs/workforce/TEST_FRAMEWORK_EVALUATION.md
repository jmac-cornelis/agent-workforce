# Test Framework Evaluation

[Back to AI Agent Workforce](README.md)

> **Warning:** **Decision Required:** This document evaluates whether Fuze Test / ATF is the right test framework for the agent platform, or whether we should adopt or migrate to an alternative. This decision affects Galileo (test planning), Curie (test generation), Faraday (test execution), and Tesla (environment management).

## Current State

Cornelis Networks currently uses **Fuze Test / ATF** (Automated Test Framework) as the primary test execution framework for OPX fabric hardware. It is a custom, internally-built framework with deep integration into the hardware-in-the-loop (HIL) lab environment.

The agent platform design currently assumes Fuze Test as the execution substrate — Faraday wraps it, Galileo plans against its suite vocabulary, and Curie generates inputs in its format. If Fuze Test is replaced, all three agents need adaptation.

## Evaluation Criteria

| Criterion | Weight | What We Need |
|-----------|--------|-------------|
| **HIL Support** | Critical | Must support real hardware test environments (DUTs, switches, fabric topology) alongside mock/simulated environments. |
| **Test Suite Management** | High | Named suites, suite selection by trigger class (PR/merge/nightly/release), machine-readable suite definitions. |
| **Structured Results** | High | Machine-readable pass/fail/skip with failure classification, log references, artifact links. Not just exit codes. |
| **Environment Reservation** | High | Integration with Tesla's reservation system. Must respect reservations and release on completion. |
| **Parallel Execution** | Medium | Run independent test suites in parallel across multiple environments. |
| **CI/CD Integration** | High | Triggerable from Jenkins/GitHub Actions. Status reporting back to CI. Non-interactive execution. |
| **Reproducibility** | High | Same inputs produce same test selection. Deterministic suite resolution. Version-pinned test configs. |
| **Developer Experience** | Medium | Easy to write new tests, debug failures, run locally. Good error messages. |
| **Extensibility** | Medium | Plugin/hook system for custom reporters, environment setup, teardown. |
| **Maintenance Burden** | High | How much ongoing effort to maintain the framework itself (vs writing tests). |

## Alternatives Evaluated

| Framework | Strengths | Weaknesses | HIL Fit |
|-----------|-----------|------------|---------|
| **Fuze Test / ATF** (current) | Purpose-built for OPX hardware. Deep HIL integration. Knows fabric topology, DUT management, ATF resource files. | Custom framework = full maintenance burden on Cornelis. May lack modern reporting, parallel execution, and API-driven operation. | Excellent |
| **pytest + custom plugins** | Industry standard. Powerful fixtures for setup/teardown. pytest-xdist for parallel. Huge ecosystem. Excellent debugging. | No built-in HIL support — requires custom fixtures for hardware reservation, DUT management, topology awareness. Significant upfront work. | Good (with investment) |
| **Robot Framework** | Keyword-driven (accessible to non-developers). Excellent built-in reporting. Good for acceptance testing. | Weaker debugging. Slower execution. Less Pythonic. Parallel execution requires pabot (third-party). HIL needs custom libraries. | Moderate |
| **Jenkins Pipeline as orchestrator** | Excellent parallel stage execution. Built-in CI/CD. Good visualization. Already deployed at Cornelis. | Not a test framework — orchestration layer only. Still needs a framework underneath for actual test execution and reporting. | N/A (orchestrator) |
| **LAVA (Linaro)** | Purpose-built for hardware testing. Device management, job scheduling, multi-device coordination. | Designed for embedded/ARM boards, not HPC fabric. Would need significant adaptation for OPX topology. Smaller community. | Moderate |

## Recommendation

> **Info:** **Recommended approach: Wrap-and-extend Fuze Test / ATF** using the Strangler Fig pattern. Do not replace it wholesale.

### Rationale

- Fuze Test has **irreplaceable domain knowledge** — it understands OPX fabric topology, DUT management, ATF resource files, and hardware-specific test patterns. Rebuilding this in pytest or Robot Framework would take 12-24 months.
- The agent platform (Faraday) only needs a **clean API wrapper** around Fuze Test, not a replacement. Faraday calls Fuze Test; it doesn't need to be Fuze Test.
- Over time, new tests can be written in **pytest with custom fixtures** that call the same underlying hardware libraries. Old tests stay in Fuze Test format.

### Migration Path

| Phase | Timeframe | Action |
|-------|-----------|--------|
| **1 — Wrap** | 3-6 months | Python API wrapper around Fuze Test CLI. Machine-readable output (JSON results, structured failures). Faraday consumes this API. pytest integration for new tests. |
| **2 — Extend** | 3-6 months | Add parallel execution support. Enhanced CI/CD integration. Dry-run validation mode for Galileo/Curie. Structured failure classification. |
| **3 — Migrate** | 12-24 months | Incrementally rewrite high-value test suites as pytest tests using shared hardware fixtures. Fuze Test suites continue to work alongside. No big-bang migration. |

### When to Reconsider

Replace Fuze Test entirely **only if**:

- Fuze Test becomes unmaintainable (key maintainers leave, codebase too fragile)
- Fundamental architectural limitations block agent integration (no API possible, no structured output possible)
- Hardware platform changes make Fuze Test's domain knowledge obsolete
- Licensing or dependency issues arise

## Impact on Agents

| Agent | Impact of Framework Choice |
|-------|---------------------------|
| **Galileo** (Test Planner) | Plans against suite vocabulary. If framework changes, Galileo's PolicyResolver and suite selection logic must adapt. Wrapper API insulates Galileo from underlying framework. |
| **Curie** (Test Generator) | Generates runtime inputs in framework-specific format. Wrapper API provides stable input contract regardless of underlying framework. |
| **Faraday** (Test Executor) | Directly invokes the test framework. Wrapper API is Faraday's primary integration point. Framework change = update wrapper, not Faraday. |
| **Tesla** (Environment Mgr) | Manages reservations independent of test framework. ATF resource files are the integration point. If framework changes, Tesla's resource file parser may need updates. |

> **Note:** **Action item:** Schedule a technical evaluation session with the Fuze Test maintainers to assess: (1) feasibility of the wrapper API approach, (2) effort to add machine-readable output, (3) effort to add dry-run mode, (4) any known architectural blockers.
