import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agents.base import AgentResponse
from agents.gantt_models import (
    BugSummary,
    DependencyGraph,
    PlanningRequest,
    PlanningSnapshot,
    ReleaseMonitorReport,
    ReleaseSurveyRequest,
)
from tools.base import ToolResult


def test_gantt_agent_create_snapshot_builds_milestones_dependencies_and_risks(
    monkeypatch: pytest.MonkeyPatch,
    fake_issue_resource_factory,
):
    from agents.gantt_agent import GanttProjectPlannerAgent
    from agents import gantt_agent

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'gantt prompt'),
    )

    jira = MagicMock()

    blocking_story = fake_issue_resource_factory(
        key='STL-101',
        summary='Implement planning snapshot',
        issue_type='Story',
        status='In Progress',
        priority='High',
        assignee='Jane Dev',
        fix_versions=['12.1.0'],
        updated='2026-02-15T10:00:00.000+0000',
        issuelinks=[
            {
                'type': {
                    'name': 'Blocks',
                    'outward': 'blocks',
                    'inward': 'is blocked by',
                },
                'outwardIssue': {'key': 'STL-102'},
            }
        ],
    )

    dependent_story = fake_issue_resource_factory(
        key='STL-102',
        summary='Add milestone view',
        issue_type='Story',
        status='Open',
        priority='High',
        assignee=None,
        fix_versions=['12.1.0'],
        updated='2026-02-20T10:00:00.000+0000',
    )

    stale_bug = fake_issue_resource_factory(
        key='STL-103',
        summary='Old backlog bug',
        issue_type='Bug',
        status='Blocked',
        priority='P1-Critical',
        assignee=None,
        fix_versions=[],
        updated='2026-01-01T10:00:00.000+0000',
    )
    stale_bug.raw['fields']['fixVersions'] = []

    jira.search_issues.return_value = [blocking_story, dependent_story, stale_bug]

    monkeypatch.setattr(gantt_agent, 'get_jira', lambda: jira)
    monkeypatch.setattr(
        gantt_agent,
        'get_project_info',
        lambda project_key: ToolResult.success({
            'key': project_key,
            'name': 'Storage Team',
            'url': 'https://example.test/browse/STL',
        }),
    )
    monkeypatch.setattr(
        gantt_agent,
        'get_releases',
        lambda project_key, include_released=True, include_unreleased=True: ToolResult.success([
            {
                'id': '1001',
                'name': '12.1.0',
                'released': False,
                'releaseDate': '2026-04-01',
            }
        ]),
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_utc_now',
        staticmethod(lambda: datetime(2026, 3, 15, tzinfo=timezone.utc)),
    )

    agent = GanttProjectPlannerAgent()
    snapshot = agent.create_snapshot(
        PlanningRequest(project_key='STL', planning_horizon_days=90, limit=50)
    )

    assert snapshot.project_key == 'STL'
    assert snapshot.backlog_overview['total_issues'] == 3
    assert snapshot.backlog_overview['blocked_issues'] == 2
    assert snapshot.backlog_overview['stale_issues'] == 1

    milestone_names = [milestone.name for milestone in snapshot.milestones]
    assert '12.1.0' in milestone_names
    assert 'Unscheduled Backlog' in milestone_names

    risk_types = {risk.risk_type for risk in snapshot.risks}
    assert 'stale_work' in risk_types
    assert 'blocked_work' in risk_types
    assert 'unassigned_priority_work' in risk_types
    assert 'unscheduled_work' in risk_types

    assert snapshot.dependency_graph.edge_count == 1
    assert 'STL-102' in snapshot.dependency_graph.blocked_keys
    assert 'STL-103' in snapshot.dependency_graph.unscheduled_keys
    assert 'Build, test, release' in snapshot.evidence_gaps[0]
    assert '## Milestone Proposals' in snapshot.summary_markdown


def test_gantt_agent_run_returns_snapshot_metadata(monkeypatch: pytest.MonkeyPatch):
    from agents.gantt_agent import GanttProjectPlannerAgent

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'gantt prompt'),
    )
    snapshot = PlanningSnapshot(
        project_key='STL',
        summary_markdown='# Snapshot\n\nBody',
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        'create_snapshot',
        lambda self, request: snapshot,
    )

    agent = GanttProjectPlannerAgent(project_key='STL')
    response = agent.run({'project_key': 'STL', 'planning_horizon_days': 120})

    assert response.success is True
    assert response.content == '# Snapshot\n\nBody'
    assert response.metadata['planning_snapshot']['project_key'] == 'STL'


def test_gantt_agent_tick_persists_results_and_posts_notifications(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents import pm_runtime
    from agents.gantt_agent import GanttProjectPlannerAgent

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {'ok': True}

    notification_calls = []

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'gantt prompt'),
    )
    monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'snapshots'))
    monkeypatch.setenv('GANTT_RELEASE_MONITOR_DIR', str(tmp_path / 'reports'))
    monkeypatch.setattr(
        pm_runtime.requests,
        'post',
        lambda url, json=None, timeout=15: (
            notification_calls.append({'url': url, 'json': json, 'timeout': timeout})
            or _FakeResponse()
        ),
    )

    snapshot = PlanningSnapshot(
        project_key='STL',
        backlog_overview={'total_issues': 4, 'blocked_issues': 1},
        dependency_graph=DependencyGraph(),
        summary_markdown='# Snapshot',
    )
    snapshot.snapshot_id = 'snap-poll'

    report = ReleaseMonitorReport(
        project_key='STL',
        releases_monitored=['12.1.1.x'],
        bug_summaries=[
            BugSummary(
                release='12.1.1.x',
                total_bugs=5,
                by_priority={'P0': 1, 'P1': 2},
            )
        ],
        summary_markdown='# Release Monitor',
    )
    report.report_id = 'rep-poll'

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        'create_snapshot',
        lambda self, request: snapshot,
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        'create_release_monitor',
        lambda self, request: report,
    )

    agent = GanttProjectPlannerAgent(project_key='STL')
    result = agent.tick({
        'project_key': 'STL',
        'run_planning': True,
        'run_release_monitor': True,
        'releases': ['12.1.1.x'],
        'notify_shannon': True,
        'shannon_base_url': 'http://shannon.test',
    })

    assert result['ok'] is True
    assert len(result['tasks']) == 2
    assert len(result['notifications']) == 2
    assert (tmp_path / 'snapshots' / 'STL' / 'snap-poll' / 'snapshot.json').exists()
    assert (tmp_path / 'reports' / 'STL' / 'rep-poll' / 'report.json').exists()
    assert notification_calls[0]['url'] == 'http://shannon.test/v1/bot/notify'


