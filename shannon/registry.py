##########################################################################################
#
# Module: shannon/registry.py
#
# Description: Agent/channel registry loading for the Shannon Teams bot.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from shannon.models import AgentChannelRegistration

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class ShannonAgentRegistry:
    '''
    Load and resolve channel-to-agent registrations for Shannon.
    '''

    def __init__(self, registry_path: Optional[str] = None):
        env_path = os.getenv('SHANNON_AGENT_REGISTRY_PATH')
        self.registry_path = Path(registry_path or env_path or 'config/shannon/agent_registry.yaml')
        self._agents: List[AgentChannelRegistration] = []
        self.reload()

    def reload(self) -> None:
        if not self.registry_path.exists():
            raise FileNotFoundError(
                f'Shannon agent registry not found: {self.registry_path}'
            )

        payload = yaml.safe_load(self.registry_path.read_text(encoding='utf-8')) or {}
        agents = payload.get('agents') or []
        self._agents = [AgentChannelRegistration.from_dict(item) for item in agents]

        # Allow environment variables to override api_base_url per agent.
        # Pattern: {AGENT_ID}_API_URL  (e.g. DRUCKER_API_URL=http://cn-ai-03:8201)
        # This enables multi-host deployment without editing the YAML.
        for agent in self._agents:
            env_key = f'{agent.agent_id.upper()}_API_URL'
            env_val = os.environ.get(env_key, '').strip()
            if env_val:
                log.info(
                    f'Registry override: {agent.agent_id} api_base_url '
                    f'{agent.api_base_url!r} -> {env_val!r} (from {env_key})'
                )
                agent.api_base_url = env_val

        log.info(
            f'Loaded Shannon agent registry from {self.registry_path} '
            f'with {len(self._agents)} entries'
        )

    def list_agents(self) -> List[AgentChannelRegistration]:
        return list(self._agents)

    def get_agent(self, agent_id: str) -> Optional[AgentChannelRegistration]:
        agent_id = str(agent_id or '').strip().lower()
        if not agent_id:
            return None

        for item in self._agents:
            if item.agent_id.lower() == agent_id:
                return item
        return None

    def resolve_channel(
        self,
        channel_id: Optional[str] = None,
        team_id: Optional[str] = None,
        channel_name: Optional[str] = None,
    ) -> Optional[AgentChannelRegistration]:
        channel_id = str(channel_id or '').strip()
        team_id = str(team_id or '').strip()
        channel_name = str(channel_name or '').strip().lower()

        for item in self._agents:
            if channel_id and item.channel_id and item.channel_id == channel_id:
                if not team_id or not item.team_id or item.team_id == team_id:
                    return item

        for item in self._agents:
            if channel_name and item.channel_name and item.channel_name.lower() == channel_name:
                if not team_id or not item.team_id or item.team_id == team_id:
                    return item

        return None

    def to_dict(self) -> Dict[str, object]:
        return {
            'registry_path': str(self.registry_path),
            'agents': [item.to_dict() for item in self._agents],
        }
