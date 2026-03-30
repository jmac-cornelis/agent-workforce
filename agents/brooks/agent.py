##########################################################################################
#
# Module: agents/workforce/brooks/agent.py
#
# Description: Brooks Delivery Manager agent.
#              Monitors execution against plan, detects schedule risk and
#              coordination failures, produces forecasts and escalation prompts.
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
from agents.brooks.models import (
    DeliverySnapshot,
    DeliveryRiskRecord,
    ForecastRecord,
    StatusSummary,
    EscalationRecord,
)

log = logging.getLogger(os.path.basename(sys.argv[0]))

_PROMPT_DIR = Path(__file__).parent / 'prompts'


class BrooksAgent(BaseAgent):
    '''
    Delivery Manager agent.

    Monitors execution against plan, detects schedule risk and coordination
    failure early, and produces operational delivery summaries for humans.
    Gantt plans; Brooks watches delivery reality and flags drift.

    Zone: planning
    Phase: 6
    '''

    def __init__(self, **kwargs):
        instruction = self._load_system_prompt()
        config = AgentConfig(
            name='brooks',
            description=(
                'Monitors execution against plan, detects schedule risk and '
                'coordination failures, produces forecasts and escalation prompts'
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
        log.warning(f'Brooks system prompt not found: {prompt_path}')
        return 'You are Brooks, the Delivery Manager agent for Cornelis Networks.'

    def run(self, input_data: Any) -> AgentResponse:
        '''
        Run the Brooks agent.

        Input:
            input_data: A dict or string describing the delivery management task.

        Output:
            AgentResponse with delivery status results.
        '''
        return self._run_with_tools(str(input_data))

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def create_delivery_snapshot(
        self,
        project_key: str,
        milestone_scope: Optional[str] = None,
        time_horizon: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Create a delivery snapshot combining Jira and technical evidence.

        Input:
            project_key: Project scope.
            milestone_scope: Optional milestone filter.
            time_horizon: Optional time horizon for the snapshot.

        Output:
            DeliverySnapshot with status, risk, and forecast.
        '''
        pass

    def get_delivery_status(self, project_key: str) -> Dict[str, Any]:
        '''
        Get current delivery status summary and confidence for a project.

        Input:
            project_key: Project identifier.

        Output:
            StatusSummary with confidence and evidence references.
        '''
        pass

    def get_delivery_risks(self, project_key: str) -> List[Dict[str, Any]]:
        '''
        Get active delivery risks and escalations for a project.

        Input:
            project_key: Project identifier.

        Output:
            List of DeliveryRiskRecord entries.
        '''
        pass

    def get_forecast(
        self,
        project_key: str,
        milestone: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Get near-term delivery forecast for a project or milestone.

        Input:
            project_key: Project identifier.
            milestone: Optional specific milestone.

        Output:
            ForecastRecord with confidence and slip signals.
        '''
        pass
