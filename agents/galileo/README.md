# Galileo — Test Planner

> Status: Planned

## Overview

Galileo is the test-planning agent for the platform. It decides what should be tested and at what depth based on build context, trigger type, environment state, and coverage needs. Galileo produces a durable `TestPlan` that downstream agents (Curie and Faraday) act on.

In the test pipeline: Galileo decides what to test, Curie materializes executable test content, Faraday executes it, and Tesla manages environment reservations.

## Responsibilities

- Consume build-trigger events and determine test scope
- Select test suites and depth based on trigger class (PR, merge, nightly, release)
- Factor in environment constraints and availability from Tesla
- Produce structured `TestPlan` records for Curie
- Maintain coverage targets per product area

## Non-Goals

- Test execution (that is Faraday's job)
- Test content generation (that is Curie's job)
- Environment management (that is Tesla's job)
- Replacing Fuze Test's existing test selection logic in v1

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Josephine | Receives build-trigger events |
| Tesla | Queries environment availability |
| Curie | Produces TestPlans consumed by Curie |
| Faraday | TestPlan ultimately executed by Faraday |

## Zone

Execution Spine

## Planned Port

8211

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
