"""Canonical documentation records — shared across all agents."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentationRecord(BaseModel):
    """A documentation artifact produced or tracked by Hypatia (Documentation Agent)."""

    doc_id: str = Field(..., description="Unique document identifier (e.g. doc:engineering:interrupt-routing)")
    doc_type: str = Field(
        ...,
        description="Document category: engineering | user | as_built | api | release_notes",
    )
    title: str = Field("", description="Document title")
    source_refs: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Source references: {commit_shas: [], build_ids: [], jira_keys: []}",
    )
    repo: str | None = Field(None, description="Source repository if applicable")
    publish_target: str = Field("", description="Publication destination (e.g. internal-docs, readthedocs)")
    status: str = Field(
        "draft",
        description="Lifecycle state: draft | review | published | archived | retracted",
    )
    version: str = Field("1.0", description="Document version")
    generated_by: str = Field("", description="Agent or process that generated this document")
    reviewed_by: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    published_at: datetime | None = None
    correlation_id: str = Field("")


class DocumentationPatch(BaseModel):
    """A proposed change to an existing document."""

    patch_id: str = Field(..., description="Unique patch identifier")
    doc_id: str = Field(..., description="Target document to patch")
    patch_type: str = Field(
        ...,
        description="Type of change: content_update | metadata_update | section_add | section_remove",
    )
    description: str = Field("", description="What this patch changes and why")
    diff_text: str | None = Field(None, description="Unified diff of the content change")
    source_refs: dict[str, list[str]] = Field(
        default_factory=dict,
        description="References that triggered this patch",
    )
    status: str = Field("proposed", description="proposed | approved | applied | rejected")
    proposed_by: str = Field("")
    proposed_at: datetime = Field(default_factory=_utcnow)
    applied_at: datetime | None = None


class PublicationRecord(BaseModel):
    """Record of a document publication event."""

    publication_id: str = Field(..., description="Unique publication identifier")
    doc_id: str = Field(..., description="Document that was published")
    target: str = Field(..., description="Publication target (e.g. internal-docs, readthedocs)")
    target_url: str | None = Field(None, description="URL where the document is accessible")
    published_by: str = Field(..., description="Agent or user that triggered publication")
    published_at: datetime = Field(default_factory=_utcnow)
    status: str = Field("published", description="published | failed | retracted")
    metadata: dict[str, Any] = Field(default_factory=dict)
