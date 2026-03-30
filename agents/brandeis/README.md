# Brandeis — Legal Compliance & Code Scanning

> Status: Planned

## Overview

Brandeis is the legal compliance and code scanning agent. Named after Louis Brandeis, champion of transparency and the right to privacy, it scans dependencies for license compliance, flags policy violations on pull requests, and manages license exception workflows.

## Responsibilities

- Scan repository dependencies for license compliance
- Flag license policy violations on PRs via status checks
- Maintain an approved license allowlist and exception registry
- Generate compliance reports per repository or release
- Coordinate license exception approvals with legal stakeholders

## Non-Goals

- Code quality review (that is Linus's job)
- Security vulnerability scanning (separate tooling)
- Replacing legal counsel for license interpretation

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Linus | Receives PR events for compliance checks |
| Hedy | Provides release scope for compliance reports |
| Shannon | Delivers compliance alerts and approval requests |

## Zone

Execution Spine

## Planned Port

8227

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
