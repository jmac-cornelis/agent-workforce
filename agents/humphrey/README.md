# Humphrey — Release Manager

> Status: Planned

## Overview

Humphrey is the release-management agent for the platform. It takes build facts from Josephine, version facts from Mercator, test evidence from the test agents, and traceability context from Berners-Lee, then turns those inputs into controlled release decisions and release-state transitions.

Humphrey uses Fuze's existing release model as the underlying release engine. In v1, it orchestrates and governs release mechanics rather than replacing them.

## Responsibilities

- Evaluate release readiness across branch, hardware, customer, and policy context
- Orchestrate stage promotion (sit, qa, release) with human approval gates
- Track release-state transitions with full audit trail
- Enforce release policies (test coverage thresholds, known-issue limits)
- Coordinate with Mercator for version assignment
- Produce release readiness reports for stakeholders

## Non-Goals

- Owning build execution (that is Josephine's job)
- Owning version mapping (that is Mercator's job)
- Replacing Fuze's release mechanics in v1
- Autonomous release promotion without human approval

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Josephine | Receives build facts |
| Mercator | Receives version mappings |
| Faraday | Receives test execution evidence |
| Berners-Lee | Receives traceability context |
| Shannon | Delivers release notifications and approval requests |

## Zone

Execution Spine

## Planned Port

8220

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
