import json

import pytest

from agents.gantt.models import (
    BugSummary,
    ReleaseMonitorReport,
    ReleaseSurveyReleaseSummary,
    ReleaseSurveyReport,
)


def _payload(result):
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].type == 'text'
    return json.loads(result[0].text)


@pytest.mark.asyncio
async def test_create_gantt_snapshot_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    from agents.gantt.models import DependencyGraph, PlanningSnapshot

    class _FakeGanttAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def create_snapshot(self, request):
            assert request.evidence_paths == ['build.json']
            snapshot = PlanningSnapshot(
                project_key=request.project_key,
                created_at='2026-03-15T12:00:00+00:00',
                planning_horizon_days=request.planning_horizon_days,
                backlog_overview={'total_issues': 3},
                dependency_graph=DependencyGraph(),
                evidence_summary={'record_count': 1, 'by_type': {'build': 1}},
                summary_markdown='# Snapshot',
            )
            snapshot.snapshot_id = 'snap-401'
            return snapshot

    class _FakeStore:
        def save_snapshot(self, snapshot, summary_markdown=None):
            assert snapshot.snapshot_id == 'snap-401'
            return {
                'snapshot_id': snapshot.snapshot_id,
                'project_key': snapshot.project_key,
                'storage_dir': '/tmp/store/STL/snap-401',
            }

    monkeypatch.setattr(import_mcp_server, 'GanttProjectPlannerAgent', _FakeGanttAgent)
    monkeypatch.setattr(import_mcp_server, 'GanttSnapshotStore', _FakeStore)

    result = await import_mcp_server.create_gantt_snapshot(
        project_key='STL',
        planning_horizon_days=120,
        evidence_paths=['build.json'],
        persist=True,
    )
    data = _payload(result)

    assert data['snapshot']['project_key'] == 'STL'
    assert data['snapshot']['evidence_summary']['record_count'] == 1
    assert data['stored']['snapshot_id'] == 'snap-401'


@pytest.mark.asyncio
async def test_get_gantt_snapshot_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    class _FakeStore:
        def get_snapshot(self, snapshot_id, project_key=None):
            assert snapshot_id == 'snap-501'
            assert project_key == 'STL'
            return {
                'snapshot': {'snapshot_id': snapshot_id, 'project_key': project_key},
                'summary': {'snapshot_id': snapshot_id, 'project_key': project_key},
                'summary_markdown': '# Stored Snapshot',
            }

    monkeypatch.setattr(import_mcp_server, 'GanttSnapshotStore', _FakeStore)

    result = await import_mcp_server.get_gantt_snapshot('snap-501', project_key='STL')
    data = _payload(result)

    assert data['snapshot']['snapshot_id'] == 'snap-501'
    assert data['summary_markdown'] == '# Stored Snapshot'


@pytest.mark.asyncio
async def test_list_gantt_snapshots_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    class _FakeStore:
        def list_snapshots(self, project_key=None, limit=20):
            assert project_key == 'STL'
            assert limit == 10
            return [
                {
                    'snapshot_id': 'snap-601',
                    'project_key': 'STL',
                    'created_at': '2026-03-15T12:00:00+00:00',
                    'total_issues': 5,
                }
            ]

    monkeypatch.setattr(import_mcp_server, 'GanttSnapshotStore', _FakeStore)

    result = await import_mcp_server.list_gantt_snapshots(project_key='STL', limit=10)
    data = _payload(result)

    assert data[0]['snapshot_id'] == 'snap-601'
    assert data[0]['project_key'] == 'STL'


