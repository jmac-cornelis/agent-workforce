##########################################################################################
#
# Module: agents/drucker_agent.py
#
# Description: Drucker Jira Coordinator agent.
#              Produces deterministic Jira hygiene reports, ticket-level
#              remediation suggestions, and review-gated Jira write-back plans.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import yaml

from agents.base import BaseAgent, AgentConfig, AgentResponse
from agents.drucker.models import (
    DruckerAction,
    DruckerFinding,
    DruckerHygieneReport,
    DruckerRequest,
)
from agents.pm_runtime import notify_shannon
from agents.review_agent import ReviewAgent, ReviewItem, ReviewSession
from config.jira_identity import get_jira_actor_email
from core.monitoring import (
    MonitorConfig,
    ValidationResult,
    determine_actions,
    load_monitor_config,
    validate_ticket,
)
from core.reporting import bug_activity_today
from jira_utils import connect_to_jira
from notifications.jira_comments import JiraCommentNotifier
from agents.drucker.state.learning_store import DruckerLearningStore
from agents.drucker.state.monitor_state import DruckerMonitorState
from agents.drucker.state.report_store import DruckerReportStore
from tools.jira_tools import JiraTools, get_project_info, search_tickets
from tools.knowledge_tools import search_knowledge, list_knowledge_files, read_knowledge_file

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_MONITOR_CONFIG_PATH = os.path.join(_AGENT_DIR, 'config', 'monitor.yaml')
_DEFAULT_MONITOR_DB_PATH = 'data/drucker_monitor_state.db'
_DEFAULT_LEARNING_DB_PATH = 'data/drucker_learning.db'
_DEFAULT_POLLER_CONFIG_PATH = os.path.join(_AGENT_DIR, 'config', 'polling.yaml')

_DEFAULT_VALIDATION_RULES = {
    'Story': {
        'required': ['assignee', 'fix_versions', 'components'],
        'warn': ['description'],
    },
    'Bug': {
        'required': ['assignee', 'fix_versions', 'components', 'priority'],
        'warn': ['description'],
    },
    'Task': {
        'required': ['assignee', 'fix_versions', 'components'],
        'warn': ['description'],
    },
    'Epic': {
        'required': ['assignee'],
        'warn': ['description'],
    },
}


