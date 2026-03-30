##########################################################################################
#
# Module: agents/workforce/josephine/agent.py
#
# Description: Josephine Build & Package Agent.
#              Accepts build jobs through an API, executes them on dedicated workers
#              using the extracted fuze core, and publishes packages, logs, and
#              provenance in a Fuze-compatible format.
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
from agents.josephine.models import (
    BuildRequest,
    BuildResult,
    BuildRecord,
    FailureResult,
)

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class JosephineAgent(BaseAgent):
    '''
    Build & Package Agent for the Execution Spine.

    Josephine orchestrates build jobs through the fuze core, managing the
    full lifecycle from job submission through artifact publication. It
    preserves existing build-map behavior, package semantics, FuzeID rules,
    and Fuze-compatible metadata lineage.
    '''

    def __init__(self, **kwargs):
        # Load system prompt from the prompts directory
        prompt_path = Path(__file__).parent / 'prompts' / 'system.md'
        instruction = ''
        if prompt_path.exists():
            instruction = prompt_path.read_text(encoding='utf-8')

        config = AgentConfig(
            name='josephine',
            description='Build & Package Agent — orchestrates fuze-based build jobs',
            instruction=instruction,
            max_iterations=15,
        )

        super().__init__(config=config, **kwargs)

        # Register tools for build operations
        self._register_tools()

    def _register_tools(self) -> None:
        '''Register Josephine-specific tools for build operations.'''
        # Tools will be registered here as ToolDefinition instances
        # once the tool implementations are built.
        pass

    def run(self, input_data: Any) -> AgentResponse:
        '''
        Run the Josephine agent with the given input.

        Input:
            input_data: A BuildRequest dict, build_id string, or command dict.

        Output:
            AgentResponse with build status or result.
        '''
        if isinstance(input_data, str):
            # Treat as a build_id status query
            return self.get_build_status(build_id=input_data)
        elif isinstance(input_data, dict):
            action = input_data.get('action', 'request_build')
            if action == 'request_build':
                return self.request_build(input_data)
            elif action == 'get_status':
                return self.get_build_status(input_data.get('build_id', ''))
            elif action == 'cancel':
                return self.cancel_build(input_data.get('build_id', ''))
            elif action == 'retry':
                return self.retry_build(input_data.get('build_id', ''))
            else:
                return AgentResponse.error_response(f'Unknown action: {action}')
        return AgentResponse.error_response(
            'Invalid input: expected build_id string or request dict'
        )

    # ------------------------------------------------------------------
    # Tool methods — scaffolding with pass bodies
    # ------------------------------------------------------------------

    def request_build(self, request_data: Dict[str, Any]) -> AgentResponse:
        '''
        Submit a new build job.

        Accepts repo_url, git_ref, build_map_path, targets, packages,
        publish_mode, workspace_profile_ref, variables, and labels.
        '''
        # TODO: Validate request, create BuildRequest, submit to queue
        return AgentResponse.error_response('Not implemented')

    def get_build_status(self, build_id: str) -> AgentResponse:
        '''Get the current status of a build job.'''
        # TODO: Query job state store by build_id
        return AgentResponse.error_response('Not implemented')

    def get_artifact_manifest(self, build_id: str) -> AgentResponse:
        '''Get the artifact manifest for a completed build.'''
        # TODO: Query artifact store for build_id
        return AgentResponse.error_response('Not implemented')

    def cancel_build(self, build_id: str) -> AgentResponse:
        '''Cancel a queued or running build job.'''
        # TODO: Send cancellation to queue/worker
        return AgentResponse.error_response('Not implemented')

    def retry_build(self, build_id: str) -> AgentResponse:
        '''Retry a failed build job.'''
        # TODO: Validate retry eligibility, resubmit to queue
        return AgentResponse.error_response('Not implemented')
