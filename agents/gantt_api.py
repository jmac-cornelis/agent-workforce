from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.env_loader import load_env

load_env()

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from agents.gantt_agent import GanttProjectPlannerAgent
from agents.gantt_models import PlanningRequest, ReleaseMonitorRequest, ReleaseSurveyRequest
from agents.pm_runtime import normalize_csv_list
from state.gantt_release_monitor_store import GanttReleaseMonitorStore
from state.gantt_release_survey_store import GanttReleaseSurveyStore
from state.gantt_snapshot_store import GanttSnapshotStore

log = logging.getLogger(os.path.basename(sys.argv[0]))

snapshot_store = GanttSnapshotStore()
release_monitor_store = GanttReleaseMonitorStore()
release_survey_store = GanttReleaseSurveyStore()

_planning_run_count = 0
_release_monitor_run_count = 0
_release_survey_run_count = 0
_last_run_at = ''


class PlanningSnapshotRunRequest(BaseModel):
    project_key: str
    planning_horizon_days: int = 90
    limit: int = 200
    include_done: bool = False
    backlog_jql: Optional[str] = None
    policy_profile: str = 'default'
    evidence_paths: List[str] | str = Field(default_factory=list)
    persist: bool = True


class ReleaseMonitorRunRequest(BaseModel):
    project_key: str = 'STL'
    releases: Optional[List[str] | str] = None
    scope_label: Optional[str] = None
    include_gap_analysis: bool = True
    include_bug_report: bool = True
    include_velocity: bool = True
    include_readiness: bool = True
    compare_to_previous: bool = True
    output_file: Optional[str] = None
    persist: bool = True


class GanttPollerTickRequest(BaseModel):
    project_key: str
    run_planning: bool = True
    run_release_monitor: bool = False
    run_release_survey: bool = False
    planning_horizon_days: int = 90
    limit: int = 200
    include_done: bool = False
    backlog_jql: Optional[str] = None
    policy_profile: str = 'default'
    evidence_paths: List[str] | str = Field(default_factory=list)
    releases: Optional[List[str] | str] = None
    scope_label: Optional[str] = None
    include_gap_analysis: bool = True
    include_bug_report: bool = True
    include_velocity: bool = True
    include_readiness: bool = True
    compare_to_previous: bool = True
    output_file: Optional[str] = None
    survey_output_file: Optional[str] = None
    survey_mode: str = 'feature_dev'
    persist: bool = True
    notify_shannon: bool = False
    shannon_base_url: Optional[str] = None


class ReleaseSurveyRunRequest(BaseModel):
    project_key: str = 'STL'
    releases: Optional[List[str] | str] = None
    scope_label: Optional[str] = None
    survey_mode: str = 'feature_dev'
    output_file: Optional[str] = None
    persist: bool = True


