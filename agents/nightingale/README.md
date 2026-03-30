# Nightingale — Bug Investigation

> Status: Planned

## Overview

Nightingale is the bug-investigation agent for the platform. It reacts to Jira bug reports, qualifies the report, assembles technical context, determines whether the issue is reproducible, and coordinates targeted reproduction work until the bug is either reproduced, blocked on missing data, or clearly triaged for humans.

Nightingale turns vague bug reports into actionable technical evidence.

## Responsibilities

- React quickly to new or updated Jira bug reports
- Qualify bug reports (completeness, severity, reproducibility signals)
- Assemble technical context from builds, tests, releases, and traceability
- Determine reproduction feasibility and coordinate targeted reproduction
- Produce structured investigation summaries
- Flag bugs blocked on missing data for human follow-up
- Track investigation state across multiple reproduction attempts

## Non-Goals

- Owning Jira workflow transitions (that is Drucker's job)
- Owning release decisions related to bugs (that is Hedy's job)
- Replacing human engineers for root cause analysis
- Autonomous bug closure

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Drucker | Receives bug report signals from Jira |
| Josephine | Queries build context for reproduction |
| Faraday | Queries test execution evidence |
| Linnaeus | Queries traceability context |
| Tesla | Requests environment reservations for reproduction |
| Shannon | Delivers investigation updates and data requests |

## Zone

Intelligence & Knowledge

## Planned Port

8225

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
