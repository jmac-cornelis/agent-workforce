from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.env_loader import load_env

load_env()

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from agents.drucker.agent import DruckerCoordinatorAgent
from agents.drucker.models import DruckerRequest
from agents.drucker.state.report_store import DruckerReportStore
from agents.drucker.state.activity_counter import ActivityCounter

log = logging.getLogger(os.path.basename(sys.argv[0]))

store = DruckerReportStore()
activity = ActivityCounter()


class HygieneRunRequest(BaseModel):
    project_key: str
    limit: int = 200
    stale_days: int = 30
    include_done: bool = False
    jql: Optional[str] = None
    label_prefix: str = 'drucker'


class DruckerPollerTickRequest(BaseModel):
    project_key: Optional[str] = None
    limit: int = 200
    stale_days: int = 30
    include_done: bool = False
    jql: Optional[str] = None
    since: Optional[str] = None
    recent_only: bool = False
    label_prefix: str = 'drucker'
    persist: bool = True
    notify_shannon: bool = False
    shannon_base_url: Optional[str] = None
    config_path: Optional[str] = None
    job_name: Optional[str] = None
    github_repos: Optional[List[str]] = None
    github_stale_days: int = 5


class IssueCheckRequest(BaseModel):
    project_key: str
    ticket_key: str
    stale_days: int = 30
    label_prefix: str = 'drucker'
    persist: bool = True


class IntakeRunRequest(BaseModel):
    project_key: str
    limit: int = 200
    stale_days: int = 30
    since: Optional[str] = None
    label_prefix: str = 'drucker'
    persist: bool = True


class BugActivityRequest(BaseModel):
    project_key: str = 'STL'
    target_date: Optional[str] = None


class PRHygieneRequest(BaseModel):
    repo: str
    stale_days: int = 5


class PRStaleRequest(BaseModel):
    repo: str
    stale_days: int = 5


class PRReviewsRequest(BaseModel):
    repo: str


class NamingComplianceRequest(BaseModel):
    repo: str
    ticket_patterns: Optional[str] = None


class MergeConflictsRequest(BaseModel):
    repo: str


class CIFailuresRequest(BaseModel):
    repo: str


class StaleBranchesRequest(BaseModel):
    repo: str
    stale_days: int = 30


class ExtendedHygieneRequest(BaseModel):
    repo: str
    stale_days: int = 5
    branch_stale_days: int = 30


class PRReminderSnoozeRequest(BaseModel):
    repo: str
    pr_number: int
    snooze_days: int
    snoozed_by: str


class PRReminderMergeRequest(BaseModel):
    repo: str
    pr_number: int
    merge_method: str = 'squash'
    requested_by: str = ''
    dry_run: Optional[bool] = None


class JiraQueryRequest(BaseModel):
    project_key: str = 'STL'
    jql: str
    limit: int = 100


class JiraTicketsRequest(BaseModel):
    project_key: str = 'STL'
    issue_types: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    exclude_statuses: Optional[List[str]] = None
    date_filter: Optional[str] = None
    limit: int = 100


class JiraReleaseStatusRequest(BaseModel):
    project_key: str = 'STL'
    releases: List[str]
    issue_types: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    limit: int = 500


class JiraTicketCountsRequest(BaseModel):
    project_key: str = 'STL'
    issue_types: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    date_filter: Optional[str] = None


class JiraStatusReportRequest(BaseModel):
    project_key: str = 'STL'
    include_bugs: bool = True
    include_activity: bool = True
    recent_days: int = 7


class NLQueryRequest(BaseModel):
    query: str
    project_key: str = 'STL'


