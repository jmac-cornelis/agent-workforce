##########################################################################################
#
# Module: tests/test_gantt_cli_char.py
#
# Description: Characterization tests for agents/gantt/cli.py.
#              Covers all 10 subcommand handlers: cmd_snapshot, cmd_snapshot_get,
#              cmd_snapshot_list, cmd_release_monitor, cmd_release_monitor_get,
#              cmd_release_monitor_list, cmd_release_survey, cmd_release_survey_get,
#              cmd_release_survey_list, cmd_poll.
#
# Author: Cornelis Networks
#
##########################################################################################

import json
from types import SimpleNamespace

import pytest

from agents.base import AgentResponse


# ---------------------------------------------------------------------------
# Helpers — fake agent and model classes used across tests
# ---------------------------------------------------------------------------

def _make_fake_gantt_agent(run_result=None, monitor_report=None, survey_report=None,
                           poller_result=None):
    '''
    Build a fake GanttProjectPlannerAgent class whose methods return
    the supplied canned objects.
    '''

    class _FakeGanttAgent:
        def __init__(self, project_key=None, **kwargs):
            self.project_key = project_key

        def run(self, input_data):
            return run_result

        def create_release_monitor(self, request):
            return monitor_report

        def create_release_survey(self, request):
            return survey_report

        def run_poller(self, spec):
            return poller_result

    return _FakeGanttAgent


# ===================================================================
# cmd_snapshot — create planning snapshot
# ===================================================================

