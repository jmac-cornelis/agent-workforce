from __future__ import annotations

import logging
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.env_loader import load_env

load_env()

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from agents.gantt.agent import GanttProjectPlannerAgent
from agents.gantt.models import PlanningRequest, ReleaseMonitorRequest, ReleaseSurveyRequest
from agents.pm_runtime import normalize_csv_list
from agents.gantt.state.release_monitor_store import GanttReleaseMonitorStore
from agents.gantt.state.release_survey_store import GanttReleaseSurveyStore
from agents.gantt.state.snapshot_store import GanttSnapshotStore

log = logging.getLogger(os.path.basename(sys.argv[0]))

snapshot_store = GanttSnapshotStore()
release_monitor_store = GanttReleaseMonitorStore()
release_survey_store = GanttReleaseSurveyStore()

_planning_run_count = 0
_release_monitor_run_count = 0
_release_survey_run_count = 0
_last_run_at = ''

_EXPORT_DIR = Path(os.getenv('GANTT_EXPORT_DIR', 'data/gantt_exports'))


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


class ReleaseTasksQueryRequest(BaseModel):
    project_key: str = 'STL'
    releases: List[str] | str
    statuses: Optional[List[str] | str] = None
    issue_types: Optional[List[str] | str] = None
    scope_label: Optional[str] = None
    limit: int = 500


class PlanExportRequest(BaseModel):
    project_key: str = 'STL'
    ticket_keys: Optional[List[str] | str] = None
    releases: Optional[List[str] | str] = None
    hierarchy_depth: int = 1
    table_format: str = 'indented'
    output_file: Optional[str] = None
    limit: int = 500


class PlanImportRequest(BaseModel):
    plan_file: str
    project_key: str = 'STL'
    execute: bool = False


