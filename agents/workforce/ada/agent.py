##########################################################################################
#
# Module: agents/workforce/ada/agent.py
#
# Description: Ada Test Planner Agent.
#              Determines what to test based on trigger class, coverage targets,
#              and environment constraints. Produces durable TestPlan records.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentConfig, AgentResponse
from agents.workforce.ada.models import (
    TestPlanRequest,
    TestPlan,
    CoverageSummary,
    PlanningPolicyDecision,
)

log = logging.getLogger(os.path.basename(sys.argv[0]))


class AdaAgent(BaseAgent):
    '''
    Test Planner Agent for the Execution Spine.

    Ada turns build context, trigger type, environment state, and coverage
    needs into a durable TestPlan that downstream test agents can act on.
    '''

    def __init__(self, **kwargs):
        prompt_path = Path(__file__).parent / 'prompts' / 'system.md'
        instruction = ''
        if prompt_path.exists():
            instruction = prompt_path.read_text(encoding='utf-8')

        config = AgentConfig(
            name='ada',
            description='Test Planner Agent — determines what to test based on trigger class and coverage targets',
            instruction=instruction,
            max_iterations=12,
        )

        super().__init__(config=config, **kwargs)
        self._register_tools()

    def _register_tools(self) -> None:
        pass

    def run(self, input_data: Any) -> AgentResponse:
        if isinstance(input_data, str):
            return self.get_test_plan(test_plan_id=input_data)
        elif isinstance(input_data, dict):
            action = input_data.get('action', 'select_test_plan')
            if action == 'select_test_plan':
                return self.select_test_plan(input_data)
            elif action == 'get_plan':
                return self.get_test_plan(input_data.get('test_plan_id', ''))
            elif action == 'invalidate':
                return self.invalidate_test_plan(input_data.get('test_plan_id', ''))
            else:
                return AgentResponse.error_response(f'Unknown action: {action}')
        return AgentResponse.error_response(
            'Invalid input: expected test_plan_id string or request dict'
        )

    def select_test_plan(self, request_data: Dict[str, Any]) -> AgentResponse:
        '''Select the right test plan for the given build and trigger context.'''
        # TODO: Resolve trigger class, scope, coverage intent, produce TestPlan
        return AgentResponse.error_response('Not implemented')

    def get_test_plan(self, test_plan_id: str) -> AgentResponse:
        '''Get a test plan by ID with its trigger context and linked build ID.'''
        # TODO: Query plan store
        return AgentResponse.error_response('Not implemented')

    def invalidate_test_plan(self, test_plan_id: str) -> AgentResponse:
        '''Invalidate a test plan when source assumptions change.'''
        # TODO: Mark plan as invalidated, emit event
        return AgentResponse.error_response('Not implemented')