class TestCmdSnapshot:
    '''Tests for the snapshot creation handler.'''

    def test_success_writes_files(self, monkeypatch, tmp_path):
        '''Successful snapshot writes JSON + Markdown and exits 0.'''
        from agents.gantt.cli import cmd_snapshot
        from agents.gantt import agent as gantt_agent

        fake_cls = _make_fake_gantt_agent(
            run_result=AgentResponse.success_response(
                content='# Snapshot Summary',
                metadata={
                    'planning_snapshot': {
                        'snapshot_id': 'snap-cli-001',
                        'project_key': 'STL',
                        'created_at': '2026-03-28T12:00:00+00:00',
                        'planning_horizon_days': 90,
                        'backlog_overview': {'total_issues': 5},
                        'milestones': [],
                        'risks': [],
                        'dependency_graph': {'edge_count': 0},
                    }
                },
            ),
        )
        monkeypatch.setattr(gantt_agent, 'GanttProjectPlannerAgent', fake_cls)
        monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'store'))

        output_path = tmp_path / 'snap_out.json'
        args = SimpleNamespace(
            project='STL',
            planning_horizon=90,
            limit=200,
            include_done=False,
            output=str(output_path),
            evidence=None,
            env=None,
            json=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_snapshot(args)

        assert exc_info.value.code == 0
        assert output_path.exists()
        assert (tmp_path / 'snap_out.md').exists()

        data = json.loads(output_path.read_text(encoding='utf-8'))
        assert data['project_key'] == 'STL'
        assert data['snapshot_id'] == 'snap-cli-001'

    def test_json_flag_prints_json(self, monkeypatch, tmp_path, capsys):
        '''--json flag prints snapshot JSON to stdout and exits 0.'''
        from agents.gantt.cli import cmd_snapshot
        from agents.gantt import agent as gantt_agent

        snapshot_data = {
            'snapshot_id': 'snap-json-001',
            'project_key': 'STL',
            'created_at': '2026-03-28T12:00:00+00:00',
            'planning_horizon_days': 90,
            'backlog_overview': {'total_issues': 3},
            'milestones': [],
            'risks': [],
            'dependency_graph': {'edge_count': 0},
        }
        fake_cls = _make_fake_gantt_agent(
            run_result=AgentResponse.success_response(
                content='# Summary',
                metadata={'planning_snapshot': snapshot_data},
            ),
        )
        monkeypatch.setattr(gantt_agent, 'GanttProjectPlannerAgent', fake_cls)
        monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'store'))

        args = SimpleNamespace(
            project='STL',
            planning_horizon=90,
            limit=200,
            include_done=False,
            output=None,
            evidence=None,
            env=None,
            json=True,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_snapshot(args)

        assert exc_info.value.code == 0
        stdout = capsys.readouterr().out
        assert 'snap-json-001' in stdout
        assert '"project_key": "STL"' in stdout

    def test_agent_failure_exits_1(self, monkeypatch, tmp_path):
        '''Agent returning success=False causes exit(1).'''
        from agents.gantt.cli import cmd_snapshot
        from agents.gantt import agent as gantt_agent

        fake_cls = _make_fake_gantt_agent(
            run_result=AgentResponse(
                content='',
                success=False,
                error='Jira unreachable',
            ),
        )
        monkeypatch.setattr(gantt_agent, 'GanttProjectPlannerAgent', fake_cls)

        args = SimpleNamespace(
            project='STL',
            planning_horizon=90,
            limit=200,
            include_done=False,
            output=None,
            evidence=None,
            env=None,
            json=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_snapshot(args)

        assert exc_info.value.code == 1

    def test_missing_metadata_exits_1(self, monkeypatch, tmp_path):
        '''Agent success but missing planning_snapshot metadata causes exit(1).'''
        from agents.gantt.cli import cmd_snapshot
        from agents.gantt import agent as gantt_agent

        fake_cls = _make_fake_gantt_agent(
            run_result=AgentResponse.success_response(
                content='# Summary',
                metadata={},
            ),
        )
        monkeypatch.setattr(gantt_agent, 'GanttProjectPlannerAgent', fake_cls)

        args = SimpleNamespace(
            project='STL',
            planning_horizon=90,
            limit=200,
            include_done=False,
            output=None,
            evidence=None,
            env=None,
            json=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_snapshot(args)

        assert exc_info.value.code == 1


# ===================================================================
# cmd_snapshot_get — load stored snapshot
# ===================================================================

class TestCmdSnapshotGet:
    '''Tests for the snapshot-get handler.'''

    def test_success_prints_summary(self, monkeypatch, tmp_path, capsys):
        '''Existing snapshot is loaded and summary printed.'''
        from agents.gantt.cli import cmd_snapshot_get
        from agents.gantt.state.snapshot_store import GanttSnapshotStore

        store = GanttSnapshotStore(storage_dir=str(tmp_path / 'store'))
        store.save_snapshot(
            {
                'snapshot_id': 'snap-get-001',
                'project_key': 'STL',
                'created_at': '2026-03-28T12:00:00+00:00',
                'planning_horizon_days': 90,
                'backlog_overview': {
                    'total_issues': 10,
                    'blocked_issues': 2,
                    'stale_issues': 1,
                },
                'milestones': [{'name': '12.1.0'}],
                'risks': [{'risk_type': 'blocked_work'}],
                'dependency_graph': {'edge_count': 3},
                'summary_markdown': '# Stored Snapshot',
            },
            summary_markdown='# Stored Snapshot',
        )
        monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'store'))

        args = SimpleNamespace(
            snapshot_id='snap-get-001',
            project='STL',
            output=None,
            env=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_snapshot_get(args)

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert 'Project: STL' in out
        assert 'Total issues: 10' in out
        assert '# Stored Snapshot' in out

    def test_not_found_exits_1(self, monkeypatch, tmp_path):
        '''Non-existent snapshot ID causes exit(1).'''
        from agents.gantt.cli import cmd_snapshot_get

        monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'store'))

        args = SimpleNamespace(
            snapshot_id='nonexistent',
            project=None,
            output=None,
            env=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_snapshot_get(args)

        assert exc_info.value.code == 1


# ===================================================================
# cmd_snapshot_list — list stored snapshots
# ===================================================================

class TestCmdSnapshotList:
    '''Tests for the snapshot-list handler.'''

    def test_lists_snapshots(self, monkeypatch, tmp_path, capsys):
        '''Stored snapshots are listed in tabular format.'''
        from agents.gantt.cli import cmd_snapshot_list
        from agents.gantt.state.snapshot_store import GanttSnapshotStore

        store = GanttSnapshotStore(storage_dir=str(tmp_path / 'store'))
        store.save_snapshot(
            {
                'snapshot_id': 'snap-ls-001',
                'project_key': 'STL',
                'created_at': '2026-03-27T12:00:00+00:00',
                'planning_horizon_days': 90,
                'backlog_overview': {'total_issues': 5, 'blocked_issues': 1, 'stale_issues': 0},
                'milestones': [{'name': '12.1.0'}],
                'risks': [],
                'dependency_graph': {'edge_count': 1},
            },
            summary_markdown='# Snap 1',
        )
        store.save_snapshot(
            {
                'snapshot_id': 'snap-ls-002',
                'project_key': 'STL',
                'created_at': '2026-03-28T12:00:00+00:00',
                'planning_horizon_days': 60,
                'backlog_overview': {'total_issues': 3},
                'milestones': [],
                'risks': [{'risk_type': 'stale'}],
                'dependency_graph': {'edge_count': 0},
            },
            summary_markdown='# Snap 2',
        )
        monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'store'))

        args = SimpleNamespace(project='STL', limit=10, env=None)

        with pytest.raises(SystemExit) as exc_info:
            cmd_snapshot_list(args)

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert 'snap-ls-001' in out
        assert 'snap-ls-002' in out
        assert 'Total stored snapshots: 2' in out

    def test_empty_list(self, monkeypatch, tmp_path, capsys):
        '''No snapshots prints informational message and exits 0.'''
        from agents.gantt.cli import cmd_snapshot_list

        monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'empty'))

        args = SimpleNamespace(project='STL', limit=10, env=None)

        with pytest.raises(SystemExit) as exc_info:
            cmd_snapshot_list(args)

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert 'No stored Gantt snapshots found' in out


