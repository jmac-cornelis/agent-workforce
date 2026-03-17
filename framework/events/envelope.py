"""Canonical event envelope — the standard format for ALL agent-to-agent events."""

from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Any, Optional
import uuid


class EventEnvelope(BaseModel):
    """Canonical event envelope for all agent-to-agent communication.

    Every event flowing through the PostgreSQL event bus uses this format.
    The envelope is immutable once created — the events table is append-only.
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # e.g., "build.completed", "test.plan_selected"
    producer: str  # agent_id of the producing agent
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject_id: Optional[str] = None  # e.g., build_id, test_run_id
    payload: dict[str, Any] = Field(default_factory=dict)

    schema_version: str = "1.0"
    idempotency_key: Optional[str] = None  # For deduplication

    model_config = {"frozen": True}


# ---------------------------------------------------------------------------
# Event type constants — canonical names used across all agents
# ---------------------------------------------------------------------------

# Build events (Josephine)
BUILD_COMPLETED = "build.completed"
BUILD_FAILED = "build.failed"
ARTIFACT_PUBLISHED = "artifact.published"

# Test events (Ada / Curie / Faraday)
TEST_PLAN_SELECTED = "test.plan_selected"
TEST_EXECUTION_COMPLETED = "test.execution_completed"
COVERAGE_GAP_DETECTED = "coverage_gap_detected"

# Version events (Babbage)
VERSION_MAPPED = "version.mapped"
MAPPING_CONFLICT_DETECTED = "mapping_conflict_detected"

# Trace events (Linnaeus)
TRACE_UPDATED = "trace.updated"
ISSUE_LINKED = "issue_linked"

# Release events (Hedy)
RELEASE_CANDIDATE_CREATED = "release.candidate_created"
RELEASE_PROMOTED = "release.promoted"
RELEASE_BLOCKED = "release.blocked"

# Review events (Linus)
REVIEW_COMPLETED = "review.completed"
REVIEW_POLICY_FAILED = "review.policy_failed"
DOCUMENTATION_IMPACT_DETECTED = "documentation_impact_detected"

# Docs events (Hypatia)
DOCS_PUBLISHED = "docs.published"

# Meeting events (Herodotus)
MEETING_SUMMARY_CREATED = "meeting.summary_created"
ACTION_ITEMS_EXTRACTED = "action_items_extracted"

# Bug events (Nightingale)
BUG_INVESTIGATION_STARTED = "bug.investigation_started"
BUG_REPRODUCED = "bug.reproduced"
BUG_INVESTIGATION_SUMMARIZED = "bug.investigation_summarized"

# Approval events (cross-agent)
APPROVAL_REQUESTED = "approval.requested"
APPROVAL_COMPLETED = "approval.completed"
APPROVAL_TIMEOUT = "approval.timeout"

# Shannon events (communications)
MESSAGE_ROUTED = "message.routed"
MESSAGE_FAILED = "message.failed"
