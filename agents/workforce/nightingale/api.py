##########################################################################################
#
# Module: agents/workforce/nightingale/api.py
#
# Description: FastAPI router for the Nightingale Bug Investigation agent.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from fastapi import APIRouter

from agents.workforce.nightingale.models import BugInvestigationRequest

router = APIRouter(prefix='/v1/bugs', tags=['nightingale'])


@router.post('/investigate')
async def investigate_bug(request: BugInvestigationRequest):
    '''Start a bug investigation.'''
    raise NotImplementedError('Nightingale API not yet implemented')


@router.get('/{jira_key}')
async def get_investigation(jira_key: str):
    '''Return current investigation status, missing data, and linked evidence.'''
    raise NotImplementedError('Nightingale API not yet implemented')


@router.post('/{jira_key}/reproduce')
async def request_reproduction(jira_key: str):
    '''Request a targeted reproduction attempt.'''
    raise NotImplementedError('Nightingale API not yet implemented')


@router.get('/{jira_key}/attempts')
async def get_reproduction_attempts(jira_key: str):
    '''Return reproduction attempts and outcomes.'''
    raise NotImplementedError('Nightingale API not yet implemented')


@router.post('/{jira_key}/summarize')
async def summarize_investigation(jira_key: str):
    '''Produce an investigation summary for humans.'''
    raise NotImplementedError('Nightingale API not yet implemented')
