##########################################################################################
#
# Module: agents/mercator/models.py
#
# Description: Pydantic models for the Mercator Version Manager agent.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VersionMappingRequest(BaseModel):
    '''Request to map an internal build ID to an external version.'''
    build_id: str = Field(..., description='Internal Fuze build identifier (FuzeID)')
    product: str = Field(..., description='Product or release name')
    branch: Optional[str] = Field(None, description='Branch or release-branch context')
    release_context: Optional[Dict[str, Any]] = Field(
        None, description='Release context from Humphrey'
    )
    policy_profile: Optional[str] = Field(
        None, description='Policy profile governing mapping rules'
    )
    external_version_hint: Optional[str] = Field(
        None, description='Optional marketing or customer-facing version hint'
    )


class VersionMappingRecord(BaseModel):
    '''Durable record of a build-to-version mapping.'''
    mapping_id: str = Field(..., description='Unique mapping record identifier')
    build_id: str = Field(..., description='Internal Fuze build identifier')
    external_version: str = Field(..., description='External customer-facing version')
    product: str = Field(..., description='Product or release name')
    status: str = Field(
        'proposed', description='Mapping status: proposed, confirmed, superseded, rejected'
    )
    created_at: Optional[datetime] = Field(None, description='When the mapping was created')
    confirmed_at: Optional[datetime] = Field(None, description='When the mapping was confirmed')
    confirmed_by: Optional[str] = Field(None, description='Who confirmed the mapping')
    metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional metadata')


class VersionLineageRecord(BaseModel):
    '''Records forward and reverse mapping relationships and supersession.'''
    lineage_id: str = Field(..., description='Unique lineage record identifier')
    source_mapping_id: str = Field(..., description='Source mapping in the lineage chain')
    target_mapping_id: str = Field(..., description='Target mapping in the lineage chain')
    relationship: str = Field(
        ..., description='Relationship type: supersedes, replaces, extends'
    )
    created_at: Optional[datetime] = Field(None, description='When the lineage was recorded')
    evidence: Optional[str] = Field(None, description='Evidence or reason for the relationship')


class VersionConflict(BaseModel):
    '''Records a detected version mapping conflict.'''
    conflict_id: str = Field(..., description='Unique conflict identifier')
    conflict_type: str = Field(
        ...,
        description=(
            'Conflict type: already_assigned, incompatible_mapping, '
            'scope_mismatch, ineligible_build, ambiguous_hint'
        ),
    )
    attempted_build_id: str = Field(..., description='Build ID that triggered the conflict')
    attempted_external_version: str = Field(
        ..., description='External version that was attempted'
    )
    existing_mapping_id: Optional[str] = Field(
        None, description='Existing mapping that conflicts'
    )
    resolution: Optional[str] = Field(
        None, description='Resolution status: pending, resolved, rejected'
    )
    resolved_by: Optional[str] = Field(None, description='Who resolved the conflict')
    created_at: Optional[datetime] = Field(None, description='When the conflict was detected')


class CompatibilityRecord(BaseModel):
    '''Stores compatibility and replacement relationships between versions.'''
    record_id: str = Field(..., description='Unique compatibility record identifier')
    source_version: str = Field(..., description='Source external version')
    target_version: str = Field(..., description='Target external version')
    relationship: str = Field(
        ..., description='Relationship type: compatible, replaces, incompatible'
    )
    product: str = Field(..., description='Product scope')
    notes: Optional[str] = Field(None, description='Additional compatibility notes')
    created_at: Optional[datetime] = Field(None, description='When the record was created')