# ===================================================================
# cmd_release_monitor — create release health report
# ===================================================================

class TestCmdReleaseMonitor:
    '''Tests for the release-monitor creation handler.'''

    def test_success_writes_files(self, monkeypatch, tmp_path):
        '''Successful release monitor writes JSON + Markdown and exits 0.'''
        from agents.gantt.cli import cmd_release_monitor
        from agents.gantt import agent as gantt_agent
        from agents.gantt.models import ReleaseMonitorReport, BugSummary

        report = ReleaseMonitorReport(
            project_key='STL',
            created_at='2026-03-28T12:00:00+00:00',
            report_id='rep-cli-001',
            scope_label='CN6000',
            releases_monitored=['12.1.1.x'],
            bug_summaries=[
                BugSummary(
                    release='12.1.1.x',
                    total_bugs=5,
                    by_priority={'P0': 1, 'P1': 2},
                ),
            ],
            summary_markdown='# Release Monitor\n\nSummary',
            output_file=str(tmp_path / 'monitor.xlsx'),
        )

        fake_cls = _make_fake_gantt_agent(monitor_report=report)
        monkeypatch.setattr(gantt_agent, 'GanttProjectPlannerAgent', fake_cls)
        monkeypatch.setenv('GANTT_RELEASE_MONITOR_DIR', str(tmp_path / 'store'))

        output_path = tmp_path / 'monitor_out.json'
        args = SimpleNamespace(
            project='STL',
            releases='12.1.1.x',
            scope_label='CN6000',
            include_gap_analysis=True,
            include_bug_report=True,
            include_velocity=True,
            include_readiness=True,
            compare_to_previous=True,
            output=str(output_path),
            env=None,
            json=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_release_monitor(args)

        assert exc_info.value.code == 0
        assert output_path.exists()
        assert (tmp_path / 'monitor_out.md').exists()

        data = json.loads(output_path.read_text(encoding='utf-8'))
        assert data['project_key'] == 'STL'
        assert data['report_id'] == 'rep-cli-001'


# ===================================================================
# cmd_release_monitor_get — load stored release report
# ===================================================================

class TestCmdReleaseMonitorGet:
    '''Tests for the release-monitor-get handler.'''

    def test_success_prints_summary(self, monkeypatch, tmp_path, capsys):
        '''Existing report is loaded and summary printed.'''
        from agents.gantt.cli import cmd_release_monitor_get
        from agents.gantt.state.release_monitor_store import GanttReleaseMonitorStore

        store = GanttReleaseMonitorStore(storage_dir=str(tmp_path / 'store'))
        store.save_report(
            {
                'report_id': 'rep-get-001',
                'project_key': 'STL',
                'created_at': '2026-03-28T12:00:00+00:00',
                'scope_label': 'CN6000',
                'releases_monitored': ['12.1.1.x'],
                'bug_summaries': [],
                'summary_markdown': '# Stored Report',
                'total_bugs': 3,
                'total_p0': 1,
                'total_p1': 2,
            },
            summary_markdown='# Stored Report',
        )
        monkeypatch.setenv('GANTT_RELEASE_MONITOR_DIR', str(tmp_path / 'store'))

        args = SimpleNamespace(
            report_id='rep-get-001',
            project='STL',
            output=None,
            env=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_release_monitor_get(args)

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert 'Project: STL' in out
        assert '# Stored Report' in out

    def test_not_found_exits_1(self, monkeypatch, tmp_path):
        '''Non-existent report ID causes exit(1).'''
        from agents.gantt.cli import cmd_release_monitor_get

        monkeypatch.setenv('GANTT_RELEASE_MONITOR_DIR', str(tmp_path / 'store'))

        args = SimpleNamespace(
            report_id='nonexistent',
            project=None,
            output=None,
            env=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_release_monitor_get(args)

        assert exc_info.value.code == 1


# ===================================================================
# cmd_release_monitor_list — list stored release reports
# ===================================================================

class TestCmdReleaseMonitorList:
    '''Tests for the release-monitor-list handler.'''

    def test_lists_reports(self, monkeypatch, tmp_path, capsys):
        '''Stored reports are listed in tabular format.'''
        from agents.gantt.cli import cmd_release_monitor_list
        from agents.gantt.state.release_monitor_store import GanttReleaseMonitorStore

        store = GanttReleaseMonitorStore(storage_dir=str(tmp_path / 'store'))
        store.save_report(
            {
                'report_id': 'rep-ls-001',
                'project_key': 'STL',
                'created_at': '2026-03-27T12:00:00+00:00',
                'scope_label': 'CN6000',
                'releases_monitored': ['12.1.1.x'],
                'bug_summaries': [],
                'summary_markdown': '# Report 1',
            },
            summary_markdown='# Report 1',
        )
        store.save_report(
            {
                'report_id': 'rep-ls-002',
                'project_key': 'STL',
                'created_at': '2026-03-28T12:00:00+00:00',
                'scope_label': 'CN6000',
                'releases_monitored': ['12.2.0.x'],
                'bug_summaries': [],
                'summary_markdown': '# Report 2',
            },
            summary_markdown='# Report 2',
        )
        monkeypatch.setenv('GANTT_RELEASE_MONITOR_DIR', str(tmp_path / 'store'))

        args = SimpleNamespace(project='STL', limit=10, env=None)

        with pytest.raises(SystemExit) as exc_info:
            cmd_release_monitor_list(args)

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert 'rep-ls-001' in out
        assert 'rep-ls-002' in out
        assert 'Total stored reports: 2' in out

    def test_empty_list(self, monkeypatch, tmp_path, capsys):
        '''No reports prints informational message and exits 0.'''
        from agents.gantt.cli import cmd_release_monitor_list

        monkeypatch.setenv('GANTT_RELEASE_MONITOR_DIR', str(tmp_path / 'empty'))

        args = SimpleNamespace(project='STL', limit=10, env=None)

        with pytest.raises(SystemExit) as exc_info:
            cmd_release_monitor_list(args)

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert 'No stored release monitor reports found' in out


# ===================================================================
# cmd_release_survey — create release execution survey
# ===================================================================

class TestCmdReleaseSurvey:
    '''Tests for the release-survey creation handler.'''

    def test_success_writes_files(self, monkeypatch, tmp_path):
        '''Successful survey writes JSON + Markdown and exits 0.'''
        from agents.gantt.cli import cmd_release_survey
        from agents.gantt import agent as gantt_agent
        from agents.gantt.models import ReleaseSurveyReport, ReleaseSurveyReleaseSummary

        survey = ReleaseSurveyReport(
            project_key='STL',
            created_at='2026-03-28T12:00:00+00:00',
            survey_id='sur-cli-001',
            scope_label='CN6000',
            survey_mode='feature_dev',
            releases_surveyed=['12.2.0.x'],
            release_summaries=[
                ReleaseSurveyReleaseSummary(
                    release='12.2.0.x',
                    total_tickets=6,
                    done_tickets=[{'key': 'STL-1'}, {'key': 'STL-2'}],
                    in_progress_tickets=[{'key': 'STL-3'}],
                    remaining_tickets=[{'key': 'STL-4'}, {'key': 'STL-5'}],
                    blocked_tickets=[{'key': 'STL-6'}],
                ),
            ],
            summary_markdown='# Release Survey\n\nSummary',
            output_file=str(tmp_path / 'survey.xlsx'),
        )

        fake_cls = _make_fake_gantt_agent(survey_report=survey)
        monkeypatch.setattr(gantt_agent, 'GanttProjectPlannerAgent', fake_cls)
        monkeypatch.setenv('GANTT_RELEASE_SURVEY_DIR', str(tmp_path / 'store'))

        output_path = tmp_path / 'survey_out.json'
        args = SimpleNamespace(
            project='STL',
            releases='12.2.0.x',
            scope_label='CN6000',
            survey_mode='feature-dev',
            output=str(output_path),
            env=None,
            json=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_release_survey(args)

        assert exc_info.value.code == 0
        assert output_path.exists()
        assert (tmp_path / 'survey_out.md').exists()

        data = json.loads(output_path.read_text(encoding='utf-8'))
        assert data['project_key'] == 'STL'
        assert data['survey_id'] == 'sur-cli-001'
        assert data['done_count'] == 2


# ===================================================================
# cmd_release_survey_get — load stored survey
# ===================================================================

class TestCmdReleaseSurveyGet:
    '''Tests for the release-survey-get handler.'''

    def test_success_prints_summary(self, monkeypatch, tmp_path, capsys):
        '''Existing survey is loaded and summary printed.'''
        from agents.gantt.cli import cmd_release_survey_get
        from agents.gantt.state.release_survey_store import GanttReleaseSurveyStore

        store = GanttReleaseSurveyStore(storage_dir=str(tmp_path / 'store'))
        store.save_survey(
            {
                'survey_id': 'sur-get-001',
                'project_key': 'STL',
                'created_at': '2026-03-28T12:00:00+00:00',
                'scope_label': 'CN6000',
                'releases_surveyed': ['12.2.0.x'],
                'release_summaries': [],
                'summary_markdown': '# Stored Survey',
                'total_tickets': 8,
                'done_count': 4,
                'in_progress_count': 2,
                'remaining_count': 1,
                'blocked_count': 1,
                'stale_count': 0,
                'unassigned_count': 0,
            },
            summary_markdown='# Stored Survey',
        )
        monkeypatch.setenv('GANTT_RELEASE_SURVEY_DIR', str(tmp_path / 'store'))

        args = SimpleNamespace(
            survey_id='sur-get-001',
            project='STL',
            output=None,
            env=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_release_survey_get(args)

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert 'Project: STL' in out
        assert 'Total tickets: 8' in out
        assert '# Stored Survey' in out

    def test_not_found_exits_1(self, monkeypatch, tmp_path):
        '''Non-existent survey ID causes exit(1).'''
        from agents.gantt.cli import cmd_release_survey_get

        monkeypatch.setenv('GANTT_RELEASE_SURVEY_DIR', str(tmp_path / 'store'))

        args = SimpleNamespace(
            survey_id='nonexistent',
            project=None,
            output=None,
            env=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_release_survey_get(args)

        assert exc_info.value.code == 1


# ===================================================================
# cmd_release_survey_list — list stored surveys
# ===================================================================

class TestCmdReleaseSurveyList:
    '''Tests for the release-survey-list handler.'''

    def test_lists_surveys(self, monkeypatch, tmp_path, capsys):
        '''Stored surveys are listed in tabular format.'''
        from agents.gantt.cli import cmd_release_survey_list
        from agents.gantt.state.release_survey_store import GanttReleaseSurveyStore

        store = GanttReleaseSurveyStore(storage_dir=str(tmp_path / 'store'))
        store.save_survey(
            {
                'survey_id': 'sur-ls-001',
                'project_key': 'STL',
                'created_at': '2026-03-27T12:00:00+00:00',
                'scope_label': 'CN6000',
                'releases_surveyed': ['12.2.0.x'],
                'release_summaries': [],
                'total_tickets': 10,
                'done_count': 5,
                'in_progress_count': 3,
                'remaining_count': 1,
                'blocked_count': 1,
                'stale_count': 0,
                'unassigned_count': 0,
            },
            summary_markdown='# Survey 1',
        )
        store.save_survey(
            {
                'survey_id': 'sur-ls-002',
                'project_key': 'STL',
                'created_at': '2026-03-28T12:00:00+00:00',
                'scope_label': 'CN6000',
                'releases_surveyed': ['12.2.0.x'],
                'release_summaries': [],
                'total_tickets': 8,
                'done_count': 6,
                'in_progress_count': 1,
                'remaining_count': 1,
                'blocked_count': 0,
                'stale_count': 0,
                'unassigned_count': 0,
            },
            summary_markdown='# Survey 2',
        )
        monkeypatch.setenv('GANTT_RELEASE_SURVEY_DIR', str(tmp_path / 'store'))

        args = SimpleNamespace(project='STL', limit=10, env=None)

        with pytest.raises(SystemExit) as exc_info:
            cmd_release_survey_list(args)

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert 'sur-ls-001' in out
        assert 'sur-ls-002' in out
        assert 'Total stored surveys: 2' in out

    def test_empty_list(self, monkeypatch, tmp_path, capsys):
        '''No surveys prints informational message and exits 0.'''
        from agents.gantt.cli import cmd_release_survey_list

        monkeypatch.setenv('GANTT_RELEASE_SURVEY_DIR', str(tmp_path / 'empty'))

        args = SimpleNamespace(project=None, limit=10, env=None)

        with pytest.raises(SystemExit) as exc_info:
            cmd_release_survey_list(args)

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert 'No stored release surveys found.' in out


# ===================================================================
# cmd_poll — scheduled planning/monitoring loop
# ===================================================================

class TestCmdPoll:
    '''Tests for the poll handler.'''

    def test_success_exits_0(self, monkeypatch, tmp_path, capsys):
        '''Successful poller run prints cycle summary and exits 0.'''
        from agents.gantt.cli import cmd_poll
        from agents.gantt import agent as gantt_agent

        poller_result = {
            'ok': True,
            'cycle_summaries': [
                {
                    'cycle_number': 1,
                    'task_count': 2,
                    'notification_count': 0,
                    'ok': True,
                    'errors': [],
                },
            ],
            'last_tick': {
                'tasks': [
                    {
                        'task_type': 'planning_snapshot',
                        'stored': {'snapshot_id': 'snap-poll-001'},
                    },
                    {
                        'task_type': 'release_monitor',
                        'stored': {'report_id': 'rep-poll-001'},
                    },
                    {
                        'task_type': 'release_survey',
                        'stored': {'survey_id': 'sur-poll-001'},
                    },
                ],
            },
        }

        fake_cls = _make_fake_gantt_agent(poller_result=poller_result)
        monkeypatch.setattr(gantt_agent, 'GanttProjectPlannerAgent', fake_cls)

        args = SimpleNamespace(
            project='STL',
            planning_horizon=90,
            releases=None,
            scope_label=None,
            survey_mode='feature-dev',
            run_release_monitor=False,
            run_release_survey=False,
            include_done=False,
            include_gap_analysis=True,
            include_bug_report=True,
            include_velocity=True,
            include_readiness=True,
            compare_to_previous=True,
            evidence=None,
            poll_interval=300,
            max_cycles=1,
            notify_shannon=False,
            shannon_url='http://localhost:8200',
            limit=200,
            output=None,
            env=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_poll(args)

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert 'Cycle 1:' in out
        assert '2 task(s)' in out
        assert 'snap-poll-001' in out
        assert 'rep-poll-001' in out
        assert 'sur-poll-001' in out

    def test_failure_exits_1(self, monkeypatch, tmp_path, capsys):
        '''Poller returning ok=False causes exit(1).'''
        from agents.gantt.cli import cmd_poll
        from agents.gantt import agent as gantt_agent

        poller_result = {
            'ok': False,
            'cycle_summaries': [
                {
                    'cycle_number': 1,
                    'task_count': 0,
                    'notification_count': 0,
                    'ok': False,
                    'errors': ['Connection timeout'],
                },
            ],
            'last_tick': {'tasks': []},
        }

        fake_cls = _make_fake_gantt_agent(poller_result=poller_result)
        monkeypatch.setattr(gantt_agent, 'GanttProjectPlannerAgent', fake_cls)

        args = SimpleNamespace(
            project='STL',
            planning_horizon=90,
            releases=None,
            scope_label=None,
            survey_mode='feature-dev',
            run_release_monitor=False,
            run_release_survey=False,
            include_done=False,
            include_gap_analysis=True,
            include_bug_report=True,
            include_velocity=True,
            include_readiness=True,
            compare_to_previous=True,
            evidence=None,
            poll_interval=300,
            max_cycles=1,
            notify_shannon=False,
            shannon_url='http://localhost:8200',
            limit=200,
            output=None,
            env=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_poll(args)

        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert 'Connection timeout' in out


# ===================================================================
# cmd_snapshot_get with --output (file export path)
# ===================================================================

class TestCmdSnapshotGetWithOutput:
    '''Tests for snapshot-get with file export.'''

    def test_exports_json_and_markdown(self, monkeypatch, tmp_path, capsys):
        '''snapshot-get with --output writes JSON + Markdown files.'''
        from agents.gantt.cli import cmd_snapshot_get
        from agents.gantt.state.snapshot_store import GanttSnapshotStore

        store = GanttSnapshotStore(storage_dir=str(tmp_path / 'store'))
        store.save_snapshot(
            {
                'snapshot_id': 'snap-exp-001',
                'project_key': 'STL',
                'created_at': '2026-03-28T12:00:00+00:00',
                'planning_horizon_days': 90,
                'backlog_overview': {'total_issues': 7, 'blocked_issues': 1, 'stale_issues': 0},
                'milestones': [{'name': '12.1.0'}],
                'risks': [],
                'dependency_graph': {'edge_count': 2},
                'summary_markdown': '# Export Test',
            },
            summary_markdown='# Export Test',
        )
        monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'store'))

        export_path = tmp_path / 'exported.json'
        args = SimpleNamespace(
            snapshot_id='snap-exp-001',
            project='STL',
            output=str(export_path),
            env=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_snapshot_get(args)

        assert exc_info.value.code == 0
        assert export_path.exists()
        assert (tmp_path / 'exported.md').exists()

        data = json.loads(export_path.read_text(encoding='utf-8'))
        assert data['snapshot_id'] == 'snap-exp-001'
        md_content = (tmp_path / 'exported.md').read_text(encoding='utf-8')
        assert '# Export Test' in md_content
