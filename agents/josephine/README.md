# Josephine — Build Agent

> Status: Planned

## Overview

Josephine is an internal API-driven build service built on top of a reusable Fuze core. It runs Fuze-compatible build and packaging workflows in a hosted environment while preserving existing build maps, package semantics, FuzeID behavior, and Fuze-compatible metadata and artifact lineage.

Josephine is not a replacement for ATF, release promotion, or Jira/Bamboo workflow ownership in v1. It is the hosted build and package execution layer.

## Responsibilities

- Accept build jobs through an API
- Execute Fuze-compatible build and packaging workflows
- Produce build artifacts with proper FuzeID lineage
- Publish build metadata for consumption by downstream agents
- Maintain build logs and artifact storage
- Support multiple repository and branch configurations

## Non-Goals

- Replacing ATF executive functions
- Owning release promotion (that is Hedy's job)
- Owning Jira/Bamboo workflow management
- Replacing existing CI/CD pipelines in v1

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Ada | Triggers test planning on build completion |
| Babbage | Provides build identity for version mapping |
| Linnaeus | Publishes build records for traceability |
| Hedy | Provides build facts for release evaluation |

## Zone

Execution Spine

## Planned Port

8210

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
