"""Canonical meeting summary records — shared across all agents."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ActionItemDraft(BaseModel):
    """An action item extracted from a meeting transcript."""

    action_id: str = Field("", description="Unique action item identifier")
    owner: str = Field(..., description="Assigned owner (email or display name)")
    description: str = Field(..., description="What needs to be done")
    due_date: datetime | None = None
    priority: str = Field("medium", description="low | medium | high")
    jira_key: str | None = Field(None, description="Jira issue created from this action, if any")
    status: str = Field("open", description="open | in_progress | done | cancelled")


class DecisionRecord(BaseModel):
    """A decision captured from a meeting."""

    decision_id: str = Field("", description="Unique decision identifier")
    summary: str = Field(..., description="Concise statement of the decision")
    context: str = Field("", description="Background or rationale")
    participants: list[str] = Field(default_factory=list, description="People involved in the decision")
    impact_areas: list[str] = Field(
        default_factory=list,
        description="Affected domains (e.g. release, testing, hardware)",
    )


class MeetingRecord(BaseModel):
    """Metadata for a meeting (before summarization)."""

    meeting_id: str = Field(..., description="Unique meeting identifier (e.g. teams:meeting:2026-03-10:...)")
    title: str = Field("", description="Meeting title or subject")
    scheduled_at: datetime | None = None
    ended_at: datetime | None = None
    organizer: str = Field("", description="Meeting organizer")
    attendees: list[str] = Field(default_factory=list)
    transcript_ref: str = Field("", description="URI to the raw transcript (e.g. teams://transcripts/78421)")
    channel_id: str | None = Field(None, description="Teams channel where the meeting occurred")
    correlation_id: str = Field("")


class MeetingSummaryRecord(BaseModel):
    """Structured summary produced by Herodotus (Knowledge Capture Agent)."""

    summary_id: str = Field(..., description="Unique summary identifier")
    meeting_id: str = Field(..., description="Source meeting this summarizes")
    transcript_ref: str = Field("", description="URI to the raw transcript")
    summary_text: str = Field("", description="Full narrative summary")
    decision_items: list[DecisionRecord] = Field(default_factory=list)
    action_items: list[ActionItemDraft] = Field(default_factory=list)
    key_topics: list[str] = Field(default_factory=list, description="Main topics discussed")
    follow_up_meetings: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up meeting topics",
    )
    generated_by: str = Field("herodotus", description="Agent that produced this summary")
    status: str = Field("draft", description="draft | reviewed | published | retracted")
    created_at: datetime = Field(default_factory=_utcnow)
    published_at: datetime | None = None
    correlation_id: str = Field("")