@pytest.mark.asyncio
async def test_review_gantt_dependency_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    class _FakeReviewStore:
        def record_review(
            self,
            project_key,
            source_key,
            target_key,
            relationship,
            accepted,
            note=None,
            reviewer=None,
        ):
            assert project_key == 'STL'
            assert source_key == 'STL-701'
            assert target_key == 'STL-702'
            assert relationship == 'blocks'
            assert accepted is True
            return {
                'edge_key': 'STL-701|blocks|STL-702',
                'project_key': project_key,
                'source_key': source_key,
                'target_key': target_key,
                'relationship': relationship,
                'status': 'accepted',
                'note': note,
                'reviewer': reviewer,
            }

    monkeypatch.setattr(import_mcp_server, 'GanttDependencyReviewStore', _FakeReviewStore)

    result = await import_mcp_server.review_gantt_dependency(
        project_key='STL',
        source_key='STL-701',
        target_key='STL-702',
        relationship='blocks',
        accepted=True,
        note='Confirmed',
        reviewer='codex',
    )
    data = _payload(result)

    assert data['edge_key'] == 'STL-701|blocks|STL-702'
    assert data['status'] == 'accepted'


@pytest.mark.asyncio
async def test_list_gantt_dependency_reviews_tool(
    import_mcp_server,
    monkeypatch: pytest.MonkeyPatch,
):
    class _FakeReviewStore:
        def list_reviews(self, project_key=None, status=None, limit=20):
            assert project_key == 'STL'
            assert status == 'accepted'
            assert limit == 5
            return [
                {
                    'edge_key': 'STL-801|blocks|STL-802',
                    'project_key': 'STL',
                    'status': 'accepted',
                }
            ]

    monkeypatch.setattr(import_mcp_server, 'GanttDependencyReviewStore', _FakeReviewStore)

    result = await import_mcp_server.list_gantt_dependency_reviews(
        project_key='STL',
        status='accepted',
        limit=5,
    )
    data = _payload(result)

    assert data[0]['edge_key'] == 'STL-801|blocks|STL-802'
    assert data[0]['status'] == 'accepted'


@pytest.mark.asyncio
async def test_create_release_monitor_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
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
                        total_bugs=6,
                        by_priority={'P0': 1, 'P1': 2},
                    )
                ],
                summary_markdown='# Release Monitor',
            )
            report.report_id = 'report-401'
            return report

    class _FakeStore:
        def save_report(self, report, summary_markdown=None):
            assert report.report_id == 'report-401'
            assert summary_markdown == '# Release Monitor'
            return {
                'report_id': report.report_id,
                'project_key': report.project_key,
                'storage_dir': '/tmp/store/STL/report-401',
            }

    monkeypatch.setattr(import_mcp_server, 'GanttProjectPlannerAgent', _FakeGanttAgent)
    monkeypatch.setattr(import_mcp_server, 'GanttReleaseMonitorStore', _FakeStore)

    result = await import_mcp_server.create_release_monitor(
        project_key='STL',
        releases='12.1.1.x,12.2.0.x',
        persist=True,
    )
    data = _payload(result)

    assert data['report']['project_key'] == 'STL'
    assert data['stored']['report_id'] == 'report-401'


@pytest.mark.asyncio
async def test_get_gantt_release_monitor_report_tool(
    import_mcp_server,
    monkeypatch: pytest.MonkeyPatch,
):
    class _FakeStore:
        def get_report(self, report_id, project_key=None):
            assert report_id == 'report-501'
            assert project_key == 'STL'
            return {
                'report': {'report_id': report_id, 'project_key': project_key},
                'summary': {'report_id': report_id, 'project_key': project_key},
                'summary_markdown': '# Stored Release Monitor',
            }

    monkeypatch.setattr(import_mcp_server, 'GanttReleaseMonitorStore', _FakeStore)

    result = await import_mcp_server.get_gantt_release_monitor_report(
        'report-501',
        project_key='STL',
    )
    data = _payload(result)

    assert data['report']['report_id'] == 'report-501'
    assert data['summary_markdown'] == '# Stored Release Monitor'


