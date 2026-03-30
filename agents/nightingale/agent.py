##########################################################################################
#
# Module: agents/workforce/nightingale/agent.py
#
# Description: Nightingale Bug Investigation agent.
#              Reacts to Jira bugs, assembles build/test/release context,
#              drives targeted reproduction, and produces investigation summaries.
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
from agents.nightingale.models import (
    BugInvestigationRequest,
    BugInvestigationRecord,
    FailureSignatureRecord,
    ReproductionAttempt,
    InvestigationSummary,
)

log = logging.getLogger(os.path.basename(sys.argv[0]))

_PROMPT_DIR = Path(__file__).parent / 'prompts'


class NightingaleAgent(BaseAgent):
    '''
    Bug Investigation agent.

    Reacts to Jira bug reports, qualifies the report, assembles technical
    context, determines reproducibility, and coordinates targeted reproduction
    work until the bug is reproduced, blocked, or triaged for humans.

    Zone: intelligence
    Phase: 5
    '''

    def __init__(self, **kwargs):
        instruction = self._load_system_prompt()
        config = AgentConfig(
            name='nightingale',
            description=(
                'Reacts to Jira bugs, assembles build/test/release context, '
                'drives targeted reproduction, and produces investigation summaries'
            ),
            instruction=instruction,
            max_iterations=15,
        )
        super().__init__(config=config, **kwargs)

    @staticmethod
    def _load_system_prompt() -> str:
        prompt_path = _PROMPT_DIR / 'system.md'
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        log.warning(f'Nightingale system prompt not found: {prompt_path}')
        return 'You are Nightingale, the Bug Investigation agent for Cornelis Networks.'

    def run(self, input_data: Any) -> AgentResponse:
        '''
        Run the Nightingale agent.

        Input:
            input_data: A dict or string describing the bug investigation task.

        Output:
            AgentResponse with investigation results.
        '''
        return self._run_with_tools(str(input_data))

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def investigate_bug(
        self,
        jira_key: str,
        scope: Optional[str] = None,
        policy_profile: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Start or continue a bug investigation.

        Input:
            jira_key: Jira issue key for the bug.
            scope: Investigation scope.
            policy_profile: Policy profile governing investigation rules.

        Output:
            BugInvestigationRecord with current status and findings.
        '''
        pass

    def request_reproduction(
        self,
        jira_key: str,
        build_id: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Request a targeted reproduction attempt for a bug.

        Input:
            jira_key: Jira issue key.
            build_id: Specific build to reproduce against.
            environment: Target environment for reproduction.

        Output:
            ReproductionAttempt record.
        '''
        pass

    def get_investigation_summary(self, jira_key: str) -> Dict[str, Any]:
        '''
        Get the current investigation summary for a bug.

        Input:
            jira_key: Jira issue key.

        Output:
            InvestigationSummary with findings, status, and next steps.
        '''
        pass

    def get_reproduction_attempts(self, jira_key: str) -> List[Dict[str, Any]]:
        '''
        Get all reproduction attempts for a bug.

        Input:
            jira_key: Jira issue key.

        Output:
            List of ReproductionAttempt records.
        '''
        pass
