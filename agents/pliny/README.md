# Pliny — Knowledge Capture

> Status: Planned

## Overview

Pliny is the knowledge-capture agent for the platform. It ingests meeting transcripts and metadata, produces structured summaries, extracts decisions and action items, and preserves the human rationale that often gets lost between chat, meetings, tickets, and engineering work.

Pliny does not become a generic chatbot for meetings. It produces durable, reviewable records.

## Responsibilities

- Detect and ingest Microsoft Teams meeting transcripts and metadata
- Produce structured meeting summaries with speaker attribution
- Extract decisions, action items, and follow-ups
- Link captured knowledge to relevant Jira tickets and engineering context
- Maintain a searchable knowledge base of meeting outcomes
- Surface documentation suggestions to Hemingway

## Non-Goals

- Real-time meeting participation or transcription
- Replacing meeting notes taken by humans
- Generating action items without meeting evidence
- Owning Jira ticket creation from action items (that is Drucker's domain)

## Dependencies

| Agent | Relationship |
|-------|-------------|
| Shannon | Receives meeting notification signals |
| Drucker | Provides Jira context for linking action items |
| Hemingway | Feeds documentation suggestions |
| Gantt | Provides planning context for decision linking |

## Zone

Intelligence & Knowledge

## Planned Port

8224

## Detailed Plan

See [docs/PLAN.md](docs/PLAN.md) for the full technical specification.
