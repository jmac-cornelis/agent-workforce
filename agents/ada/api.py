##########################################################################################
#
# Module: agents/workforce/ada/api.py
#
# Description: FastAPI router for the Ada Test Planner Agent.
#              Exposes test plan selection, retrieval, and event endpoints.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict

from agents.ada.models import TestPlanRequest, TestPlan

router = APIRouter(prefix='/v1/test-plans', tags=['ada'])


@router.post('/select', response_model=Dict[str, Any])
async def select_test_plan(request: TestPlanRequest) -> Dict[str, Any]:
    '''Select a test plan based on build and trigger context.'''
    raise HTTPException(status_code=501, detail='Not implemented')


@router.get('/{test_plan_id}', response_model=Dict[str, Any])
async def get_test_plan(test_plan_id: str) -> Dict[str, Any]:
    '''Get normalized plan state, trigger context, and linked build ID.'''
    raise HTTPException(status_code=501, detail='Not implemented')


@router.get('/{test_plan_id}/events', response_model=Dict[str, Any])
async def get_test_plan_events(test_plan_id: str) -> Dict[str, Any]:
    '''Get planning events for a test plan.'''
    raise HTTPException(status_code=501, detail='Not implemented')
