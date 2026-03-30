##########################################################################################
#
# Module: agents/workforce/curie/models.py
#
# Description: Data models for the Curie Test Generator Agent.
#              Defines generated test inputs, suite resolution records,
#              and generation decision records.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SuiteResolutionRecord(BaseModel):
    '''Record of how suite selection was resolved from plan intent.'''
    resolution_id: str
    test_plan_id: str
    selected_suites: List[str] = Field(default_factory=list)
    excluded_suites: List[str] = Field(default_factory=list)
    exclusion_reasons: Dict[str, str] = Field(default_factory=dict)
    auto_selection_used: bool = False
    version_hash: Optional[str] = None


class GenerationDecisionRecord(BaseModel):
    '''Record of why a particular generated input set was produced.'''
    decision_id: str
    test_plan_id: str
    build_id: str
    inputs_evaluated: Dict[str, Any] = Field(default_factory=dict)
    generation_strategy: str = ''
    rationale: str = ''
    deterministic: bool = True


class GeneratedTestInput(BaseModel):
    '''
    Concrete Fuze Test runtime inputs materialized from a TestPlan.

    These are ephemeral, auditable artifacts tied to a specific
    build_id and test_plan_id.
    '''
    generated_input_id: str
    test_plan_id: str
    build_id: str
    suite_file_list: List[str] = Field(default_factory=list)
    runtime_overlays: List[str] = Field(default_factory=list)
    dut_filters: Optional[Dict[str, List[str]]] = None
    generation_explanation: str = ''
    suite_resolution: Optional[SuiteResolutionRecord] = None
    decision_record: Optional[GenerationDecisionRecord] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