class DruckerCoordinatorAgent(BaseAgent):
    '''
    Deterministic-first Jira hygiene coordinator.

    Drucker analyzes project hygiene, identifies risky ticket states, proposes
    low-risk Jira actions, and hands execution off through review-gated paths.
    '''

    DEFAULT_FIELDS = [
        'summary',
        'description',
        'issuetype',
        'status',
        'priority',
        'assignee',
        'reporter',
        'created',
        'updated',
        'resolutiondate',
        'project',
        'fixVersions',
        'versions',
        'components',
        'labels',
    ]

    CATEGORY_LABELS = {
        'stale_ticket': 'stale',
        'blocked_stale_ticket': 'blocked',
        'unassigned_ticket': 'needs-owner',
        'missing_fix_version': 'needs-release-target',
        'missing_component': 'needs-component',
        'missing_labels': 'needs-triage',
        'missing_required_fields': 'needs-required-fields',
        'missing_recommended_fields': 'needs-metadata-review',
    }

    def __init__(self, project_key: Optional[str] = None, **kwargs):
        instruction = self._load_prompt_file()
        if not instruction:
            raise FileNotFoundError(
                'agents/drucker/prompts/system.md is required but not found. '
                'The Drucker Coordinator Agent has no hardcoded fallback prompt.'
            )

        config = AgentConfig(
            name='drucker_coordinator',
            description='Coordinates Jira hygiene analysis and review-gated Jira actions',
            instruction=instruction,
            max_iterations=12,
        )

        super().__init__(config=config, tools=[JiraTools()], **kwargs)
        self.register_tool(search_knowledge)
        self.register_tool(list_knowledge_files)
        self.register_tool(read_knowledge_file)
        self.project_key = project_key
        self._review_agent: Optional[ReviewAgent] = None
        self._monitor_state: Optional[DruckerMonitorState] = None
        self._learning_store: Optional[DruckerLearningStore] = None
        self.monitor_config = self._load_monitor_config(project_key=project_key)

    @staticmethod
    def _load_prompt_file() -> Optional[str]:
        prompt_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'prompts', 'system.md'
        )
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                log.warning(f'Failed to load Drucker agent prompt: {e}')
        return None

    @property
    def review_agent(self) -> ReviewAgent:
        if self._review_agent is None:
            self._review_agent = ReviewAgent()
        return self._review_agent

    @property
    def monitor_state(self) -> DruckerMonitorState:
        if self._monitor_state is None:
            self._monitor_state = DruckerMonitorState(
                db_path=os.getenv('DRUCKER_MONITOR_STATE_DB', _DEFAULT_MONITOR_DB_PATH)
            )
        return self._monitor_state

    @property
    def learning_store(self) -> DruckerLearningStore:
        if self._learning_store is None:
            self._learning_store = DruckerLearningStore(
                db_path=os.getenv('DRUCKER_LEARNING_DB', _DEFAULT_LEARNING_DB_PATH),
                min_observations=self.monitor_config.min_observations,
            )
        else:
            self._learning_store.set_min_observations(
                self.monitor_config.min_observations
            )
        return self._learning_store

    @staticmethod
    def _load_monitor_config(project_key: Optional[str] = None) -> MonitorConfig:
        if os.path.exists(_DEFAULT_MONITOR_CONFIG_PATH):
            try:
                config = load_monitor_config(_DEFAULT_MONITOR_CONFIG_PATH)
            except Exception as e:
                log.warning(f'Failed to load Drucker monitor config: {e}')
                config = MonitorConfig(validation_rules=dict(_DEFAULT_VALIDATION_RULES))
        else:
            config = MonitorConfig(validation_rules=dict(_DEFAULT_VALIDATION_RULES))

        if not config.validation_rules:
            config.validation_rules = dict(_DEFAULT_VALIDATION_RULES)
        if not config.project and project_key:
            config.project = project_key
        return config

    def _build_request(self, input_data: Any) -> DruckerRequest:
        if isinstance(input_data, str):
            return DruckerRequest(project_key=input_data)

        if isinstance(input_data, dict):
            return DruckerRequest(
                project_key=input_data.get('project_key', self.project_key or ''),
                ticket_key=input_data.get('ticket_key'),
                limit=int(input_data.get('limit', 200)),
                include_done=bool(input_data.get('include_done', False)),
                stale_days=int(input_data.get('stale_days', 30)),
                jql=input_data.get('jql'),
                since=input_data.get('since'),
                recent_only=bool(input_data.get('recent_only', False)),
                label_prefix=str(
                    input_data.get('label_prefix', 'drucker') or 'drucker'
                ),
                requested_by=input_data.get('requested_by'),
                approved_by=input_data.get('approved_by'),
                correlation_id=input_data.get('correlation_id'),
                trigger=str(input_data.get('trigger', 'interactive') or 'interactive'),
            )

        raise ValueError('Invalid input: expected project key string or request dict')

    def _analyze_request(self, request: DruckerRequest) -> tuple[DruckerHygieneReport, str]:
        if request.ticket_key:
            return self.analyze_ticket_hygiene(request), 'issue_check'
        if request.recent_only:
            return self.analyze_recent_ticket_intake(request), 'ticket_intake_report'
        return self.analyze_project_hygiene(request), 'hygiene_report'

    def run(self, input_data: Any) -> AgentResponse:
        '''
        Build a Jira hygiene report and corresponding review session.
        '''
        log.debug(f'DruckerCoordinatorAgent.run(input_data={input_data})')

        try:
            request = self._build_request(input_data)
        except ValueError as e:
            return AgentResponse.error_response(
                str(e)
            )

        if not request.project_key:
            return AgentResponse.error_response('No project_key provided')

        try:
            report, task_type = self._analyze_request(request)
            review_session = self.create_review_session(report)
        except Exception as e:
            log.error(f'Drucker hygiene analysis failed: {e}')
            return AgentResponse.error_response(str(e))

        return AgentResponse.success_response(
            content=report.summary_markdown,
            metadata={
                'task_type': task_type,
                'hygiene_report': report.to_dict(),
                'review_session': review_session.to_dict(),
            },
        )

    def run_once(
        self,
        request: DruckerRequest,
        *,
        persist: bool = True,
    ) -> Dict[str, Any]:
        '''
        Execute one deterministic Drucker hygiene task and optionally persist it.
        '''
        self.project_key = request.project_key or self.project_key
        report, task_type = self._analyze_request(request)
        review_session = self.create_review_session(report)

        result: Dict[str, Any] = {
            'ok': True,
            'task_type': task_type,
            'project_key': report.project_key,
            'report': report.to_dict(),
            'review_session': review_session.to_dict(),
            'summary_markdown': report.summary_markdown,
        }
        if persist:
            result['stored'] = DruckerReportStore().save_report(
                report,
                summary_markdown=report.summary_markdown,
            )
        return result

    @staticmethod
    def _build_hygiene_notification_payload(result: Dict[str, Any]) -> Dict[str, Any]:
        report = result.get('report', {})
        summary = report.get('summary', {})
        task_type = str(result.get('task_type') or 'hygiene_report')
        stored = result.get('stored', {})
        text = (
            f'{report.get("project_key", "")}: '
            f'{summary.get("finding_count", 0)} findings, '
            f'{summary.get("action_count", 0)} proposed actions'
        )
        body_lines = [
            f'Report ID: {stored.get("report_id") or report.get("report_id", "")}',
            f'Tickets with findings: {summary.get("tickets_with_findings", 0)}',
            f'Total tickets scanned: {summary.get("total_tickets", 0)}',
        ]
        title = 'Drucker Hygiene Report'
        if task_type == 'issue_check':
            title = 'Drucker Issue Check'
        elif task_type == 'ticket_intake_report':
            title = 'Drucker Ticket Intake'
        return {
            'title': f'{title} — {report.get("project_key", "")}',
            'text': text,
            'body_lines': body_lines,
        }

    @staticmethod
    def _load_poller_config(config_path: str) -> Dict[str, Any]:
        if not config_path:
            raise ValueError('Drucker polling config path is required')
        if not os.path.exists(config_path):
            raise FileNotFoundError(f'Drucker polling config not found: {config_path}')

        with open(config_path, 'r', encoding='utf-8') as f:
            payload = yaml.safe_load(f.read()) or {}

        if not isinstance(payload, dict):
            raise ValueError('Drucker polling config must deserialize to a mapping')

        return payload

    def _resolve_poller_jobs(
        self,
        poller_spec: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        config_path = str(poller_spec.get('config_path') or '').strip()
        job_name = str(poller_spec.get('job_name') or '').strip()

        if not config_path:
            return [dict(poller_spec)]

        payload = self._load_poller_config(config_path)
        defaults = payload.get('defaults') or {}
        raw_jobs = payload.get('jobs') or []

        if not isinstance(defaults, dict):
            raise ValueError('Drucker polling config defaults must be a mapping')
        if not isinstance(raw_jobs, list):
            raise ValueError('Drucker polling config jobs must be a list')

        jobs: List[Dict[str, Any]] = []
        for raw_job in raw_jobs:
            if not isinstance(raw_job, dict):
                continue
            if raw_job.get('enabled', True) is False:
                continue

            current_job_name = str(raw_job.get('job_id') or '').strip()
            if job_name and current_job_name != job_name:
                continue

            merged_job = dict(defaults)
            merged_job.update(raw_job)

            project_key = str(poller_spec.get('project_key') or '').strip()
            if project_key:
                merged_job['project_key'] = project_key

            if poller_spec.get('since'):
                merged_job['since'] = poller_spec.get('since')
            if poller_spec.get('jql'):
                merged_job['jql'] = poller_spec.get('jql')
            if poller_spec.get('shannon_base_url'):
                merged_job['shannon_base_url'] = poller_spec.get('shannon_base_url')
            if poller_spec.get('notify_shannon') is True:
                merged_job['notify_shannon'] = True

            jobs.append(merged_job)

        if not jobs:
            detail = job_name or 'enabled jobs'
            raise ValueError(
                f'No Drucker polling jobs matched {detail} in {config_path}'
            )

        return jobs

    def analyze_bug_activity(
        self,
        project_key: Optional[str] = None,
        target_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        resolved_project = str(project_key or self.project_key or '').strip()
        if not resolved_project:
            raise ValueError('Drucker bug activity requires project_key')

        jira = connect_to_jira()
        result = bug_activity_today(
            jira,
            resolved_project,
            target_date or date.today().isoformat(),
        )
        result['task_type'] = 'bug_activity'
        result['generated_at'] = datetime.now(timezone.utc).isoformat()
        return result

    @staticmethod
    def format_bug_activity_report(activity: Dict[str, Any]) -> str:
        lines = [
            f'# DRUCKER BUG ACTIVITY: {activity.get("project", "")}',
            '',
            f'**Date**: {activity.get("date", "")}',
            f'**Generated At**: {activity.get("generated_at", "")}',
            '',
            '## Summary',
            '',
        ]

        summary = activity.get('summary', {}) or {}
        lines.extend([
            f'- Bugs Opened: {summary.get("bugs_opened", 0)}',
            f'- Status Transitions: {summary.get("status_transitions", 0)}',
            f'- Bugs With Comments: {summary.get("bugs_with_comments", 0)}',
            f'- Total Active Bugs: {summary.get("total_active_bugs", 0)}',
            '',
        ])

        def add_section(title: str, rows: List[str]) -> None:
            lines.append(f'## {title}')
            lines.append('')
            if rows:
                lines.extend(rows)
            else:
                lines.append('- None')
            lines.append('')

        add_section(
            'Opened Today',
            [
                f'- {bug.get("key", "")} [{bug.get("priority", "")}] {bug.get("summary", "")}'.rstrip()
                for bug in (activity.get('opened') or [])
            ],
        )
        add_section(
            'Status Changes',
            [
                (
                    f'- {change.get("key", "")}: '
                    f'{change.get("from_status", "")} -> {change.get("to_status", "")} '
                    f'({change.get("changed_by", "")})'
                )
                for change in (activity.get('status_changed') or [])
            ],
        )
        add_section(
            'Comments',
            [
                (
                    f'- {comment.get("key", "")}: '
                    f'{comment.get("comment_count", 0)} comment(s), '
                    f'latest by {comment.get("latest_author", "")}'
                )
                for comment in (activity.get('commented') or [])
            ],
        )

        return '\n'.join(lines).rstrip()

    def tick(self, poller_spec: Dict[str, Any]) -> Dict[str, Any]:
        '''
        Execute one scheduled Drucker hygiene cycle.
        '''
        tasks: List[Dict[str, Any]] = []
        notifications: List[Dict[str, Any]] = []
        errors: List[str] = []

        job_specs = self._resolve_poller_jobs(poller_spec)
        resolved_project_key = ''

        for index, job_spec in enumerate(job_specs, 1):
            job_id = str(
                job_spec.get('job_id') or f'drucker-job-{index}'
            ).strip()
            scan_type = str(job_spec.get('scan_type', 'jira')).strip()

            notify_enabled = bool(job_spec.get('notify_shannon', False))
            shannon_base_url = job_spec.get('shannon_base_url')

            # ── GitHub PR hygiene scan ──────────────────────────────
            if scan_type == 'github':
                github_repos = job_spec.get('github_repos') or []
                if isinstance(github_repos, str):
                    github_repos = [github_repos]
                github_stale_days = int(
                    job_spec.get('github_stale_days', 5)
                )

                for repo in github_repos:
                    try:
                        import github_utils
                        report = github_utils.analyze_repo_pr_hygiene(
                            repo, stale_days=github_stale_days,
                        )
                        tasks.append({
                            'ok': True,
                            'task_type': 'github_pr_hygiene',
                            'job_id': job_id,
                            'repo': repo,
                            'report': report,
                        })
                        if notify_enabled:
                            finding_count = len(
                                report.get('findings', [])
                            )
                            stale_count = report.get('stale_count', 0)
                            missing_count = report.get(
                                'missing_review_count', 0
                            )
                            notifications.append(
                                notify_shannon(
                                    agent_id='drucker',
                                    shannon_base_url=shannon_base_url,
                                    title=f'GitHub PR Hygiene: {repo}',
                                    text=(
                                        f'{finding_count} finding(s) '
                                        f'in {repo}'
                                    ),
                                    body_lines=[
                                        f'Stale PRs (>{github_stale_days} '
                                        f'days): {stale_count}',
                                        f'Missing reviews: {missing_count}',
                                        f'Total open PRs: '
                                        f'{report.get("open_pr_count", 0)}',
                                    ],
                                )
                            )
                    except Exception as exc:
                        errors.append(f'{job_id}:{repo}: {exc}')
                continue

            # ── GitHub extended hygiene scan ───────────────────────
            elif scan_type == 'github-extended':
                github_repos = job_spec.get('github_repos') or []
                if isinstance(github_repos, str):
                    github_repos = [github_repos]
                github_stale_days = int(
                    job_spec.get('github_stale_days', 5)
                )
                branch_stale_days = int(
                    job_spec.get('branch_stale_days', 30)
                )

                for repo in github_repos:
                    try:
                        import github_utils
                        report = github_utils.analyze_extended_hygiene(
                            repo,
                            stale_days=github_stale_days,
                            branch_stale_days=branch_stale_days,
                        )
                        tasks.append({
                            'ok': True,
                            'task_type': 'github_extended_hygiene',
                            'job_id': job_id,
                            'repo': repo,
                            'report': report,
                        })
                        if notify_enabled:
                            total_findings = report.get(
                                'total_findings', 0
                            )
                            notifications.append(
                                notify_shannon(
                                    agent_id='drucker',
                                    shannon_base_url=shannon_base_url,
                                    title=f'GitHub Extended Hygiene: {repo}',
                                    text=(
                                        f'{total_findings} finding(s) '
                                        f'in {repo}'
                                    ),
                                    body_lines=[
                                        f'Stale PRs: {len(report.get("stale_prs", []))}',
                                        f'Missing reviews: {len(report.get("missing_reviews", []))}',
                                        f'Naming findings: {report.get("naming_findings", {}).get("total_findings", 0)}',
                                        f'Merge conflicts: {report.get("merge_conflicts", {}).get("total_conflicts", 0)}',
                                        f'CI failures: {report.get("ci_failures", {}).get("total_failures", 0)}',
                                        f'Stale branches: {report.get("stale_branches", {}).get("total_findings", 0)}',
                                    ],
                                )
                            )
                    except Exception as exc:
                        errors.append(f'{job_id}:{repo}: {exc}')
                continue

            # ── GitHub PR reminder scan ─────────────────────────────
            elif scan_type == 'github-pr-reminders':
                github_repos = job_spec.get('github_repos') or []
                if isinstance(github_repos, str):
                    github_repos = [github_repos]

                try:
                    from pr_reminders import PRReminderEngine
                    engine = PRReminderEngine()
                    engine.scan_repos(repos=github_repos or None)
                    result = engine.process_due_reminders()
                    tasks.append({
                        'ok': True,
                        'task_type': 'github_pr_reminders',
                        'job_id': job_id,
                        'result': result,
                    })
                    if notify_enabled:
                        sent = result.get('sent', 0)
                        due = result.get('due', 0)
                        notifications.append(
                            notify_shannon(
                                agent_id='drucker',
                                shannon_base_url=shannon_base_url,
                                title='PR Reminder Scan',
                                text=f'{sent}/{due} reminder(s) sent',
                                body_lines=[
                                    f'Due reminders: {due}',
                                    f'Sent: {sent}',
                                    f'Errors: {result.get("errors", 0)}',
                                ],
                            )
                        )
                except Exception as exc:
                    errors.append(f'{job_id}: {exc}')
                continue

            # ── Jira hygiene scan (default) ─────────────────────────
            project_key = str(
                job_spec.get('project_key') or self.project_key or ''
            ).strip()
            if not project_key:
                errors.append(f'{job_id}: Drucker tick requires project_key')
                continue

            resolved_project_key = resolved_project_key or project_key
            self.project_key = project_key

            persist = bool(job_spec.get('persist', True))

            try:
                request = DruckerRequest(
                    project_key=project_key,
                    ticket_key=job_spec.get('ticket_key'),
                    limit=int(job_spec.get('limit', 200)),
                    include_done=bool(job_spec.get('include_done', False)),
                    stale_days=int(job_spec.get('stale_days', 30)),
                    jql=job_spec.get('jql'),
                    since=job_spec.get('since'),
                    recent_only=bool(job_spec.get('recent_only', False)),
                    label_prefix=str(
                        job_spec.get('label_prefix', 'drucker') or 'drucker'
                    ),
                    requested_by=job_spec.get('requested_by'),
                    approved_by=job_spec.get('approved_by'),
                    correlation_id=job_spec.get('correlation_id'),
                    trigger='polling',
                )
                result = self.run_once(request, persist=persist)
                result['job_id'] = job_id
                tasks.append(result)
                if notify_enabled:
                    notifications.append(
                        notify_shannon(
                            agent_id='drucker',
                            shannon_base_url=shannon_base_url,
                            **self._build_hygiene_notification_payload(result),
                        )
                    )
            except Exception as e:
                errors.append(f'{job_id}: {e}')

        return {
            'ok': not errors,
            'agent_id': 'drucker',
            'project_key': resolved_project_key,
            'tasks': tasks,
            'notifications': notifications,
            'errors': errors,
            'completed_at': datetime.now(timezone.utc).isoformat(),
        }

    def run_poller(
        self,
        poller_spec: Dict[str, Any],
        *,
        sleep_fn: Any = time.sleep,
    ) -> Dict[str, Any]:
        '''
        Run the Drucker polling loop for a bounded number of cycles.
        '''
        interval_seconds = max(int(poller_spec.get('interval_seconds', 300) or 0), 0)
        max_cycles = int(poller_spec.get('max_cycles', 1) or 0)
        if max_cycles < 0:
            raise ValueError('max_cycles must be >= 0')
        if max_cycles == 0 and interval_seconds <= 0:
            raise ValueError(
                'Continuous polling requires interval_seconds > 0'
            )

        cycle_summaries: List[Dict[str, Any]] = []
        cycles_run = 0
        last_tick: Optional[Dict[str, Any]] = None

        while True:
            cycles_run += 1
            last_tick = self.tick(poller_spec)
            cycle_summaries.append({
                'cycle_number': cycles_run,
                'ok': last_tick.get('ok', False),
                'task_count': len(last_tick.get('tasks', [])),
                'notification_count': len(last_tick.get('notifications', [])),
                'errors': list(last_tick.get('errors', [])),
                'completed_at': last_tick.get('completed_at', ''),
            })

            if max_cycles > 0 and cycles_run >= max_cycles:
                break
            if interval_seconds > 0:
                sleep_fn(interval_seconds)

        return {
            'ok': all(item.get('ok', False) for item in cycle_summaries),
            'agent_id': 'drucker',
            'project_key': str(
                poller_spec.get('project_key') or self.project_key or ''
            ).strip(),
            'cycles_run': cycles_run,
            'cycle_summaries': cycle_summaries,
            'last_tick': last_tick or {},
        }

    def analyze_project_hygiene(
        self,
        request: DruckerRequest,
    ) -> DruckerHygieneReport:
        '''
        Produce a deterministic Jira hygiene report for a project.
        '''
        log.info(f'Creating Drucker hygiene report for {request.project_key}')

        project_info = self._load_project_info(request.project_key)
        tickets = self._load_tickets(request)
        self._attach_policy_analysis(tickets)
        findings = self._build_findings(tickets, stale_days=request.stale_days)
        findings.extend(self._build_policy_findings_for_tickets(tickets))
        actions = self._build_actions(
            tickets,
            findings,
            label_prefix=request.label_prefix,
        )
        summary = self._build_summary(tickets, findings, actions)

        report = DruckerHygieneReport(
            project_key=request.project_key,
            request=request.to_dict(),
            project_info=project_info,
            summary=summary,
            findings=findings,
            proposed_actions=actions,
            tickets=tickets,
        )
        report.summary_markdown = self._format_report(report)
        return report

    def analyze_ticket_hygiene(
        self,
        request: DruckerRequest,
    ) -> DruckerHygieneReport:
        '''
        Run a one-shot ticket intake check for a specific Jira issue.
        '''
        if not request.ticket_key:
            raise ValueError('Drucker ticket hygiene requires ticket_key')

        log.info(
            f'Creating Drucker issue check for {request.project_key}:{request.ticket_key}'
        )

        project_info = self._load_project_info(request.project_key)
        ticket = self._load_ticket(request)
        return self._build_intake_report(
            request,
            project_info=project_info,
            tickets=[ticket],
            monitor_scope='ticket',
        )

    def analyze_recent_ticket_intake(
        self,
        request: DruckerRequest,
    ) -> DruckerHygieneReport:
        '''
        Run a checkpointed scan of recently created tickets for intake issues.
        '''
        log.info(f'Creating Drucker recent-ticket intake report for {request.project_key}')

        project_info = self._load_project_info(request.project_key)
        since_value, tickets = self._load_recent_tickets(request)
        report = self._build_intake_report(
            request,
            project_info=project_info,
            tickets=tickets,
            monitor_scope='recent_ticket_intake',
        )
        report.request['since'] = since_value

        findings_by_ticket: Dict[str, List[DruckerFinding]] = defaultdict(list)
        for finding in report.findings:
            findings_by_ticket[finding.ticket_key].append(finding)

        processed_at = self._format_jql_datetime(datetime.now(timezone.utc))
        for ticket in tickets:
            ticket_key = str(ticket.get('key') or '')
            if not ticket_key:
                continue
            self.monitor_state.mark_processed(
                ticket_key,
                project=request.project_key,
                result={
                    'monitor_scope': 'recent_ticket_intake',
                    'finding_count': len(findings_by_ticket.get(ticket_key, [])),
                },
                timestamp=processed_at,
            )

        self.monitor_state.set_last_checked(
            request.project_key,
            timestamp=processed_at,
        )
        return report

    def _build_intake_report(
        self,
        request: DruckerRequest,
        *,
        project_info: Dict[str, Any],
        tickets: List[Dict[str, Any]],
        monitor_scope: str,
    ) -> DruckerHygieneReport:
        findings = self._build_intake_findings(tickets, stale_days=request.stale_days)
        actions = self._build_actions(
            tickets,
            findings,
            label_prefix=request.label_prefix,
        )
        summary = self._build_summary(tickets, findings, actions)
        summary['monitor_scope'] = monitor_scope
        summary['source_ticket_count'] = len(tickets)
        if request.ticket_key:
            summary['ticket_key'] = request.ticket_key

        report = DruckerHygieneReport(
            project_key=request.project_key,
            request=request.to_dict(),
            project_info=project_info,
            summary=summary,
            findings=findings,
            proposed_actions=actions,
            tickets=tickets,
        )
        report.summary_markdown = self._format_report(report)
        return report

    def _build_intake_findings(
        self,
        tickets: List[Dict[str, Any]],
        stale_days: int,
    ) -> List[DruckerFinding]:
        findings: List[DruckerFinding] = []

        for ticket in tickets:
            findings.extend(self._build_findings([ticket], stale_days=stale_days))
            findings.extend(self._build_policy_findings(ticket))

        for index, finding in enumerate(findings, 1):
            finding.finding_id = f'F{index:03d}'

        return findings

    def _build_policy_findings(
        self,
        ticket: Dict[str, Any],
    ) -> List[DruckerFinding]:
        policy = self._policy_analysis(ticket)
        validation = policy['validation']
        required_fields = policy['required_fields']
        warned_fields = policy['warned_fields']
        suggestion_findings = policy['suggestion_findings']

        findings: List[DruckerFinding] = []
        if required_fields:
            findings.append(
                DruckerFinding(
                    finding_id='',
                    ticket_key=str(ticket.get('key') or ''),
                    category='missing_required_fields',
                    severity='high',
                    title='Ticket intake policy has missing required fields',
                    description=(
                        f'{ticket.get("key", "")} is missing required intake fields '
                        f'for {validation.issue_type}: {", ".join(required_fields)}.'
                    ),
                    evidence=self._policy_evidence_lines(validation),
                    recommendation=(
                        'Populate the required intake fields before the ticket is '
                        'treated as ready for active project management.'
                    ),
                )
            )

        if warned_fields:
            findings.append(
                DruckerFinding(
                    finding_id='',
                    ticket_key=str(ticket.get('key') or ''),
                    category='missing_recommended_fields',
                    severity='medium',
                    title='Ticket intake policy has missing recommended fields',
                    description=(
                        f'{ticket.get("key", "")} is missing recommended intake fields '
                        f'for {validation.issue_type}: {", ".join(warned_fields)}.'
                    ),
                    evidence=self._policy_evidence_lines(validation),
                    recommendation=(
                        'Add the recommended context fields so routing, prioritization, '
                        'and downstream reporting stay reliable.'
                    ),
                )
            )

        findings.extend(suggestion_findings)

        return findings

    def _build_policy_findings_for_tickets(
        self,
        tickets: List[Dict[str, Any]],
    ) -> List[DruckerFinding]:
        findings: List[DruckerFinding] = []
        for ticket in tickets:
            if ticket.get('is_done'):
                continue
            findings.extend(self._build_policy_findings(ticket))

        for index, finding in enumerate(findings, 1):
            finding.finding_id = f'P{index:03d}'

        return findings

    @staticmethod
    def _covered_hygiene_fields(ticket: Dict[str, Any]) -> set[str]:
        covered: set[str] = set()
        assignee = str(
            ticket.get('assignee_display') or ticket.get('assignee') or ''
        ).strip()

        if assignee in ('', 'Unassigned'):
            covered.add('assignee')
        if not ticket.get('fix_versions'):
            covered.add('fix_versions')
        if not ticket.get('components'):
            covered.add('components')
        if not ticket.get('labels'):
            covered.add('labels')

        return covered

    @staticmethod
    def _policy_evidence_lines(validation: ValidationResult) -> List[str]:
        action_lines = [
            f'{action.get("field", "")}:{action.get("action", "")}'
            for action in validation.actions
            if action.get('field')
        ]
        evidence = [f'issue_type={validation.issue_type}']
        if validation.missing_required:
            evidence.append(
                f'missing_required={", ".join(validation.missing_required)}'
            )
        if validation.missing_warned:
            evidence.append(
                f'missing_warned={", ".join(validation.missing_warned)}'
            )
        if action_lines:
            evidence.append(f'policy_actions={", ".join(action_lines)}')
        return evidence

    def _policy_analysis(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        existing = ticket.get('_drucker_policy')
        if isinstance(existing, dict):
            return existing

        validation = determine_actions(
            validate_ticket(ticket, self.monitor_config),
            self.learning_store if self.monitor_config.learning_enabled else None,
            self.monitor_config,
        )
        covered_fields = self._covered_hygiene_fields(ticket)
        required_fields = [
            field for field in validation.missing_required
            if field not in covered_fields
        ]
        warned_fields = [
            field for field in validation.missing_warned
            if field not in covered_fields
        ]
        suggested_updates, suggestion_findings = self._build_suggested_policy_updates(
            ticket,
            validation,
        )

        policy = {
            'validation': validation,
            'required_fields': required_fields,
            'warned_fields': warned_fields,
            'suggested_updates': suggested_updates,
            'suggestion_findings': suggestion_findings,
        }
        ticket['_drucker_policy'] = policy
        return policy

    def _build_suggested_policy_updates(
        self,
        ticket: Dict[str, Any],
        validation: ValidationResult,
    ) -> tuple[Dict[str, Any], List[DruckerFinding]]:
        suggested_updates: Dict[str, Any] = {}
        findings: List[DruckerFinding] = []
        ticket_key = str(ticket.get('key') or '')

        for action in validation.actions:
            action_name = str(action.get('action') or '')
            if action_name not in {'auto_fill', 'suggest'}:
                continue

            field_name = str(action.get('field') or '')
            value = action.get('value')
            confidence = float(action.get('confidence') or 0.0)
            update_payload = self._field_update_payload(field_name, value)
            if not update_payload:
                continue

            suggested_updates.update(update_payload)
            confidence_label = 'high' if action_name == 'auto_fill' else 'medium'
            value_display = self._format_suggested_value(update_payload)
            findings.append(
                DruckerFinding(
                    finding_id='',
                    ticket_key=ticket_key,
                    category='suggested_field_update',
                    severity=confidence_label,
                    title=f'Drucker suggests a {field_name} update',
                    description=(
                        f'Historical intake patterns suggest {field_name} should be '
                        f'{value_display} for {ticket_key} ({confidence:.0%} confidence).'
                    ),
                    evidence=[
                        f'field={field_name}',
                        f'suggested_value={value_display}',
                        f'confidence={confidence:.2f}',
                        f'issue_type={validation.issue_type}',
                    ],
                    recommendation=(
                        'Review the suggested metadata update and approve it only if '
                        'it matches the intended routing and release plan.'
                    ),
                )
            )

        return suggested_updates, findings

    @staticmethod
    def _field_update_payload(field_name: str, value: Any) -> Dict[str, Any]:
        if value in (None, ''):
            return {}

        normalized_field = str(field_name or '').strip().lower()
        if normalized_field in {'components', 'component'}:
            values = value if isinstance(value, list) else [str(value)]
            cleaned = [str(item).strip() for item in values if str(item).strip()]
            return {'components': cleaned} if cleaned else {}
        if normalized_field in {'fix_versions', 'fix_version'}:
            values = value if isinstance(value, list) else [str(value)]
            cleaned = [str(item).strip() for item in values if str(item).strip()]
            return {'fix_versions': cleaned} if cleaned else {}
        if normalized_field == 'priority':
            priority_value = str(value).strip()
            return {'priority': priority_value} if priority_value else {}

        return {}

    @staticmethod
    def _format_suggested_value(update_payload: Dict[str, Any]) -> str:
        if not update_payload:
            return ''
        key = next(iter(update_payload.keys()))
        value = update_payload[key]
        if isinstance(value, list):
            return ', '.join(str(item) for item in value)
        return str(value)

    def _load_ticket(self, request: DruckerRequest) -> Dict[str, Any]:
        if not request.ticket_key:
            raise ValueError('Drucker ticket hygiene requires ticket_key')

        ticket_key = str(request.ticket_key).strip()
        jql = (
            f'project = "{request.project_key}" AND key = "{ticket_key}" '
            'ORDER BY updated DESC'
        )
        result = search_tickets(
            jql,
            limit=1,
            fields=self.DEFAULT_FIELDS,
        )
        if result.is_error:
            raise RuntimeError(
                result.error or f'Failed to load ticket {ticket_key}'
            )
        tickets = result.data or []
        if not tickets:
            raise RuntimeError(f'Ticket {ticket_key} was not found')

        normalized = self._normalize_ticket(tickets[0], stale_days=request.stale_days)
        self._record_learning_ticket(normalized)
        return normalized

    def _load_recent_tickets(
        self,
        request: DruckerRequest,
    ) -> tuple[str, List[Dict[str, Any]]]:
        since_value = self._resolve_recent_since(request)
        result = search_tickets(
            self._build_recent_jql(request, since_value),
            limit=request.limit,
            fields=self.DEFAULT_FIELDS,
        )
        if result.is_error:
            raise RuntimeError(
                result.error or f'Failed to search recent tickets for {request.project_key}'
            )

        tickets = [
            self._normalize_ticket(ticket, stale_days=request.stale_days)
            for ticket in result.data
        ]
        for ticket in tickets:
            self._record_learning_ticket(ticket)
        tickets = [
            ticket for ticket in tickets
            if not self.monitor_state.is_processed(str(ticket.get('key') or ''))
        ]
        return since_value, tickets

    def _resolve_recent_since(self, request: DruckerRequest) -> str:
        if request.since:
            normalized = self._normalize_since_value(request.since)
            if normalized:
                return normalized

        stored = self.monitor_state.get_last_checked(request.project_key)
        normalized_stored = self._normalize_since_value(stored or '')
        if normalized_stored:
            return normalized_stored

        return self._format_jql_datetime(
            datetime.now(timezone.utc) - timedelta(hours=24)
        )

    def _build_recent_jql(
        self,
        request: DruckerRequest,
        since_value: str,
    ) -> str:
        if request.jql:
            return request.jql

        clauses = [
            f'project = "{request.project_key}"',
            f'created >= "{since_value}"',
        ]
        if not request.include_done:
            clauses.append('statusCategory != Done')
        return ' AND '.join(clauses) + ' ORDER BY created ASC'

    @classmethod
    def _normalize_since_value(cls, value: str) -> Optional[str]:
        parsed = cls._parse_jira_datetime(value)
        if parsed is not None:
            return cls._format_jql_datetime(parsed)

        if not value:
            return None

        for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d'):
            try:
                parsed = datetime.strptime(value, fmt)
                return cls._format_jql_datetime(
                    parsed.replace(tzinfo=timezone.utc)
                )
            except ValueError:
                continue
        return None

    @staticmethod
    def _format_jql_datetime(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M')

    def _attach_policy_analysis(
        self,
        tickets: List[Dict[str, Any]],
    ) -> None:
        for ticket in tickets:
            self._policy_analysis(ticket)

    def _record_learning_ticket(self, ticket: Dict[str, Any]) -> None:
        if not self.monitor_config.learning_enabled:
            return
        self.learning_store.record_ticket(ticket)

    def create_review_session(self, report: DruckerHygieneReport) -> ReviewSession:
        '''
        Convert proposed Drucker actions into a review-gated execution session.
        '''
        request_meta = report.request or {}
        trigger = str(request_meta.get('trigger') or 'interactive').strip() or 'interactive'
        requested_by = str(request_meta.get('requested_by') or '').strip()
        approved_by = str(request_meta.get('approved_by') or '').strip() or None
        correlation_root = str(request_meta.get('correlation_id') or '').strip()

        if not requested_by:
            fallback_actor = 'service_account' if trigger == 'polling' else 'requester'
            requested_by = get_jira_actor_email(fallback_actor)

        session = ReviewSession(
            session_id=report.report_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        ticket_summaries = {
            str(ticket.get('key') or ''): str(ticket.get('summary') or '')
            for ticket in report.tickets
        }

        for action in report.proposed_actions:
            data: Dict[str, Any] = {
                'ticket_key': action.ticket_key,
                'ticket_summary': ticket_summaries.get(action.ticket_key, ''),
                'title': action.title,
                'reason': action.description,
                'finding_ids': action.finding_ids,
                'confidence': action.confidence,
            }

            if action.action_type == 'comment':
                data['body'] = action.comment
            elif action.action_type == 'update':
                data.update(action.update_fields)
            elif action.action_type == 'transition':
                data['to_status'] = action.transition_to
                if action.comment:
                    data['comment'] = action.comment

            session.add_item(ReviewItem(
                id=action.action_id,
                item_type='ticket',
                action=action.action_type,
                data=data,
                trigger=trigger,
                requested_by=requested_by or None,
                approved_by=approved_by,
                correlation_id=(
                    f'{correlation_root}:{action.action_id}'
                    if correlation_root
                    else f'{report.report_id}:{action.action_id}'
                ),
            ))

        return session

    def execute_approved_actions(self, session: ReviewSession) -> List[Dict[str, Any]]:
        '''
        Execute already-approved Drucker actions through the shared ReviewAgent.
        '''
        return self.review_agent.execute_approved(session)

    def _load_project_info(self, project_key: str) -> Dict[str, Any]:
        result = get_project_info(project_key)
        if result.is_success:
            return result.data
        raise RuntimeError(result.error or f'Failed to load project info for {project_key}')

    def _load_tickets(self, request: DruckerRequest) -> List[Dict[str, Any]]:
        result = search_tickets(
            self._build_jql(request),
            limit=request.limit,
            fields=self.DEFAULT_FIELDS,
        )
        if result.is_error:
            raise RuntimeError(
                result.error or f'Failed to search tickets for {request.project_key}'
            )

        tickets = [
            self._normalize_ticket(ticket, stale_days=request.stale_days)
            for ticket in result.data
        ]
        for ticket in tickets:
            self._record_learning_ticket(ticket)
        return tickets

    @staticmethod
    def _build_jql(request: DruckerRequest) -> str:
        if request.jql:
            return request.jql

        clauses = [f'project = "{request.project_key}"']
        if not request.include_done:
            clauses.append('statusCategory != Done')
        return ' AND '.join(clauses) + ' ORDER BY updated ASC'

    def _normalize_ticket(
        self,
        ticket: Dict[str, Any],
        stale_days: int,
    ) -> Dict[str, Any]:
        normalized = dict(ticket)
        updated_dt = self._parse_jira_datetime(str(ticket.get('updated') or ''))
        now = datetime.now(timezone.utc)
        age_days = (now - updated_dt).days if updated_dt else 0
        is_done = self._is_done_status(ticket.get('status', ''))
        is_blocked = self._is_blocked_status(ticket.get('status', ''))
        labels = [
            str(label)
            for label in (ticket.get('labels') or [])
            if str(label).strip()
        ]

        normalized.update({
            'age_days': age_days,
            'is_done': is_done,
            'is_blocked': is_blocked,
            'is_high_priority': self._is_high_priority(ticket.get('priority', '')),
            'is_stale': age_days >= stale_days and not is_done,
            'labels': labels,
            'components': list(ticket.get('components') or []),
            'fix_versions': list(ticket.get('fix_versions') or []),
        })
        return normalized

    def _build_findings(
        self,
        tickets: List[Dict[str, Any]],
        stale_days: int,
    ) -> List[DruckerFinding]:
        findings: List[DruckerFinding] = []
        finding_index = 1

        for ticket in tickets:
            if ticket.get('is_done'):
                continue

            key = str(ticket.get('key') or '')
            priority = str(ticket.get('priority') or '')
            age_days = int(ticket.get('age_days') or 0)
            status = str(ticket.get('status') or '')

            def add_finding(
                category: str,
                severity: str,
                title: str,
                description: str,
                evidence: List[str],
                recommendation: str,
            ) -> None:
                nonlocal finding_index
                findings.append(
                    DruckerFinding(
                        finding_id=f'F{finding_index:03d}',
                        ticket_key=key,
                        category=category,
                        severity=severity,
                        title=title,
                        description=description,
                        evidence=evidence,
                        recommendation=recommendation,
                    )
                )
                finding_index += 1

            if ticket.get('is_stale'):
                severity = 'high' if ticket.get('is_high_priority') else 'medium'
                add_finding(
                    category='stale_ticket',
                    severity=severity,
                    title='Active ticket is stale',
                    description=(
                        f'{key} has not been updated in {age_days} days and may need triage or owner confirmation.'
                    ),
                    evidence=[
                        f'status={status}',
                        f'priority={priority}',
                        f'updated={ticket.get("updated_date", "")}',
                    ],
                    recommendation='Confirm the current owner, status, and next action for this ticket.',
                )

            if ticket.get('is_blocked') and age_days >= min(stale_days, 14):
                add_finding(
                    category='blocked_stale_ticket',
                    severity='high',
                    title='Blocked ticket has gone stale',
                    description=(
                        f'{key} is blocked and has not moved in {age_days} days.'
                    ),
                    evidence=[
                        f'status={status}',
                        f'updated={ticket.get("updated_date", "")}',
                    ],
                    recommendation='Escalate or clarify the blocker before the ticket remains blocked indefinitely.',
                )

            if str(ticket.get('assignee_display') or ticket.get('assignee') or '').strip() in ('', 'Unassigned'):
                add_finding(
                    category='unassigned_ticket',
                    severity='high' if ticket.get('is_high_priority') else 'medium',
                    title='Active ticket has no assignee',
                    description=f'{key} is active work without a clear owner.',
                    evidence=[
                        f'priority={priority}',
                        f'status={status}',
                    ],
                    recommendation='Assign an owner or explicitly de-scope the ticket from active work.',
                )

            if not ticket.get('fix_versions'):
                add_finding(
                    category='missing_fix_version',
                    severity='high' if ticket.get('is_high_priority') else 'medium',
                    title='Active ticket has no release target',
                    description=f'{key} has no fix version or release target assigned.',
                    evidence=[
                        f'priority={priority}',
                        f'labels={", ".join(ticket.get("labels", [])) or "none"}',
                    ],
                    recommendation='Either assign a target release or explicitly classify the ticket as unscheduled backlog.',
                )

            if not ticket.get('components'):
                add_finding(
                    category='missing_component',
                    severity='medium',
                    title='Ticket is missing component metadata',
                    description=f'{key} has no Jira component set.',
                    evidence=[
                        f'issue_type={ticket.get("issue_type", "")}',
                    ],
                    recommendation='Add a component so routing, ownership, and reporting are more reliable.',
                )

            if not ticket.get('labels'):
                add_finding(
                    category='missing_labels',
                    severity='low',
                    title='Ticket has no labels',
                    description=f'{key} has no Jira labels for triage or reporting.',
                    evidence=[
                        f'issue_type={ticket.get("issue_type", "")}',
                        f'components={", ".join(ticket.get("components", [])) or "none"}',
                    ],
                    recommendation='Add at least one durable label to help filtering and triage.',
                )

        return findings

    def _build_actions(
        self,
        tickets: List[Dict[str, Any]],
        findings: List[DruckerFinding],
        label_prefix: str,
    ) -> List[DruckerAction]:
        actions: List[DruckerAction] = []
        findings_by_ticket: Dict[str, List[DruckerFinding]] = defaultdict(list)
        tickets_by_key = {
            str(ticket.get('key') or ''): ticket
            for ticket in tickets
        }

        for finding in findings:
            findings_by_ticket[finding.ticket_key].append(finding)

        action_index = 1
        for ticket_key in sorted(findings_by_ticket):
            ticket_findings = findings_by_ticket[ticket_key]
            ticket = tickets_by_key.get(ticket_key, {})
            existing_labels = {
                str(label).strip()
                for label in (ticket.get('labels') or [])
                if str(label).strip()
            }

            derived_labels = {
                f'{label_prefix}-{self.CATEGORY_LABELS[finding.category]}'
                for finding in ticket_findings
                if finding.category in self.CATEGORY_LABELS
            }
            merged_labels = sorted(existing_labels | derived_labels)
            policy = self._policy_analysis(ticket)
            suggested_updates = dict(policy.get('suggested_updates') or {})

            if merged_labels != sorted(existing_labels):
                update_action = DruckerAction(
                    action_id=f'D{action_index:03d}',
                    ticket_key=ticket_key,
                    action_type='update',
                    title='Apply Drucker hygiene labels',
                    description='Add Jira labels that reflect the hygiene issues detected for this ticket.',
                    finding_ids=[finding.finding_id for finding in ticket_findings],
                    confidence='high',
                    update_fields={'labels': merged_labels},
                )
                actions.append(update_action)
                for finding in ticket_findings:
                    finding.action_ids.append(update_action.action_id)
                action_index += 1

            if suggested_updates:
                suggested_field_names = ', '.join(sorted(suggested_updates.keys()))
                suggestion_action = DruckerAction(
                    action_id=f'D{action_index:03d}',
                    ticket_key=ticket_key,
                    action_type='update',
                    title='Apply Drucker suggested metadata updates',
                    description=(
                        'Apply review-gated metadata suggestions derived from '
                        'historical intake patterns.'
                    ),
                    finding_ids=[
                        finding.finding_id for finding in ticket_findings
                        if finding.category == 'suggested_field_update'
                    ],
                    confidence='medium',
                    update_fields=suggested_updates,
                )
                actions.append(suggestion_action)
                for finding in ticket_findings:
                    if finding.category == 'suggested_field_update':
                        finding.action_ids.append(suggestion_action.action_id)
                action_index += 1

            comment_action = DruckerAction(
                action_id=f'D{action_index:03d}',
                ticket_key=ticket_key,
                action_type='comment',
                title='Post Drucker hygiene summary',
                description='Add a Jira comment summarizing the hygiene issues and recommended follow-up.',
                finding_ids=[finding.finding_id for finding in ticket_findings],
                confidence='medium',
                comment=self._build_comment(
                    ticket,
                    ticket_findings,
                    suggested_updates=suggested_updates,
                ),
            )
            actions.append(comment_action)
            for finding in ticket_findings:
                finding.action_ids.append(comment_action.action_id)
            action_index += 1

        return actions

    def _build_summary(
        self,
        tickets: List[Dict[str, Any]],
        findings: List[DruckerFinding],
        actions: List[DruckerAction],
    ) -> Dict[str, Any]:
        category_counts = Counter(finding.category for finding in findings)
        severity_counts = Counter(finding.severity for finding in findings)
        open_tickets = sum(1 for ticket in tickets if not ticket.get('is_done'))
        tickets_with_findings = sorted({finding.ticket_key for finding in findings})

        return {
            'total_tickets': len(tickets),
            'open_tickets': open_tickets,
            'finding_count': len(findings),
            'action_count': len(actions),
            'tickets_with_findings': len(tickets_with_findings),
            'by_category': dict(category_counts),
            'by_severity': dict(severity_counts),
            'ticket_keys_with_findings': tickets_with_findings,
        }

    def _build_comment(
        self,
        ticket: Dict[str, Any],
        findings: List[DruckerFinding],
        suggested_updates: Optional[Dict[str, Any]] = None,
    ) -> str:
        comment_text = JiraCommentNotifier.build_hygiene_comment(
            ticket=ticket,
            findings=findings,
            suggested_updates=suggested_updates,
        )
        return (
            f'{comment_text}\n\n'
            f'Summary: {len(findings)} hygiene issue(s) identified for review.'
        )

    def _format_report(self, report: DruckerHygieneReport) -> str:
        summary = report.summary
        findings_by_ticket: Dict[str, List[DruckerFinding]] = defaultdict(list)
        for finding in report.findings:
            findings_by_ticket[finding.ticket_key].append(finding)

        lines = [
            f'# DRUCKER HYGIENE REPORT: {report.project_key}',
            '',
            f'**Report ID**: {report.report_id}',
            f'**Created At**: {report.created_at}',
            '',
            '## Project Summary',
            '',
            f"- Project: {report.project_info.get('name', report.project_key)}",
            f"- Total tickets analyzed: {summary.get('total_tickets', 0)}",
            f"- Open tickets analyzed: {summary.get('open_tickets', 0)}",
            f"- Tickets with findings: {summary.get('tickets_with_findings', 0)}",
            f"- Findings: {summary.get('finding_count', 0)}",
            f"- Proposed actions: {summary.get('action_count', 0)}",
            '',
            '## Severity Breakdown',
            '',
        ]

        severity_counts = summary.get('by_severity', {})
        for severity in ('high', 'medium', 'low'):
            lines.append(f"- {severity.title()}: {int(severity_counts.get(severity, 0) or 0)}")

        lines.extend([
            '',
            '## Finding Categories',
            '',
        ])
        for category, count in sorted((summary.get('by_category') or {}).items()):
            lines.append(f'- {category}: {count}')

        lines.extend([
            '',
            '## Ticket Remediation Suggestions',
            '',
        ])

        if findings_by_ticket:
            tickets_by_key = {
                str(ticket.get('key') or ''): ticket
                for ticket in report.tickets
            }
            for ticket_key in sorted(findings_by_ticket):
                ticket = tickets_by_key.get(ticket_key, {})
                lines.append(
                    f"- **{ticket_key}** {ticket.get('summary', '')}".rstrip()
                )
                for finding in findings_by_ticket[ticket_key]:
                    lines.append(
                        f"  [{finding.severity.upper()}] {finding.title}: {finding.recommendation}"
                    )
        else:
            lines.append('- No hygiene issues were detected for the current Jira scope.')

        lines.extend([
            '',
            '## Proposed Jira Actions',
            '',
        ])

        if report.proposed_actions:
            for action in report.proposed_actions:
                lines.append(
                    f"- [{action.action_type.upper()}] {action.ticket_key}: {action.title}"
                )
                if action.action_type == 'update' and action.update_fields.get('labels'):
                    lines.append(
                        f"  Labels: {', '.join(action.update_fields['labels'])}"
                    )
                if action.action_type == 'update':
                    if action.update_fields.get('components'):
                        lines.append(
                            '  Components: '
                            f"{', '.join(action.update_fields['components'])}"
                        )
                    if action.update_fields.get('fix_versions'):
                        lines.append(
                            '  Fix Versions: '
                            f"{', '.join(action.update_fields['fix_versions'])}"
                        )
                    if action.update_fields.get('priority'):
                        lines.append(
                            f"  Priority: {action.update_fields['priority']}"
                        )
        else:
            lines.append('- No Jira write-back actions proposed.')

        if report.errors:
            lines.extend([
                '',
                '## Errors',
                '',
            ])
            for error in report.errors:
                lines.append(f'- {error}')

        return '\n'.join(lines)

    @staticmethod
    def _parse_jira_datetime(value: str) -> Optional[datetime]:
        if not value:
            return None

        formats = [
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d',
        ]
        for fmt in formats:
            try:
                parsed = datetime.strptime(value, fmt)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                continue
        return None

    @staticmethod
    def _is_done_status(status: str) -> bool:
        return str(status).casefold() in {'done', 'closed', 'resolved'}

    @staticmethod
    def _is_blocked_status(status: str) -> bool:
        normalized = str(status).casefold()
        return any(token in normalized for token in ('blocked', 'on hold', 'impeded'))

    @staticmethod
    def _is_high_priority(priority: str) -> bool:
        normalized = str(priority).casefold()
        return any(
            token in normalized
            for token in ('blocker', 'critical', 'highest', 'high', 'p0', 'p1')
        )