def test_gantt_agent_create_release_monitor_uses_previous_report_history(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents import gantt_agent as gantt_agent_module
    from agents.gantt_agent import GanttProjectPlannerAgent
    from agents.gantt_models import ReleaseMonitorRequest
    from core import release_tracking as release_tracking_module
    from core.release_tracking import ReleaseSnapshot
    from state.gantt_release_monitor_store import GanttReleaseMonitorStore

    class _FixedReadinessDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 3, 25, 12, 0, tzinfo=tz or timezone.utc)

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'gantt prompt'),
    )
    monkeypatch.setattr(release_tracking_module, 'datetime', _FixedReadinessDateTime)
    monkeypatch.setenv('GANTT_RELEASE_MONITOR_DIR', str(tmp_path / 'reports'))

    previous_tickets = [
        {
            'key': 'STL-100',
            'summary': 'Carry-over bug',
            'status': 'Open',
            'priority': 'P1-Critical',
            'issuetype': 'Bug',
            'assignee': 'Jane Dev',
            'fix_versions': ['12.1.1.x'],
            'components': ['Fabric'],
            'created': '2026-03-10T08:00:00+00:00',
            'updated': '2026-03-20T08:00:00+00:00',
            'resolutiondate': '',
        },
        {
            'key': 'STL-101',
            'summary': 'Will close out',
            'status': 'In Progress',
            'priority': 'P2-High',
            'issuetype': 'Bug',
            'assignee': 'Jane Dev',
            'fix_versions': ['12.1.1.x'],
            'components': ['Fabric'],
            'created': '2026-03-12T08:00:00+00:00',
            'updated': '2026-03-20T08:00:00+00:00',
            'resolutiondate': '',
        },
        {
            'key': 'STL-200',
            'summary': 'Previously closed bug',
            'status': 'Closed',
            'priority': 'P0-Stopper',
            'issuetype': 'Bug',
            'assignee': 'Jane Dev',
            'fix_versions': ['12.1.1.x'],
            'components': ['Fabric'],
            'created': '2026-03-05T08:00:00+00:00',
            'updated': '2026-03-06T08:00:00+00:00',
            'resolutiondate': '2026-03-06T08:00:00+00:00',
        },
    ]

    store = GanttReleaseMonitorStore(storage_dir=str(tmp_path / 'reports'))
    store.save_report(
        {
            'report_id': 'rep-prev',
            'project_key': 'STL',
            'created_at': '2026-03-20T12:00:00+00:00',
            'scope_label': 'cn6000',
            'releases_monitored': ['12.1.1.x'],
            'bug_summaries': [],
            'release_snapshots': {
                '12.1.1.x': {
                    'release': '12.1.1.x',
                    'timestamp': '2026-03-20T12:00:00+00:00',
                    'total_tickets': len(previous_tickets),
                    'tickets': previous_tickets,
                }
            },
            'cycle_time_samples': [
                {
                    'release': '12.1.1.x',
                    'ticket_key': 'STL-200',
                    'component': 'Fabric',
                    'priority': 'P0-Stopper',
                    'duration_hours': 24.0,
                }
            ],
            'summary_markdown': '# Previous Report',
        },
        summary_markdown='# Previous Report',
    )

    current_tickets = [
        {
            'key': 'STL-100',
            'summary': 'Carry-over bug',
            'status': 'Open',
            'priority': 'P0-Stopper',
            'issuetype': 'Bug',
            'assignee': 'Jane Dev',
            'fix_versions': ['12.1.1.x'],
            'components': ['Fabric'],
            'created': '2026-03-10T08:00:00+00:00',
            'updated': '2026-03-20T08:00:00+00:00',
            'resolutiondate': '',
        },
        {
            'key': 'STL-102',
            'summary': 'New active bug',
            'status': 'Open',
            'priority': 'P1-Critical',
            'issuetype': 'Bug',
            'assignee': 'Jane Dev',
            'fix_versions': ['12.1.1.x'],
            'components': ['Fabric'],
            'created': '2026-03-24T08:00:00+00:00',
            'updated': '2026-03-25T08:00:00+00:00',
            'resolutiondate': '',
        },
        {
            'key': 'STL-200',
            'summary': 'Previously closed bug',
            'status': 'Closed',
            'priority': 'P0-Stopper',
            'issuetype': 'Bug',
            'assignee': 'Jane Dev',
            'fix_versions': ['12.1.1.x'],
            'components': ['Fabric'],
            'created': '2026-03-05T08:00:00+00:00',
            'updated': '2026-03-06T08:00:00+00:00',
            'resolutiondate': '2026-03-06T08:00:00+00:00',
        },
        {
            'key': 'STL-201',
            'summary': 'Newly closed bug',
            'status': 'Closed',
            'priority': 'P1-Critical',
            'issuetype': 'Bug',
            'assignee': 'Jane Dev',
            'fix_versions': ['12.1.1.x'],
            'components': ['Fabric'],
            'created': '2026-03-19T08:00:00+00:00',
            'updated': '2026-03-20T08:00:00+00:00',
            'resolutiondate': '2026-03-20T08:00:00+00:00',
        },
        {
            'key': 'STL-300',
            'summary': 'Story should not appear in bug deltas',
            'status': 'Open',
            'priority': 'High',
            'issuetype': 'Story',
            'assignee': 'Jane Dev',
            'fix_versions': ['12.1.1.x'],
            'components': ['Fabric'],
            'created': '2026-03-24T08:00:00+00:00',
            'updated': '2026-03-25T08:00:00+00:00',
            'resolutiondate': '',
        },
    ]

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_query_release_tickets',
        lambda self, release, scope_label=None: list(current_tickets),
    )
    monkeypatch.setattr(
        gantt_agent_module,
        'build_release_snapshot',
        lambda tickets, release: ReleaseSnapshot(
            release=release,
            timestamp='2026-03-25T12:00:00+00:00',
            total_tickets=len(tickets),
            tickets=[dict(ticket) for ticket in tickets],
        ),
    )

    report = GanttProjectPlannerAgent(project_key='STL').create_release_monitor(
        ReleaseMonitorRequest(
            project_key='STL',
            releases=['12.1.1.x'],
            scope_label='cn6000',
            include_gap_analysis=False,
        )
    )

    bug_summary = report.bug_summaries[0]
    assert bug_summary.new_since_last == ['STL-102', 'STL-201']
    assert bug_summary.closed_since_last == ['STL-101']
    assert bug_summary.priority_changes == [
        {'key': 'STL-100', 'from': 'P1-Critical', 'to': 'P0-Stopper'}
    ]

    assert report.delta['comparison_basis'] == 'previous_report'
    assert report.delta['previous_report_id'] == 'rep-prev'
    assert report.delta['new_tickets'] == [
        {'release': '12.1.1.x', 'key': 'STL-102'},
        {'release': '12.1.1.x', 'key': 'STL-201'},
    ]
    assert report.delta['closed_tickets'] == [
        {'release': '12.1.1.x', 'key': 'STL-101'}
    ]
    assert report.delta['priority_changes'] == [
        {
            'release': '12.1.1.x',
            'key': 'STL-100',
            'from': 'P1-Critical',
            'to': 'P0-Stopper',
        }
    ]

    assert report.release_snapshots['12.1.1.x']['total_tickets'] == 5
    assert {item['ticket_key'] for item in report.cycle_time_samples} == {
        'STL-200',
        'STL-201',
    }
    assert len(report.cycle_time_samples) == 2

    stats_by_priority = {
        item['priority']: item for item in report.cycle_time_stats
    }
    assert stats_by_priority['P0-Stopper']['sample_size'] == 1
    assert stats_by_priority['P1-Critical']['sample_size'] == 1
    assert report.readiness['release'] == '12.1.1.x'
    assert report.readiness['daily_close_rate'] > 0
    assert 'STL-100' in report.readiness['stale_tickets']
    assert 'New since last' in report.summary_markdown