def create_app() -> FastAPI:
    app = FastAPI(title='Gantt Agent API', version='1.0.0')

    @app.get('/v1/health')
    def health() -> Dict[str, Any]:
        return {'service': 'gantt', 'ok': True}

    @app.get('/v1/status/stats')
    def status_stats() -> Dict[str, Any]:
        snapshots = snapshot_store.list_snapshots(limit=200)
        reports = release_monitor_store.list_reports(limit=200)
        surveys = release_survey_store.list_surveys(limit=200)
        return {
            'ok': True,
            'data': {
                'planning_snapshots_generated': len(snapshots),
                'release_reports_generated': len(reports),
                'release_surveys_generated': len(surveys),
                'runs_this_session': (
                    _planning_run_count
                    + _release_monitor_run_count
                    + _release_survey_run_count
                ),
            },
        }

    @app.get('/v1/status/load')
    def status_load() -> Dict[str, Any]:
        run_count = (
            _planning_run_count + _release_monitor_run_count + _release_survey_run_count
        )
        state = 'idle' if run_count == 0 else 'working'
        return {
            'ok': True,
            'data': {
                'state': state,
                'planning_runs_this_session': _planning_run_count,
                'release_runs_this_session': _release_monitor_run_count,
                'release_surveys_this_session': _release_survey_run_count,
                'last_run_at': _last_run_at or 'none',
            },
        }

    @app.get('/v1/status/work-summary')
    def status_work_summary() -> Dict[str, Any]:
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        snapshots = snapshot_store.list_snapshots(limit=200)
        reports = release_monitor_store.list_reports(limit=200)
        surveys = release_survey_store.list_surveys(limit=200)
        today_snapshots = [
            item for item in snapshots
            if str(item.get('created_at') or '').startswith(today)
        ]
        today_reports = [
            item for item in reports
            if str(item.get('created_at') or '').startswith(today)
        ]
        today_surveys = [
            item for item in surveys
            if str(item.get('created_at') or '').startswith(today)
        ]
        return {
            'ok': True,
            'data': {
                'planning_snapshots_today': len(today_snapshots),
                'release_reports_today': len(today_reports),
                'release_surveys_today': len(today_surveys),
                'last_run_at': _last_run_at or 'none',
            },
        }

    @app.get('/v1/status/tokens')
    def status_tokens() -> Dict[str, Any]:
        return {
            'ok': True,
            'data': {
                'llm_enabled': True,
                'token_usage_today': 0,
                'token_usage_cumulative': 0,
                'notes': (
                    'Gantt is deterministic-first. Planning snapshots and release monitoring '
                    'are deterministic; roadmap gap analysis may use an LLM when enabled. '
                    'Release surveys are also deterministic.'
                ),
            },
        }

    @app.get('/v1/status/decisions')
    def status_decisions(
        limit: int = Query(default=10, ge=1, le=100),
    ) -> Dict[str, Any]:
        decisions: List[Dict[str, Any]] = []

        for item in snapshot_store.list_snapshots(limit=limit):
            decisions.append({
                'record_id': item.get('snapshot_id', ''),
                'record_type': 'planning_snapshot',
                'project_key': item.get('project_key', ''),
                'created_at': item.get('created_at', ''),
            })

        for item in release_monitor_store.list_reports(limit=limit):
            decisions.append({
                'record_id': item.get('report_id', ''),
                'record_type': 'release_monitor',
                'project_key': item.get('project_key', ''),
                'created_at': item.get('created_at', ''),
            })

        for item in release_survey_store.list_surveys(limit=limit):
            decisions.append({
                'record_id': item.get('survey_id', ''),
                'record_type': 'release_survey',
                'project_key': item.get('project_key', ''),
                'created_at': item.get('created_at', ''),
            })

        decisions.sort(
            key=lambda item: str(item.get('created_at') or ''),
            reverse=True,
        )
        return {'ok': True, 'data': decisions[:limit]}

    @app.get('/v1/status/decisions/{record_id}')
    def status_decision_detail(record_id: str) -> Dict[str, Any]:
        for loader_name, loader in (
            ('planning_snapshot', snapshot_store.get_snapshot),
            ('release_monitor', release_monitor_store.get_report),
            ('release_survey', release_survey_store.get_survey),
        ):
            result = loader(record_id)
            if result is not None:
                return {
                    'ok': True,
                    'data': {
                        'record_id': record_id,
                        'record_type': loader_name,
                        'summary': result.get('summary', {}),
                    },
                }

        raise HTTPException(status_code=404, detail=f'Record {record_id} not found')

    @app.post('/v1/planning/snapshot')
    def planning_snapshot(body: PlanningSnapshotRunRequest) -> Dict[str, Any]:
        global _planning_run_count, _last_run_at

        agent = GanttProjectPlannerAgent(project_key=body.project_key)
        request = PlanningRequest(
            project_key=body.project_key,
            planning_horizon_days=body.planning_horizon_days,
            limit=body.limit,
            include_done=body.include_done,
            backlog_jql=body.backlog_jql,
            policy_profile=body.policy_profile,
            evidence_paths=normalize_csv_list(body.evidence_paths),
        )

        try:
            snapshot = agent.create_snapshot(request)
        except Exception as e:
            log.error(f'Gantt planning snapshot failed: {e}')
            return {'ok': False, 'error': str(e)}

        result: Dict[str, Any] = {
            'snapshot': snapshot.to_dict(),
        }
        if body.persist:
            result['stored'] = snapshot_store.save_snapshot(
                snapshot,
                summary_markdown=snapshot.summary_markdown,
            )

        _planning_run_count += 1
        _last_run_at = datetime.now(timezone.utc).isoformat()
        return {'ok': True, 'data': result}

    @app.get('/v1/planning/snapshots/{snapshot_id}')
    def planning_snapshot_get(
        snapshot_id: str,
        project_key: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        result = snapshot_store.get_snapshot(snapshot_id, project_key=project_key)
        if result is None:
            raise HTTPException(status_code=404, detail=f'Snapshot {snapshot_id} not found')
        return {'ok': True, 'data': result}

    @app.get('/v1/planning/snapshots')
    def planning_snapshot_list(
        project_key: Optional[str] = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> Dict[str, Any]:
        return {
            'ok': True,
            'data': snapshot_store.list_snapshots(project_key=project_key, limit=limit),
        }

    @app.post('/v1/release-monitor/run')
    def release_monitor_run(body: ReleaseMonitorRunRequest) -> Dict[str, Any]:
        global _release_monitor_run_count, _last_run_at

        agent = GanttProjectPlannerAgent(project_key=body.project_key)
        request = ReleaseMonitorRequest(
            project_key=body.project_key,
            releases=normalize_csv_list(body.releases) or None,
            scope_label=body.scope_label,
            include_gap_analysis=body.include_gap_analysis,
            include_bug_report=body.include_bug_report,
            include_velocity=body.include_velocity,
            include_readiness=body.include_readiness,
            compare_to_previous=body.compare_to_previous,
            output_file=body.output_file or f'{body.project_key}_release_monitor.xlsx',
        )

        try:
            report = agent.create_release_monitor(request)
        except Exception as e:
            log.error(f'Gantt release monitor failed: {e}')
            return {'ok': False, 'error': str(e)}

        result: Dict[str, Any] = {
            'report': report.to_dict(),
        }
        if body.persist:
            result['stored'] = release_monitor_store.save_report(
                report,
                summary_markdown=report.summary_markdown,
            )

        _release_monitor_run_count += 1
        _last_run_at = datetime.now(timezone.utc).isoformat()
        return {'ok': True, 'data': result}

    @app.post('/v1/release-survey/run')
    def release_survey_run(body: ReleaseSurveyRunRequest) -> Dict[str, Any]:
        global _release_survey_run_count, _last_run_at

        agent = GanttProjectPlannerAgent(project_key=body.project_key)
        request = ReleaseSurveyRequest(
            project_key=body.project_key,
            releases=normalize_csv_list(body.releases) or None,
            scope_label=body.scope_label,
            survey_mode=body.survey_mode,
            output_file=body.output_file or f'{body.project_key}_release_survey.xlsx',
        )

        try:
            survey = agent.create_release_survey(request)
        except Exception as e:
            log.error(f'Gantt release survey failed: {e}')
            return {'ok': False, 'error': str(e)}

        result: Dict[str, Any] = {
            'survey': survey.to_dict(),
        }
        if body.persist:
            result['stored'] = release_survey_store.save_survey(
                survey,
                summary_markdown=survey.summary_markdown,
            )

        _release_survey_run_count += 1
        _last_run_at = datetime.now(timezone.utc).isoformat()
        return {'ok': True, 'data': result}

    @app.post('/v1/poller/tick')
    def poller_tick(body: GanttPollerTickRequest) -> Dict[str, Any]:
        global _planning_run_count, _release_monitor_run_count
        global _release_survey_run_count, _last_run_at

        agent = GanttProjectPlannerAgent(project_key=body.project_key)
        result = agent.tick({
            'project_key': body.project_key,
            'run_planning': body.run_planning,
            'run_release_monitor': body.run_release_monitor,
            'run_release_survey': body.run_release_survey,
            'planning_horizon_days': body.planning_horizon_days,
            'limit': body.limit,
            'include_done': body.include_done,
            'backlog_jql': body.backlog_jql,
            'policy_profile': body.policy_profile,
            'evidence_paths': normalize_csv_list(body.evidence_paths),
            'releases': normalize_csv_list(body.releases),
            'scope_label': body.scope_label,
            'include_gap_analysis': body.include_gap_analysis,
            'include_bug_report': body.include_bug_report,
            'include_velocity': body.include_velocity,
            'include_readiness': body.include_readiness,
            'compare_to_previous': body.compare_to_previous,
            'output_file': body.output_file,
            'survey_output_file': body.survey_output_file,
            'survey_mode': body.survey_mode,
            'persist': body.persist,
            'notify_shannon': body.notify_shannon,
            'shannon_base_url': body.shannon_base_url,
        })

        for task in result.get('tasks', []):
            if task.get('task_type') == 'planning_snapshot':
                _planning_run_count += 1
            elif task.get('task_type') == 'release_monitor':
                _release_monitor_run_count += 1
            elif task.get('task_type') == 'release_survey':
                _release_survey_run_count += 1

        _last_run_at = datetime.now(timezone.utc).isoformat()
        return {'ok': result.get('ok', False), 'data': result}

    @app.get('/v1/release-monitor/report/{report_id}')
    def release_monitor_get(
        report_id: str,
        project_key: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        result = release_monitor_store.get_report(report_id, project_key=project_key)
        if result is None:
            raise HTTPException(status_code=404, detail=f'Report {report_id} not found')
        return {'ok': True, 'data': result}

    @app.get('/v1/release-monitor/reports')
    def release_monitor_list(
        project_key: Optional[str] = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> Dict[str, Any]:
        return {
            'ok': True,
            'data': release_monitor_store.list_reports(project_key=project_key, limit=limit),
        }

    @app.get('/v1/release-survey/report/{survey_id}')
    def release_survey_get(
        survey_id: str,
        project_key: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        result = release_survey_store.get_survey(survey_id, project_key=project_key)
        if result is None:
            raise HTTPException(status_code=404, detail=f'Survey {survey_id} not found')
        return {'ok': True, 'data': result}

    @app.get('/v1/release-survey/reports')
    def release_survey_list(
        project_key: Optional[str] = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> Dict[str, Any]:
        return {
            'ok': True,
            'data': release_survey_store.list_surveys(project_key=project_key, limit=limit),
        }

    return app


app = create_app()


def run() -> None:
    import uvicorn

    host = str(os.getenv('GANTT_HOST', '0.0.0.0') or '0.0.0.0').strip()
    port = int(os.getenv('GANTT_PORT', '8202') or '8202')
    uvicorn.run('agents.gantt_api:app', host=host, port=port, log_level='info')


if __name__ == '__main__':
    run()
