##########################################################################################
#
# Module: shannon/service.py
#
# Description: Core Shannon service logic for Teams command handling and
#              notification posting.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, List, Optional

import requests

from shannon.cards import (
    build_bug_activity_card,
    build_drucker_hygiene_card,
    build_drucker_summary_card,
    build_fact_card,
    build_gantt_release_monitor_card,
    build_gantt_snapshot_card,
)
from shannon.models import AuditRecord, ConversationReference, ShannonResponse, normalize_command_text
from shannon.poster import BasePoster, build_poster_from_env
from shannon.registry import ShannonAgentRegistry
from state.shannon_state_store import ShannonStateStore

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class ShannonService:
    '''
    Shannon command router and Teams notification service.
    '''

    def __init__(
        self,
        registry: Optional[ShannonAgentRegistry] = None,
        state_store: Optional[ShannonStateStore] = None,
        poster: Optional[BasePoster] = None,
        bot_name: Optional[str] = None,
        send_welcome_on_install: Optional[bool] = None,
    ):
        self.registry = registry or ShannonAgentRegistry()
        self.state_store = state_store or ShannonStateStore()
        self.poster = poster or build_poster_from_env()
        self.bot_name = str(bot_name or os.getenv('SHANNON_TEAMS_BOT_NAME', 'Shannon')).strip()
        if send_welcome_on_install is None:
            send_welcome_on_install = (
                str(os.getenv('SHANNON_SEND_WELCOME_ON_INSTALL', 'true')).strip().lower() == 'true'
            )
        self.send_welcome_on_install = bool(send_welcome_on_install)

    def get_health(self) -> Dict[str, Any]:
        stats = self.state_store.compute_stats()
        return {
            'service': 'shannon',
            'ok': True,
            'bot_name': self.bot_name,
            'registry_path': str(self.registry.registry_path),
            'registry_count': len(self.registry.list_agents()),
            'poster_mode': self.poster.__class__.__name__,
            'stats': stats,
        }

    def get_stats(self) -> Dict[str, Any]:
        stats = self.state_store.compute_stats()
        stats.update({
            'poster_mode': self.poster.__class__.__name__,
            'registry_count': len(self.registry.list_agents()),
        })
        return stats

    def get_load(self) -> Dict[str, Any]:
        stats = self.state_store.compute_stats()
        recent = int(stats.get('messages_last_hour') or 0)
        if recent == 0:
            state = 'idle'
        elif recent <= 5:
            state = 'working'
        elif recent <= 20:
            state = 'busy'
        else:
            state = 'overloaded'

        return {
            'state': state,
            'messages_last_hour': recent,
            'active_conversations': stats.get('conversation_reference_count', 0),
            'pending_approvals': 0,
            'rate_limit_headroom': 'unbounded-v1',
        }

    def get_work_summary(self) -> Dict[str, Any]:
        stats = self.state_store.compute_stats()
        return {
            'messages_received_today': stats.get('messages_today', 0),
            'commands_handled_today': stats.get('commands_today', 0),
            'notifications_posted_today': stats.get('notifications_today', 0),
            'errors_today': stats.get('errors_today', 0),
            'last_activity_at': stats.get('last_activity_at', ''),
        }

    def get_token_status(self) -> Dict[str, Any]:
        return {
            'deterministic_actions': 'v1-default',
            'llm_enabled': False,
            'token_usage_today': 0,
            'token_usage_cumulative': 0,
            'notes': 'Shannon v1 command parsing and routing are deterministic.',
        }

    def get_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        decisions = self.state_store.list_audit_records(limit=limit, event_type='decision')
        return [item.to_dict() for item in decisions]

    def get_decision(self, record_id: str) -> Optional[Dict[str, Any]]:
        record = self.state_store.get_audit_record(record_id)
        return record.to_dict() if record else None

    def _record(
        self,
        event_type: str,
        *,
        status: str = 'ok',
        agent_id: str = 'shannon',
        reference: Optional[ConversationReference] = None,
        command: str = '',
        decision: str = '',
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        record = AuditRecord(
            event_type=event_type,
            status=status,
            agent_id=agent_id,
            channel_id=reference.channel_id if reference else '',
            conversation_id=reference.conversation_id if reference else '',
            team_id=reference.team_id if reference else '',
            user_id=reference.user_id if reference else '',
            user_name=reference.user_name if reference else '',
            command=command,
            decision=decision,
            details=details or {},
        )
        self.state_store.append_audit_record(record)
        return record

    def _build_status_response(self) -> ShannonResponse:
        stats = self.get_stats()
        card = build_fact_card(
            title='Shannon Status',
            subtitle='Communications service health and throughput',
            facts={
                'Messages today': stats.get('messages_today', 0),
                'Commands today': stats.get('commands_today', 0),
                'Notifications today': stats.get('notifications_today', 0),
                'Errors today': stats.get('errors_today', 0),
                'Poster mode': stats.get('poster_mode', ''),
            },
            body_lines=[
                f'Registry entries: {stats.get("registry_count", 0)}',
                f'Last activity: {stats.get("last_activity_at", "n/a")}',
            ],
        )
        return ShannonResponse(
            text=(
                'Shannon is online. '
                f'Messages today: {stats.get("messages_today", 0)}, '
                f'commands today: {stats.get("commands_today", 0)}, '
                f'errors today: {stats.get("errors_today", 0)}.'
            ),
            card=card,
            command='/stats',
            decision='reported_service_stats',
        )

    def _build_load_response(self) -> ShannonResponse:
        load = self.get_load()
        card = build_fact_card(
            title='Shannon Load',
            subtitle='Current queue and conversation posture',
            facts={
                'State': load.get('state'),
                'Messages last hour': load.get('messages_last_hour'),
                'Active conversations': load.get('active_conversations'),
                'Pending approvals': load.get('pending_approvals'),
            },
        )
        return ShannonResponse(
            text=(
                f'Shannon load is {load.get("state")}. '
                f'{load.get("messages_last_hour")} message(s) in the last hour.'
            ),
            card=card,
            command='/busy',
            decision='reported_service_load',
        )

    def _build_work_summary_response(self) -> ShannonResponse:
        summary = self.get_work_summary()
        card = build_fact_card(
            title='Shannon Work Today',
            subtitle='Today’s routing and notification summary',
            facts={
                'Messages received': summary.get('messages_received_today'),
                'Commands handled': summary.get('commands_handled_today'),
                'Notifications posted': summary.get('notifications_posted_today'),
                'Errors': summary.get('errors_today'),
            },
            body_lines=[f'Last activity: {summary.get("last_activity_at", "n/a")}'],
        )
        return ShannonResponse(
            text=(
                f'Today Shannon handled {summary.get("commands_handled_today", 0)} command(s) '
                f'and posted {summary.get("notifications_posted_today", 0)} notification(s).'
            ),
            card=card,
            command='/work-today',
            decision='reported_work_summary',
        )

    def _build_token_status_response(self) -> ShannonResponse:
        tokens = self.get_token_status()
        card = build_fact_card(
            title='Shannon Token Status',
            subtitle='Deterministic-first execution summary',
            facts={
                'LLM enabled': tokens.get('llm_enabled'),
                'Token usage today': tokens.get('token_usage_today'),
                'Token usage cumulative': tokens.get('token_usage_cumulative'),
            },
            body_lines=[str(tokens.get('notes') or '')],
        )
        return ShannonResponse(
            text='Shannon v1 is running deterministically with zero token usage.',
            card=card,
            command='/token-status',
            decision='reported_token_status',
        )

    def _build_decision_tree_response(self) -> ShannonResponse:
        decisions = self.get_decisions(limit=5)
        if not decisions:
            lines = ['No recorded decisions yet.']
        else:
            lines = [
                f'{item["record_id"]}: {item.get("decision") or item.get("event_type")} '
                f'[{item.get("status", "ok")}]'
                for item in decisions
            ]

        card = build_fact_card(
            title='Shannon Decision Tree',
            subtitle='Most recent routing and posting decisions',
            body_lines=lines,
        )
        return ShannonResponse(
            text='Recent Shannon decisions:\n' + '\n'.join(lines),
            card=card,
            command='/decision-tree',
            decision='reported_recent_decisions',
        )

    def _build_why_response(self, record_id: str) -> ShannonResponse:
        record = self.get_decision(record_id)
        if not record:
            return ShannonResponse(
                text=f'No Shannon decision found with id {record_id}.',
                command='/why',
                decision='decision_not_found',
            )

        card = build_fact_card(
            title=f'Why {record_id}',
            subtitle=str(record.get('decision') or record.get('event_type') or 'decision'),
            facts={
                'Status': record.get('status'),
                'Agent': record.get('agent_id'),
                'Command': record.get('command'),
                'When': record.get('timestamp'),
            },
            body_lines=[
                f'Details: {record.get("details") or {}}',
            ],
        )
        return ShannonResponse(
            text=(
                f'{record_id}: {record.get("decision") or record.get("event_type")} '
                f'[{record.get("status", "ok")}]'
            ),
            card=card,
            command='/why',
            decision='reported_specific_decision',
            metadata={'record_id': record_id},
        )

    def _build_help_response(self) -> ShannonResponse:
        lines = [
            '/stats',
            '/busy',
            '/work-today',
            '/token-status',
            '/decision-tree',
            '/why <record-id>',
            '/help',
        ]
        card = build_fact_card(
            title='Shannon Commands',
            subtitle='Available v1 commands in #agent-shannon',
            body_lines=lines,
        )
        return ShannonResponse(
            text='Available Shannon commands:\n' + '\n'.join(lines),
            card=card,
            command='/help',
            decision='reported_help',
        )

    def _handle_shannon_command(self, command_text: str) -> ShannonResponse:
        normalized = normalize_command_text(command_text)
        parts = normalized.split()
        command = parts[0].lower() if parts else '/help'

        if command == '/stats':
            return self._build_status_response()
        if command == '/busy':
            return self._build_load_response()
        if command == '/work-today':
            return self._build_work_summary_response()
        if command == '/token-status':
            return self._build_token_status_response()
        if command == '/decision-tree':
            return self._build_decision_tree_response()
        if command == '/why':
            if len(parts) < 2:
                return ShannonResponse(
                    text='Usage: /why <record-id>',
                    command='/why',
                    decision='missing_decision_id',
                )
            return self._build_why_response(parts[1])
        if command in ('/help', 'help'):
            return self._build_help_response()

        return ShannonResponse(
            text=(
                f'Unknown Shannon command: {command}. '
                'Try /help for the current command list.'
            ),
            command=command,
            decision='unknown_command',
        )

    STANDARD_COMMAND_ROUTES = {
        '/stats': ('GET', '/v1/status/stats'),
        '/busy': ('GET', '/v1/status/load'),
        '/work-today': ('GET', '/v1/status/work-summary'),
        '/token-status': ('GET', '/v1/status/tokens'),
        '/decision-tree': ('GET', '/v1/status/decisions'),
    }

    def _call_agent_api(
        self,
        registration: Any,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f'{registration.api_base_url.rstrip("/")}{path}'
        timeout = getattr(registration, 'timeout_seconds', 30) or 30
        try:
            resp = requests.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_body,
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.Timeout:
            return {'ok': False, 'error': f'{registration.agent_id} timed out after {timeout}s'}
        except requests.ConnectionError:
            return {'ok': False, 'error': f'{registration.agent_id} is not reachable at {registration.api_base_url}'}
        except requests.HTTPError as e:
            return {'ok': False, 'error': f'{registration.agent_id} returned {e.response.status_code}'}
        except Exception as e:
            return {'ok': False, 'error': f'{registration.agent_id} error: {e}'}

    AGENT_CARD_BUILDERS = {
        'drucker': {
            '/issue-check': build_drucker_hygiene_card,
            '/intake-report': build_drucker_hygiene_card,
            '/hygiene-run': build_drucker_hygiene_card,
            '/hygiene-report': build_drucker_hygiene_card,
            '/bug-activity': build_bug_activity_card,
        },
        'gantt': {
            '/planning-snapshot': build_gantt_snapshot_card,
            '/release-monitor': build_gantt_release_monitor_card,
            '/release-report': build_gantt_release_monitor_card,
        },
    }

    def _agent_response_to_shannon(
        self,
        agent_id: str,
        command: str,
        result: Dict[str, Any],
    ) -> ShannonResponse:
        if not result.get('ok', False):
            return ShannonResponse(
                text=f'{agent_id}: {result.get("error", "unknown error")}',
                command=command,
                decision='agent_call_failed',
            )

        data = result.get('data', result)

        card_builder = self.AGENT_CARD_BUILDERS.get(agent_id, {}).get(command)
        if card_builder and isinstance(data, dict):
            if agent_id == 'drucker':
                report = data.get('report', data)
                card = card_builder(report)
                if command == '/bug-activity':
                    summary = report.get('summary', {})
                    return ShannonResponse(
                        text=(
                            f'{report.get("project", "")}: '
                            f'{summary.get("bugs_opened", 0)} opened, '
                            f'{summary.get("status_transitions", 0)} status changes, '
                            f'{summary.get("bugs_with_comments", 0)} commented'
                        ),
                        card=card,
                        command=command,
                        decision='agent_call_success',
                    )
                summary = report.get('summary', {})
                total = summary.get(
                    'finding_count',
                    summary.get('total_findings', len(report.get('findings', []))),
                )
                actions = summary.get(
                    'action_count',
                    len(report.get('proposed_actions', [])),
                )
                return ShannonResponse(
                    text=f'{report.get("project_key", "")}: {total} findings, {actions} proposed actions',
                    card=card,
                    command=command,
                    decision='agent_call_success',
                )

            card = card_builder(data)
            if agent_id == 'gantt' and command == '/planning-snapshot':
                snapshot = data.get('snapshot', {})
                overview = snapshot.get('backlog_overview', {})
                return ShannonResponse(
                    text=(
                        f'{snapshot.get("project_key", "")}: '
                        f'{overview.get("total_issues", 0)} issues, '
                        f'{overview.get("blocked_issues", 0)} blocked, '
                        f'{len(snapshot.get("milestones", []))} milestones'
                    ),
                    card=card,
                    command=command,
                    decision='agent_call_success',
                )

            if agent_id == 'gantt' and command in ('/release-monitor', '/release-report'):
                report = data.get('report', {})
                return ShannonResponse(
                    text=(
                        f'{report.get("project_key", "")}: '
                        f'{report.get("total_bugs", 0)} bugs, '
                        f'P0={report.get("total_p0", 0)}, '
                        f'P1={report.get("total_p1", 0)}'
                    ),
                    card=card,
                    command=command,
                    decision='agent_call_success',
                )

        if agent_id == 'drucker' and command == '/stats' and isinstance(data, dict):
            card = build_drucker_summary_card(data)
            return ShannonResponse(
                text=f'Reports: {data.get("reports_generated", 0)}, Findings: {data.get("total_findings", 0)}',
                card=card,
                command=command,
                decision='agent_call_success',
            )

        if isinstance(data, list):
            lines = [str(item) for item in data[:10]]
            if len(data) > 10:
                lines.append(f'...and {len(data) - 10} more')
            card = build_fact_card(
                title=f'{agent_id.title()} — {command}',
                body_lines=lines or ['No data returned.'],
            )
            return ShannonResponse(
                text='\n'.join(lines) if lines else 'No data.',
                card=card,
                command=command,
                decision='agent_call_success',
            )

        if isinstance(data, dict):
            facts = {
                str(k): str(v)
                for k, v in data.items()
                if not isinstance(v, (dict, list)) and v is not None
            }
            nested_lines = []
            for k, v in data.items():
                if isinstance(v, dict):
                    nested_lines.append(f'{k}: {len(v)} entries')
                elif isinstance(v, list):
                    nested_lines.append(f'{k}: {len(v)} items')

            card = build_fact_card(
                title=f'{agent_id.title()} — {command}',
                facts=facts or None,
                body_lines=nested_lines or None,
            )
            text_parts = [f'{k}: {v}' for k, v in facts.items()]
            return ShannonResponse(
                text=', '.join(text_parts) if text_parts else str(data),
                card=card,
                command=command,
                decision='agent_call_success',
            )

        return ShannonResponse(
            text=str(data),
            command=command,
            decision='agent_call_success',
        )

    def _handle_registered_agent_command(
        self,
        agent_id: str,
        command_text: str,
    ) -> ShannonResponse:
        registration = self.registry.get_agent(agent_id)
        if not registration or not getattr(registration, 'api_base_url', ''):
            return ShannonResponse(
                text=f'{agent_id} is registered but has no API endpoint configured.',
                command=command_text.split()[0] if command_text else '',
                decision='agent_no_api_base_url',
            )

        normalized = normalize_command_text(command_text)
        parts = normalized.split()
        command = parts[0].lower() if parts else '/help'

        if command == '/help':
            lines = list(self.STANDARD_COMMAND_ROUTES.keys())
            custom_commands = getattr(registration, 'custom_commands', []) or []
            for cc in custom_commands:
                desc = cc.get('description', '')
                lines.append(f'{cc["command"]}: {desc}' if desc else cc['command'])
            card = build_fact_card(
                title=f'{registration.display_name} Commands',
                subtitle=f'Available commands for {agent_id}',
                body_lines=lines,
            )
            return ShannonResponse(
                text=f'Commands for {agent_id}:\n' + '\n'.join(lines),
                card=card,
                command='/help',
                decision='reported_agent_help',
            )

        if command == '/why' and len(parts) >= 2:
            result = self._call_agent_api(
                registration, 'GET', f'/v1/status/decisions/{parts[1]}',
            )
            return self._agent_response_to_shannon(agent_id, command, result)

        if command in self.STANDARD_COMMAND_ROUTES:
            method, path = self.STANDARD_COMMAND_ROUTES[command]
            result = self._call_agent_api(registration, method, path)
            return self._agent_response_to_shannon(agent_id, command, result)

        custom_commands = getattr(registration, 'custom_commands', []) or []
        for cc in custom_commands:
            if cc.get('command', '').lower() == command:
                method = cc.get('api_method', 'GET')
                path = cc.get('api_path', '')
                json_body = None
                params = None
                args = parts[1:] if len(parts) > 1 else []
                if method.upper() == 'POST':
                    json_body = {
                        args[i]: args[i + 1]
                        for i in range(0, len(args) - 1, 2)
                    } if args else {}
                elif args:
                    # Append first arg as path segment (e.g. /hygiene-report <id>)
                    # and pass remaining as query params
                    path = f'{path.rstrip("/")}/{args[0]}'
                    if len(args) > 1:
                        params = {'args': ' '.join(args[1:])}
                result = self._call_agent_api(
                    registration, method, path, params=params, json_body=json_body,
                )
                return self._agent_response_to_shannon(agent_id, command, result)

        return ShannonResponse(
            text=f'Unknown {agent_id} command: {command}. Try /help.',
            command=command,
            decision='unknown_agent_command',
        )

    def _resolve_activity_agent(self, activity: Dict[str, Any]) -> str:
        channel_data = activity.get('channelData') or {}
        channel = channel_data.get('channel') or {}
        team = channel_data.get('team') or {}
        registration = self.registry.resolve_channel(
            channel_id=str(channel.get('id') or '').strip(),
            team_id=str(team.get('id') or '').strip(),
            channel_name=str(channel.get('name') or '').strip(),
        ) or self.registry.get_agent('shannon')
        return registration.agent_id if registration else 'shannon'

    def _build_command_response(
        self,
        activity: Dict[str, Any],
    ) -> tuple[ConversationReference, ShannonResponse]:
        agent_id = self._resolve_activity_agent(activity)
        reference = ConversationReference.from_activity(activity, agent_id=agent_id)
        raw_text = str(activity.get('text') or '').strip()
        command_text = normalize_command_text(raw_text)
        if not command_text:
            command_text = '/help'

        if agent_id == 'shannon':
            response = self._handle_shannon_command(command_text)
        else:
            response = self._handle_registered_agent_command(agent_id, command_text)

        return reference, response

    def _post_response(
        self,
        reference: ConversationReference,
        response: ShannonResponse,
        *,
        reply: bool,
    ) -> Dict[str, Any]:
        activity = response.to_message_activity()
        if reply and reference.reply_to_id:
            return self.poster.reply_to_activity(reference, reference.reply_to_id, activity)
        return self.poster.send_to_conversation(reference, activity)

    def process_teams_activity(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        '''
        Process a Teams activity and return a structured result for the webhook.
        '''
        raw_type = str(activity.get('type') or '').strip()
        agent_id = self._resolve_activity_agent(activity)
        reference = ConversationReference.from_activity(activity, agent_id=agent_id)
        self.state_store.save_conversation_reference(reference)
        self._record(
            'activity_received',
            reference=reference,
            agent_id=agent_id,
            details={'activity_type': raw_type},
        )

        if raw_type == 'conversationUpdate':
            result: Dict[str, Any] = {
                'ok': True,
                'activity_type': raw_type,
                'stored_reference': True,
                'agent_id': agent_id,
            }
            if self.send_welcome_on_install:
                welcome = ShannonResponse(
                    text=(
                        f'{self.bot_name} is online in this channel. '
                        f'Try @${self.bot_name} /stats or @${self.bot_name} /help.'
                    ).replace('@$', '@'),
                    card=build_fact_card(
                        title='Shannon Connected',
                        subtitle='Teams bot service is ready',
                        body_lines=[
                            f'Channel mapped to agent: {agent_id}',
                            'Try /stats or /help to verify the bot is reachable.',
                        ],
                    ),
                    decision='posted_install_welcome',
                )
                post_result = self._post_response(reference, welcome, reply=False)
                self._record(
                    'notification_posted',
                    reference=reference,
                    agent_id=agent_id,
                    decision='posted_install_welcome',
                    details=post_result,
                )
                result['post_result'] = post_result
            return result

        if raw_type != 'message':
            return {
                'ok': True,
                'activity_type': raw_type,
                'stored_reference': True,
                'ignored': True,
            }

        reference, response = self._build_command_response(activity)

        decision_record = self._record(
            'decision',
            reference=reference,
            agent_id=agent_id,
            command=response.command or '/help',
            decision=response.decision,
            details={'input': normalize_command_text(str(activity.get('text') or ''))},
        )
        post_result = self._post_response(reference, response, reply=True)
        self._record(
            'notification_posted',
            reference=reference,
            agent_id=agent_id,
            command=response.command,
            decision=response.decision,
            details=post_result,
        )
        return {
            'ok': True,
            'activity_type': raw_type,
            'agent_id': agent_id,
            'command': response.command,
            'decision': response.decision,
            'reply_preview': response.text,
            'decision_id': decision_record.record_id,
            'post_result': post_result,
        }

    def process_outgoing_webhook_activity(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        '''
        Process a Teams Outgoing Webhook activity and return the synchronous
        response body expected by Teams.
        '''
        raw_type = str(activity.get('type') or '').strip()
        agent_id = self._resolve_activity_agent(activity)
        reference = ConversationReference.from_activity(activity, agent_id=agent_id)
        self.state_store.save_conversation_reference(reference)
        self._record(
            'activity_received',
            reference=reference,
            agent_id=agent_id,
            details={'activity_type': raw_type, 'transport': 'outgoing_webhook'},
        )

        if raw_type != 'message':
            response = ShannonResponse(
                text='Shannon only handles message activities through the outgoing webhook.',
                decision='ignored_non_message_outgoing_webhook_activity',
            )
        else:
            reference, response = self._build_command_response(activity)

        self._record(
            'decision',
            reference=reference,
            agent_id=agent_id,
            command=response.command or '/help',
            decision=response.decision,
            details={
                'input': normalize_command_text(str(activity.get('text') or '')),
                'transport': 'outgoing_webhook',
            },
        )
        return response.to_outgoing_webhook_response()

    def post_notification(
        self,
        *,
        agent_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        title: str,
        text: str,
        body_lines: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        '''
        Post a notification to a registered channel using a stored conversation reference.
        '''
        registration = None
        if channel_id:
            registration = self.registry.resolve_channel(channel_id=channel_id)
        if registration is None and agent_id:
            registration = self.registry.get_agent(agent_id)
        if registration is None:
            raise ValueError('Unknown Shannon agent/channel target')

        reference = self.state_store.get_conversation_reference(
            agent_id=registration.agent_id,
            channel_id=registration.channel_id or channel_id or '',
        )
        if reference is None:
            raise ValueError(
                'No stored conversation reference for this channel yet. '
                'Install the bot in the team and send a first message or wait for a '
                'conversationUpdate event.'
            )

        response = ShannonResponse(
            text=text,
            card=build_fact_card(
                title=title,
                subtitle=f'Notification for {registration.display_name}',
                body_lines=body_lines or [text],
            ),
            decision='posted_agent_notification',
        )
        post_result = self._post_response(reference, response, reply=False)
        self._record(
            'notification_posted',
            reference=reference,
            agent_id=registration.agent_id,
            decision='posted_agent_notification',
            details=post_result,
        )
        return {
            'ok': True,
            'agent_id': registration.agent_id,
            'channel_id': reference.channel_id,
            'post_result': post_result,
        }
