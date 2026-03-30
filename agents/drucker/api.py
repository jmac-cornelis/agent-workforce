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

log = logging.getLogger(os.path.basename(sys.argv[0]))

store = DruckerReportStore()

_run_count = 0
_total_findings = 0
_last_run_at = ''


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


def create_app() -> FastAPI:
    app = FastAPI(title='Drucker Agent API', version='1.0.0')

    @app.get('/v1/health')
    def health() -> Dict[str, Any]:
        return {'service': 'drucker', 'ok': True}

    @app.get('/v1/status/stats')
    def status_stats() -> Dict[str, Any]:
        reports = store.list_reports(limit=100)
        total_findings = sum(int(r.get('finding_count', 0)) for r in reports)
        return {
            'ok': True,
            'data': {
                'reports_generated': len(reports),
                'total_findings': total_findings,
                'runs_this_session': _run_count,
            },
        }

    @app.get('/v1/status/load')
    def status_load() -> Dict[str, Any]:
        return {
            'ok': True,
            'data': {
                'state': 'idle',
                'runs_this_session': _run_count,
                'last_run_at': _last_run_at,
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
        return {
            'ok': True,
            'data': {
                'reports_today': len(today_reports),
                'findings_today': sum(int(r.get('finding_count', 0)) for r in today_reports),
                'last_run_at': _last_run_at or 'none',
            },
        }

    @app.get('/v1/status/tokens')
    def status_tokens() -> Dict[str, Any]:
        return {
            'ok': True,
            'data': {
                'llm_enabled': False,
                'token_usage_today': 0,
                'token_usage_cumulative': 0,
                'notes': 'Drucker is fully deterministic — zero token usage.',
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
        global _run_count, _total_findings, _last_run_at

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
            return {'ok': False, 'error': str(e)}

        save_result = store.save_report(report)
        _run_count += 1
        _total_findings += len(report.findings)
        _last_run_at = datetime.now(timezone.utc).isoformat()

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
        global _run_count, _total_findings, _last_run_at

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
            return {'ok': False, 'error': str(e)}

        save_result = None
        if body.persist:
            save_result = store.save_report(report)
        _run_count += 1
        _total_findings += len(report.findings)
        _last_run_at = datetime.now(timezone.utc).isoformat()

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
        global _run_count, _total_findings, _last_run_at

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
            return {'ok': False, 'error': str(e)}

        save_result = None
        if body.persist:
            save_result = store.save_report(report)
        _run_count += 1
        _total_findings += len(report.findings)
        _last_run_at = datetime.now(timezone.utc).isoformat()

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
        global _run_count, _total_findings, _last_run_at

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

        for task in result.get('tasks', []):
            report = task.get('report', {})
            summary = report.get('summary', {})
            _run_count += 1
            _total_findings += int(summary.get('finding_count', 0))

        _last_run_at = datetime.now(timezone.utc).isoformat()
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
            return {'ok': True, 'data': result}
        except Exception as e:
            log.error(f'Bug activity report failed: {e}')
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/pr-hygiene')
    def github_pr_hygiene(body: PRHygieneRequest) -> Dict[str, Any]:
        try:
            import github_utils
            report = github_utils.analyze_repo_pr_hygiene(
                body.repo,
                stale_days=body.stale_days,
            )
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub PR hygiene scan failed: {e}')
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/pr-stale')
    def github_pr_stale(body: PRStaleRequest) -> Dict[str, Any]:
        try:
            import github_utils
            stale = github_utils.analyze_pr_staleness(
                body.repo,
                stale_days=body.stale_days,
            )
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
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/pr-reviews')
    def github_pr_reviews(body: PRReviewsRequest) -> Dict[str, Any]:
        try:
            import github_utils
            findings = github_utils.analyze_missing_reviews(body.repo)
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
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/naming-compliance')
    def github_naming_compliance(body: NamingComplianceRequest) -> Dict[str, Any]:
        try:
            import github_utils
            report = github_utils.analyze_naming_compliance(
                body.repo,
                ticket_patterns=body.ticket_patterns,
            )
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub naming compliance scan failed: {e}')
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/merge-conflicts')
    def github_merge_conflicts(body: MergeConflictsRequest) -> Dict[str, Any]:
        try:
            import github_utils
            report = github_utils.analyze_merge_conflicts(body.repo)
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub merge conflicts scan failed: {e}')
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/ci-failures')
    def github_ci_failures(body: CIFailuresRequest) -> Dict[str, Any]:
        try:
            import github_utils
            report = github_utils.analyze_ci_failures(body.repo)
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub CI failures scan failed: {e}')
            return {'ok': False, 'error': str(e)}

    @app.post('/v1/github/stale-branches')
    def github_stale_branches(body: StaleBranchesRequest) -> Dict[str, Any]:
        try:
            import github_utils
            report = github_utils.analyze_stale_branches(
                body.repo,
                stale_days=body.stale_days,
            )
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub stale branches scan failed: {e}')
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
            return {'ok': True, 'data': report}
        except Exception as e:
            log.error(f'GitHub extended hygiene scan failed: {e}')
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
