##########################################################################################
#
# Module: agents/workforce/curie/api.py
#
# Description: FastAPI router for the Curie Test Generator Agent.
#              Exposes test input generation, retrieval, and artifact endpoints.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict

router = APIRouter(prefix='/v1/test-inputs', tags=['curie'])


@router.post('/generate', response_model=Dict[str, Any])
async def generate_test_inputs(request: Dict[str, Any]) -> Dict[str, Any]:
    '''Generate concrete Fuze Test inputs from a TestPlan.'''
    raise HTTPException(status_code=501, detail='Not implemented')


@router.get('/{generated_input_id}', response_model=Dict[str, Any])
async def get_test_input(generated_input_id: str) -> Dict[str, Any]:
    '''Get generated suite inputs, overlays, and explanation.'''
    raise HTTPException(status_code=501, detail='Not implemented')


@router.get('/{generated_input_id}/artifacts', response_model=Dict[str, Any])
async def get_test_artifacts(generated_input_id: str) -> Dict[str, Any]:
    '''Get links to generated runtime artifacts.'''
    raise HTTPException(status_code=501, detail='Not implemented')
