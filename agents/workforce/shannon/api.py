##########################################################################################
#
# Module: agents/workforce/shannon/api.py
#
# Description: FastAPI router for the Shannon Communications agent.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from fastapi import APIRouter

from agents.workforce.shannon.models import NotificationRequest

router = APIRouter(prefix='/v1/bot', tags=['shannon'])


@router.post('/notify')
async def notify_channel(request: NotificationRequest):
    '''Agent posts activity notification to its channel.'''
    raise NotImplementedError('Shannon API not yet implemented')


@router.post('/request-approval')
async def request_approval(agent_id: str, approval_type: str, title: str,
                           description: str):
    '''Agent requests human approval via Adaptive Card.'''
    raise NotImplementedError('Shannon API not yet implemented')


@router.post('/request-input')
async def request_input(agent_id: str, title: str):
    '''Agent requests structured human input via form card.'''
    raise NotImplementedError('Shannon API not yet implemented')


@router.post('/alert')
async def send_alert(agent_id: str, severity: str, message: str):
    '''Agent posts error alert to its channel.'''
    raise NotImplementedError('Shannon API not yet implemented')


@router.get('/approvals/{approval_id}')
async def check_approval_status(approval_id: str):
    '''Check approval status.'''
    raise NotImplementedError('Shannon API not yet implemented')


@router.get('/health')
async def health_check():
    '''Bot health check — uptime, agent connectivity, pending approvals.'''
    raise NotImplementedError('Shannon API not yet implemented')
