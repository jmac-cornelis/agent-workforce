##########################################################################################
#
# Module: agents/bernerslee/api.py
#
# Description: FastAPI router for the Berners-Lee Traceability agent.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from agents.bernerslee.models import TraceAssertion

router = APIRouter(prefix='/v1/trace', tags=['bernerslee'])


@router.post('/assert', response_model=TraceAssertion)
async def assert_trace(source_type: str, source_id: str, target_type: str,
                       target_id: str, edge_type: str):
    '''Assert a traceability relationship between two records.'''
    raise NotImplementedError('Berners-Lee API not yet implemented')


@router.get('/builds/{build_id}')
async def get_build_trace(build_id: str):
    '''Return related issues, tests, releases, and external versions for a build.'''
    raise NotImplementedError('Berners-Lee API not yet implemented')


@router.get('/issues/{jira_key}')
async def get_issue_trace(jira_key: str):
    '''Return linked builds, tests, release relevance, and gap flags for an issue.'''
    raise NotImplementedError('Berners-Lee API not yet implemented')


@router.get('/releases/{release_id}')
async def get_release_trace(release_id: str):
    '''Return linked builds, issues, tests, and versions for a release.'''
    raise NotImplementedError('Berners-Lee API not yet implemented')


@router.get('/gaps')
async def get_coverage_gaps(project: Optional[str] = None,
                            severity: Optional[str] = None):
    '''Return missing-link findings by project, product, or severity.'''
    raise NotImplementedError('Berners-Lee API not yet implemented')
