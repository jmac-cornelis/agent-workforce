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

import asyncio
import json
import logging
import os
import sys
import uuid

from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentConfig, AgentResponse
from agents.shannon.cards import (
    activity_card, decision_card, alert_card,
)
from agents.shannon.graph_client import TeamsGraphClient, GraphAPIError
from agents.shannon.registry import ChannelRegistry
from tools.base import ToolDefinition, ToolParameter, ToolResult

log = logging.getLogger(os.path.basename(sys.argv[0]))

_PROMPT_DIR = Path(__file__).parent / 'prompts'


def _run_async(coro):
    """Run an async coroutine from synchronous context.

    BaseAgent.execute_tool is synchronous, so tool functions that call the
    async Graph client need this bridge. Uses the running loop if available,
    otherwise creates a new one.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


class ShannonAgent(BaseAgent):
    """Communications agent — single Teams bot for all agent channels.

    Provides tools for posting messages, Adaptive Cards, activity
    notifications, decision records, and alerts to Microsoft Teams
    via the Graph API.
    """

    def __init__(self, config_path: Optional[str] = None, **kwargs):
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

        self._graph = TeamsGraphClient()
        self._registry = ChannelRegistry(config_path)

        self._register_shannon_tools()

    @staticmethod
    def _load_system_prompt() -> str:
        prompt_path = _PROMPT_DIR / 'system.md'
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        log.warning(f'Shannon system prompt not found: {prompt_path}')
        return 'You are Shannon, the Communications agent for Cornelis Networks.'

    def run(self, input_data: Any) -> AgentResponse:
        return self._run_with_tools(str(input_data))

    # ------------------------------------------------------------------
    # Tool registration
    # ------------------------------------------------------------------

    def _register_shannon_tools(self) -> None:
        for tool_def in self._build_tool_definitions():
            self.register_tool(tool_def)

    def _build_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name='post_message',
                description='Post a plain-text or HTML message to a Teams channel.',
                parameters=[
                    ToolParameter(name='channel_name', type='string',
                                  description='Logical channel name from registry'),
                    ToolParameter(name='text', type='string',
                                  description='Message content (HTML supported)'),
                ],
                returns='Message delivery status with message ID',
                func=self._tool_post_message,
            ),
            ToolDefinition(
                name='post_card',
                description='Post an Adaptive Card JSON payload to a Teams channel.',
                parameters=[
                    ToolParameter(name='channel_name', type='string',
                                  description='Logical channel name from registry'),
                    ToolParameter(name='card_json', type='string',
                                  description='Adaptive Card JSON as a string'),
                ],
                returns='Card delivery status with message ID',
                func=self._tool_post_card,
            ),
            ToolDefinition(
                name='post_activity',
                description='Post a formatted activity notification card to a Teams channel.',
                parameters=[
                    ToolParameter(name='channel_name', type='string',
                                  description='Logical channel name from registry'),
                    ToolParameter(name='agent_id', type='string',
                                  description='Agent that performed the action'),
                    ToolParameter(name='action', type='string',
                                  description='Description of the action taken'),
                    ToolParameter(name='details', type='string',
                                  description='JSON string of additional details',
                                  required=False, default='{}'),
                ],
                returns='Activity card delivery status',
                func=self._tool_post_activity,
            ),
            ToolDefinition(
                name='post_decision',
                description='Post a decision notification card showing rationale.',
                parameters=[
                    ToolParameter(name='channel_name', type='string',
                                  description='Logical channel name from registry'),
                    ToolParameter(name='agent_id', type='string',
                                  description='Agent that made the decision'),
                    ToolParameter(name='decision_type', type='string',
                                  description='Type of decision made'),
                    ToolParameter(name='selected', type='string',
                                  description='The selected option'),
                    ToolParameter(name='rationale', type='string',
                                  description='Reasoning behind the decision'),
                ],
                returns='Decision card delivery status',
                func=self._tool_post_decision,
            ),
            ToolDefinition(
                name='post_alert',
                description='Post an error/alert notification card to a Teams channel.',
                parameters=[
                    ToolParameter(name='channel_name', type='string',
                                  description='Logical channel name from registry'),
                    ToolParameter(name='agent_id', type='string',
                                  description='Agent raising the alert'),
                    ToolParameter(name='severity', type='string',
                                  description='Alert severity: critical, high, medium, low'),
                    ToolParameter(name='message', type='string',
                                  description='Alert message'),
                    ToolParameter(name='details', type='string',
                                  description='JSON string of additional details',
                                  required=False, default='{}'),
                ],
                returns='Alert card delivery status',
                func=self._tool_post_alert,
            ),
            ToolDefinition(
                name='get_channels',
                description='List all configured and enabled Teams channels.',
                parameters=[],
                returns='List of channel names and their configuration',
                func=self._tool_get_channels,
            ),
        ]

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def _tool_post_message(self, channel_name: str, text: str) -> ToolResult:
        try:
            mapping = self._registry.resolve_or_raise(channel_name)
        except KeyError as e:
            return ToolResult.failure(str(e))

        try:
            result = _run_async(
                self._graph.send_message(
                    team_id=mapping.team_id,
                    channel_id=mapping.channel_id,
                    content=text,
                    content_type='html',
                )
            )
            return ToolResult.success({
                'status': 'sent',
                'channel': channel_name,
                'message_id': result.get('id', 'unknown'),
            })
        except GraphAPIError as e:
            log.error(f'post_message failed for {channel_name}: {e}')
            return ToolResult.failure(f'Graph API error: {e}')
        except Exception as e:
            log.error(f'post_message unexpected error: {e}')
            return ToolResult.failure(str(e))

    def _tool_post_card(self, channel_name: str, card_json: str) -> ToolResult:
        try:
            mapping = self._registry.resolve_or_raise(channel_name)
        except KeyError as e:
            return ToolResult.failure(str(e))

        try:
            card = json.loads(card_json)
        except json.JSONDecodeError as e:
            return ToolResult.failure(f'Invalid card JSON: {e}')

        try:
            result = _run_async(
                self._graph.send_adaptive_card(
                    team_id=mapping.team_id,
                    channel_id=mapping.channel_id,
                    card=card,
                )
            )
            return ToolResult.success({
                'status': 'sent',
                'channel': channel_name,
                'message_id': result.get('id', 'unknown'),
            })
        except GraphAPIError as e:
            log.error(f'post_card failed for {channel_name}: {e}')
            return ToolResult.failure(f'Graph API error: {e}')
        except Exception as e:
            log.error(f'post_card unexpected error: {e}')
            return ToolResult.failure(str(e))

    def _tool_post_activity(
        self, channel_name: str, agent_id: str, action: str,
        details: str = '{}',
    ) -> ToolResult:
        try:
            mapping = self._registry.resolve_or_raise(channel_name)
        except KeyError as e:
            return ToolResult.failure(str(e))

        try:
            details_dict = json.loads(details) if details else {}
        except json.JSONDecodeError:
            details_dict = {'raw': details}

        card = activity_card(
            agent_id=agent_id,
            action=action,
            details=details_dict or None,
        )

        try:
            result = _run_async(
                self._graph.send_adaptive_card(
                    team_id=mapping.team_id,
                    channel_id=mapping.channel_id,
                    card=card,
                    summary=f'{agent_id}: {action}',
                )
            )
            return ToolResult.success({
                'status': 'sent',
                'channel': channel_name,
                'card_type': 'activity',
                'message_id': result.get('id', 'unknown'),
            })
        except GraphAPIError as e:
            log.error(f'post_activity failed for {channel_name}: {e}')
            return ToolResult.failure(f'Graph API error: {e}')
        except Exception as e:
            log.error(f'post_activity unexpected error: {e}')
            return ToolResult.failure(str(e))

    def _tool_post_decision(
        self, channel_name: str, agent_id: str, decision_type: str,
        selected: str, rationale: str,
    ) -> ToolResult:
        try:
            mapping = self._registry.resolve_or_raise(channel_name)
        except KeyError as e:
            return ToolResult.failure(str(e))

        decision_id = str(uuid.uuid4())[:8]
        card = decision_card(
            agent_id=agent_id,
            decision_type=decision_type,
            selected=selected,
            rationale=rationale,
            decision_id=decision_id,
        )

        try:
            result = _run_async(
                self._graph.send_adaptive_card(
                    team_id=mapping.team_id,
                    channel_id=mapping.channel_id,
                    card=card,
                    summary=f'{agent_id} decision: {decision_type}',
                )
            )
            return ToolResult.success({
                'status': 'sent',
                'channel': channel_name,
                'card_type': 'decision',
                'decision_id': decision_id,
                'message_id': result.get('id', 'unknown'),
            })
        except GraphAPIError as e:
            log.error(f'post_decision failed for {channel_name}: {e}')
            return ToolResult.failure(f'Graph API error: {e}')
        except Exception as e:
            log.error(f'post_decision unexpected error: {e}')
            return ToolResult.failure(str(e))

    def _tool_post_alert(
        self, channel_name: str, agent_id: str, severity: str,
        message: str, details: str = '{}',
    ) -> ToolResult:
        try:
            mapping = self._registry.resolve_or_raise(channel_name)
        except KeyError as e:
            return ToolResult.failure(str(e))

        try:
            details_dict = json.loads(details) if details else {}
        except json.JSONDecodeError:
            details_dict = {'raw': details}

        card = alert_card(
            agent_id=agent_id,
            severity=severity,
            message=message,
            details=details_dict or None,
        )

        try:
            result = _run_async(
                self._graph.send_adaptive_card(
                    team_id=mapping.team_id,
                    channel_id=mapping.channel_id,
                    card=card,
                    summary=f'[{severity.upper()}] {agent_id}: {message[:80]}',
                )
            )
            return ToolResult.success({
                'status': 'sent',
                'channel': channel_name,
                'card_type': 'alert',
                'severity': severity,
                'message_id': result.get('id', 'unknown'),
            })
        except GraphAPIError as e:
            log.error(f'post_alert failed for {channel_name}: {e}')
            return ToolResult.failure(f'Graph API error: {e}')
        except Exception as e:
            log.error(f'post_alert unexpected error: {e}')
            return ToolResult.failure(str(e))

    def _tool_get_channels(self) -> ToolResult:
        channel_list = []
        for mapping in self._registry.list_channels():
            channel_list.append({
                'name': mapping.name,
                'display_name': mapping.channel_display_name,
                'team_id': mapping.team_id,
                'channel_id': mapping.channel_id,
                'enabled': mapping.enabled,
            })
        return ToolResult.success({
            'channels': channel_list,
            'count': len(channel_list),
        })

    # ------------------------------------------------------------------
    # Direct API (non-tool) for programmatic use by other agents
    # ------------------------------------------------------------------

    async def async_post_message(self, channel_name: str, text: str) -> Dict[str, Any]:
        mapping = self._registry.resolve_or_raise(channel_name)
        return await self._graph.send_message(
            team_id=mapping.team_id,
            channel_id=mapping.channel_id,
            content=text,
        )

    async def async_post_card(self, channel_name: str,
                              card: Dict[str, Any]) -> Dict[str, Any]:
        mapping = self._registry.resolve_or_raise(channel_name)
        return await self._graph.send_adaptive_card(
            team_id=mapping.team_id,
            channel_id=mapping.channel_id,
            card=card,
        )

    async def async_post_activity(self, channel_name: str, agent_id: str,
                                  action: str,
                                  details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        mapping = self._registry.resolve_or_raise(channel_name)
        card = activity_card(agent_id=agent_id, action=action, details=details)
        return await self._graph.send_adaptive_card(
            team_id=mapping.team_id,
            channel_id=mapping.channel_id,
            card=card,
            summary=f'{agent_id}: {action}',
        )

    async def async_post_alert(self, channel_name: str, agent_id: str,
                               severity: str, message: str,
                               details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        mapping = self._registry.resolve_or_raise(channel_name)
        card = alert_card(
            agent_id=agent_id, severity=severity,
            message=message, details=details,
        )
        return await self._graph.send_adaptive_card(
            team_id=mapping.team_id,
            channel_id=mapping.channel_id,
            card=card,
            summary=f'[{severity.upper()}] {agent_id}: {message[:80]}',
        )

    async def close(self) -> None:
        await self._graph.close()
