##########################################################################################
#
# Module: agents/workforce/linus/models.py
#
# Description: Data models for the Linus Code Review Agent.
#              Defines review requests, findings, summaries, and
#              policy profiles.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    INFO = 'info'


class FindingCategory(str, Enum):
    CORRECTNESS_RISK = 'correctness_risk'
    SAFETY_RISK = 'safety_risk'
    CONCURRENCY_RISK = 'concurrency_risk'
    MAINTAINABILITY_RISK = 'maintainability_risk'
    POLICY_VIOLATION = 'policy_violation'
    DOCUMENTATION_IMPACT = 'documentation_impact'
    TEST_ATTENTION_NEEDED = 'test_attention_needed'


class ReviewRequest(BaseModel):
    '''Request to review a pull request.'''
    repo: str
    pr_number: int
    policy_profile: Optional[str] = None
    base_sha: Optional[str] = None
    head_sha: Optional[str] = None
    changed_files: List[str] = Field(default_factory=list)


class ReviewFinding(BaseModel):
    '''A single structured review finding tied to a code location.'''
    finding_id: str
    severity: FindingSeverity
    category: FindingCategory
    file_path: str
    line: Optional[int] = None
    confidence: float = 0.8
    explanation: str = ''
    recommendation: str = ''
    suppressed: bool = False
    suppression_reason: Optional[str] = None


class ReviewSummary(BaseModel):
    '''Summarized review verdict for a pull request.'''
    repo: str
    pr_number: int
    findings: List[ReviewFinding] = Field(default_factory=list)
    finding_count_by_severity: Dict[str, int] = Field(default_factory=dict)
    finding_count_by_category: Dict[str, int] = Field(default_factory=dict)
    policy_profile_used: Optional[str] = None
    overall_verdict: str = 'pending'
    reviewed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class PolicyProfile(BaseModel):
    '''Review policy profile for a repository or path scope.'''
    profile_id: str
    name: str
    description: str = ''
    rules: List[str] = Field(default_factory=list)
    severity_overrides: Dict[str, str] = Field(default_factory=dict)
    suppressions: List[str] = Field(default_factory=list)
    applicable_paths: List[str] = Field(default_factory=list)
    applicable_languages: List[str] = Field(default_factory=list)
