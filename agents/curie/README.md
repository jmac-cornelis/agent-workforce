# Curie — Test Generator

> Status: Planned

## Overview

Curie is the test-generation agent for the platform. It takes Ada's `TestPlan` and turns it into concrete Fuze Test runtime inputs that Faraday can execute through Fuze Test in ATF. Ada defines the testing intent; Curie materializes executable test content and runtime inputs.

## Responsibilities

- Consume Ada's `TestPlan` and resolve it into executable test inputs
- Generate Fuze Test configuration files and runtime parameters
- Produce reproducible version hashes for test content
- Handle test parameterization based on environment and hardware constraints from Tesla
- Maintain a registry of available test suites and their capabilities

## Non-Goals

- Deciding what to test (that is Ada's job)
- Executing tests (that is Faraday's job)
- Managing test environments (that is Tesla's job)
- Replacing existing Fuze Test content authoring workflows

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Ada | Receives TestPlan inputs |
| Faraday | Produces executable inputs for Faraday |
| Tesla | Queries environment constraints for parameterization |

## Zone

Execution Spine

## Planned Port

8212

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
