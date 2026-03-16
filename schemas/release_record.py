"""Canonical release records — shared across all agents."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReleaseCandidate(BaseModel):
    """A release candidate proposed by Hedy (Release Manager Agent)."""

    release_id: str = Field(..., description="Unique release identifier (e.g. release:2.4.0-rc2)")
    build_id: str = Field(..., description="Fuze build ID backing this candidate")
    external_version: str = Field(..., description="Customer-facing version string")
    release_branch: str = Field(..., description="Source branch (e.g. release/2.4)")
    hardware_targets: list[str] = Field(default_factory=list, description="Target hardware revisions")
    customer_profiles: list[str] = Field(default_factory=list, description="Customer profile tags")
    stage: str = Field(
        "candidate",
        description="Promotion stage: candidate | sit | qa | release | deprecated",
    )
    approval_state: str = Field(
        "pending",
        description="Approval state: pending | approved | blocked | withdrawn",
    )
    blocker_issues: list[str] = Field(
        default_factory=list,
        description="Jira keys of blocking issues",
    )
    test_evidence: list[str] = Field(
        default_factory=list,
        description="test_run_ids providing release evidence",
    )
    created_at: datetime = Field(default_factory=_utcnow)
    promoted_at: datetime | None = None
    promoted_by: str | None = None
    correlation_id: str = Field("")


class ReleaseDecision(BaseModel):
    """A human or agent decision on a release candidate."""

    decision_id: str = Field(..., description="Unique decision identifier")
    release_id: str = Field(..., description="Release candidate this decision applies to")
    decision: str = Field(..., description="approve | block | withdraw | promote")
    reason: str = Field("", description="Human-readable rationale")
    decided_by: str = Field(..., description="User principal or agent name")
    decided_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReleaseReadinessSummary(BaseModel):
    """Aggregated readiness assessment for a release candidate."""

    release_id: str = Field(..., description="Release candidate being assessed")
    build_id: str = Field(...)
    external_version: str = Field(...)
    total_tests: int = Field(0)
    passed_tests: int = Field(0)
    failed_tests: int = Field(0)
    coverage_summary: dict[str, float] = Field(default_factory=dict)
    open_blockers: list[str] = Field(default_factory=list, description="Jira keys of open blockers")
    open_p0_count: int = Field(0)
    open_p1_count: int = Field(0)
    traceability_gaps: list[str] = Field(
        default_factory=list,
        description="Descriptions of missing traceability links",
    )
    recommendation: str = Field(
        "",
        description="Agent recommendation: ready | not_ready | needs_review",
    )
    summary_text: str = Field("", description="Human-readable summary paragraph")
    generated_at: datetime = Field(default_factory=_utcnow)
    correlation_id: str = Field("")