@pytest.mark.asyncio
async def test_list_gantt_release_monitor_reports_tool(
    import_mcp_server,
    monkeypatch: pytest.MonkeyPatch,
):
    class _FakeStore:
        def list_reports(self, project_key=None, limit=20):
            assert project_key == 'STL'
            assert limit == 10
            return [
                {
                    'report_id': 'report-601',
                    'project_key': 'STL',
                    'created_at': '2026-03-25T12:00:00+00:00',
                    'total_bugs': 9,
                }
            ]

    monkeypatch.setattr(import_mcp_server, 'GanttReleaseMonitorStore', _FakeStore)

    result = await import_mcp_server.list_gantt_release_monitor_reports(
        project_key='STL',
        limit=10,
    )
    data = _payload(result)

    assert data[0]['report_id'] == 'report-601'
    assert data[0]['project_key'] == 'STL'


@pytest.mark.asyncio
async def test_create_release_survey_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    class _FakeGanttAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def create_release_survey(self, request):
            assert request.releases == ['12.2.0.x']
            assert request.survey_mode == 'bug'
            survey = ReleaseSurveyReport(
                project_key=request.project_key,
                created_at='2026-03-25T12:00:00+00:00',
                survey_mode='bug',
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
                summary_markdown='# Release Survey',
            )
            survey.survey_id = 'survey-401'
            return survey

    class _FakeStore:
        def save_survey(self, survey, summary_markdown=None):
            assert survey.survey_id == 'survey-401'
            assert summary_markdown == '# Release Survey'
            return {
                'survey_id': survey.survey_id,
                'project_key': survey.project_key,
                'storage_dir': '/tmp/store/STL/survey-401',
            }

    monkeypatch.setattr(import_mcp_server, 'GanttProjectPlannerAgent', _FakeGanttAgent)
    monkeypatch.setattr(import_mcp_server, 'GanttReleaseSurveyStore', _FakeStore)

    result = await import_mcp_server.create_release_survey(
        project_key='STL',
        releases='12.2.0.x',
        survey_mode='bug',
        persist=True,
    )
    data = _payload(result)

    assert data['survey']['project_key'] == 'STL'
    assert data['survey']['survey_mode'] == 'bug'
    assert data['stored']['survey_id'] == 'survey-401'


@pytest.mark.asyncio
async def test_get_gantt_release_survey_tool(
    import_mcp_server,
    monkeypatch: pytest.MonkeyPatch,
):
    class _FakeStore:
        def get_survey(self, survey_id, project_key=None):
            assert survey_id == 'survey-501'
            assert project_key == 'STL'
            return {
                'survey': {'survey_id': survey_id, 'project_key': project_key},
                'summary': {'survey_id': survey_id, 'project_key': project_key},
                'summary_markdown': '# Stored Release Survey',
            }

    monkeypatch.setattr(import_mcp_server, 'GanttReleaseSurveyStore', _FakeStore)

    result = await import_mcp_server.get_gantt_release_survey(
        'survey-501',
        project_key='STL',
    )
    data = _payload(result)

    assert data['survey']['survey_id'] == 'survey-501'
    assert data['summary_markdown'] == '# Stored Release Survey'


@pytest.mark.asyncio
async def test_list_gantt_release_surveys_tool(
    import_mcp_server,
    monkeypatch: pytest.MonkeyPatch,
):
    class _FakeStore:
        def list_surveys(self, project_key=None, limit=20):
            assert project_key == 'STL'
            assert limit == 10
            return [
                {
                    'survey_id': 'survey-601',
                    'project_key': 'STL',
                    'created_at': '2026-03-25T12:00:00+00:00',
                    'total_tickets': 8,
                }
            ]

    monkeypatch.setattr(import_mcp_server, 'GanttReleaseSurveyStore', _FakeStore)

    result = await import_mcp_server.list_gantt_release_surveys(
        project_key='STL',
        limit=10,
    )
    data = _payload(result)

    assert data[0]['survey_id'] == 'survey-601'
    assert data[0]['project_key'] == 'STL'
