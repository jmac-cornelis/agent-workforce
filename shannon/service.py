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
import re as re_mod
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from shannon.notification_router import NotificationRouter, send_notification

from agents.rename_registry import agent_display_name, canonical_agent_name
from shannon.cards import (
    build_bug_activity_card,
    build_ci_failures_card,
    build_drucker_hygiene_card,
    build_drucker_summary_card,
    build_dry_run_preview_card,
    build_fact_card,
    build_gantt_nl_query_card,
    build_gantt_release_monitor_card,
    build_gantt_release_survey_card,
    build_gantt_snapshot_card,
    build_hemingway_confluence_publish_card,
    build_hemingway_doc_card,
    build_hemingway_pr_review_card,
    build_hemingway_impact_card,
    build_hemingway_publication_card,
    build_hemingway_find_card,
    build_hemingway_records_card,
    build_hemingway_nl_query_card,
    build_hemingway_search_card,
    build_jira_query_card,
    build_jira_release_status_card,
    build_jira_status_report_card,
    build_nl_query_card,
    build_jira_ticket_counts_card,
    build_merge_conflicts_card,
    build_naming_compliance_card,
    build_pr_hygiene_card,
    build_pr_list_card,
    build_pr_reviews_card,
    build_pr_stale_card,
    build_stale_branches_card,
)
from shannon.models import AuditRecord, ConversationReference, ConversationState, ShannonResponse, normalize_command_text
from shannon.poster import BasePoster, WorkflowsPoster, build_poster_from_env
from shannon.registry import ShannonAgentRegistry
from agents.shannon.state_store import ShannonStateStore

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


def _coerce_params(raw: Dict[str, str], param_defs: List[Dict[str, Any]]) -> Dict[str, Any]:
    '''
    Coerce flat string key-value pairs from Teams into typed JSON values
    using the ``params`` metadata from agent_registry.yaml.

    Handles: ``list`` (comma-split), ``int``, ``bool``, ``str`` (pass-through).
    Unknown keys pass through unchanged.
    '''
    type_map = {p['name']: p.get('type', 'str') for p in param_defs}
    result: Dict[str, Any] = {}
    for key, value in raw.items():
        ptype = type_map.get(key, 'str')
        if ptype == 'list':
            result[key] = [v.strip() for v in value.split(',') if v.strip()]
        elif ptype == 'int':
            try:
                result[key] = int(value)
            except ValueError:
                result[key] = value
        elif ptype == 'bool':
            result[key] = value.lower() in ('true', '1', 'yes', 'on')
        else:
            result[key] = value
    return result


