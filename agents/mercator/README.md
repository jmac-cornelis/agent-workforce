# Mercator — Version Manager

> Status: Planned

## Overview

Mercator is the version-mapping agent for the platform. It connects internal build identity from Fuze with external release versions and maintains the lineage between the two. Josephine produces internal build IDs, Humphrey decides release intent, and Mercator maps between them as a durable record.

## Responsibilities

- Map internal Fuze build IDs to external customer-facing version strings
- Detect and prevent version mapping conflicts
- Maintain lineage and audit trail for all version assignments
- Serve version lookups for other agents (Humphrey, Berners-Lee, Hemingway)
- Track version progression across branches and release trains

## Non-Goals

- Owning release decisions (that is Humphrey's job)
- Owning build identity creation (that is Josephine's job)
- Replacing Fuze's internal versioning mechanics

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Josephine | Receives internal build identity |
| Humphrey | Receives release intent and scope |
| Berners-Lee | Provides version facts for traceability |
| Hemingway | Provides version context for documentation |

## Zone

Intelligence & Knowledge

## Planned Port

8222

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