def test_gantt_agent_create_release_survey_buckets_done_active_and_remaining(
    monkeypatch: pytest.MonkeyPatch,
):
    from agents.gantt_agent import GanttProjectPlannerAgent

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'gantt prompt'),
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_query_release_tickets',
        lambda self, release, scope_label=None: [
            {
                'key': 'STL-401',
                'summary': 'Completed work',
                'status': 'Closed',
                'priority': 'P2-High',
                'issuetype': 'Story',
                'assignee': 'Jane Dev',
                'reporter': 'PM',
                'components': ['Fabric'],
                'product_family': [{'value': 'CN6000'}],
                'labels': ['CN6000'],
                'created': '2026-03-10T08:00:00+00:00',
                'updated': '2026-03-20T08:00:00+00:00',
                'resolutiondate': '2026-03-21T08:00:00+00:00',
                'url': 'https://example.test/browse/STL-401',
            },
            {
                'key': 'STL-402',
                'summary': 'Active feature work',
                'status': 'In Progress',
                'priority': 'P1-Critical',
                'issuetype': 'Task',
                'assignee': 'Jane Dev',
                'reporter': 'PM',
                'components': ['Fabric'],
                'product_family': [{'value': 'CN5000'}, {'value': 'CN6000'}],
                'labels': ['CN6000'],
                'created': '2026-03-12T08:00:00+00:00',
                'updated': '2026-03-25T08:00:00+00:00',
                'resolutiondate': '',
                'url': 'https://example.test/browse/STL-402',
            },
            {
                'key': 'STL-403',
                'summary': 'Blocked work',
                'status': 'Blocked',
                'priority': 'P0-Stopper',
                'issuetype': 'Task',
                'assignee': 'Unassigned',
                'reporter': 'PM',
                'components': ['Platform'],
                'product_family': ['CN6000'],
                'labels': ['CN6000'],
                'created': '2026-03-11T08:00:00+00:00',
                'updated': '2026-03-15T08:00:00+00:00',
                'resolutiondate': '',
                'url': 'https://example.test/browse/STL-403',
            },
            {
                'key': 'STL-404',
                'summary': 'Not started work',
                'status': 'Open',
                'priority': 'P3-Medium',
                'issuetype': 'Story',
                'assignee': 'Unassigned',
                'reporter': 'PM',
                'components': [],
                'product_family': ['CN5000'],
                'labels': ['CN6000'],
                'created': '2026-03-09T08:00:00+00:00',
                'updated': '2026-02-10T08:00:00+00:00',
                'resolutiondate': '',
                'url': 'https://example.test/browse/STL-404',
            },
            {
                'key': 'STL-405',
                'summary': 'Bug should stay out of feature survey',
                'status': 'Open',
                'priority': 'P1-Critical',
                'issuetype': 'Bug',
                'assignee': 'Jane Dev',
                'reporter': 'PM',
                'components': ['Fabric'],
                'labels': ['CN6000'],
                'created': '2026-03-08T08:00:00+00:00',
                'updated': '2026-03-25T08:00:00+00:00',
                'resolutiondate': '',
                'url': 'https://example.test/browse/STL-405',
            },
        ],
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_utc_now',
        staticmethod(lambda: datetime(2026, 3, 25, tzinfo=timezone.utc)),
    )

    report = GanttProjectPlannerAgent(project_key='STL').create_release_survey(
        ReleaseSurveyRequest(
            project_key='STL',
            releases=['12.2.0.x'],
            scope_label='CN6000',
        )
    )

    assert report.total_tickets == 4
    assert report.done_count == 1
    assert report.in_progress_count == 1
    assert report.remaining_count == 1
    assert report.blocked_count == 1
    assert report.stale_count == 1
    assert report.unassigned_count == 2
    assert report.survey_mode == 'feature_dev'

    release_summary = report.release_summaries[0]
    assert release_summary.release == '12.2.0.x'
    assert release_summary.done_tickets[0]['key'] == 'STL-401'
    assert release_summary.in_progress_tickets[0]['key'] == 'STL-402'
    assert release_summary.blocked_tickets[0]['key'] == 'STL-403'
    assert release_summary.remaining_tickets[0]['key'] == 'STL-404'
    assert release_summary.in_progress_tickets[0]['product_family_csv'] == 'CN5000, CN6000'
    assert release_summary.remaining_tickets[0]['product_family_csv'] == 'CN5000'
    assert release_summary.component_breakdown['Fabric'] == 2
    assert release_summary.component_breakdown['Platform'] == 1
    assert release_summary.component_breakdown['Unspecified'] == 1
    assert '## 12.2.0.x' in report.summary_markdown
    assert '### In Progress (1)' in report.summary_markdown
    assert '### Done (1)' in report.summary_markdown
    assert 'Feature Dev' in report.summary_markdown
    assert '[STL-402](https://example.test/browse/STL-402)' in report.summary_markdown
    assert '[STL-401](https://example.test/browse/STL-401)' in report.summary_markdown


def test_gantt_agent_create_release_survey_bug_mode_only_includes_bugs(
    monkeypatch: pytest.MonkeyPatch,
):
    from agents.gantt_agent import GanttProjectPlannerAgent

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'gantt prompt'),
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_query_release_tickets',
        lambda self, release, scope_label=None: [
            {
                'key': 'STL-501',
                'summary': 'Closed bug',
                'status': 'Closed',
                'priority': 'P1-High',
                'issuetype': 'Bug',
                'assignee': 'Owner',
                'reporter': 'QA',
                'components': ['Fabric'],
                'labels': ['CN6000'],
                'created': '2026-03-10T08:00:00+00:00',
                'updated': '2026-03-21T08:00:00+00:00',
                'resolutiondate': '2026-03-21T08:00:00+00:00',
                'url': 'https://example.test/browse/STL-501',
            },
            {
                'key': 'STL-502',
                'summary': 'Active bug',
                'status': 'In Progress',
                'priority': 'P0-Stopper',
                'issuetype': 'Bug',
                'assignee': 'Owner',
                'reporter': 'QA',
                'components': ['Platform'],
                'labels': ['CN6000'],
                'created': '2026-03-11T08:00:00+00:00',
                'updated': '2026-03-24T08:00:00+00:00',
                'resolutiondate': '',
                'url': 'https://example.test/browse/STL-502',
            },
            {
                'key': 'STL-503',
                'summary': 'Story should stay out of bug survey',
                'status': 'Open',
                'priority': 'P2-Medium',
                'issuetype': 'Story',
                'assignee': 'Owner',
                'reporter': 'PM',
                'components': ['Platform'],
                'labels': ['CN6000'],
                'created': '2026-03-12T08:00:00+00:00',
                'updated': '2026-03-22T08:00:00+00:00',
                'resolutiondate': '',
                'url': 'https://example.test/browse/STL-503',
            },
        ],
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_utc_now',
        staticmethod(lambda: datetime(2026, 3, 25, tzinfo=timezone.utc)),
    )

    report = GanttProjectPlannerAgent(project_key='STL').create_release_survey(
        ReleaseSurveyRequest(
            project_key='STL',
            releases=['12.2.0.x'],
            scope_label='CN6000',
            survey_mode='bug',
        )
    )

    assert report.survey_mode == 'bug'
    assert report.total_tickets == 2
    assert report.done_count == 1
    assert report.in_progress_count == 1
    assert report.remaining_count == 0
    assert report.blocked_count == 0
    assert report.release_summaries[0].issue_type_breakdown == {'Bug': 2}