def create_app() -> FastAPI:
    app = FastAPI(title='Gantt Agent API', version='1.0.0')

    @app.get('/v1/health')
    def health() -> Dict[str, Any]:
        return {'service': 'gantt', 'ok': True}

    @app.get('/v1/info')
    def info() -> Dict[str, Any]:
        return {
            'agent_id': 'gantt',
            'name': 'Gantt Project Planner Agent',
            'version': '1.1.0',
            'description': (
                'Planning snapshots and release-health monitoring for '
                'Jira-backed delivery work. Deterministic-first with '
                'optional LLM for roadmap gap analysis.'
            ),
            'capabilities': [
                'Create planning snapshots from Jira backlogs',
                'Release health monitoring with gap analysis and velocity tracking',
                'Release execution surveys',
                'Query and count release tickets by fixVersion, status, and type',
                'Export plan scope to indented Excel',
                'Import plan files (Excel/CSV/JSON) into Jira with dry-run support',
                'Scheduled poller for automated snapshot/monitor cycles',
            ],
            'endpoints': [
                {'method': 'GET', 'path': '/v1/health', 'description': 'Service liveness check'},
                {'method': 'GET', 'path': '/v1/info', 'description': 'Agent identity and capabilities'},
                {'method': 'GET', 'path': '/v1/status/stats', 'description': 'Snapshot and report counts'},
                {'method': 'GET', 'path': '/v1/status/load', 'description': 'Current load state'},
                {'method': 'GET', 'path': '/v1/status/work-summary', 'description': 'Activity generated today'},
                {'method': 'GET', 'path': '/v1/status/tokens', 'description': 'LLM token usage'},
                {'method': 'GET', 'path': '/v1/status/decisions', 'description': 'Recent planning records'},
                {'method': 'GET', 'path': '/v1/status/decisions/{record_id}', 'description': 'Detail for one record'},
                {'method': 'POST', 'path': '/v1/planning/snapshot', 'description': 'Create a planning snapshot'},
                {'method': 'GET', 'path': '/v1/planning/snapshots', 'description': 'List stored snapshots'},
                {'method': 'GET', 'path': '/v1/planning/snapshots/{snapshot_id}', 'description': 'Get a specific snapshot'},
                {'method': 'POST', 'path': '/v1/release-monitor/run', 'description': 'Create a release monitor report'},
                {'method': 'GET', 'path': '/v1/release-monitor/reports', 'description': 'List release monitor reports'},
                {'method': 'GET', 'path': '/v1/release-monitor/report/{report_id}', 'description': 'Get a specific report'},
                {'method': 'POST', 'path': '/v1/release-survey/run', 'description': 'Create a release execution survey'},
                {'method': 'GET', 'path': '/v1/release-survey/reports', 'description': 'List release surveys'},
                {'method': 'GET', 'path': '/v1/release-survey/report/{survey_id}', 'description': 'Get a specific survey'},
                {'method': 'POST', 'path': '/v1/poller/tick', 'description': 'Scheduled poller entrypoint'},
                {'method': 'POST', 'path': '/v1/query/release-tasks', 'description': 'Query/count tickets by fixVersion'},
                {'method': 'POST', 'path': '/v1/plan/export', 'description': 'Export plan scope to indented Excel'},
                {'method': 'POST', 'path': '/v1/plan/import', 'description': 'Import plan file into Jira (dry-run or execute)'},
            ],
            'shannon_commands': [
                {'command': '/planning-snapshot', 'description': 'Create a planning snapshot'},
                {'command': '/planning-snapshots', 'description': 'List stored planning snapshots'},
                {'command': '/release-monitor', 'description': 'Create a release monitor report'},
                {'command': '/release-survey', 'description': 'Create a release execution survey'},
                {'command': '/release-report', 'description': 'Get a stored release monitor report'},
                {'command': '/release-reports', 'description': 'List stored release monitor reports'},
                {'command': '/release-survey-report', 'description': 'Get a stored release survey'},
                {'command': '/release-survey-reports', 'description': 'List stored release surveys'},
                {'command': '/release-tasks', 'description': 'Query tickets by fixVersion'},
                {'command': '/plan-export', 'description': 'Export plan to Excel'},
                {'command': '/plan-import', 'description': 'Import plan into Jira'},
            ],
        }

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

    @app.post('/v1/query/release-tasks')
    def query_release_tasks(body: ReleaseTasksQueryRequest) -> Dict[str, Any]:
        import jira_utils as _jira_utils

        releases = normalize_csv_list(body.releases)
        if not releases:
            return {'ok': False, 'error': 'At least one release name is required'}

        statuses = normalize_csv_list(body.statuses)
        issue_types = normalize_csv_list(body.issue_types)

        try:
            jira = _jira_utils.connect_to_jira()
        except Exception as e:
            log.error(f'Jira connection failed for release-tasks query: {e}')
            return {'ok': False, 'error': f'Jira connection failed: {e}'}

        all_releases: Dict[str, Any] = {}
        total_count = 0

        for release in releases:
            try:
                jql_parts = [
                    f'project = "{body.project_key}"',
                    f'fixVersion = "{release}"',
                ]
                if statuses:
                    status_list = ', '.join(f'"{s}"' for s in statuses)
                    jql_parts.append(f'status IN ({status_list})')
                if issue_types:
                    type_list = ', '.join(f'"{t}"' for t in issue_types)
                    jql_parts.append(f'issuetype IN ({type_list})')
                if body.scope_label:
                    jql_parts.append(
                        f'(labels = "{body.scope_label}" OR '
                        f'"product family" = "{body.scope_label}")'
                    )

                jql = ' AND '.join(jql_parts) + ' ORDER BY priority ASC, updated DESC'
                issues = _jira_utils.run_jql_query(jira, jql, limit=body.limit) or []

                tickets = []
                for t in issues:
                    fields = t.get('fields', {}) or {}
                    status_obj = fields.get('status') or {}
                    type_obj = fields.get('issuetype') or {}
                    priority_obj = fields.get('priority') or {}
                    assignee_obj = fields.get('assignee') or {}
                    fix_versions = fields.get('fixVersions') or []
                    fv_names = ', '.join(v.get('name', '') for v in fix_versions if isinstance(v, dict))
                    tickets.append({
                        'key': t.get('key', ''),
                        'summary': fields.get('summary', ''),
                        'status': status_obj.get('name', '') if isinstance(status_obj, dict) else str(status_obj),
                        'issue_type': type_obj.get('name', '') if isinstance(type_obj, dict) else str(type_obj),
                        'priority': priority_obj.get('name', '') if isinstance(priority_obj, dict) else str(priority_obj),
                        'assignee': assignee_obj.get('displayName', '') if isinstance(assignee_obj, dict) else str(assignee_obj),
                        'fix_version': fv_names,
                    })

                all_releases[release] = {
                    'release': release,
                    'total': len(tickets),
                    'jql': jql,
                    'tickets': tickets,
                }
                total_count += len(tickets)

            except Exception as e:
                log.error(f'Failed to query release {release}: {e}')
                all_releases[release] = {
                    'release': release,
                    'total': 0,
                    'error': str(e),
                    'tickets': [],
                }

        status_breakdown: Dict[str, int] = {}
        type_breakdown: Dict[str, int] = {}
        for rel_data in all_releases.values():
            for t in rel_data.get('tickets', []):
                s = t.get('status', 'Unknown')
                status_breakdown[s] = status_breakdown.get(s, 0) + 1
                it = t.get('issue_type', 'Unknown')
                type_breakdown[it] = type_breakdown.get(it, 0) + 1

        return {
            'ok': True,
            'data': {
                'project_key': body.project_key,
                'total_tickets': total_count,
                'by_status': status_breakdown,
                'by_issue_type': type_breakdown,
                'releases': all_releases,
            },
        }

    @app.post('/v1/plan/export')
    def plan_export(body: PlanExportRequest) -> Dict[str, Any]:
        ticket_keys = normalize_csv_list(body.ticket_keys)
        releases = normalize_csv_list(body.releases)

        if not ticket_keys and not releases:
            return {
                'ok': False,
                'error': 'Provide either ticket_keys (epic keys) or releases (fixVersion names)',
            }

        _EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

        if ticket_keys:
            import excel_utils as _excel_utils

            output_name = body.output_file or f'{body.project_key}_plan_export_{timestamp}.xlsx'
            if not output_name.endswith('.xlsx'):
                output_name += '.xlsx'
            output_path = str(_EXPORT_DIR / output_name)

            try:
                _excel_utils.build_excel_map(
                    ticket_keys=ticket_keys,
                    hierarchy_depth=body.hierarchy_depth,
                    limit=body.limit,
                    output_file=output_path,
                    project_key=body.project_key,
                )
            except Exception as e:
                log.error(f'Plan export (build_excel_map) failed: {e}')
                return {'ok': False, 'error': str(e)}

            return {
                'ok': True,
                'data': {
                    'mode': 'ticket_keys',
                    'ticket_keys': ticket_keys,
                    'hierarchy_depth': body.hierarchy_depth,
                    'output_file': output_path,
                },
            }

        import jira_utils as _jira_utils

        try:
            jira = _jira_utils.connect_to_jira()
        except Exception as e:
            log.error(f'Jira connection failed for plan export: {e}')
            return {'ok': False, 'error': f'Jira connection failed: {e}'}

        all_issues: list = []
        for release in releases:
            try:
                jql = (
                    f'project = "{body.project_key}" AND fixVersion = "{release}" '
                    f'ORDER BY priority ASC, updated DESC'
                )
                issues = _jira_utils.run_jql_query(jira, jql, limit=body.limit) or []
                all_issues.extend(issues)
            except Exception as e:
                log.error(f'Failed to query release {release} for export: {e}')
                return {'ok': False, 'error': f'Query for release {release} failed: {e}'}

        if not all_issues:
            return {
                'ok': True,
                'data': {
                    'mode': 'releases',
                    'releases': releases,
                    'total_tickets': 0,
                    'output_file': None,
                    'message': 'No tickets found for the specified releases',
                },
            }

        release_tag = '_'.join(r.replace('.', '-') for r in releases[:3])
        output_name = body.output_file or f'{body.project_key}_{release_tag}_{timestamp}.xlsx'
        if not output_name.endswith('.xlsx'):
            output_name += '.xlsx'
        output_path = str(_EXPORT_DIR / output_name)

        try:
            _jira_utils.dump_tickets_to_file(
                all_issues,
                dump_file=output_path,
                dump_format='excel',
                table_format=body.table_format,
            )
        except Exception as e:
            log.error(f'Plan export (dump_tickets_to_file) failed: {e}')
            return {'ok': False, 'error': str(e)}

        return {
            'ok': True,
            'data': {
                'mode': 'releases',
                'releases': releases,
                'total_tickets': len(all_issues),
                'table_format': body.table_format,
                'output_file': output_path,
            },
        }

    @app.post('/v1/plan/import')
    def plan_import(body: PlanImportRequest) -> Dict[str, Any]:
        if not body.plan_file:
            return {'ok': False, 'error': 'plan_file path is required'}

        if not os.path.isfile(body.plan_file):
            return {'ok': False, 'error': f'File not found: {body.plan_file}'}

        ext = os.path.splitext(body.plan_file)[1].lower()

        if ext in ('.csv', '.xlsx', '.xls'):
            try:
                from tools.plan_export_tools import plan_file_to_json
                plan_data = plan_file_to_json(
                    body.plan_file,
                    project_key=body.project_key,
                )
            except Exception as e:
                log.error(f'Failed to parse plan file {body.plan_file}: {e}')
                return {'ok': False, 'error': f'Parse failed: {e}'}
        elif ext == '.json':
            import json as _json
            try:
                with open(body.plan_file, 'r', encoding='utf-8') as f:
                    plan_data = _json.load(f)
            except Exception as e:
                log.error(f'Failed to read JSON plan file {body.plan_file}: {e}')
                return {'ok': False, 'error': f'JSON read failed: {e}'}
        else:
            return {
                'ok': False,
                'error': f'Unsupported file type: {ext}. Use .xlsx, .csv, or .json',
            }

        total_epics = plan_data.get('total_epics', 0)
        total_stories = plan_data.get('total_stories', 0)
        total_tickets = plan_data.get('total_tickets', total_epics + total_stories)
        project_key = plan_data.get('project_key', body.project_key)

        plan_summary = {
            'file': body.plan_file,
            'file_type': ext,
            'project_key': project_key,
            'total_epics': total_epics,
            'total_stories': total_stories,
            'total_tickets': total_tickets,
        }

        epics = plan_data.get('epics', [])
        if epics:
            plan_summary['epics'] = [
                {
                    'summary': e.get('summary', ''),
                    'story_count': len(e.get('stories', [])),
                }
                for e in epics[:50]
            ]

        if not body.execute:
            return {
                'ok': True,
                'data': {
                    'mode': 'dry_run',
                    'plan': plan_summary,
                    'message': (
                        f'Parsed {total_tickets} tickets '
                        f'({total_epics} epics, {total_stories} stories). '
                        f'Set execute=true to create in Jira.'
                    ),
                },
            }

        try:
            from agents.feature_planning_orchestrator import FeaturePlanningOrchestrator

            orchestrator = FeaturePlanningOrchestrator(
                project_key=body.project_key,
            )
            exec_result = orchestrator._run_execute_plan(
                plan_file=body.plan_file,
                project_key=body.project_key,
                execute=True,
            )

            if hasattr(exec_result, 'status') and exec_result.status == 'error':
                return {
                    'ok': False,
                    'error': getattr(exec_result, 'message', str(exec_result)),
                    'plan': plan_summary,
                }

            exec_data = {}
            if hasattr(exec_result, 'data'):
                exec_data = exec_result.data if isinstance(exec_result.data, dict) else {}
            elif isinstance(exec_result, dict):
                exec_data = exec_result

            return {
                'ok': True,
                'data': {
                    'mode': 'execute',
                    'plan': plan_summary,
                    'execution': exec_data,
                    'message': f'Created {total_tickets} tickets in {body.project_key}',
                },
            }

        except ImportError:
            log.error('FeaturePlanningOrchestrator not available')
            return {
                'ok': False,
                'error': (
                    'Execution mode requires FeaturePlanningOrchestrator. '
                    'Module not available in this deployment.'
                ),
                'plan': plan_summary,
            }
        except Exception as e:
            log.error(f'Plan execution failed: {e}')
            return {
                'ok': False,
                'error': f'Execution failed: {e}',
                'plan': plan_summary,
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
