import json

import pytest


def _payload(result):
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].type == 'text'
    return json.loads(result[0].text)


@pytest.mark.asyncio
async def test_create_drucker_hygiene_report_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    from agents.drucker_models import DruckerHygieneReport
    from agents.review_agent import ReviewItem, ReviewSession

    class _FakeDruckerAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def analyze_project_hygiene(self, request):
            assert request.stale_days == 21
            return DruckerHygieneReport(
                project_key=request.project_key,
                report_id='rep-401',
                summary={'finding_count': 2},
                summary_markdown='# Report',
            )

        def create_review_session(self, report):
            return ReviewSession(
                session_id=report.report_id,
                items=[ReviewItem(id='D001', item_type='ticket', action='comment', data={})],
            )

    class _FakeStore:
        def save_report(self, report, summary_markdown=None):
            return {'report_id': report.report_id, 'storage_dir': '/tmp/drucker/rep-401'}

    monkeypatch.setattr(import_mcp_server, 'DruckerCoordinatorAgent', _FakeDruckerAgent)
    monkeypatch.setattr(import_mcp_server, 'DruckerReportStore', _FakeStore)

    result = await import_mcp_server.create_drucker_hygiene_report(
        project_key='STL',
        stale_days=21,
        persist=True,
    )
    data = _payload(result)

    assert data['report']['report_id'] == 'rep-401'
    assert data['stored']['report_id'] == 'rep-401'


@pytest.mark.asyncio
async def test_create_drucker_issue_check_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    from agents.drucker_models import DruckerHygieneReport
    from agents.review_agent import ReviewItem, ReviewSession

    class _FakeDruckerAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def analyze_ticket_hygiene(self, request):
            assert request.ticket_key == 'STL-201'
            return DruckerHygieneReport(
                project_key=request.project_key,
                report_id='rep-402',
                summary={'finding_count': 2},
                summary_markdown='# Report',
            )

        def create_review_session(self, report):
            return ReviewSession(
                session_id=report.report_id,
                items=[ReviewItem(id='D001', item_type='ticket', action='comment', data={})],
            )

    class _FakeStore:
        def save_report(self, report, summary_markdown=None):
            return {'report_id': report.report_id, 'storage_dir': '/tmp/drucker/rep-402'}

    monkeypatch.setattr(import_mcp_server, 'DruckerCoordinatorAgent', _FakeDruckerAgent)
    monkeypatch.setattr(import_mcp_server, 'DruckerReportStore', _FakeStore)

    result = await import_mcp_server.create_drucker_issue_check(
        project_key='STL',
        ticket_key='STL-201',
        stale_days=21,
        persist=True,
    )
    data = _payload(result)

    assert data['report']['report_id'] == 'rep-402'
    assert data['stored']['report_id'] == 'rep-402'


@pytest.mark.asyncio
async def test_get_and_list_drucker_reports_tools(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    class _FakeStore:
        def get_report(self, report_id, project_key=None):
            assert report_id == 'rep-501'
            return {'report': {'report_id': report_id}, 'summary_markdown': '# Stored'}

        def list_reports(self, project_key=None, limit=20):
            assert project_key == 'STL'
            assert limit == 5
            return [{'report_id': 'rep-501', 'project_key': 'STL'}]

    monkeypatch.setattr(import_mcp_server, 'DruckerReportStore', _FakeStore)

    get_result = await import_mcp_server.get_drucker_report('rep-501', project_key='STL')
    list_result = await import_mcp_server.list_drucker_reports(project_key='STL', limit=5)

    assert _payload(get_result)['report']['report_id'] == 'rep-501'
    assert _payload(list_result)[0]['report_id'] == 'rep-501'
