"""Canonical traceability records — shared across all agents."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TraceabilityRecord(BaseModel):
    """Full traceability view linking a Jira issue to builds, tests, releases, and requirements.

    Maintained by Linnaeus (Traceability Agent). This is the primary queryable
    record for answering "what tested this bug?" or "which release contains this fix?"
    """

    trace_id: str = Field(..., description="Unique trace identifier (e.g. trace:bug:PROJ-4421)")
    jira_issue_key: str = Field(..., description="Jira issue key")
    build_ids: list[str] = Field(default_factory=list, description="Linked Fuze build IDs")
    release_ids: list[str] = Field(default_factory=list, description="Linked release IDs")
    commit_shas: list[str] = Field(default_factory=list, description="Linked commit SHAs")
    test_run_ids: list[str] = Field(default_factory=list, description="Linked test run IDs")
    requirements: list[str] = Field(default_factory=list, description="Linked requirement IDs (e.g. REQ-NET-0042)")
    doc_ids: list[str] = Field(default_factory=list, description="Linked documentation record IDs")
    status: str = Field("active", description="active | archived")
    last_updated: datetime = Field(default_factory=_utcnow)
    correlation_id: str = Field("")


class RelationshipEdge(BaseModel):
    """A single directed relationship between two artifacts in the traceability graph."""

    edge_id: str = Field(..., description="Unique edge identifier")
    source_type: str = Field(..., description="Source artifact type: jira | build | test | release | commit | requirement | doc")
    source_id: str = Field(..., description="Source artifact identifier")
    target_type: str = Field(..., description="Target artifact type")
    target_id: str = Field(..., description="Target artifact identifier")
    relationship: str = Field(
        ...,
        description="Edge label: fixes | tested_by | built_from | released_in | documents | implements",
    )
    confidence: float = Field(1.0, description="Confidence score 0.0-1.0 (1.0 = deterministic link)")
    created_by: str = Field("", description="Agent or user that created this edge")
    created_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CoverageGapRecord(BaseModel):
    """A detected gap in traceability coverage."""

    gap_id: str = Field(..., description="Unique gap identifier")
    gap_type: str = Field(
        ...,
        description="Type of gap: untested_requirement | unlinked_build | missing_test_evidence | orphan_commit",
    )
    subject_type: str = Field(..., description="Artifact type with the gap")
    subject_id: str = Field(..., description="Artifact identifier with the gap")
    description: str = Field("", description="Human-readable gap description")
    severity: str = Field("medium", description="low | medium | high | critical")
    suggested_action: str = Field("", description="Recommended remediation")
    detected_at: datetime = Field(default_factory=_utcnow)
    resolved_at: datetime | None = None
    correlation_id: str = Field("")