def test_gantt_release_survey_markdown_sorts_in_progress_and_remaining_by_priority():
    from agents.gantt_agent import GanttProjectPlannerAgent
    from agents.gantt_models import ReleaseSurveyReport, ReleaseSurveyReleaseSummary

    manager_names = {
        'Owner': 'Manager One',
    }

    original_lookup = GanttProjectPlannerAgent._lookup_release_survey_manager_name
    GanttProjectPlannerAgent._lookup_release_survey_manager_name = (
        lambda assignee, manager_lookup=None: manager_names.get(
            str(assignee or ''),
            'Manager Not Found',
        )
    )

    try:
        report = ReleaseSurveyReport(
            project_key='STL',
            created_at='2026-03-25T12:00:00+00:00',
            releases_surveyed=['12.2.0.x'],
            release_summaries=[
                ReleaseSurveyReleaseSummary(
                    release='12.2.0.x',
                    total_tickets=4,
                    in_progress_tickets=[
                        {
                            'key': 'STL-9102',
                            'summary': 'Lower priority progress item',
                            'product_family_csv': 'CN6000',
                            'status': 'In Progress',
                            'assignee': 'Owner',
                            'priority': 'P3-Medium',
                            'updated': '2026-03-20T00:00:00+00:00',
                            'url': 'https://example.test/browse/STL-9102',
                            'age_days': 1,
                        },
                        {
                            'key': 'STL-9101',
                            'summary': 'Higher priority progress item',
                            'product_family_csv': 'CN5000, CN6000',
                            'status': 'In Progress',
                            'assignee': 'Owner',
                            'priority': 'P1-Critical',
                            'updated': '2026-03-19T00:00:00+00:00',
                            'url': 'https://example.test/browse/STL-9101',
                            'age_days': 3,
                        },
                    ],
                    remaining_tickets=[
                        {
                            'key': 'STL-9202',
                            'summary': 'Lower priority remaining item',
                            'product_family_csv': 'CN5000',
                            'status': 'Open',
                            'assignee': 'Owner',
                            'priority': 'P4-Low',
                            'updated': '2026-03-18T00:00:00+00:00',
                            'url': 'https://example.test/browse/STL-9202',
                            'age_days': 2,
                        },
                        {
                            'key': 'STL-9201',
                            'summary': 'Higher priority remaining item',
                            'product_family_csv': 'CN6000',
                            'status': 'Open',
                            'assignee': 'Owner',
                            'priority': 'P0-Stopper',
                            'updated': '2026-03-17T00:00:00+00:00',
                            'url': 'https://example.test/browse/STL-9201',
                            'age_days': 5,
                        },
                    ],
                )
            ],
        )

        summary_markdown = GanttProjectPlannerAgent._format_release_survey_summary(
            report
        )
    finally:
        GanttProjectPlannerAgent._lookup_release_survey_manager_name = original_lookup

    assert summary_markdown.index('[STL-9101]') < summary_markdown.index('[STL-9102]')
    assert summary_markdown.index('[STL-9201]') < summary_markdown.index('[STL-9202]')
    assert '| Ticket | Summary | Product Family | Status | Assignee | Manager | Priority | Updated |' in summary_markdown
    assert '| [STL-9101](https://example.test/browse/STL-9101) | Higher priority progress item | CN5000, CN6000 | In Progress | Owner | Manager One | P1-Critical | 2026-03-19 |' in summary_markdown


def test_gantt_release_survey_manager_lookup_normalizes_jira_assignee_names():
    from agents.gantt_agent import GanttProjectPlannerAgent

    manager_lookup = {
        'denny dalessandro': 'Heqing Zhu',
        'nick child': 'Heqing Zhu',
        'samuel cook': 'Eugene Novak',
    }

    assert (
        GanttProjectPlannerAgent._lookup_release_survey_manager_name(
            'Child, Nicholas',
            manager_lookup=manager_lookup,
        )
        == 'Heqing Zhu'
    )
    assert (
        GanttProjectPlannerAgent._lookup_release_survey_manager_name(
            'Cook, Sam',
            manager_lookup=manager_lookup,
        )
        == 'Eugene Novak'
    )
    assert (
        GanttProjectPlannerAgent._lookup_release_survey_manager_name(
            'Dalessandro, Dennis',
            manager_lookup=manager_lookup,
        )
        == 'Heqing Zhu'
    )
    assert (
        GanttProjectPlannerAgent._lookup_release_survey_manager_name(
            'Unknown Person',
            manager_lookup=manager_lookup,
        )
        == 'Manager Not Found'
    )


