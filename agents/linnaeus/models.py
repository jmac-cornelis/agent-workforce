##########################################################################################
#
# Module: agents/workforce/linnaeus/models.py
#
# Description: Pydantic models for the Linnaeus Traceability agent.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TraceabilityRecord(BaseModel):
    '''A stored traceability record linking two system entities.'''
    record_id: str = Field(..., description='Unique traceability record identifier')
    source_type: str = Field(..., description='Type of source record (issue, build, test, etc.)')
    source_id: str = Field(..., description='Identifier of the source record')
    target_type: str = Field(..., description='Type of target record')
    target_id: str = Field(..., description='Identifier of the target record')
    edge_type: str = Field(
        ...,
        description=(
            'Relationship type: issue_affects_build, issue_fixed_in_build, '
            'build_validated_by_test_run, build_promoted_to_release, '
            'build_mapped_to_external_version, requirement_implemented_by_commit, '
            'requirement_verified_by_test_run, release_impacted_by_issue'
        ),
    )
    confidence: str = Field('explicit', description='Confidence level: explicit, inferred')
    evidence_source: Optional[str] = Field(None, description='Where the evidence came from')
    created_at: Optional[datetime] = Field(None, description='When the record was created')
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RelationshipEdge(BaseModel):
    '''A directed edge in the traceability graph.'''
    edge_id: str = Field(..., description='Unique edge identifier')
    source_type: str = Field(..., description='Source record type')
    source_id: str = Field(..., description='Source record identifier')
    target_type: str = Field(..., description='Target record type')
    target_id: str = Field(..., description='Target record identifier')
    edge_type: str = Field(..., description='Relationship type')
    confidence: str = Field('explicit', description='explicit or inferred')
    evidence_source: Optional[str] = Field(None, description='Evidence origin')
    created_at: Optional[datetime] = Field(None)


class TraceQuery(BaseModel):
    '''A query against the traceability graph.'''
    record_type: str = Field(..., description='Type of record to query from')
    record_id: str = Field(..., description='Identifier of the record')
    depth: int = Field(1, description='Traversal depth')
    edge_types: Optional[List[str]] = Field(None, description='Filter by edge types')
    include_inferred: bool = Field(True, description='Include inferred relationships')


class CoverageGapRecord(BaseModel):
    '''A missing or incomplete link in a critical traceability chain.'''
    gap_id: str = Field(..., description='Unique gap identifier')
    gap_class: str = Field(
        ...,
        description='Gap class: missing_build_link, missing_test_link, missing_release_link',
    )
    record_type: str = Field(..., description='Record type where the gap was detected')
    record_id: str = Field(..., description='Record identifier')
    expected_target_type: str = Field(..., description='What type of link is missing')
    severity: str = Field('medium', description='Gap severity: high, medium, low')
    project: Optional[str] = Field(None, description='Project scope')
    detected_at: Optional[datetime] = Field(None)
    suppressed: bool = Field(False, description='Whether this gap has been suppressed')


class TraceAssertion(BaseModel):
    '''An explicit assertion of a traceability relationship.'''
    assertion_id: str = Field(..., description='Unique assertion identifier')
    source_type: str = Field(..., description='Source record type')
    source_id: str = Field(..., description='Source record identifier')
    target_type: str = Field(..., description='Target record type')
    target_id: str = Field(..., description='Target record identifier')
    edge_type: str = Field(..., description='Relationship type')
    evidence_source: str = Field(..., description='Where the evidence came from')
    asserted_by: Optional[str] = Field(None, description='Who or what made the assertion')
    created_at: Optional[datetime] = Field(None)
