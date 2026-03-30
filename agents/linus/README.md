# Linus — Code Review Agent

> Status: Planned

## Overview

Linus is the code-review agent for the platform. It evaluates pull requests against code-quality and review-policy rules, produces structured findings, surfaces likely correctness risks early, and emits clear signals to downstream agents when documentation, build, or test attention is warranted.

Linus focuses on high-signal review findings tied to correctness, maintainability, and policy. It should not become a style bot or a generic lint wrapper.

## Responsibilities

- Consume GitHub pull request events and diff context
- Evaluate PRs against configurable policy profiles (kernel, embedded C++, Python)
- Produce structured code review findings with severity and confidence
- Emit cross-agent impact signals (e.g., "this PR affects API contracts")
- Flag correctness risks, security concerns, and maintainability issues
- Support per-repository and per-team review policy configuration

## Non-Goals

- PR lifecycle hygiene (staleness, review coverage — that is Drucker's job)
- Style enforcement or linting (use existing tooling)
- Automatic code fixes or suggestions
- Replacing human code reviewers

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Drucker | Drucker owns PR lifecycle; Linus owns review quality |
| Hypatia | Emits documentation-impact signals |
| Ada | Emits test-impact signals |
| Brandeis | Coordinates on compliance-related PR findings |

## Zone

Execution Spine

## Planned Port

8221

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