def test_gantt_release_survey_builds_family_breakouts_and_open_epic_analysis(
    monkeypatch: pytest.MonkeyPatch,
):
    from agents.gantt_agent import GanttProjectPlannerAgent
    from agents import gantt_agent as gantt_agent_module

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'gantt prompt'),
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_query_release_tickets',
        lambda self, release, scope_label=None: [
            {
                'key': 'STL-5000',
                'summary': 'CN5000 platform epic',
                'status': 'Open',
                'priority': 'P2-High',
                'issuetype': 'Epic',
                'assignee': 'Owner',
                'reporter': 'PM',
                'components': ['Platform'],
                'product_family': ['CN5000'],
                'labels': ['CN5000'],
                'created': '2026-03-01T08:00:00+00:00',
                'updated': '2026-03-25T08:00:00+00:00',
                'resolutiondate': '',
                'url': 'https://example.test/browse/STL-5000',
            },
            {
                'key': 'STL-6000',
                'summary': 'CN6000 service epic',
                'status': 'In Progress',
                'priority': 'P1-Critical',
                'issuetype': 'Epic',
                'assignee': 'Owner',
                'reporter': 'PM',
                'components': ['Services'],
                'product_family': ['CN6000'],
                'labels': ['CN6000'],
                'created': '2026-03-02T08:00:00+00:00',
                'updated': '2026-03-25T08:00:00+00:00',
                'resolutiondate': '',
                'url': 'https://example.test/browse/STL-6000',
            },
            {
                'key': 'STL-7000',
                'summary': 'Shared integration work',
                'status': 'In Progress',
                'priority': 'P3-Medium',
                'issuetype': 'Story',
                'assignee': 'Owner',
                'reporter': 'PM',
                'components': ['Integration'],
                'product_family': ['CN5000', 'CN6000'],
                'labels': ['CN5000', 'CN6000'],
                'created': '2026-03-03T08:00:00+00:00',
                'updated': '2026-03-24T08:00:00+00:00',
                'resolutiondate': '',
                'url': 'https://example.test/browse/STL-7000',
            },
        ],
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_utc_now',
        staticmethod(lambda: datetime(2026, 3, 25, tzinfo=timezone.utc)),
    )

    def _fake_hierarchy(root_key, limit=500):
        if root_key == 'STL-5000':
            return ToolResult.success([
                {
                    'key': 'STL-5000',
                    'summary': 'CN5000 platform epic',
                    'type': 'Epic',
                    'status': 'Open',
                    'priority': 'P2-High',
                    'assignee': 'Owner',
                    'fix_versions': ['12.2.0.x'],
                    'components': ['Platform'],
                    'labels': ['CN5000'],
                    'url': 'https://example.test/browse/STL-5000',
                    'depth': 0,
                },
                {
                    'key': 'STL-5100',
                    'summary': 'Open CN5000 story',
                    'type': 'Story',
                    'status': 'In Progress',
                    'priority': 'P2-High',
                    'assignee': 'Owner',
                    'fix_versions': ['12.2.0.x'],
                    'components': ['Platform'],
                    'labels': ['CN5000'],
                    'url': 'https://example.test/browse/STL-5100',
                    'depth': 1,
                },
                {
                    'key': 'STL-5101',
                    'summary': 'Closed CN5000 task',
                    'type': 'Task',
                    'status': 'Closed',
                    'priority': 'P3-Medium',
                    'assignee': 'Owner',
                    'fix_versions': ['12.2.0.x'],
                    'components': ['Platform'],
                    'labels': ['CN5000'],
                    'url': 'https://example.test/browse/STL-5101',
                    'depth': 1,
                },
                {
                    'key': 'STL-5102',
                    'summary': 'Bug child should not appear in feature mode',
                    'type': 'Bug',
                    'status': 'Open',
                    'priority': 'P1-Critical',
                    'assignee': 'Owner',
                    'fix_versions': ['12.2.0.x'],
                    'components': ['Platform'],
                    'labels': ['CN5000'],
                    'url': 'https://example.test/browse/STL-5102',
                    'depth': 1,
                },
            ])

        return ToolResult.success([
            {
                'key': 'STL-6000',
                'summary': 'CN6000 service epic',
                'type': 'Epic',
                'status': 'In Progress',
                'priority': 'P1-Critical',
                'assignee': 'Owner',
                'fix_versions': ['12.2.0.x'],
                'components': ['Services'],
                'labels': ['CN6000'],
                'url': 'https://example.test/browse/STL-6000',
                'depth': 0,
            },
            {
                'key': 'STL-6100',
                'summary': 'Open CN6000 task',
                'type': 'Task',
                'status': 'Open',
                'priority': 'P2-High',
                'assignee': 'Owner',
                'fix_versions': ['12.2.0.x'],
                'components': ['Services'],
                'labels': ['CN6000'],
                'url': 'https://example.test/browse/STL-6100',
                'depth': 1,
            },
        ])

    monkeypatch.setattr(gantt_agent_module, 'get_children_hierarchy', _fake_hierarchy)

    report = GanttProjectPlannerAgent(project_key='STL').create_release_survey(
        ReleaseSurveyRequest(
            project_key='STL',
            releases=['12.2.0.x'],
            scope_label='CN5000,CN6000',
            survey_mode='feature_dev',
        )
    )

    release_summary = report.release_summaries[0]
    assert release_summary.family_breakdowns['CN5000']['in_progress_tickets'][0]['key'] == 'STL-7000'
    assert release_summary.family_breakdowns['CN6000']['in_progress_tickets'][0]['key'] == 'STL-6000'
    assert release_summary.family_breakdowns['CN5000']['epics'][0]['key'] == 'STL-5000'
    assert release_summary.family_epic_analysis['CN5000'][0]['open_child_count'] == 1
    assert release_summary.family_epic_analysis['CN5000'][0]['open_children'][0]['key'] == 'STL-5100'
    assert release_summary.family_epic_analysis['CN6000'][0]['open_children'][0]['key'] == 'STL-6100'
    assert '#### CN5000 In Progress (1)' in report.summary_markdown
    assert '#### CN6000 Epics (1)' in report.summary_markdown
    assert '#### CN5000 Open Epic Child Analysis (1)' in report.summary_markdown
    assert '- Open type mix: Story=1\n\n| Depth | Ticket | Type | Summary | Status | Assignee | Manager | Priority | Fix Versions |' in report.summary_markdown
    assert '| 1 | [STL-5100](https://example.test/browse/STL-5100) | Story | Open CN5000 story | In Progress | Owner | Manager Not Found | P2-High | 12.2.0.x |' in report.summary_markdown


def test_gantt_agent_query_release_tickets_uses_product_family_scope_clause(
    monkeypatch: pytest.MonkeyPatch,
):
    from agents.gantt_agent import GanttProjectPlannerAgent
    from tools.base import ToolResult
    from agents import gantt_agent as gantt_agent_module

    captured = {}

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'gantt prompt'),
    )

    def _fake_search_tickets(*, jql, limit=500):
        captured['jql'] = jql
        captured['limit'] = limit
        return ToolResult.success([])

    monkeypatch.setattr(gantt_agent_module, 'search_tickets', _fake_search_tickets)

    agent = GanttProjectPlannerAgent(project_key='STL')
    tickets = agent._query_release_tickets('12.2.0.x', 'CN6000')

    assert tickets == []
    assert captured['limit'] == 500
    assert 'fixVersion = "12.2.0.x"' in captured['jql']
    assert '(labels = "CN6000" OR "product family" = "CN6000")' in captured['jql']


def test_gantt_release_survey_confluence_markdown_uses_live_jira_macros():
    from agents.gantt_agent import GanttProjectPlannerAgent
    from agents.gantt_models import ReleaseSurveyReport, ReleaseSurveyReleaseSummary

    report = ReleaseSurveyReport(
        project_key='STL',
        created_at='2026-03-25T12:00:00+00:00',
        scope_label='CN5000,CN6000',
        survey_mode='feature_dev',
        releases_surveyed=['12.2.0.x'],
        release_summaries=[
            ReleaseSurveyReleaseSummary(
                release='12.2.0.x',
                total_tickets=5,
                status_breakdown={
                    'Closed': 1,
                    'In Progress': 2,
                    'Open': 2,
                },
                done_tickets=[
                    {
                        'key': 'STL-9001',
                        'summary': 'Done work',
                        'status': 'Closed',
                        'assignee': 'Owner',
                        'priority': 'P3-Medium',
                        'updated': '2026-03-22T00:00:00+00:00',
                        'url': 'https://example.test/browse/STL-9001',
                        'product_family_csv': 'CN5000',
                    }
                ],
                in_progress_tickets=[
                    {
                        'key': 'STL-9002',
                        'summary': 'Active work',
                        'status': 'In Progress',
                        'assignee': 'Owner',
                        'priority': 'P1-Critical',
                        'updated': '2026-03-23T00:00:00+00:00',
                        'url': 'https://example.test/browse/STL-9002',
                        'product_family_csv': 'CN5000',
                    }
                ],
                remaining_tickets=[
                    {
                        'key': 'STL-9003',
                        'summary': 'Queued work',
                        'status': 'Open',
                        'assignee': 'Owner',
                        'priority': 'P2-High',
                        'updated': '2026-03-24T00:00:00+00:00',
                        'url': 'https://example.test/browse/STL-9003',
                        'product_family_csv': 'CN6000',
                    }
                ],
                family_breakdowns={
                    'CN5000': {
                        'in_progress_tickets': [
                            {
                                'key': 'STL-9002',
                                'status': 'In Progress',
                            }
                        ],
                        'remaining_tickets': [],
                        'epics': [
                            {
                                'key': 'STL-9004',
                                'status': 'Open',
                            }
                        ],
                    },
                    'CN6000': {
                        'in_progress_tickets': [],
                        'remaining_tickets': [
                            {
                                'key': 'STL-9003',
                                'status': 'Open',
                            }
                        ],
                        'epics': [],
                    },
                },
                family_epic_analysis={
                    'CN5000': [
                        {
                            'epic': {
                                'key': 'STL-9004',
                                'summary': 'CN5000 epic',
                                'status': 'Open',
                                'url': 'https://example.test/browse/STL-9004',
                            },
                            'open_child_count': 1,
                            'total_descendant_count': 2,
                            'open_by_type': {'Story': 1},
                            'open_children': [
                                {
                                    'key': 'STL-9005',
                                    'summary': 'Epic child',
                                    'issue_type': 'Story',
                                    'status': 'Open',
                                    'assignee': 'Owner',
                                    'priority': 'P2-High',
                                    'depth': 1,
                                    'fix_version_csv': '12.2.0.x',
                                    'url': 'https://example.test/browse/STL-9005',
                                }
                            ],
                        }
                    ]
                },
            )
        ],
    )

    markdown = GanttProjectPlannerAgent._format_release_survey_confluence_markdown(
        report
    )

    assert '<ac:structured-macro ac:name="jira" ac:schema-version="1" data-layout="full-width">' in markdown
    assert '<ac:parameter ac:name="server">System Jira</ac:parameter>' in markdown
    assert '<ac:parameter ac:name="serverId">332fe428-27be-3c06-ad09-b2cd4d269bee</ac:parameter>' in markdown
    assert '<ac:parameter ac:name="jqlQuery">project = STL AND fixVersion = &quot;12.2.0.x&quot;' in markdown
    assert 'issuetype != Bug' in markdown
    assert '#### CN5000 Epics' in markdown
    assert '#### CN5000 Open Epic Child Analysis (1)' in markdown
    assert 'Snapshot count at publish time: 1. This Jira table stays live after publication.' in markdown


