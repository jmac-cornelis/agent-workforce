from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from agents.drucker_agent import DruckerCoordinatorAgent
from agents.drucker_models import DruckerRequest
from core.reporting import bug_activity_today
from state.drucker_report_store import DruckerReportStore

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

    class BugActivityRequest(BaseModel):
        project_key: str = 'STL'
        target_date: Optional[str] = None

    @app.post('/v1/activity/bugs')
    def activity_bugs(
        body: Optional[BugActivityRequest] = None,
        project_key: Optional[str] = Query(default=None),
        target_date: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        from jira_utils import connect_to_jira
        pk = (body.project_key if body and body.project_key else None) or project_key or 'STL'
        td = (body.target_date if body and body.target_date else None) or target_date
        try:
            jira = connect_to_jira()
            result = bug_activity_today(jira, pk, td)
            return {'ok': True, 'data': result}
        except Exception as e:
            log.error(f'Bug activity report failed: {e}')
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
