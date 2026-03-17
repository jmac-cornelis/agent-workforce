##########################################################################################
#
# Module: agents/workforce/curie/agent.py
#
# Description: Curie Test Generator Agent.
#              Materializes Ada's TestPlan into concrete Fuze Test runtime
#              inputs that Faraday can execute.
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
from agents.workforce.curie.models import (
    GeneratedTestInput,
    SuiteResolutionRecord,
    GenerationDecisionRecord,
)

log = logging.getLogger(os.path.basename(sys.argv[0]))


class CurieAgent(BaseAgent):
    '''
    Test Generator Agent for the Execution Spine.

    Curie takes Ada's TestPlan and turns it into concrete Fuze Test
    runtime inputs — explicit suite lists, runtime overlays, and DUT
    filters — that Faraday can execute reproducibly.
    '''

    def __init__(self, **kwargs):
        prompt_path = Path(__file__).parent / 'prompts' / 'system.md'
        instruction = ''
        if prompt_path.exists():
            instruction = prompt_path.read_text(encoding='utf-8')

        config = AgentConfig(
            name='curie',
            description='Test Generator Agent — materializes test plans into executable Fuze Test inputs',
            instruction=instruction,
            max_iterations=10,
        )

        super().__init__(config=config, **kwargs)
        self._register_tools()

    def _register_tools(self) -> None:
        pass

    def run(self, input_data: Any) -> AgentResponse:
        if isinstance(input_data, str):
            return self.get_test_input(generated_input_id=input_data)
        elif isinstance(input_data, dict):
            action = input_data.get('action', 'generate')
            if action == 'generate':
                return self.generate_test_inputs(input_data)
            elif action == 'get_input':
                return self.get_test_input(input_data.get('generated_input_id', ''))
            elif action == 'get_artifacts':
                return self.get_test_artifacts(input_data.get('generated_input_id', ''))
            else:
                return AgentResponse.error_response(f'Unknown action: {action}')
        return AgentResponse.error_response(
            'Invalid input: expected generated_input_id string or request dict'
        )

    def generate_test_inputs(self, request_data: Dict[str, Any]) -> AgentResponse:
        '''Generate concrete Fuze Test inputs from a TestPlan.'''
        # TODO: Resolve suites, build runtime inputs, store artifacts
        return AgentResponse.error_response('Not implemented')

    def get_test_input(self, generated_input_id: str) -> AgentResponse:
        '''Get generated test input by ID with suite inputs and explanation.'''
        # TODO: Query generation store
        return AgentResponse.error_response('Not implemented')

    def get_test_artifacts(self, generated_input_id: str) -> AgentResponse:
        '''Get generated runtime artifacts for a test input set.'''
        # TODO: Query artifact store for generated inputs
        return AgentResponse.error_response('Not implemented')