def test_workflow_gantt_poll_runs_poller(monkeypatch: pytest.MonkeyPatch):
    import pm_agent
    from agents import gantt_agent as gantt_agent_module

    class _FakeGanttAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def run_poller(self, spec):
            assert spec['project_key'] == 'STL'
            assert spec['run_release_monitor'] is True
            assert spec['run_release_survey'] is False
            assert spec['survey_mode'] == 'feature-dev'
            assert spec['notify_shannon'] is True
            assert spec['max_cycles'] == 2
            return {
                'ok': True,
                'cycles_run': 2,
                'cycle_summaries': [
                    {
                        'cycle_number': 1,
                        'ok': True,
                        'task_count': 2,
                        'notification_count': 2,
                        'errors': [],
                    },
                    {
                        'cycle_number': 2,
                        'ok': True,
                        'task_count': 2,
                        'notification_count': 2,
                        'errors': [],
                    },
                ],
                'last_tick': {
                    'tasks': [
                        {
                            'task_type': 'planning_snapshot',
                            'stored': {'snapshot_id': 'snap-701'},
                        },
                        {
                            'task_type': 'release_monitor',
                            'stored': {'report_id': 'rep-701'},
                        },
                    ]
                },
            }

    monkeypatch.setattr(gantt_agent_module, 'GanttProjectPlannerAgent', _FakeGanttAgent)
    monkeypatch.setattr(pm_agent, 'output', lambda *args, **kwargs: None)

    args = SimpleNamespace(
        project='STL',
        planning_horizon=90,
        limit=50,
        include_done=False,
        evidence=['build.json'],
        releases='12.1.1.x',
        scope_label=None,
        include_gap_analysis=True,
        include_bug_report=True,
        include_velocity=True,
        include_readiness=True,
        compare_to_previous=True,
        run_release_monitor=True,
        run_release_survey=False,
        survey_mode='feature-dev',
        notify_shannon=True,
        shannon_url='http://shannon.test',
        poll_interval=60,
        max_cycles=2,
    )

    assert pm_agent._workflow_gantt_poll(args) == 0


def test_gantt_agent_loads_evidence_bundle(monkeypatch: pytest.MonkeyPatch, tmp_path):
    from agents.gantt_agent import GanttProjectPlannerAgent

    evidence_path = tmp_path / 'build.json'
    evidence_path.write_text(
        '{"evidence_type": "build", "title": "Build 42", "summary": "stable"}',
        encoding='utf-8',
    )

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'gantt prompt'),
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_project_info',
        lambda self, project_key: {'key': project_key},
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_releases',
        lambda self, project_key: [],
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_backlog_issues',
        lambda self, request: [],
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_build_dependency_graph',
        lambda self, issues: PlanningSnapshot().dependency_graph,
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_build_milestones',
        lambda self, issues, releases, dependency_graph: [],
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_build_risks',
        lambda self, issues, milestones, dependency_graph: [],
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_build_backlog_overview',
        lambda self, issues, milestones, dependency_graph, risks: {'total_issues': 0},
    )

    snapshot = GanttProjectPlannerAgent(project_key='STL').create_snapshot(
        PlanningRequest(
            project_key='STL',
            evidence_paths=[str(evidence_path)],
        )
    )

    assert snapshot.evidence_summary['record_count'] == 1
    assert snapshot.evidence_summary['by_type']['build'] == 1
    assert 'Missing evidence inputs for:' in snapshot.evidence_gaps[0]


def test_gantt_agent_applies_dependency_review_store(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    fake_issue_resource_factory,
):
    from agents.gantt_agent import GanttProjectPlannerAgent
    from agents import gantt_agent
    from state.gantt_dependency_review_store import GanttDependencyReviewStore

    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'gantt prompt'),
    )
    monkeypatch.setenv('GANTT_DEPENDENCY_REVIEW_DIR', str(tmp_path / 'reviews'))

    review_store = GanttDependencyReviewStore(storage_dir=str(tmp_path / 'reviews'))
    review_store.record_review(
        project_key='STL',
        source_key='STL-201',
        target_key='STL-202',
        relationship='blocks',
        accepted=True,
    )
    review_store.record_review(
        project_key='STL',
        source_key='STL-202',
        target_key='STL-203',
        relationship='blocks',
        accepted=False,
    )

    jira = MagicMock()
    jira.search_issues.return_value = [
        fake_issue_resource_factory(
            key='STL-201',
            summary='Foundation task',
            description='',
            issue_type='Story',
            status='In Progress',
            priority='High',
            assignee='Jane Dev',
            fix_versions=['12.1.0'],
            updated='2026-03-01T10:00:00.000+0000',
        ),
        fake_issue_resource_factory(
            key='STL-202',
            summary='Integration task',
            description='Blocked by STL-201. Blocks STL-203.',
            issue_type='Story',
            status='Open',
            priority='High',
            assignee='Jane Dev',
            fix_versions=['12.1.0'],
            updated='2026-03-05T10:00:00.000+0000',
        ),
        fake_issue_resource_factory(
            key='STL-203',
            summary='Validation task',
            description='',
            issue_type='Story',
            status='Open',
            priority='Medium',
            assignee='Jane Dev',
            fix_versions=['12.1.0'],
            updated='2026-03-10T10:00:00.000+0000',
        ),
    ]

    monkeypatch.setattr(gantt_agent, 'get_jira', lambda: jira)
    monkeypatch.setattr(
        gantt_agent,
        'get_project_info',
        lambda project_key: ToolResult.success({'key': project_key, 'name': 'Storage Team'}),
    )
    monkeypatch.setattr(
        gantt_agent,
        'get_releases',
        lambda project_key, include_released=True, include_unreleased=True: ToolResult.success([
            {'id': '1001', 'name': '12.1.0', 'released': False, 'releaseDate': '2026-04-01'}
        ]),
    )
    monkeypatch.setattr(
        GanttProjectPlannerAgent,
        '_utc_now',
        staticmethod(lambda: datetime(2026, 3, 15, tzinfo=timezone.utc)),
    )

    snapshot = GanttProjectPlannerAgent(project_key='STL').create_snapshot(
        PlanningRequest(project_key='STL')
    )

    assert snapshot.dependency_graph.inferred_edge_count == 1
    assert snapshot.dependency_graph.suppressed_edge_count == 1
    assert snapshot.dependency_graph.review_summary == {
        'accepted': 1,
        'pending': 0,
        'rejected': 1,
    }