# Regex for GitHub blob URLs - used by /generate-doc URL support
GITHUB_URL_RE = re_mod.compile(
    r"https?://github\.com/([^/]+/[^/]+)/blob/([^/]+)/(.+)"
)


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
        self.notification_router = NotificationRouter()

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

        owner_channel = self._find_command_owner(command)
        if owner_channel:
            return ShannonResponse(
                text=f'{command} is a command for **#{owner_channel}**. Try it there instead.',
                command=command,
                decision='wrong_channel_redirect',
            )
        return ShannonResponse(
            text=(
                f'Unknown Shannon command: {command}. '
                'Try /help for the current command list.'
            ),
            command=command,
            decision='unknown_command',
        )

    def _find_command_owner(self, command: str) -> Optional[str]:
        command = command.lower()
        for agent in self.registry.list_agents():
            for cc in getattr(agent, 'custom_commands', None) or []:
                if cc.get('command', '').lower() == command:
                    return agent.channel_name or agent.agent_id
        return None

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
            '/pr-hygiene': build_pr_hygiene_card,
            '/pr-stale': build_pr_stale_card,
            '/pr-reviews': build_pr_reviews_card,
            '/pr-list': build_pr_list_card,
            '/naming-compliance': build_naming_compliance_card,
            '/merge-conflicts': build_merge_conflicts_card,
            '/ci-failures': build_ci_failures_card,
            '/stale-branches': build_stale_branches_card,
            '/extended-hygiene': build_pr_hygiene_card,
            '/jira-query': build_jira_query_card,
            '/jira-tickets': build_jira_query_card,
            '/jira-release-status': build_jira_release_status_card,
            '/jira-ticket-counts': build_jira_ticket_counts_card,
            '/jira-status-report': build_jira_status_report_card,
            '/ask': build_nl_query_card,
        },
        'gantt': {
            '/planning-snapshot': build_gantt_snapshot_card,
            '/release-monitor': build_gantt_release_monitor_card,
            '/release-report': build_gantt_release_monitor_card,
            '/release-survey': build_gantt_release_survey_card,
            '/release-survey-report': build_gantt_release_survey_card,
            '/ask': build_gantt_nl_query_card,
        },
        'hemingway': {
            '/generate-doc': build_hemingway_doc_card,
            '/impact-detect': build_hemingway_impact_card,
            '/doc-records': build_hemingway_records_card,
            '/doc-record': build_hemingway_records_card,
            '/publish-doc': build_hemingway_publication_card,
            '/search-docs': build_hemingway_search_card,
            '/find': build_hemingway_find_card,
            '/confluence-publish': build_hemingway_confluence_publish_card,
            '/pr-review': build_hemingway_pr_review_card,
            '/ask': build_hemingway_nl_query_card,
        },
    }

    MUTATION_COMMANDS: set[str] = set()

    def _agent_response_to_shannon(
        self,
        agent_id: str,
        command: str,
        result: Dict[str, Any],
    ) -> ShannonResponse:
        canonical_agent_id = canonical_agent_name(agent_id) or str(agent_id or '').strip().lower()
        display_name = agent_display_name(canonical_agent_id) or canonical_agent_id

        if not result.get('ok', False):
            return ShannonResponse(
                text=f'{display_name}: {result.get("error", "unknown error")}',
                command=command,
                decision='agent_call_failed',
            )

        data = result.get('data', result)

        if isinstance(data, dict) and data.get('dry_run') is True:
            card = build_dry_run_preview_card(canonical_agent_id, command, data)
            return ShannonResponse(
                text=f'Dry-run preview for {command}. Send again with "execute" to confirm.',
                card=card,
                command=command,
                decision='dry_run_preview',
            )

        card_builder = self.AGENT_CARD_BUILDERS.get(canonical_agent_id, {}).get(command)
        if card_builder and isinstance(data, dict):
            if canonical_agent_id == 'drucker' and command in (
                '/pr-hygiene', '/pr-stale', '/pr-reviews', '/pr-list',
                '/naming-compliance', '/merge-conflicts', '/ci-failures',
                '/stale-branches', '/extended-hygiene',
            ):
                card = card_builder(data)
                repo = data.get('repo', '')
                total = data.get('total_findings', data.get('total', len(data.get('prs', []))))
                label = 'findings' if command != '/pr-list' else 'PRs'
                return ShannonResponse(
                    text=f'{repo}: {total} {label}',
                    card=card,
                    command=command,
                    decision='agent_call_success',
                )

            if canonical_agent_id == 'drucker' and command == '/ask':
                card = card_builder(data)
                summary_text = data.get('summary', '')
                total = (
                    data.get('result', {}).get('total')
                    or data.get('result', {}).get('count')
                    or ''
                )
                prefix = f'{total} results — ' if total else ''
                return ShannonResponse(
                    text=f'{prefix}{summary_text[:300]}',
                    card=card,
                    command=command,
                    decision='agent_call_success',
                )

            if canonical_agent_id == 'gantt' and command == '/ask':
                card = card_builder(data)
                summary_text = data.get('summary', '')
                total = (
                    data.get('result', {}).get('total')
                    or data.get('result', {}).get('count')
                    or ''
                )
                prefix = f'{total} results — ' if total else ''
                return ShannonResponse(
                    text=f'{prefix}{summary_text[:300]}',
                    card=card,
                    command=command,
                    decision='agent_call_success',
                )
            if canonical_agent_id == 'hemingway' and command == '/ask':
                card = card_builder(data)
                summary_text = data.get('summary', '')
                total = (
                    data.get('result', {}).get('total')
                    or data.get('result', {}).get('count')
                    or ''
                )
                prefix = f'{total} results — ' if total else ''
                return ShannonResponse(
                    text=f'{prefix}{summary_text[:300]}',
                    card=card,
                    command=command,
                    decision='agent_call_success',
                )

            if canonical_agent_id == 'drucker':
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
            if canonical_agent_id == 'gantt' and command == '/planning-snapshot':
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

            if canonical_agent_id == 'gantt' and command in ('/release-monitor', '/release-report'):
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

            if canonical_agent_id == 'gantt' and command in (
                '/release-survey',
                '/release-survey-report',
            ):
                survey = data.get('survey', {})
                return ShannonResponse(
                    text=(
                        f'{survey.get("project_key", "")}: '
                        f'{survey.get("done_count", 0)} done, '
                        f'{survey.get("in_progress_count", 0)} in progress, '
                        f'{survey.get("remaining_count", 0)} remaining, '
                        f'{survey.get("blocked_count", 0)} blocked'
                    ),
                    card=card,
                    command=command,
                    decision='agent_call_success',
                )

        if canonical_agent_id == 'drucker' and command == '/stats' and isinstance(data, dict):
            card = build_drucker_summary_card(data)
            total = data.get('total_requests', 0)
            errors = data.get('total_errors', 0)
            return ShannonResponse(
                text=f'Requests: {total}, Errors: {errors}',
                card=card,
                command=command,
                decision='agent_call_success',
            )

        if isinstance(data, list):
            lines = [str(item) for item in data[:10]]
            if len(data) > 10:
                lines.append(f'...and {len(data) - 10} more')
            card = build_fact_card(
                title=f'{display_name} — {command}',
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
                title=f'{display_name} — {command}',
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
        activity: Optional[Dict[str, Any]] = None,
    ) -> ShannonResponse:
        canonical_agent_id = canonical_agent_name(agent_id) or str(agent_id or '').strip().lower()

        # -- Conversation mode: check for pending Q&A state --
        user_id = self._get_user_id(activity) if activity else 'unknown'
        normalized_check = normalize_command_text(command_text)
        pending = self.state_store.get_conversation_state(user_id, canonical_agent_id)
        if pending:
            if normalized_check.startswith('/'):
                # New slash command -- abandon conversation and process normally
                self.state_store.clear_conversation_state(user_id, canonical_agent_id)
                log.info(f'Conversation abandoned by {user_id}: new command {normalized_check}')
            else:
                # Not a slash command -- treat as conversation response
                return self._handle_conversation_response(pending, command_text, user_id)

        registration = self.registry.get_agent(canonical_agent_id)
        if not registration or not getattr(registration, 'api_base_url', ''):
            return ShannonResponse(
                text=f'{canonical_agent_id} is registered but has no API endpoint configured.',
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
                cmd_name = cc['command']
                desc = cc.get('description', '')
                cc_params = cc.get('params') or []
                if cc_params:
                    param_parts = []
                    for p in cc_params:
                        name = p['name']
                        ptype = p.get('type', 'str')
                        hint = f'{name}' if ptype == 'str' else f'{name}({ptype})'
                        if p.get('required'):
                            param_parts.append(f'<{hint}>')
                        else:
                            param_parts.append(f'[{hint}]')
                    usage = f'{cmd_name} {" ".join(param_parts)}'
                    lines.append(f'{usage}: {desc}' if desc else usage)
                else:
                    lines.append(f'{cmd_name}: {desc}' if desc else cmd_name)
            card = build_fact_card(
                title=f'{registration.display_name} Commands',
                subtitle=f'Available commands for {agent_id}',
                body_lines=lines,
            )
            return ShannonResponse(
                text=f'Commands for {registration.display_name}:\n' + '\n'.join(lines),
                card=card,
                command='/help',
                decision='reported_agent_help',
            )

        if command == '/why' and len(parts) >= 2:
            result = self._call_agent_api(
                registration, 'GET', f'/v1/status/decisions/{parts[1]}',
            )
            return self._agent_response_to_shannon(canonical_agent_id, command, result)

        if command in self.STANDARD_COMMAND_ROUTES:
            method, path = self.STANDARD_COMMAND_ROUTES[command]
            result = self._call_agent_api(registration, method, path)
            return self._agent_response_to_shannon(canonical_agent_id, command, result)

        custom_commands = getattr(registration, 'custom_commands', []) or []
        for cc in custom_commands:
            if cc.get('command', '').lower() == command:
                method = cc.get('api_method', 'GET')
                path = cc.get('api_path', '')
                json_body = None
                params = None
                args = parts[1:] if len(parts) > 1 else []

                execute_requested = (
                    len(args) > 0
                    and args[-1].lower() == 'execute'
                )
                if execute_requested:
                    args = args[:-1]

                if method.upper() == 'POST':
                    cc_params = cc.get('params') or []
                    required_params = [p for p in cc_params if p.get('required')]

                    # -- URL support for /generate-doc --
                    if command == '/generate-doc' and args:
                        url_match = GITHUB_URL_RE.match(args[0])
                        if url_match:
                            repo, branch, filepath = url_match.groups()
                            json_body = _coerce_params({
                                'doc_title': filepath.rsplit('/', 1)[-1].replace('.md', '').replace('-', ' ').title(),
                                'source_paths': filepath,
                                'repo_name': repo,
                                'doc_type': 'engineering_reference',
                            }, cc_params)
                            result = self._call_agent_api(
                                registration, method, path, json_body=json_body,
                            )
                            return self._agent_response_to_shannon(canonical_agent_id, command, result)

                    # -- Conversation mode: start Q&A if required params missing --
                    if required_params and not args and activity:
                        return self._start_conversation(
                            user_id=user_id,
                            agent_id=canonical_agent_id,
                            command=command,
                            params=cc_params,
                            cc=cc,
                        )

                    if (
                        len(required_params) == 1
                        and required_params[0].get('type', 'str') == 'str'
                        and args
                    ):
                        raw_body = {required_params[0]['name']: ' '.join(args)}
                    else:
                        raw_body = {
                            args[i]: args[i + 1]
                            for i in range(0, len(args) - 1, 2)
                        } if args else {}
                    json_body = _coerce_params(raw_body, cc_params)
                    is_mutation = (
                        command in self.MUTATION_COMMANDS
                        or cc.get('mutation', False)
                    )
                    if is_mutation:
                        json_body['dry_run'] = not execute_requested
                elif args:
                    path = f'{path.rstrip("/")}/{args[-1]}'
                result = self._call_agent_api(
                    registration, method, path, params=params, json_body=json_body,
                )
                return self._agent_response_to_shannon(canonical_agent_id, command, result)

        if not command.startswith('/'):
            nl_result = self._call_agent_api(
                registration, 'POST', '/v1/nl/query',
                json_body={'query': command_text, 'project_key': 'STL'},
            )
            if nl_result.get('ok'):
                return self._agent_response_to_shannon(canonical_agent_id, '/ask', nl_result)
            return ShannonResponse(
                text=nl_result.get('summary') or nl_result.get('error', 'Query failed.'),
                command='nl-query',
                decision='nl_query_fallback',
            )

        owner_channel = self._find_command_owner(command)
        if owner_channel and owner_channel.lower() != (registration.channel_name or '').lower():
            return ShannonResponse(
                text=f'{command} is a command for **#{owner_channel}**. Try it there instead.',
                command=command,
                decision='wrong_channel_redirect',
            )
        return ShannonResponse(
            text=f'Unknown {registration.display_name} command: {command}. Try /help.',
            command=command,
            decision='unknown_agent_command',
        )

    # -- Conversation mode helpers ------------------------------------------------

    @staticmethod
    def _get_user_id(activity):
        """Extract a stable user ID from a Teams activity."""
        if not activity:
            return 'unknown'
        from_obj = activity.get('from') or {}
        return (
            str(from_obj.get('aadObjectId') or '').strip()
            or str(from_obj.get('id') or '').strip()
            or 'unknown'
        )

    def _start_conversation(
        self,
        user_id,
        agent_id,
        command,
        params,
        cc=None,
    ):
        """Start a Q&A flow for a command with missing required parameters."""
        remaining = [p for p in params if p.get('required')]
        state = ConversationState(
            state_id=str(uuid.uuid4())[:8],
            user_id=user_id,
            agent_id=agent_id,
            command=command,
            collected_params={},
            remaining_params=remaining,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.state_store.save_conversation_state(state)

        first = remaining[0]
        label = first.get('label', first['name'])
        hint = first.get('description', '')
        prompt = f"**{command}** -- I need a few details.\n\n**{label}**?"
        if hint:
            prompt += f"\n_{hint}_"
        prompt += "\n\n_Type **cancel** to abort._"

        log.info(f'Conversation started: user={user_id} agent={agent_id} command={command}')
        return ShannonResponse(
            text=prompt,
            command=command,
            decision='conversation_started',
        )

    def _handle_conversation_response(self, state, response_text, user_id):
        """Process a user answer in an active Q&A conversation."""
        text = normalize_command_text(response_text).strip()

        # Handle cancel
        if text.lower() in ('cancel', '/cancel', 'stop', 'quit'):
            self.state_store.clear_conversation_state(user_id, state.agent_id)
            log.info(f'Conversation cancelled: user={user_id} command={state.command}')
            return ShannonResponse(
                text='Cancelled.',
                command=state.command,
                decision='conversation_cancelled',
            )

        # Collect the current param
        current_param = state.remaining_params[0]
        state.collected_params[current_param['name']] = text
        state.remaining_params = state.remaining_params[1:]

        if state.remaining_params:
            # More params needed -- ask for the next one
            self.state_store.save_conversation_state(state)
            next_param = state.remaining_params[0]
            label = next_param.get('label', next_param['name'])
            hint = next_param.get('description', '')
            collected_summary = ', '.join(
                f"**{k}**: {v}" for k, v in state.collected_params.items()
            )
            prompt = f"Got it. ({collected_summary})\n\n**{label}**?"
            if hint:
                prompt += f"\n_{hint}_"
            return ShannonResponse(
                text=prompt,
                command=state.command,
                decision='conversation_collecting',
            )

        # All params collected -- execute the command
        self.state_store.clear_conversation_state(user_id, state.agent_id)
        log.info(
            f'Conversation complete: user={user_id} command={state.command} '
            f'params={state.collected_params}'
        )

        # Look up the registration and command config to call the API
        registration = self.registry.get_agent(state.agent_id)
        if not registration or not getattr(registration, 'api_base_url', ''):
            return ShannonResponse(
                text=f'{state.agent_id} has no API endpoint configured.',
                command=state.command,
                decision='conversation_no_api',
            )

        custom_commands = getattr(registration, 'custom_commands', []) or []
        cc = None
        for candidate in custom_commands:
            if candidate.get('command', '').lower() == state.command:
                cc = candidate
                break

        if not cc:
            return ShannonResponse(
                text=f'Could not find command config for {state.command}.',
                command=state.command,
                decision='conversation_command_not_found',
            )

        method = cc.get('api_method', 'POST')
        api_path = cc.get('api_path', '')
        cc_params = cc.get('params') or []
        json_body = _coerce_params(state.collected_params, cc_params)

        # Respect mutation/dry_run semantics
        is_mutation = (
            state.command in self.MUTATION_COMMANDS
            or cc.get('mutation', False)
        )
        if is_mutation:
            json_body['dry_run'] = True

        result = self._call_agent_api(
            registration, method, api_path, json_body=json_body,
        )
        return self._agent_response_to_shannon(state.agent_id, state.command, result)

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
            response = self._handle_registered_agent_command(agent_id, command_text, activity=activity)

        return reference, response

    def _get_poster_for_agent(self, agent_id: str) -> BasePoster:
        '''
        Return an agent-specific poster if the agent has its own webhook URL,
        otherwise fall back to the default Shannon poster.
        '''
        registration = self.registry.get_agent(agent_id)
        if registration and registration.notifications_webhook_url:
            return WorkflowsPoster(webhook_url=registration.notifications_webhook_url)
        return self.poster

    def _post_response(
        self,
        reference: ConversationReference,
        response: ShannonResponse,
        *,
        reply: bool,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        poster = self._get_poster_for_agent(agent_id) if agent_id else self.poster
        activity = response.to_message_activity()
        if reply and reference.reply_to_id:
            return poster.reply_to_activity(reference, reference.reply_to_id, activity, dry_run=False)
        return poster.send_to_conversation(reference, activity, dry_run=False)

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
                post_result = self._post_response(reference, welcome, reply=False, agent_id=agent_id)
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
        post_result = self._post_response(reference, response, reply=True, agent_id=agent_id)
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

    _SLOW_COMMANDS = frozenset({'/ask', '/planning-snapshot', '/release-monitor', '/release-survey'})

    def _is_slow_command(self, command_text: str) -> bool:
        parts = normalize_command_text(command_text).split()
        command = parts[0].lower() if parts else ''
        if command in self._SLOW_COMMANDS:
            return True
        if not command.startswith('/'):
            return True
        return False

    def _run_async_and_post(
        self,
        activity: Dict[str, Any],
        agent_id: str,
        reference: ConversationReference,
    ) -> None:
        try:
            reference, response = self._build_command_response(activity)
            self._record(
                'decision',
                reference=reference,
                agent_id=agent_id,
                command=response.command or '/ask',
                decision=response.decision,
                details={
                    'input': normalize_command_text(str(activity.get('text') or '')),
                    'transport': 'outgoing_webhook_async',
                },
            )
            post_result = self._post_response(reference, response, reply=True, agent_id=agent_id)
            self._record(
                'notification_posted',
                reference=reference,
                agent_id=agent_id,
                command=response.command,
                decision=response.decision,
                details=post_result,
            )
        except Exception:
            log.exception('Async outgoing webhook handler failed for %s', agent_id)

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
            return response.to_outgoing_webhook_response()

        raw_text = str(activity.get('text') or '').strip()
        command_text = normalize_command_text(raw_text)
        if self._is_slow_command(command_text):
            thread = threading.Thread(
                target=self._run_async_and_post,
                args=(activity, agent_id, reference),
                daemon=True,
            )
            thread.start()
            ack = ShannonResponse(
                text='Processing your query — results will follow shortly.',
                decision='deferred_slow_command',
            )
            self._record(
                'decision',
                reference=reference,
                agent_id=agent_id,
                command='/ask',
                decision='deferred_slow_command',
                details={
                    'input': command_text,
                    'transport': 'outgoing_webhook',
                },
            )
            return ack.to_outgoing_webhook_response()

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

        response = ShannonResponse(
            text=text,
            card=build_fact_card(
                title=title,
                subtitle=f'Notification for {registration.display_name}',
                body_lines=body_lines or [text],
            ),
            decision='posted_agent_notification',
        )

        if registration.notifications_webhook_url:
            poster = WorkflowsPoster(webhook_url=registration.notifications_webhook_url)
            activity = response.to_message_activity()
            ref = ConversationReference(channel_id=registration.channel_id or '', agent_id=registration.agent_id)
            post_result = poster.send_to_conversation(ref, activity, dry_run=False)
        else:
            ref = self.state_store.get_conversation_reference(
                agent_id=registration.agent_id,
                channel_id=registration.channel_id or channel_id or '',
            )
            if ref is None:
                raise ValueError(
                    'No stored conversation reference for this channel yet. '
                    'Install the bot in the team and send a first message or wait for a '
                    'conversationUpdate event.'
                )
            post_result = self._post_response(ref, response, reply=False, agent_id=registration.agent_id)
        self._record(
            'notification_posted',
            reference=ref,
            agent_id=registration.agent_id,
            decision='posted_agent_notification',
            details=post_result,
        )

        # --- DM + email via NotificationRouter ---
        try:
            dm_result = send_notification(
                agent_id=agent_id,
                title=title,
                text=text,
                body_lines=list(body_lines) if body_lines else None,
            )
            log.info('NotificationRouter result for %s: %s', agent_id, dm_result.get('ok'))
        except Exception as e:
            log.warning('NotificationRouter dispatch failed (non-fatal): %s', e)
            dm_result = {'error': str(e)}

        return {
            'ok': True,
            'agent_id': registration.agent_id,
            'channel_id': ref.channel_id,
            'post_result': post_result,
            'dm_result': dm_result,
        }
