# Brooks — Delivery Manager

> Status: Planned

## Overview

Brooks is the delivery-management agent for the platform. It monitors execution against plan, detects schedule risk and coordination failures early, and produces operational delivery summaries for humans. Gantt plans; Brooks watches delivery reality and flags drift, blockage, and risk.

## Responsibilities

- Monitor work-in-flight against milestones and release targets
- Detect schedule risk from blocked dependencies, stale work, and velocity changes
- Produce operational delivery summaries and status reports
- Flag coordination failures between teams or agents
- Track delivery metrics over time for trend analysis

## Non-Goals

- Project planning (that is Gantt's job)
- Direct scope changes without human approval
- Automatic assignment of people to work
- Replacing Jira as the delivery tracking system

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Gantt | Receives planning baselines and milestones |
| Drucker | Receives hygiene and workflow state |
| Hedy | Receives release readiness signals |
| Shannon | Delivers status summaries and risk alerts |

## Zone

Planning & Delivery

## Planned Port

8226

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