def test_workflow_gantt_snapshot_writes_json_and_markdown(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    import pm_agent
    from agents import gantt_agent

    class _FakeGanttAgent:
        def __init__(self, project_key=None, **kwargs):
            self.project_key = project_key

        def run(self, input_data):
            return AgentResponse.success_response(
                content='# Gantt Snapshot\n\nSummary',
                metadata={
                    'planning_snapshot': {
                        'snapshot_id': 'snap-001',
                        'project_key': input_data['project_key'],
                        'created_at': '2026-03-15T12:00:00+00:00',
                        'planning_horizon_days': input_data['planning_horizon_days'],
                        'backlog_overview': {'total_issues': 2},
                        'milestones': [],
                        'risks': [],
                        'dependency_graph': {'edge_count': 0},
                    }
                },
            )

    monkeypatch.setattr(gantt_agent, 'GanttProjectPlannerAgent', _FakeGanttAgent)
    monkeypatch.setattr(pm_agent, 'output', lambda *args, **kwargs: None)
    monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'store'))

    output_path = tmp_path / 'snapshot.json'
    args = SimpleNamespace(
        project='STL',
        planning_horizon=90,
        limit=25,
        include_done=False,
        output=str(output_path),
    )

    exit_code = pm_agent._workflow_gantt_snapshot(args)

    assert exit_code == 0
    assert output_path.exists()
    assert (tmp_path / 'snapshot.md').exists()

    snapshot_data = json.loads(output_path.read_text(encoding='utf-8'))
    assert snapshot_data['project_key'] == 'STL'
    assert '# Gantt Snapshot' in (tmp_path / 'snapshot.md').read_text(encoding='utf-8')
    assert (tmp_path / 'store' / 'STL' / 'snap-001' / 'snapshot.json').exists()
    assert (tmp_path / 'store' / 'STL' / 'snap-001' / 'summary.md').exists()


def test_gantt_snapshot_store_save_load_and_list(tmp_path):
    from state.gantt_snapshot_store import GanttSnapshotStore

    store = GanttSnapshotStore(storage_dir=str(tmp_path / 'snapshots'))

    first_summary = store.save_snapshot(
        {
            'snapshot_id': 'snap-001',
            'project_key': 'STL',
            'created_at': '2026-03-14T12:00:00+00:00',
            'planning_horizon_days': 90,
            'backlog_overview': {
                'total_issues': 5,
                'blocked_issues': 2,
                'stale_issues': 1,
            },
            'milestones': [{'name': '12.1.0'}],
            'risks': [{'risk_type': 'blocked_work'}],
            'dependency_graph': {'edge_count': 3},
        },
        summary_markdown='# Snapshot 1',
    )
    store.save_snapshot(
        {
            'snapshot_id': 'snap-002',
            'project_key': 'STL',
            'created_at': '2026-03-15T12:00:00+00:00',
            'planning_horizon_days': 120,
            'backlog_overview': {
                'total_issues': 8,
                'blocked_issues': 1,
                'stale_issues': 0,
            },
            'milestones': [{'name': '12.2.0'}, {'name': 'Unscheduled Backlog'}],
            'risks': [],
            'dependency_graph': {'edge_count': 4},
        },
        summary_markdown='# Snapshot 2',
    )
    store.save_snapshot(
        {
            'snapshot_id': 'snap-003',
            'project_key': 'ABC',
            'created_at': '2026-03-13T12:00:00+00:00',
            'planning_horizon_days': 60,
            'backlog_overview': {'total_issues': 3},
            'milestones': [],
            'risks': [],
            'dependency_graph': {'edge_count': 0},
        },
        summary_markdown='# Snapshot 3',
    )

    record = store.get_snapshot('snap-001')
    assert record is not None
    assert record['snapshot']['project_key'] == 'STL'
    assert record['summary_markdown'] == '# Snapshot 1'
    assert first_summary['storage_dir'].endswith('STL/snap-001')

    listed = store.list_snapshots(project_key='STL')
    assert [item['snapshot_id'] for item in listed] == ['snap-002', 'snap-001']
    assert listed[0]['milestone_count'] == 2
    assert listed[1]['risk_count'] == 1


def test_gantt_release_monitor_store_get_latest_compatible_report(tmp_path):
    from state.gantt_release_monitor_store import GanttReleaseMonitorStore

    store = GanttReleaseMonitorStore(storage_dir=str(tmp_path / 'reports'))

    store.save_report(
        {
            'report_id': 'rep-101',
            'project_key': 'STL',
            'created_at': '2026-03-20T12:00:00+00:00',
            'scope_label': 'cn6000',
            'releases_monitored': ['12.1.1.x'],
            'bug_summaries': [],
            'summary_markdown': '# Compatible',
        },
        summary_markdown='# Compatible',
    )
    store.save_report(
        {
            'report_id': 'rep-102',
            'project_key': 'STL',
            'created_at': '2026-03-21T12:00:00+00:00',
            'scope_label': 'other-scope',
            'releases_monitored': ['12.1.1.x'],
            'bug_summaries': [],
            'summary_markdown': '# Wrong Scope',
        },
        summary_markdown='# Wrong Scope',
    )
    store.save_report(
        {
            'report_id': 'rep-103',
            'project_key': 'STL',
            'created_at': '2026-03-22T12:00:00+00:00',
            'scope_label': 'cn6000',
            'releases_monitored': ['12.2.0.x'],
            'bug_summaries': [],
            'summary_markdown': '# Wrong Release',
        },
        summary_markdown='# Wrong Release',
    )

    record = store.get_latest_compatible_report(
        project_key='STL',
        releases=['12.1.1.x'],
        scope_label='cn6000',
    )

    assert record is not None
    assert record['report']['report_id'] == 'rep-101'


