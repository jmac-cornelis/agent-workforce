##########################################################################################
#
# Module: agents/humphrey/models.py
#
# Description: Data models for the Humphrey Release Manager Agent.
#              Defines release candidates, decisions, readiness summaries,
#              and promotion requests.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReleaseStage(str, Enum):
    SIT = 'sit'
    QA = 'qa'
    RELEASE = 'release'
    DEPRECATED = 'deprecated'
    REJECTED = 'rejected'
    TEST_ONLY = 'test_only'


class ApprovalStatus(str, Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    NOT_REQUIRED = 'not_required'


class ReleaseCandidate(BaseModel):
    '''A build being evaluated or promoted as a release candidate.'''
    release_candidate_id: str
    build_id: str
    release_branch: str = ''
    hardware_targets: List[str] = Field(default_factory=list)
    customer_targets: List[str] = Field(default_factory=list)
    proposed_stage: ReleaseStage = ReleaseStage.SIT
    external_version_ref: Optional[str] = None
    readiness_summary: Optional[Dict[str, Any]] = None
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ReleaseDecision(BaseModel):
    '''Record of a release evaluation decision.'''
    decision_id: str
    build_id: str
    decision: str
    eligible: bool = False
    blocking_reasons: List[str] = Field(default_factory=list)
    evidence_refs: Dict[str, str] = Field(default_factory=dict)
    rationale: str = ''


class ReleaseReadinessSummary(BaseModel):
    '''Human-readable and machine-readable release readiness summary.'''
    release_id: str
    build_id: str
    current_stage: ReleaseStage = ReleaseStage.SIT
    build_success: bool = False
    packages_available: bool = False
    test_evidence_sufficient: bool = False
    blocking_defects: List[str] = Field(default_factory=list)
    version_mapped: bool = False
    approval_history: List[Dict[str, Any]] = Field(default_factory=list)
    overall_ready: bool = False


class ReleasePromotionRequest(BaseModel):
    '''Request to promote a release to the next stage.'''
    release_id: str
    target_stage: ReleaseStage
    approval_ref: Optional[str] = None
    requestor: Optional[str] = None
    rationale: str = ''
