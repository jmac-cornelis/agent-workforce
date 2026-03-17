##########################################################################################
#
# Module: agents/workforce/nightingale/models.py
#
# Description: Pydantic models for the Nightingale Bug Investigation agent.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BugInvestigationRequest(BaseModel):
    '''Request to investigate a Jira bug report.'''
    jira_key: str = Field(..., description='Jira issue key for the bug')
    scope: Optional[str] = Field(None, description='Investigation scope')
    policy_profile: Optional[str] = Field(None, description='Policy profile')
    priority_override: Optional[str] = Field(
        None, description='Priority override for investigation ordering'
    )
    requested_by: Optional[str] = Field(None, description='Who requested the investigation')


class BugInvestigationRecord(BaseModel):
    '''Durable record of a bug investigation.'''
    investigation_id: str = Field(..., description='Unique investigation identifier')
    jira_key: str = Field(..., description='Jira issue key')
    status: str = Field(
        'open',
        description=(
            'Investigation status: open, context_assembled, '
            'awaiting_info, reproducing, reproduced, '
            'not_reproduced, blocked, closed'
        ),
    )
    build_context: Optional[Dict[str, Any]] = Field(
        None, description='Build context from Josephine/Linnaeus'
    )
    test_context: Optional[Dict[str, Any]] = Field(
        None, description='Test context from Faraday'
    )
    release_context: Optional[Dict[str, Any]] = Field(
        None, description='Release context from Hedy/Babbage'
    )
    missing_data: List[str] = Field(
        default_factory=list, description='Missing information items'
    )
    findings: List[str] = Field(default_factory=list, description='Investigation findings')
    created_at: Optional[datetime] = Field(None)
    updated_at: Optional[datetime] = Field(None)


class FailureSignatureRecord(BaseModel):
    '''A repeatable failure signature for clustering similar bugs.'''
    signature_id: str = Field(..., description='Unique signature identifier')
    jira_key: str = Field(..., description='Originating Jira issue key')
    signature_hash: str = Field(..., description='Hash of the failure signature')
    failure_pattern: str = Field(..., description='Description of the failure pattern')
    stack_trace_excerpt: Optional[str] = Field(
        None, description='Relevant stack trace excerpt'
    )
    component: Optional[str] = Field(None, description='Affected component')
    related_bugs: List[str] = Field(
        default_factory=list, description='Jira keys of related bugs'
    )
    created_at: Optional[datetime] = Field(None)


class ReproductionAttempt(BaseModel):
    '''Record of a targeted bug reproduction attempt.'''
    attempt_id: str = Field(..., description='Unique attempt identifier')
    jira_key: str = Field(..., description='Jira issue key')
    build_id: Optional[str] = Field(None, description='Build used for reproduction')
    environment: Optional[str] = Field(None, description='Environment used')
    test_run_id: Optional[str] = Field(None, description='Faraday test run identifier')
    outcome: str = Field(
        'pending',
        description='Outcome: pending, reproduced, not_reproduced, blocked, error',
    )
    evidence: Optional[Dict[str, Any]] = Field(
        None, description='Evidence from the reproduction attempt'
    )
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)


class InvestigationSummary(BaseModel):
    '''Human-readable summary of a bug investigation.'''
    summary_id: str = Field(..., description='Unique summary identifier')
    jira_key: str = Field(..., description='Jira issue key')
    investigation_id: str = Field(..., description='Associated investigation identifier')
    status: str = Field(..., description='Current investigation status')
    summary_text: str = Field(..., description='Human-readable summary')
    findings: List[str] = Field(default_factory=list, description='Key findings')
    next_steps: List[str] = Field(default_factory=list, description='Recommended next steps')
    reproduction_count: int = Field(0, description='Number of reproduction attempts')
    reproduced: bool = Field(False, description='Whether the bug has been reproduced')
    confidence: str = Field('medium', description='Summary confidence: high, medium, low')
    created_at: Optional[datetime] = Field(None)
