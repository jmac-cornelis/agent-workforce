##########################################################################################
#
# Module: agents/workforce/ada/models.py
#
# Description: Data models for the Ada Test Planner Agent.
#              Defines test plan requests, plans, coverage summaries,
#              and planning policy decisions.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TriggerType(str, Enum):
    PULL_REQUEST = 'pull_request'
    MERGE = 'merge'
    NIGHTLY = 'nightly'
    RELEASE_VALIDATION = 'release_validation'


class ExecutionMode(str, Enum):
    MOCK = 'mock'
    HIL = 'hil'


class TestPlanRequest(BaseModel):
    '''Normalized input for test plan selection.'''
    build_id: str
    repo: str
    commit_sha: str
    branch: str
    trigger_type: TriggerType
    module: str
    project: str
    module_version: Optional[str] = None
    hardware_profile: Optional[str] = None
    location: Optional[str] = None
    test_setup: Optional[str] = None
    environment_state: Optional[Dict[str, Any]] = None
    coverage_context: Optional[Dict[str, Any]] = None
    policy_profile: Optional[str] = None


class CoverageSummary(BaseModel):
    '''Coverage intent and gap summary for a test plan.'''
    coverage_target: float = 0.0
    known_gaps: List[str] = Field(default_factory=list)
    modules_covered: List[str] = Field(default_factory=list)
    modules_uncovered: List[str] = Field(default_factory=list)


class PlanningPolicyDecision(BaseModel):
    '''Record of a planning policy decision with rationale.'''
    decision_id: str
    trigger_type: TriggerType
    plan_class: str
    inputs_evaluated: Dict[str, Any] = Field(default_factory=dict)
    candidates_considered: List[str] = Field(default_factory=list)
    selected: str = ''
    rationale: str = ''
    fallback_applied: bool = False


class TestPlan(BaseModel):
    '''
    Durable test plan produced by Ada.

    Links build context to suite selection intent, environment requirements,
    and execution constraints for downstream agents.
    '''
    plan_id: str
    build_id: str
    trigger_class: TriggerType
    suite_selection_intent: List[str] = Field(default_factory=list)
    environment_class: str = 'mock'
    execution_mode: ExecutionMode = ExecutionMode.MOCK
    timeout_budget_seconds: int = 3600
    result_retention_class: str = 'standard'
    coverage_intent: Optional[CoverageSummary] = None
    policy_decision: Optional[PlanningPolicyDecision] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
