import pytest

from agents.gantt_models import (
    BugSummary,
    DependencyGraph,
    PlanningSnapshot,
    ReleaseMonitorReport,
)
from tools.gantt_tools import (
    GanttTools,
    create_gantt_snapshot,
    create_release_monitor,
    get_gantt_release_monitor_report,
    list_gantt_dependency_reviews,
    list_gantt_release_monitor_reports,
    review_gantt_dependency,
)


def test_create_gantt_snapshot_tool_persists_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents import gantt_agent as gantt_agent_module

    class _FakeGanttAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def create_snapshot(self, request):
            assert request.evidence_paths == ['build.json']
            snapshot = PlanningSnapshot(
                project_key=request.project_key,
                created_at='2026-03-15T12:00:00+00:00',
                planning_horizon_days=request.planning_horizon_days,
                backlog_overview={'total_issues': 2},
                dependency_graph=DependencyGraph(),
                evidence_summary={'record_count': 1, 'by_type': {'build': 1}},
                summary_markdown='# Gantt Snapshot\n\nSummary',
            )
            snapshot.snapshot_id = 'snap-201'
            return snapshot

    monkeypatch.setattr(gantt_agent_module, 'GanttProjectPlannerAgent', _FakeGanttAgent)
    monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'store'))

    result = create_gantt_snapshot(
        'STL',
        planning_horizon_days=120,
        evidence_paths=['build.json'],
        persist=True,
    )

    assert result.is_success
    assert result.data['snapshot']['project_key'] == 'STL'
    assert result.data['snapshot']['evidence_summary']['record_count'] == 1
    assert result.data['stored']['snapshot_id'] == 'snap-201'
    assert (tmp_path / 'store' / 'STL' / 'snap-201' / 'snapshot.json').exists()
    assert result.metadata['persisted'] is True


def test_get_and_list_gantt_snapshots_tools(monkeypatch: pytest.MonkeyPatch, tmp_path):
    from state.gantt_snapshot_store import GanttSnapshotStore
    from tools import gantt_tools

    store = GanttSnapshotStore(storage_dir=str(tmp_path / 'store'))
    store.save_snapshot(
        {
            'snapshot_id': 'snap-301',
            'project_key': 'STL',
            'created_at': '2026-03-15T12:00:00+00:00',
            'planning_horizon_days': 90,
            'backlog_overview': {'total_issues': 4, 'blocked_issues': 1, 'stale_issues': 0},
            'milestones': [],
            'risks': [],
            'dependency_graph': {'edge_count': 1},
            'summary_markdown': '# Stored Snapshot',
        },
        summary_markdown='# Stored Snapshot',
    )

    monkeypatch.setenv('GANTT_SNAPSHOT_DIR', str(tmp_path / 'store'))

    get_result = gantt_tools.get_gantt_snapshot('snap-301', project_key='STL')
    list_result = gantt_tools.list_gantt_snapshots(project_key='STL', limit=5)

    assert get_result.is_success
    assert get_result.data['snapshot']['snapshot_id'] == 'snap-301'
    assert get_result.data['summary_markdown'] == '# Stored Snapshot'

    assert list_result.is_success
    assert list_result.data[0]['snapshot_id'] == 'snap-301'
    assert list_result.metadata['count'] == 1


def test_create_release_monitor_tool_persists_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents import gantt_agent as gantt_agent_module

    class _FakeGanttAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def create_release_monitor(self, request):
            assert request.releases == ['12.1.1.x', '12.2.0.x']
            report = ReleaseMonitorReport(
                project_key=request.project_key,
                created_at='2026-03-25T12:00:00+00:00',
                releases_monitored=request.releases or [],
                bug_summaries=[
                    BugSummary(
                        release='12.1.1.x',
                        total_bugs=5,
                        by_priority={'P0': 1, 'P1': 2},
                    )
                ],
                summary_markdown='# Release Monitor',
            )
            report.report_id = 'report-201'
            return report

    monkeypatch.setattr(gantt_agent_module, 'GanttProjectPlannerAgent', _FakeGanttAgent)
    monkeypatch.setenv('GANTT_RELEASE_MONITOR_DIR', str(tmp_path / 'reports'))

    result = create_release_monitor(
        project_key='STL',
        releases='12.1.1.x,12.2.0.x',
        persist=True,
    )

    assert result.is_success
    assert result.data['report']['project_key'] == 'STL'
    assert result.data['stored']['report_id'] == 'report-201'
    assert (tmp_path / 'reports' / 'STL' / 'report-201' / 'report.json').exists()
    assert result.metadata['report_id'] == 'report-201'


def test_get_and_list_gantt_release_monitor_reports_tools(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from state.gantt_release_monitor_store import GanttReleaseMonitorStore

    store = GanttReleaseMonitorStore(storage_dir=str(tmp_path / 'reports'))
    store.save_report(
        {
            'report_id': 'report-301',
            'project_key': 'STL',
            'created_at': '2026-03-25T12:00:00+00:00',
            'releases_monitored': ['12.1.1.x'],
            'bug_summaries': [],
            'summary_markdown': '# Stored Release Monitor',
            'total_bugs': 7,
            'total_p0': 1,
            'total_p1': 2,
        },
        summary_markdown='# Stored Release Monitor',
    )

    monkeypatch.setenv('GANTT_RELEASE_MONITOR_DIR', str(tmp_path / 'reports'))

    get_result = get_gantt_release_monitor_report('report-301', project_key='STL')
    list_result = list_gantt_release_monitor_reports(project_key='STL', limit=5)

    assert get_result.is_success
    assert get_result.data['report']['report_id'] == 'report-301'
    assert get_result.data['summary_markdown'] == '# Stored Release Monitor'

    assert list_result.is_success
    assert list_result.data[0]['report_id'] == 'report-301'
    assert list_result.metadata['count'] == 1


def test_gantt_tools_collection_registers_methods():
    tools = GanttTools()

    assert tools.get_tool('create_gantt_snapshot') is not None
    assert tools.get_tool('get_gantt_snapshot') is not None
    assert tools.get_tool('list_gantt_snapshots') is not None
    assert tools.get_tool('create_release_monitor') is not None
    assert tools.get_tool('get_gantt_release_monitor_report') is not None
    assert tools.get_tool('list_gantt_release_monitor_reports') is not None
    assert tools.get_tool('review_gantt_dependency') is not None
    assert tools.get_tool('list_gantt_dependency_reviews') is not None


def test_review_and_list_gantt_dependency_reviews_tools(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    monkeypatch.setenv('GANTT_DEPENDENCY_REVIEW_DIR', str(tmp_path / 'reviews'))

    record_result = review_gantt_dependency(
        project_key='STL',
        source_key='STL-401',
        target_key='STL-402',
        relationship='blocks',
        accepted=False,
        note='No longer a real blocker',
        reviewer='codex',
    )
    list_result = list_gantt_dependency_reviews(
        project_key='STL',
        status='rejected',
        limit=5,
    )

    assert record_result.is_success
    assert record_result.data['status'] == 'rejected'
    assert record_result.metadata['status'] == 'rejected'

    assert list_result.is_success
    assert list_result.metadata['count'] == 1
    assert list_result.data[0]['edge_key'] == 'STL-401|blocks|STL-402'
    assert list_result.data[0]['reviewer'] == 'codex'
