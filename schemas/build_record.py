"""Canonical BuildRecord — shared across all agents for build traceability."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BuildRecord(BaseModel):
    """Normalized build record produced by Josephine (Build & Package Agent).

    The build_id is the Fuze-generated internal build identity and serves as
    the authoritative technical identifier across the entire agent system.
    """

    build_id: str = Field(..., description="Authoritative Fuze-generated build identity")
    fuze_id: str | None = Field(None, description="Fuze configuration ID (e.g. cfg-network-card-a1)")
    repo_url: str = Field(..., description="Source repository URL")
    git_ref: str = Field(..., description="Git ref that triggered the build (branch, tag, PR ref)")
    commit_sha: str = Field(..., description="HEAD commit SHA at build time")
    branch: str = Field(..., description="Branch name (e.g. release/2.4)")
    build_map_path: str = Field("", description="Path to the Fuze build map file")
    targets: list[str] = Field(default_factory=list, description="Hardware/firmware targets built")
    packages: list[str] = Field(default_factory=list, description="Package names produced")
    status: str = Field(
        ...,
        description="Build lifecycle state: queued | running | completed | failed | cancelled",
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    artifact_manifest: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of artifact descriptors (uri, checksum, size, type)",
    )
    trigger_type: str = Field("", description="What triggered the build: pull_request | merge | tag | manual")
    trigger_ref: str = Field("", description="Reference to the trigger (e.g. PR-1842)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary key-value metadata")
    correlation_id: str = Field("", description="Cross-agent correlation identifier")
    created_at: datetime = Field(default_factory=_utcnow)
