##########################################################################################
#
# Module: agents/workforce/linus/agent.py
#
# Description: Linus Code Review Agent.
#              Evaluates PRs against policy profiles and emits structured
#              findings and cross-agent impact signals.
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
from agents.workforce.linus.models import (
    ReviewRequest,
    ReviewFinding,
    ReviewSummary,
    PolicyProfile,
)

log = logging.getLogger(os.path.basename(sys.argv[0]))


class LinusAgent(BaseAgent):
    '''
    Code Review Agent for the Execution Spine.

    Linus evaluates pull requests against code-quality and review-policy
    rules, produces structured findings, surfaces correctness risks early,
    and emits signals to downstream agents when documentation, build, or
    test attention is warranted.
    '''

    def __init__(self, **kwargs):
        prompt_path = Path(__file__).parent / 'prompts' / 'system.md'
        instruction = ''
        if prompt_path.exists():
            instruction = prompt_path.read_text(encoding='utf-8')

        config = AgentConfig(
            name='linus',
            description='Code Review Agent — evaluates PRs against policy profiles and emits impact signals',
            instruction=instruction,
            max_iterations=10,
        )

        super().__init__(config=config, **kwargs)
        self._register_tools()

    def _register_tools(self) -> None:
        pass

    def run(self, input_data: Any) -> AgentResponse:
        if isinstance(input_data, str):
            return self.get_review_summary(pr_ref=input_data)
        elif isinstance(input_data, dict):
            action = input_data.get('action', 'review')
            if action == 'review':
                return self.review_pr(input_data)
            elif action == 'summary':
                return self.get_review_summary(input_data.get('pr_ref', ''))
            elif action == 'findings':
                return self.get_review_findings(input_data.get('pr_ref', ''))
            elif action == 'publish':
                return self.publish_review(input_data.get('pr_ref', ''))
            else:
                return AgentResponse.error_response(f'Unknown action: {action}')
        return AgentResponse.error_response(
            'Invalid input: expected pr_ref string or request dict'
        )

    def review_pr(self, request_data: Dict[str, Any]) -> AgentResponse:
        '''Evaluate a PR against the appropriate policy profile.'''
        # TODO: Parse diff, select policy profile, generate findings
        return AgentResponse.error_response('Not implemented')

    def get_review_summary(self, pr_ref: str) -> AgentResponse:
        '''Get the current review summary and structured findings for a PR.'''
        # TODO: Query review store
        return AgentResponse.error_response('Not implemented')

    def get_review_findings(self, pr_ref: str) -> AgentResponse:
        '''Get detailed findings and inline comment payloads for a PR.'''
        # TODO: Query findings store
        return AgentResponse.error_response('Not implemented')

    def publish_review(self, pr_ref: str) -> AgentResponse:
        '''Publish review comments or summary status to GitHub.'''
        # TODO: Post inline comments and summary to GitHub
        return AgentResponse.error_response('Not implemented')
