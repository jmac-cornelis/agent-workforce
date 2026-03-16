##########################################################################################
#
# Module: agents/workforce/shannon/agent.py
#
# Description: Shannon Communications agent.
#              Single Teams bot serving all agent channels. Routes commands,
#              manages approvals, posts notifications, and logs all
#              human-agent interactions.
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
from agents.workforce.shannon.models import (
    AgentRegistryEntry,
    ConversationRecord,
    ApprovalRecord,
    NotificationRequest,
    InputRequest,
)

log = logging.getLogger(os.path.basename(sys.argv[0]))

_PROMPT_DIR = Path(__file__).parent / 'prompts'


class ShannonAgent(BaseAgent):
    '''
    Communications agent.

    Single Microsoft Teams bot serving all 15 domain agent channels.
    Routes commands, manages approval workflows, posts notifications,
    and logs every human-agent interaction for audit.

    Zone: service_infrastructure
    Phase: 0
    '''

    def __init__(self, **kwargs):
        instruction = self._load_system_prompt()
        config = AgentConfig(
            name='shannon',
            description=(
                'Single Teams bot serving all agent channels. Routes commands, '
                'manages approvals, posts notifications, and logs all '
                'human-agent interactions'
            ),
            instruction=instruction,
            max_iterations=10,
        )
        super().__init__(config=config, **kwargs)

    @staticmethod
    def _load_system_prompt() -> str:
        prompt_path = _PROMPT_DIR / 'system.md'
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        log.warning(f'Shannon system prompt not found: {prompt_path}')
        return 'You are Shannon, the Communications agent for Cornelis Networks.'

    def run(self, input_data: Any) -> AgentResponse:
        '''
        Run the Shannon agent.

        Input:
            input_data: A dict or string describing the communications task.

        Output:
            AgentResponse with routing or notification results.
        '''
        return self._run_with_tools(str(input_data))

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def notify_channel(
        self,
        agent_id: str,
        message: str,
        card_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        '''
        Post an activity notification to an agent's Teams channel.

        Input:
            agent_id: Target agent identifier.
            message: Notification message content.
            card_type: Optional Adaptive Card type to render.
            metadata: Optional additional metadata for the card.

        Output:
            Notification delivery status.
        '''
        pass

    def request_approval(
        self,
        agent_id: str,
        approval_type: str,
        title: str,
        description: str,
        evidence: Optional[Dict[str, Any]] = None,
        timeout_hours: Optional[int] = None,
        escalation_targets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        '''
        Request human approval via an Adaptive Card in the agent's channel.

        Input:
            agent_id: Requesting agent identifier.
            approval_type: Type of approval being requested.
            title: Approval request title.
            description: Description of what is being approved.
            evidence: Supporting evidence for the approval.
            timeout_hours: Hours before timeout triggers escalation.
            escalation_targets: Users to escalate to on timeout.

        Output:
            ApprovalRecord with pending status.
        '''
        pass

    def request_input(
        self,
        agent_id: str,
        title: str,
        fields: List[Dict[str, Any]],
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Request structured human input via a form card.

        Input:
            agent_id: Requesting agent identifier.
            title: Input request title.
            fields: List of field definitions for the form.
            context: Optional context for the request.

        Output:
            Input request record with pending status.
        '''
        pass

    def send_alert(
        self,
        agent_id: str,
        severity: str,
        message: str,
        suggested_actions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        '''
        Post an error alert to an agent's Teams channel.

        Input:
            agent_id: Source agent identifier.
            severity: Alert severity: critical, high, medium, low.
            message: Alert message.
            suggested_actions: Optional suggested remediation actions.

        Output:
            Alert delivery status.
        '''
        pass

    def check_approval_status(self, approval_id: str) -> Dict[str, Any]:
        '''
        Check the status of a pending approval.

        Input:
            approval_id: Approval record identifier.

        Output:
            Current approval status and response details.
        '''
        pass
