##########################################################################################
#
# Module: agents/workforce/herodotus/models.py
#
# Description: Pydantic models for the Herodotus Knowledge Capture agent.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MeetingRecord(BaseModel):
    '''Record of an ingested meeting with transcript and metadata.'''
    meeting_id: str = Field(..., description='Teams meeting identifier')
    title: Optional[str] = Field(None, description='Meeting title')
    organizer: Optional[str] = Field(None, description='Meeting organizer')
    attendees: List[str] = Field(default_factory=list, description='List of attendees')
    channel: Optional[str] = Field(None, description='Teams channel')
    transcript_ref: Optional[str] = Field(None, description='URI to the transcript')
    transcript_status: str = Field(
        'pending', description='Transcript status: pending, available, partial, unavailable'
    )
    started_at: Optional[datetime] = Field(None, description='Meeting start time')
    ended_at: Optional[datetime] = Field(None, description='Meeting end time')
    ingested_at: Optional[datetime] = Field(None, description='When the meeting was ingested')
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptRecord(BaseModel):
    '''Normalized transcript content for a meeting.'''
    transcript_id: str = Field(..., description='Unique transcript record identifier')
    meeting_id: str = Field(..., description='Associated meeting identifier')
    content: Optional[str] = Field(None, description='Normalized transcript text')
    word_count: int = Field(0, description='Word count of the transcript')
    speaker_count: int = Field(0, description='Number of distinct speakers')
    completeness: str = Field(
        'unknown', description='Completeness: complete, partial, unknown'
    )
    source_ref: Optional[str] = Field(None, description='Original transcript source URI')
    created_at: Optional[datetime] = Field(None)


class MeetingSummaryRecord(BaseModel):
    '''Structured summary of a meeting.'''
    summary_id: str = Field(..., description='Unique summary identifier')
    meeting_id: str = Field(..., description='Associated meeting identifier')
    executive_summary: str = Field(..., description='Short executive summary')
    decisions: List[str] = Field(default_factory=list, description='Decisions made')
    action_items: List[str] = Field(
        default_factory=list, description='Action items identified'
    )
    open_questions: List[str] = Field(
        default_factory=list, description='Unresolved questions'
    )
    referenced_artifacts: List[str] = Field(
        default_factory=list,
        description='Jira keys, build IDs, repo refs mentioned',
    )
    confidence: str = Field('medium', description='Summary confidence: high, medium, low')
    status: str = Field(
        'draft', description='Summary status: draft, approved, published, retracted'
    )
    created_at: Optional[datetime] = Field(None)
    published_at: Optional[datetime] = Field(None)


class ActionItemDraft(BaseModel):
    '''A draft action item extracted from a meeting.'''
    action_id: str = Field(..., description='Unique action item identifier')
    meeting_id: str = Field(..., description='Source meeting identifier')
    action_text: str = Field(..., description='Description of the action')
    proposed_owner: Optional[str] = Field(None, description='Proposed owner if identifiable')
    due_date: Optional[str] = Field(None, description='Due date if explicit')
    confidence: str = Field('medium', description='Extraction confidence: high, medium, low')
    source_excerpt: Optional[str] = Field(
        None, description='Transcript excerpt supporting this action'
    )
    recommended_destination: Optional[str] = Field(
        None, description='Suggested target: jira, docs, manual_followup'
    )
    status: str = Field(
        'draft', description='Status: draft, accepted, rejected, forwarded'
    )


class DecisionRecord(BaseModel):
    '''A decision captured from a meeting.'''
    decision_id: str = Field(..., description='Unique decision identifier')
    meeting_id: str = Field(..., description='Source meeting identifier')
    decision_text: str = Field(..., description='Description of the decision')
    context: Optional[str] = Field(None, description='Context or rationale')
    participants: List[str] = Field(
        default_factory=list, description='Participants involved in the decision'
    )
    source_excerpt: Optional[str] = Field(
        None, description='Transcript excerpt supporting this decision'
    )
    created_at: Optional[datetime] = Field(None)
