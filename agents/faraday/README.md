# Faraday — Test Executor

> Status: Planned

## Overview

Faraday is the test-execution agent for the platform. It takes a resolved `TestPlan`, acquires the required environment through Tesla, executes the plan through Fuze Test in ATF, collects results, and publishes machine-readable test execution records tied to the originating build ID.

In v1, Faraday wraps the existing Fuze Test execution path rather than replacing the ATF executive or Product Test Adapter layers.

## Responsibilities

- Consume concrete TestPlans from Curie
- Acquire test environments through Tesla reservations
- Execute ATF/Fuze Test cycles with proper isolation
- Capture logs, artifacts, and test results
- Classify failures (test bug, product bug, infra issue)
- Produce structured `TestExecutionRecord` objects
- Publish results for consumption by Linnaeus, Hedy, and Nightingale

## Non-Goals

- Test planning (that is Ada's job)
- Test content generation (that is Curie's job)
- Environment provisioning (that is Tesla's job)
- Replacing the ATF executive in v1

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Curie | Receives executable test inputs |
| Tesla | Acquires environment reservations |
| Linnaeus | Publishes test execution records for traceability |
| Hedy | Provides test evidence for release decisions |
| Nightingale | Provides test evidence for bug investigation |

## Zone

Execution Spine

## Planned Port

8213

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
