##########################################################################################
#
# Module: agents/workforce/babbage/api.py
#
# Description: FastAPI router for the Babbage Version Manager agent.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from fastapi import APIRouter

from agents.workforce.babbage.models import (
    VersionMappingRequest,
    VersionMappingRecord,
)

router = APIRouter(prefix='/v1/version-mappings', tags=['babbage'])


@router.post('/', response_model=VersionMappingRecord)
async def create_version_mapping(request: VersionMappingRequest):
    '''Create a new version mapping from build ID to external version.'''
    raise NotImplementedError('Babbage API not yet implemented')


@router.get('/{mapping_id}', response_model=VersionMappingRecord)
async def get_version_mapping(mapping_id: str):
    '''Get a specific version mapping record and lineage.'''
    raise NotImplementedError('Babbage API not yet implemented')


@router.get('/by-build/{build_id}')
async def get_mappings_by_build(build_id: str):
    '''Get external version mappings for a build.'''
    raise NotImplementedError('Babbage API not yet implemented')


@router.get('/by-external/{external_version}')
async def get_mappings_by_external(external_version: str):
    '''Get internal builds and lineage for an external version.'''
    raise NotImplementedError('Babbage API not yet implemented')


@router.post('/{mapping_id}/confirm', response_model=VersionMappingRecord)
async def confirm_mapping(mapping_id: str):
    '''Confirm a proposed mapping when required by policy.'''
    raise NotImplementedError('Babbage API not yet implemented')
