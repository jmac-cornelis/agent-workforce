# Linnaeus — Traceability Agent

> Status: Planned

## Overview

Linnaeus is the traceability agent for the platform. It maintains exact, queryable relationships between requirements, Jira issues, commits, builds, test executions, releases, and external version mappings.

Linnaeus is not a vague reporting layer. It is the system that establishes and serves relationship facts.

## Responsibilities

- Consume identity-bearing events from Jira, GitHub, Josephine, Faraday, Hedy, and Babbage
- Maintain a structured traceability graph linking requirements to releases
- Serve traceability queries for any agent or human
- Detect traceability gaps (untested commits, unlinked builds, orphaned requirements)
- Produce traceability reports per release or milestone
- Enforce traceability policies (e.g., every release build must link to test evidence)

## Non-Goals

- Owning build, test, or release execution
- Replacing Jira as the requirements source of truth
- Generating traceability links from inference alone (must be evidence-backed)

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Josephine | Receives build identity events |
| Faraday | Receives test execution records |
| Hedy | Receives release-state transitions |
| Babbage | Receives version mapping records |
| Drucker | Receives Jira issue state |
| Hemingway | Provides traceability context for documentation |

## Zone

Intelligence & Knowledge

## Planned Port

8223

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
