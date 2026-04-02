##########################################################################################
#
# Module: agents/shackleton/models.py
#
# Description: Pydantic models for the Shackleton Delivery Manager agent.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DeliverySnapshot(BaseModel):
    '''Point-in-time delivery status combining Jira and technical evidence.'''
    snapshot_id: str = Field(..., description='Unique snapshot identifier')
    project_key: str = Field(..., description='Project scope')
    milestone_scope: Optional[str] = Field(None, description='Milestone filter applied')
    status: str = Field(
        'unknown',
        description='Overall status: on_track, at_risk, behind, blocked, unknown',
    )
    confidence: str = Field('medium', description='Confidence: high, medium, low')
    open_work_items: int = Field(0, description='Count of open work items')
    blocked_items: int = Field(0, description='Count of blocked items')
    missing_evidence: List[str] = Field(
        default_factory=list, description='Missing technical evidence items'
    )
    risks: List[str] = Field(default_factory=list, description='Active risk summaries')
    created_at: Optional[datetime] = Field(None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeliveryRiskRecord(BaseModel):
    '''A detected delivery risk.'''
    risk_id: str = Field(..., description='Unique risk identifier')
    project_key: str = Field(..., description='Project scope')
    risk_class: str = Field(
        ...,
        description=(
            'Risk class: schedule_slip, blocked_handoff, missing_approval, '
            'stale_action, release_readiness_mismatch, coordination_failure'
        ),
    )
    severity: str = Field('medium', description='Severity: critical, high, medium, low')
    description: str = Field(..., description='Risk description')
    evidence: List[str] = Field(default_factory=list, description='Supporting evidence')
    status: str = Field(
        'active', description='Status: active, acknowledged, dismissed, resolved'
    )
    detected_at: Optional[datetime] = Field(None)
    acknowledged_by: Optional[str] = Field(None)


class ForecastRecord(BaseModel):
    '''Near-term delivery forecast for a project or milestone.'''
    forecast_id: str = Field(..., description='Unique forecast identifier')
    project_key: str = Field(..., description='Project scope')
    milestone: Optional[str] = Field(None, description='Specific milestone')
    on_time_probability: float = Field(
        0.0, description='Probability of on-time delivery (0.0 to 1.0)'
    )
    confidence: str = Field('medium', description='Forecast confidence: high, medium, low')
    major_factors: List[str] = Field(
        default_factory=list, description='Factors driving the forecast'
    )
    slip_signals: List[str] = Field(
        default_factory=list, description='Signals indicating potential slip'
    )
    created_at: Optional[datetime] = Field(None)


class StatusSummary(BaseModel):
    '''Delivery status summary for human consumption.'''
    summary_id: str = Field(..., description='Unique summary identifier')
    project_key: str = Field(..., description='Project scope')
    headline: str = Field(..., description='One-line status headline')
    status: str = Field(..., description='Overall status')
    confidence: str = Field('medium', description='Confidence level')
    key_risks: List[str] = Field(default_factory=list, description='Top risks')
    blocked_handoffs: List[str] = Field(
        default_factory=list, description='Blocked handoff descriptions'
    )
    pending_approvals: List[str] = Field(
        default_factory=list, description='Pending approval items'
    )
    created_at: Optional[datetime] = Field(None)


class EscalationRecord(BaseModel):
    '''Record of a delivery escalation.'''
    escalation_id: str = Field(..., description='Unique escalation identifier')
    project_key: str = Field(..., description='Project scope')
    risk_id: str = Field(..., description='Associated risk identifier')
    severity: str = Field(..., description='Escalation severity')
    description: str = Field(..., description='Escalation description')
    escalated_to: List[str] = Field(
        default_factory=list, description='Escalation targets'
    )
    status: str = Field(
        'pending', description='Status: pending, acknowledged, deferred, resolved'
    )
    created_at: Optional[datetime] = Field(None)
    acknowledged_at: Optional[datetime] = Field(None)