def create_app() -> FastAPI:
    app = FastAPI(title='Drucker Agent API', version='1.3.0')

    @app.get('/v1/health')
    def health() -> Dict[str, Any]:
        return {'service': 'drucker', 'ok': True}

    @app.get('/v1/info')
    def info() -> Dict[str, Any]:
        return {
            'agent_id': 'drucker',
            'name': 'Drucker Engineering Hygiene Agent',
            'version': '1.3.0',
            'description': (
                'Deterministic engineering hygiene analysis for Jira ticket quality '
                'and GitHub PR lifecycle. Zero LLM token usage.'
            ),
            'capabilities': [
                'Jira project-wide hygiene analysis (stale tickets, missing fields, label compliance)',
                'Single-ticket intake validation',
                'Recent ticket intake reports',
                'GitHub PR hygiene (stale PRs, missing reviews, naming compliance)',
                'GitHub CI failure and merge conflict detection',
                'Stale branch analysis',
                'Bug activity reporting',
                'PR reminder DMs with snooze and merge actions via Teams',
                'Jira JQL query execution with ticket normalization',
                'Jira ticket search with status/type/date filters',
                'Jira release status reporting across multiple versions',
                'Jira ticket count aggregation',
                'Jira project status reports with bug and activity breakdowns',
                'Natural language query translation via LLM function calling',
            ],
            'endpoints': [
                {'method': 'GET', 'path': '/v1/health', 'description': 'Service liveness check'},
                {'method': 'GET', 'path': '/v1/info', 'description': 'Agent identity and capabilities'},
                {'method': 'GET', 'path': '/v1/status/stats', 'description': 'Report counts and finding totals'},
                {'method': 'GET', 'path': '/v1/status/load', 'description': 'Current load state'},
                {'method': 'GET', 'path': '/v1/status/work-summary', 'description': 'Reports generated today'},
                {'method': 'GET', 'path': '/v1/status/tokens', 'description': 'Token usage (always zero)'},
                {'method': 'GET', 'path': '/v1/status/decisions', 'description': 'Recent hygiene reports'},
                {'method': 'GET', 'path': '/v1/status/decisions/{record_id}', 'description': 'Detail for one report'},
                {'method': 'POST', 'path': '/v1/hygiene/run', 'description': 'Run project-wide hygiene analysis'},
                {'method': 'POST', 'path': '/v1/hygiene/issue', 'description': 'Run single-ticket intake validation'},
                {'method': 'POST', 'path': '/v1/hygiene/intake', 'description': 'Run recent ticket intake report'},
                {'method': 'GET', 'path': '/v1/hygiene/reports', 'description': 'List stored hygiene reports'},
                {'method': 'GET', 'path': '/v1/hygiene/report/{report_id}', 'description': 'Get a specific report'},
                {'method': 'POST', 'path': '/v1/activity/bugs', 'description': 'Bug activity report for a date'},
                {'method': 'POST', 'path': '/v1/github/pr-hygiene', 'description': 'Full PR hygiene scan'},
                {'method': 'POST', 'path': '/v1/github/pr-stale', 'description': 'Find stale PRs'},
                {'method': 'POST', 'path': '/v1/github/pr-reviews', 'description': 'Find PRs missing code review'},
                {'method': 'GET', 'path': '/v1/github/prs/{owner}/{repo}', 'description': 'List PRs for a repo'},
                {'method': 'POST', 'path': '/v1/github/naming-compliance', 'description': 'Check branch/PR naming'},
                {'method': 'POST', 'path': '/v1/github/merge-conflicts', 'description': 'Find PRs with merge conflicts'},
                {'method': 'POST', 'path': '/v1/github/ci-failures', 'description': 'Find PRs with failing CI'},
                {'method': 'POST', 'path': '/v1/github/stale-branches', 'description': 'Find stale branches'},
                {'method': 'POST', 'path': '/v1/github/extended-hygiene', 'description': 'Comprehensive hygiene scan'},
                {'method': 'POST', 'path': '/v1/poller/tick', 'description': 'Scheduled poller entrypoint'},
                {'method': 'POST', 'path': '/v1/github/pr-reminders/scan', 'description': 'Scan repos and track open PRs'},
                {'method': 'POST', 'path': '/v1/github/pr-reminders/process', 'description': 'Send due PR reminder DMs'},
                {'method': 'GET', 'path': '/v1/github/pr-reminders/active', 'description': 'List active PR reminders'},
                {'method': 'GET', 'path': '/v1/github/pr-reminders/history', 'description': 'PR reminder action history'},
                {'method': 'POST', 'path': '/v1/github/pr-reminders/snooze', 'description': 'Snooze PR reminders'},
                {'method': 'POST', 'path': '/v1/github/pr-reminders/merge', 'description': 'Merge a PR (dry-run default)'},
                {'method': 'POST', 'path': '/v1/jira/query', 'description': 'Run arbitrary JQL query'},
                {'method': 'POST', 'path': '/v1/jira/tickets', 'description': 'Query tickets with filters'},
                {'method': 'POST', 'path': '/v1/jira/release-status', 'description': 'Release status across versions'},
                {'method': 'POST', 'path': '/v1/jira/ticket-counts', 'description': 'Get ticket count aggregations'},
                {'method': 'POST', 'path': '/v1/jira/status-report', 'description': 'Project status report with breakdowns'},
                {'method': 'POST', 'path': '/v1/nl/query', 'description': 'Translate plain English to Jira/GitHub queries'},
            ],
            'shannon_commands': [
                {'command': '/issue-check', 'description': 'Run intake validation for one Jira ticket'},
                {'command': '/intake-report', 'description': 'Run a recent-ticket intake report'},
                {'command': '/hygiene-run', 'description': 'Run project-wide hygiene analysis'},
                {'command': '/hygiene-report', 'description': 'Get a stored report'},
                {'command': '/hygiene-list', 'description': 'List stored reports'},
                {'command': '/bug-activity', 'description': 'Bug ticket activity today'},
                {'command': '/pr-hygiene', 'description': 'Full PR hygiene scan'},
                {'command': '/pr-stale', 'description': 'Find stale PRs'},
                {'command': '/pr-reviews', 'description': 'Find PRs missing code review'},
                {'command': '/pr-list', 'description': 'List open PRs for a repository'},
                {'command': '/naming-compliance', 'description': 'Check branch/PR naming compliance'},
                {'command': '/merge-conflicts', 'description': 'Find PRs with merge conflicts'},
                {'command': '/ci-failures', 'description': 'Find PRs with failing CI checks'},
                {'command': '/stale-branches', 'description': 'Find stale branches'},
                {'command': '/extended-hygiene', 'description': 'Run comprehensive extended hygiene analysis'},
                {'command': '/pr-reminder-scan', 'description': 'Scan repos and schedule PR reminders'},
                {'command': '/pr-reminder-process', 'description': 'Send due PR reminder DMs'},
                {'command': '/pr-reminder-active', 'description': 'List active PR reminders'},
                {'command': '/pr-reminder-history', 'description': 'PR reminder action history'},
                {'command': '/pr-reminder-snooze', 'description': 'Snooze a PR reminder'},
                {'command': '/pr-reminder-merge', 'description': 'Merge a PR via reminder'},
                {'command': '/ask', 'description': 'Ask Drucker a question in plain English'},
            ],
        }

    @app.get('/v1/status/stats')
    def status_stats() -> Dict[str, Any]:
        reports = store.list_reports(limit=100)
        total_findings = sum(int(r.get('finding_count', 0)) for r in reports)
        totals = activity.get_totals()
        breakdown = activity.get_all()

        pr_state = None
        try:
            from agents.drucker.pr_reminders import PRReminderEngine
            engine = PRReminderEngine()
            pr_active = engine._state.list_active(limit=1000)
            pr_state = {'tracked_prs': len(pr_active)}
        except Exception:
            pass

        return {
            'ok': True,
            'data': {
                'total_requests': totals['total_requests'],
                'total_errors': totals['total_errors'],
                'first_request_at': totals['first_request_at'],
                'last_request_at': totals['last_request_at'],
                'hygiene_reports': len(reports),
                'hygiene_findings': total_findings,
                'pr_reminders': pr_state,
                'by_category': breakdown,
            },
        }

    @app.get('/v1/status/load')
    def status_load() -> Dict[str, Any]:
        totals = activity.get_totals()
        return {
            'ok': True,
            'data': {
                'state': 'idle',
                'total_requests': totals['total_requests'],
                'last_request_at': totals['last_request_at'],
            },
        }

    @app.get('/v1/status/work-summary')
    def status_work_summary() -> Dict[str, Any]:
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        reports = store.list_reports(limit=50)
        today_reports = [
            r for r in reports
            if str(r.get('created_at', '')).startswith(today)
        ]
        totals = activity.get_totals()
        return {
            'ok': True,
            'data': {
                'reports_today': len(today_reports),
                'findings_today': sum(int(r.get('finding_count', 0)) for r in today_reports),
                'total_requests': totals['total_requests'],
                'last_request_at': totals['last_request_at'] or 'none',
            },
        }

    @app.get('/v1/status/tokens')
    def status_tokens() -> Dict[str, Any]:
        breakdown = activity.get_all()
        nl_count = breakdown.get('nl', {}).get('request_count', 0)
        return {
            'ok': True,
            'data': {
                'llm_enabled': nl_count > 0,
                'nl_queries_served': nl_count,
                'notes': 'LLM used only for /ask NL query translation. All other endpoints are deterministic.',
            },
        }

    @app.get('/v1/status/decisions')
    def status_decisions(
        limit: int = Query(default=10, ge=1, le=100),
    ) -> Dict[str, Any]:
        reports = store.list_reports(limit=limit)
        decisions = []
        for r in reports:
            decisions.append({
                'record_id': r.get('report_id', ''),
                'project_key': r.get('project_key', ''),
                'created_at': r.get('created_at', ''),
                'finding_count': r.get('finding_count', 0),
                'action_count': r.get('action_count', 0),
            })
        return {'ok': True, 'data': decisions}

    @app.get('/v1/status/decisions/{record_id}')
    def status_decision_detail(record_id: str) -> Dict[str, Any]:
        result = store.get_report(record_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f'Report {record_id} not found')
        report = result.get('report', {})
        return {
            'ok': True,
            'data': {
                'report_id': report.get('report_id', ''),
                'project_key': report.get('project_key', ''),
                'created_at': report.get('created_at', ''),
                'summary': report.get('summary', {}),
                'finding_count': len(report.get('findings', [])),
                'action_count': len(report.get('proposed_actions', [])),
            },
        }

    @app.post('/v1/hygiene/run')
    def hygiene_run(body: HygieneRunRequest) -> Dict[str, Any]:
        agent = DruckerCoordinatorAgent(project_key=body.project_key)
        request = DruckerRequest(
            project_key=body.project_key,
            limit=body.limit,
            stale_days=body.stale_days,
            include_done=body.include_done,
            jql=body.jql,
            label_prefix=body.label_prefix,
        )

        try:
            report = agent.analyze_project_hygiene(request)
        except Exception as e:
            log.error(f'Drucker hygiene run failed: {e}')
            activity.record('hygiene', is_error=True)
            return {'ok': False, 'error': str(e)}

        save_result = store.save_report(report)
        activity.record('hygiene')

        return {
            'ok': True,
            'data': {
                'report_id': report.report_id,
                'project_key': report.project_key,
                'created_at': report.created_at,
                'summary': report.summary,
                'finding_count': len(report.findings),
                'action_count': len(report.proposed_actions),
                'storage': save_result,
            },
        }

    @app.post('/v1/hygiene/issue')
    def hygiene_issue(body: IssueCheckRequest) -> Dict[str, Any]:
        agent = DruckerCoordinatorAgent(project_key=body.project_key)
        request = DruckerRequest(
            project_key=body.project_key,
            ticket_key=body.ticket_key,
            stale_days=body.stale_days,
            label_prefix=body.label_prefix,
        )

        try:
            report = agent.analyze_ticket_hygiene(request)
            review_session = agent.create_review_session(report)
        except Exception as e:
            log.error(f'Drucker issue check failed: {e}')
            activity.record('hygiene', is_error=True)
            return {'ok': False, 'error': str(e)}

        save_result = None
        if body.persist:
            save_result = store.save_report(report)
        activity.record('hygiene')

        return {
            'ok': True,
            'data': {
                'report': report.to_dict(),
                'review_session': review_session.to_dict(),
                'stored': save_result,
            },
        }

    @app.post('/v1/hygiene/intake')
    def hygiene_intake(body: IntakeRunRequest) -> Dict[str, Any]:
        agent = DruckerCoordinatorAgent(project_key=body.project_key)
        request = DruckerRequest(
            project_key=body.project_key,
            limit=body.limit,
            stale_days=body.stale_days,
            since=body.since,
            recent_only=True,
            label_prefix=body.label_prefix,
        )

        try:
            report = agent.analyze_recent_ticket_intake(request)
            review_session = agent.create_review_session(report)
        except Exception as e:
            log.error(f'Drucker intake report failed: {e}')
            activity.record('hygiene', is_error=True)
            return {'ok': False, 'error': str(e)}

        save_result = None
        if body.persist:
            save_result = store.save_report(report)
        activity.record('hygiene')

        return {
            'ok': True,
            'data': {
                'report': report.to_dict(),
                'review_session': review_session.to_dict(),
                'stored': save_result,
            },
        }

    @app.post('/v1/poller/tick')
    def poller_tick(body: DruckerPollerTickRequest) -> Dict[str, Any]:
        agent = DruckerCoordinatorAgent(project_key=body.project_key)
        spec = {
            'project_key': body.project_key,
            'limit': body.limit,
            'stale_days': body.stale_days,
            'include_done': body.include_done,
            'jql': body.jql,
            'since': body.since,
            'recent_only': body.recent_only,
            'label_prefix': body.label_prefix,
            'persist': body.persist,
            'notify_shannon': body.notify_shannon,
            'shannon_base_url': body.shannon_base_url,
            'config_path': body.config_path,
            'job_name': body.job_name,
        }
        if body.github_repos:
            spec['github_repos'] = body.github_repos
            spec['github_stale_days'] = body.github_stale_days
        result = agent.tick(spec)
        activity.record('poller')
        return {'ok': result.get('ok', False), 'data': result}

    @app.get('/v1/hygiene/report/{report_id}')
    def hygiene_report(
        report_id: str,
        project_key: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        result = store.get_report(report_id, project_key=project_key)
        if result is None:
            raise HTTPException(status_code=404, detail=f'Report {report_id} not found')
        return {'ok': True, 'data': result}

    @app.get('/v1/hygiene/reports')
    def hygiene_reports(
        project_key: Optional[str] = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> Dict[str, Any]:
        reports = store.list_reports(project_key=project_key, limit=limit)
        return {'ok': True, 'data': reports}

    @app.post('/v1/activity/bugs')
    def activity_bugs(
        body: Optional[BugActivityRequest] = None,
        project_key: Optional[str] = Query(default=None),
        target_date: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        pk = (body.project_key if body and body.project_key else None) or project_key or 'STL'
        td = (body.target_date if body and body.target_date else None) or target_date
        try:
            agent = DruckerCoordinatorAgent(project_key=pk)
            result = agent.analyze_bug_activity(
                project_key=pk,
                target_date=td,
            )
            activity.record('jira')
            return {'ok': True, 'data': result}
        except Exception as e:
            log.error(f'Bug activity report failed: {e}')
            activity.record('jira', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/pr-hygiene')
    def github_pr_hygiene(body: PRHygieneRequest) -> Dict[str, Any]:
        try:
            import github_utils
            report = github_utils.analyze_repo_pr_hygiene(
                body.repo,
                stale_days=body.stale_days,
            )
            activity.record('github')
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub PR hygiene scan failed: {e}')
            activity.record('github', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/pr-stale')
    def github_pr_stale(body: PRStaleRequest) -> Dict[str, Any]:
        try:
            import github_utils
            stale = github_utils.analyze_pr_staleness(
                body.repo,
                stale_days=body.stale_days,
            )
            activity.record('github')
            return {
                'ok': True,
                'data': {
                    'repo': body.repo,
                    'stale_days': body.stale_days,
                    'stale_prs': stale,
                    'total_findings': len(stale),
                },
            }
        except Exception as e:
            log.error(f'GitHub stale PR scan failed: {e}')
            activity.record('github', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/pr-reviews')
    def github_pr_reviews(body: PRReviewsRequest) -> Dict[str, Any]:
        try:
            import github_utils
            findings = github_utils.analyze_missing_reviews(body.repo)
            activity.record('github')
            return {
                'ok': True,
                'data': {
                    'repo': body.repo,
                    'missing_reviews': findings,
                    'total_findings': len(findings),
                },
            }
        except Exception as e:
            log.error(f'GitHub missing reviews scan failed: {e}')
            activity.record('github', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.get('/v1/github/prs/{owner}/{repo}')
    def github_pr_list(
        owner: str,
        repo: str,
        state: str = Query(default='open', regex='^(open|closed|all)$'),
        limit: int = Query(default=50, ge=1, le=500),
    ) -> Dict[str, Any]:
        repo_name = f'{owner}/{repo}'
        try:
            import github_utils
            prs = github_utils.list_pull_requests(
                repo_name,
                state=state,
                limit=limit,
            )
            activity.record('github')
            return {
                'ok': True,
                'data': {
                    'repo': repo_name,
                    'state': state,
                    'prs': prs,
                    'total': len(prs),
                },
            }
        except Exception as e:
            log.error(f'GitHub PR list failed: {e}')
            activity.record('github', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/naming-compliance')
    def github_naming_compliance(body: NamingComplianceRequest) -> Dict[str, Any]:
        try:
            import github_utils
            report = github_utils.analyze_naming_compliance(
                body.repo,
                ticket_patterns=body.ticket_patterns,
            )
            activity.record('github')
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub naming compliance scan failed: {e}')
            activity.record('github', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/merge-conflicts')
    def github_merge_conflicts(body: MergeConflictsRequest) -> Dict[str, Any]:
        try:
            import github_utils
            report = github_utils.analyze_merge_conflicts(body.repo)
            activity.record('github')
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub merge conflicts scan failed: {e}')
            activity.record('github', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/ci-failures')
    def github_ci_failures(body: CIFailuresRequest) -> Dict[str, Any]:
        try:
            import github_utils
            report = github_utils.analyze_ci_failures(body.repo)
            activity.record('github')
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub CI failures scan failed: {e}')
            activity.record('github', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/stale-branches')
    def github_stale_branches(body: StaleBranchesRequest) -> Dict[str, Any]:
        try:
            import github_utils
            report = github_utils.analyze_stale_branches(
                body.repo,
                stale_days=body.stale_days,
            )
            activity.record('github')
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub stale branches scan failed: {e}')
            activity.record('github', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/extended-hygiene')
    def github_extended_hygiene(body: ExtendedHygieneRequest) -> Dict[str, Any]:
        try:
            import github_utils
            report = github_utils.analyze_extended_hygiene(
                body.repo,
                stale_days=body.stale_days,
                branch_stale_days=body.branch_stale_days,
            )
            activity.record('github')
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub extended hygiene scan failed: {e}')
            activity.record('github', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/pr-reminders/scan')
    def pr_reminders_scan() -> Dict[str, Any]:
        try:
            from agents.drucker.pr_reminders import PRReminderEngine
            engine = PRReminderEngine()
            result = engine.scan_repos()
            activity.record('pr-reminders')
            return {'ok': True, 'data': result}
        except Exception as e:
            log.error(f'PR reminder scan failed: {e}')
            activity.record('pr-reminders', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/pr-reminders/process')
    def pr_reminders_process() -> Dict[str, Any]:
        try:
            from agents.drucker.pr_reminders import PRReminderEngine
            engine = PRReminderEngine()
            result = engine.process_due_reminders()
            activity.record('pr-reminders')
            return {'ok': True, 'data': result}
        except Exception as e:
            log.error(f'PR reminder processing failed: {e}')
            activity.record('pr-reminders', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.get('/v1/github/pr-reminders/active')
    def pr_reminders_active(
        repo: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=500),
    ) -> Dict[str, Any]:
        try:
            from agents.drucker.pr_reminders import PRReminderEngine
            engine = PRReminderEngine()
            active = engine._state.list_active(repo=repo, limit=limit)
            return {'ok': True, 'data': {'prs': active, 'total': len(active)}}
        except Exception as e:
            log.error(f'PR reminder active list failed: {e}')
            return {'ok': False, 'error': str(e)}

    @app.get('/v1/github/pr-reminders/history')
    def pr_reminders_history(
        repo: Optional[str] = Query(default=None),
        pr_number: Optional[int] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=500),
    ) -> Dict[str, Any]:
        try:
            from agents.drucker.pr_reminders import PRReminderEngine
            engine = PRReminderEngine()
            history = engine._state.get_history(
                repo=repo, pr_number=pr_number, limit=limit,
            )
            return {'ok': True, 'data': {'entries': history, 'total': len(history)}}
        except Exception as e:
            log.error(f'PR reminder history query failed: {e}')
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/pr-reminders/snooze')
    def pr_reminders_snooze(body: PRReminderSnoozeRequest) -> Dict[str, Any]:
        try:
            from agents.drucker.pr_reminders import PRReminderEngine
            engine = PRReminderEngine()
            result = engine.handle_snooze(
                repo=body.repo,
                pr_number=body.pr_number,
                snooze_days=body.snooze_days,
                snoozed_by=body.snoozed_by,
            )
            activity.record('pr-reminders')
            return {'ok': True, 'data': result}
        except Exception as e:
            log.error(f'PR reminder snooze failed: {e}')
            activity.record('pr-reminders', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/pr-reminders/merge')
    def pr_reminders_merge(body: PRReminderMergeRequest) -> Dict[str, Any]:
        from config.env_loader import resolve_dry_run
        is_dry_run = resolve_dry_run(body.dry_run)
        try:
            from agents.drucker.pr_reminders import PRReminderEngine
            engine = PRReminderEngine()
            result = engine.handle_merge_request(
                repo=body.repo,
                pr_number=body.pr_number,
                merge_method=body.merge_method,
                requested_by=body.requested_by,
                dry_run=is_dry_run,
            )
            activity.record('pr-reminders')
            return {'ok': result.get('ok', False), 'data': result}
        except Exception as e:
            log.error(f'PR reminder merge failed: {e}')
            activity.record('pr-reminders', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/jira/query')
    def jira_query(body: JiraQueryRequest) -> Dict[str, Any]:
        try:
            from agents.drucker.jira_reporting import query_jql
            result = query_jql(jql=body.jql, project_key=body.project_key, limit=body.limit)
            activity.record('jira')
            return {'ok': True, 'data': result}
        except Exception as e:
            log.error(f'Jira query failed: {e}')
            activity.record('jira', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/jira/tickets')
    def jira_tickets(body: JiraTicketsRequest) -> Dict[str, Any]:
        try:
            from agents.drucker.jira_reporting import query_tickets
            result = query_tickets(
                project_key=body.project_key,
                issue_types=body.issue_types,
                statuses=body.statuses,
                exclude_statuses=body.exclude_statuses,
                date_filter=body.date_filter,
                limit=body.limit,
            )
            activity.record('jira')
            return {'ok': True, 'data': result}
        except Exception as e:
            log.error(f'Jira tickets query failed: {e}')
            activity.record('jira', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/jira/release-status')
    def jira_release_status(body: JiraReleaseStatusRequest) -> Dict[str, Any]:
        try:
            from agents.drucker.jira_reporting import query_release_status
            result = query_release_status(
                project_key=body.project_key,
                releases=body.releases,
                issue_types=body.issue_types,
                statuses=body.statuses,
                limit=body.limit,
            )
            activity.record('jira')
            return {'ok': True, 'data': result}
        except Exception as e:
            log.error(f'Jira release status failed: {e}')
            activity.record('jira', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/jira/ticket-counts')
    def jira_ticket_counts(body: JiraTicketCountsRequest) -> Dict[str, Any]:
        try:
            from agents.drucker.jira_reporting import get_ticket_counts
            result = get_ticket_counts(
                project_key=body.project_key,
                issue_types=body.issue_types,
                statuses=body.statuses,
                date_filter=body.date_filter,
            )
            activity.record('jira')
            return {'ok': True, 'data': result}
        except Exception as e:
            log.error(f'Jira ticket counts failed: {e}')
            activity.record('jira', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/jira/status-report')
    def jira_status_report(body: JiraStatusReportRequest) -> Dict[str, Any]:
        try:
            from agents.drucker.jira_reporting import get_status_report
            result = get_status_report(
                project_key=body.project_key,
                include_bugs=body.include_bugs,
                include_activity=body.include_activity,
                recent_days=body.recent_days,
            )
            activity.record('jira')
            return {'ok': True, 'data': result}
        except Exception as e:
            log.error(f'Jira status report failed: {e}')
            activity.record('jira', is_error=True)
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/nl/query')
    def nl_query(body: NLQueryRequest) -> Dict[str, Any]:
        try:
            from agents.drucker.nl_query import run_nl_query
            result = run_nl_query(
                query=body.query,
                project_key=body.project_key,
            )
            activity.record('nl')
            return result
        except Exception as e:
            log.error(f'NL query failed: {e}')
            activity.record('nl', is_error=True)
            return {'ok': False, 'error': str(e)}

    return app


app = create_app()


def run() -> None:
    import uvicorn
    host = str(os.getenv('DRUCKER_HOST', '0.0.0.0') or '0.0.0.0').strip()
    port = int(os.getenv('DRUCKER_PORT', '8201') or '8201')
    uvicorn.run('agents.drucker_api:app', host=host, port=port, log_level='info')


if __name__ == '__main__':
    run()
