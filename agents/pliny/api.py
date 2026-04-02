##########################################################################################
#
# Module: agents/pliny/api.py
#
# Description: FastAPI router for the Pliny Knowledge Capture agent.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix='/v1/meetings', tags=['pliny'])


@router.post('/ingest')
async def ingest_meeting(meeting_id: str, transcript_ref: str):
    '''Ingest a meeting transcript and metadata.'''
    raise NotImplementedError('Pliny API not yet implemented')


@router.post('/{meeting_id}/summarize')
async def summarize_meeting(meeting_id: str):
    '''Generate or regenerate a structured meeting summary.'''
    raise NotImplementedError('Pliny API not yet implemented')


@router.get('/{meeting_id}')
async def get_meeting(meeting_id: str):
    '''Return ingest status, transcript status, and linked summary records.'''
    raise NotImplementedError('Pliny API not yet implemented')


@router.get('/{meeting_id}/summary')
async def get_meeting_summary(meeting_id: str):
    '''Return structured summary, decisions, action items, and open questions.'''
    raise NotImplementedError('Pliny API not yet implemented')


@router.post('/{meeting_id}/publish')
async def publish_summary(meeting_id: str):
    '''Publish approved outputs to configured targets.'''
    raise NotImplementedError('Pliny API not yet implemented')
