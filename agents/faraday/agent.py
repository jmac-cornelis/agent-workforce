##########################################################################################
#
# Module: agents/workforce/faraday/agent.py
#
# Description: Faraday Test Executor Agent.
#              Runs ATF/Fuze Test cycles, captures results and artifacts,
#              classifies failures, and produces TestExecutionRecords.
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
from agents.faraday.models import (
    TestRunRequest,
    TestExecutionRecord,
    TestFailureRecord,
    EnvironmentReservation,
)

log = logging.getLogger(os.path.basename(sys.argv[0]))


class FaradayAgent(BaseAgent):
    '''
    Test Executor Agent for the Execution Spine.

    Faraday takes resolved TestPlans, acquires environments through Tesla,
    executes tests through Fuze Test, collects results, and publishes
    machine-readable execution records tied to the originating build ID.
    '''

    def __init__(self, **kwargs):
        prompt_path = Path(__file__).parent / 'prompts' / 'system.md'
        instruction = ''
        if prompt_path.exists():
            instruction = prompt_path.read_text(encoding='utf-8')

        config = AgentConfig(
            name='faraday',
            description='Test Executor Agent — runs ATF/Fuze Test cycles and produces execution records',
            instruction=instruction,
            max_iterations=15,
        )

        super().__init__(config=config, **kwargs)
        self._register_tools()

    def _register_tools(self) -> None:
        pass

    def run(self, input_data: Any) -> AgentResponse:
        if isinstance(input_data, str):
            return self.get_test_run_status(test_run_id=input_data)
        elif isinstance(input_data, dict):
            action = input_data.get('action', 'create_run')
            if action == 'create_run':
                return self.create_test_run(input_data)
            elif action == 'cancel':
                return self.cancel_test_run(input_data.get('test_run_id', ''))
            elif action == 'get_status':
                return self.get_test_run_status(input_data.get('test_run_id', ''))
            elif action == 'get_results':
                return self.get_test_results(input_data.get('test_run_id', ''))
            else:
                return AgentResponse.error_response(f'Unknown action: {action}')
        return AgentResponse.error_response(
            'Invalid input: expected test_run_id string or request dict'
        )

    def create_test_run(self, request_data: Dict[str, Any]) -> AgentResponse:
        '''Create and dispatch a new test run.'''
        # TODO: Validate reservation, stage runtime, invoke Fuze Test
        return AgentResponse.error_response('Not implemented')

    def cancel_test_run(self, test_run_id: str) -> AgentResponse:
        '''Cancel a queued or running test execution.'''
        # TODO: Send cancellation signal to worker
        return AgentResponse.error_response('Not implemented')

    def get_test_run_status(self, test_run_id: str) -> AgentResponse:
        '''Get current run state, stage, worker, environment, and summary.'''
        # TODO: Query run state store
        return AgentResponse.error_response('Not implemented')

    def get_test_results(self, test_run_id: str) -> AgentResponse:
        '''Get normalized result record and artifact links for a test run.'''
        # TODO: Query result store
        return AgentResponse.error_response('Not implemented')