def test_gantt_release_survey_store_save_load_and_list(tmp_path):
    from state.gantt_release_survey_store import GanttReleaseSurveyStore

    store = GanttReleaseSurveyStore(storage_dir=str(tmp_path / 'surveys'))

    first_summary = store.save_survey(
        {
            'survey_id': 'sur-001',
            'project_key': 'STL',
            'created_at': '2026-03-25T12:00:00+00:00',
            'scope_label': 'CN6000',
            'releases_surveyed': ['12.2.0.x'],
            'release_summaries': [],
            'total_tickets': 12,
            'done_count': 5,
            'in_progress_count': 3,
            'remaining_count': 3,
            'blocked_count': 1,
            'stale_count': 2,
            'unassigned_count': 1,
        },
        summary_markdown='# Survey 1',
    )
    store.save_survey(
        {
            'survey_id': 'sur-002',
            'project_key': 'STL',
            'created_at': '2026-03-26T12:00:00+00:00',
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

    record = store.get_survey('sur-001')
    assert record is not None
    assert record['survey']['project_key'] == 'STL'
    assert record['summary_markdown'] == '# Survey 1'
    assert first_summary['storage_dir'].endswith('STL/sur-001')

    listed = store.list_surveys(project_key='STL')
    assert [item['survey_id'] for item in listed] == ['sur-002', 'sur-001']
    assert listed[0]['done_count'] == 6
    assert listed[1]['blocked_count'] == 1


def test_workflow_gantt_snapshot_get_and_list(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    import pm_agent
    from state.gantt_snapshot_store import GanttSnapshotStore

    store = GanttSnapshotStore(storage_dir=str(tmp_path / 'store'))
    store.save_snapshot(
        {
            'snapshot_id': 'snap-010',
            'project_key': 'STL',
            'created_at': '2026-03-15T12:00:00+00:00',
            'planning_horizon_days': 90,
            'backlog_overview': {
                'total_issues': 6,
                'blocked_issues': 2,
                'stale_issues': 1,
            },
            'milestones': [{'name': '12.1.0'}],
            'risks': [{'risk_type': 'blocked_work'}],
            'dependency_graph': {'edge_count': 2},
            'summary_markdown': '# Stored Snapshot\n\nBody',
        },
        summary_markdown='# Stored Snapshot\n\nBody',
    )
    store.save_snapshot(
        {
            'snapshot_id': 'snap-011',
            'project_key': 'STL',
            'created_at': '2026-03-14T12:00:00+00:00',
            'planning_horizon_days': 60,
            'backlog_overview': {'total_issues': 2},
            'milestones': [],
            'risks': [],
            'dependency_graph': {'edge_count': 0},
        },
        summary_markdown='# Older Snapshot',
    )

    monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'store'))

    get_messages = []
    monkeypatch.setattr(pm_agent, 'output', lambda message='', **_kwargs: get_messages.append(str(message)))

    export_path = tmp_path / 'exported_snapshot.json'
    get_args = SimpleNamespace(
        snapshot_id='snap-010',
        project='STL',
        output=str(export_path),
    )

    get_exit_code = pm_agent._workflow_gantt_snapshot_get(get_args)

    assert get_exit_code == 0
    assert export_path.exists()
    assert (tmp_path / 'exported_snapshot.md').exists()
    exported = json.loads(export_path.read_text(encoding='utf-8'))
    assert exported['snapshot_id'] == 'snap-010'
    assert any('Stored in:' in message for message in get_messages)

    list_messages = []
    monkeypatch.setattr(pm_agent, 'output', lambda message='', **_kwargs: list_messages.append(str(message)))

    list_args = SimpleNamespace(project='STL', limit=10)
    list_exit_code = pm_agent._workflow_gantt_snapshot_list(list_args)

    assert list_exit_code == 0
    assert any('snap-010' in message for message in list_messages)
    assert any('snap-011' in message for message in list_messages)


def test_workflow_gantt_release_survey_writes_json_and_markdown(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    import pm_agent
    from agents import gantt_agent
    from agents.gantt_models import ReleaseSurveyReport, ReleaseSurveyReleaseSummary

    class _FakeGanttAgent:
        def __init__(self, project_key=None, **kwargs):
            self.project_key = project_key

        def create_release_survey(self, request):
            assert request.releases == ['12.2.0.x']
            assert request.survey_mode == 'feature-dev'
            survey = ReleaseSurveyReport(
                project_key=request.project_key,
                created_at='2026-03-25T12:00:00+00:00',
                scope_label=request.scope_label or '',
                survey_mode='feature_dev',
                releases_surveyed=request.releases or [],
                release_summaries=[
                    ReleaseSurveyReleaseSummary(
                        release='12.2.0.x',
                        total_tickets=4,
                        done_tickets=[{'key': 'STL-1'}],
                        in_progress_tickets=[{'key': 'STL-2'}],
                        remaining_tickets=[{'key': 'STL-3'}],
                        blocked_tickets=[{'key': 'STL-4'}],
                    )
                ],
                summary_markdown='# Release Survey\n\nSummary',
                output_file=str(tmp_path / 'survey.xlsx'),
            )
            survey.survey_id = 'sur-101'
            return survey

    monkeypatch.setattr(gantt_agent, 'GanttProjectPlannerAgent', _FakeGanttAgent)
    monkeypatch.setattr(pm_agent, 'output', lambda *args, **kwargs: None)
    monkeypatch.setenv('GANTT_RELEASE_SURVEY_DIR', str(tmp_path / 'store'))

    output_path = tmp_path / 'release_survey.json'
    args = SimpleNamespace(
        project='STL',
        releases='12.2.0.x',
        scope_label='CN6000',
        survey_mode='feature-dev',
        output=str(output_path),
    )

    exit_code = pm_agent._workflow_gantt_release_survey(args)

    assert exit_code == 0
    assert output_path.exists()
    assert (tmp_path / 'release_survey.md').exists()

    survey_data = json.loads(output_path.read_text(encoding='utf-8'))
    assert survey_data['project_key'] == 'STL'
    assert survey_data['done_count'] == 1
    assert '# Release Survey' in (tmp_path / 'release_survey.md').read_text(
        encoding='utf-8'
    )
    assert (tmp_path / 'store' / 'STL' / 'sur-101' / 'survey.json').exists()
    assert (tmp_path / 'store' / 'STL' / 'sur-101' / 'summary.md').exists()


def test_workflow_gantt_release_survey_get_and_list(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    import pm_agent
    from state.gantt_release_survey_store import GanttReleaseSurveyStore

    store = GanttReleaseSurveyStore(storage_dir=str(tmp_path / 'store'))
    store.save_survey(
        {
            'survey_id': 'sur-010',
            'project_key': 'STL',
            'created_at': '2026-03-25T12:00:00+00:00',
            'scope_label': 'CN6000',
            'releases_surveyed': ['12.2.0.x'],
            'release_summaries': [],
            'summary_markdown': '# Stored Survey\n\nBody',
            'total_tickets': 10,
            'done_count': 3,
            'in_progress_count': 4,
            'remaining_count': 2,
            'blocked_count': 1,
            'stale_count': 0,
            'unassigned_count': 0,
        },
        summary_markdown='# Stored Survey\n\nBody',
    )
    store.save_survey(
        {
            'survey_id': 'sur-011',
            'project_key': 'STL',
            'created_at': '2026-03-24T12:00:00+00:00',
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
        summary_markdown='# Older Survey',
    )

    monkeypatch.setenv('GANTT_RELEASE_SURVEY_DIR', str(tmp_path / 'store'))

    get_messages = []
    monkeypatch.setattr(
        pm_agent,
        'output',
        lambda message='', **_kwargs: get_messages.append(str(message)),
    )

    export_path = tmp_path / 'exported_survey.json'
    get_args = SimpleNamespace(
        survey_id='sur-010',
        project='STL',
        output=str(export_path),
    )

    get_exit_code = pm_agent._workflow_gantt_release_survey_get(get_args)

    assert get_exit_code == 0
    assert export_path.exists()
    assert (tmp_path / 'exported_survey.md').exists()
    exported = json.loads(export_path.read_text(encoding='utf-8'))
    assert exported['survey_id'] == 'sur-010'
    assert any('Stored in:' in message for message in get_messages)

    list_messages = []
    monkeypatch.setattr(
        pm_agent,
        'output',
        lambda message='', **_kwargs: list_messages.append(str(message)),
    )

    list_args = SimpleNamespace(project='STL', limit=10)
    list_exit_code = pm_agent._workflow_gantt_release_survey_list(list_args)

    assert list_exit_code == 0
    assert any('sur-010' in message for message in list_messages)
    assert any('sur-011' in message for message in list_messages)
