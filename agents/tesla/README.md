# Tesla — Test Environment Manager

> Status: Planned

## Overview

Tesla is the shared service that exposes lab and mock-environment state to the test agents and manages reservations for scarce test resources. It sits in front of Fuze Test so Ada, Curie, and Faraday can make reservation-aware decisions before invoking test execution.

In the test pipeline: Ada decides what environment is needed, Curie may refine that into runtime constraints, Tesla decides whether the environment is available and reserves it, and Faraday uses the reserved location and runtime context to execute.

## Responsibilities

- Maintain a real-time inventory of HIL lab environments and mock environments
- Match test requirements to available environment capabilities
- Manage reservations with time-bounded leases and automatic cleanup
- Monitor environment health and flag degraded or offline resources
- Provide environment availability signals to Ada for test planning
- Support priority-based reservation queuing

## Non-Goals

- Test planning (that is Ada's job)
- Test execution (that is Faraday's job)
- Physical lab provisioning or hardware management
- Replacing Fuze Test's environment selection logic in v1

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Ada | Receives environment requirement queries |
| Curie | Receives refined environment constraints |
| Faraday | Provides reserved environment context for execution |

## Zone

Execution Spine

## Planned Port

8214

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
