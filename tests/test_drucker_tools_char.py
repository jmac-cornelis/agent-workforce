import pytest

from tools.drucker_tools import (
    DruckerTools,
    create_drucker_issue_check,
    create_drucker_hygiene_report,
    get_drucker_report,
    list_drucker_reports,
)


def test_create_drucker_hygiene_report_tool_persists_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents import drucker_agent as drucker_agent_module
    from agents.drucker_models import DruckerHygieneReport
    from agents.review_agent import ReviewItem, ReviewSession

    class _FakeDruckerAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def analyze_project_hygiene(self, request):
            return DruckerHygieneReport(
                project_key=request.project_key,
                report_id='rep-201',
                summary={'finding_count': 1, 'action_count': 1},
                summary_markdown='# Drucker Report\n\nSummary',
            )

        def create_review_session(self, report):
            return ReviewSession(
                session_id=report.report_id,
                created_at='2026-03-16T12:00:00+00:00',
                items=[ReviewItem(id='D001', item_type='ticket', action='comment', data={})],
            )

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeDruckerAgent)
    monkeypatch.setenv('DRUCKER_REPORT_DIR', str(tmp_path / 'store'))

    result = create_drucker_hygiene_report('STL', stale_days=21, persist=True)

    assert result.is_success
    assert result.data['report']['report_id'] == 'rep-201'
    assert result.data['stored']['report_id'] == 'rep-201'
    assert (tmp_path / 'store' / 'STL' / 'rep-201' / 'report.json').exists()


def test_create_drucker_issue_check_tool_persists_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents import drucker_agent as drucker_agent_module
    from agents.drucker_models import DruckerHygieneReport
    from agents.review_agent import ReviewItem, ReviewSession

    class _FakeDruckerAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def analyze_ticket_hygiene(self, request):
            assert request.ticket_key == 'STL-201'
            return DruckerHygieneReport(
                project_key=request.project_key,
                report_id='rep-202',
                summary={'finding_count': 2, 'action_count': 2},
                summary_markdown='# Drucker Issue Check\n\nSummary',
            )

        def create_review_session(self, report):
            return ReviewSession(
                session_id=report.report_id,
                created_at='2026-03-16T12:00:00+00:00',
                items=[ReviewItem(id='D001', item_type='ticket', action='comment', data={})],
            )

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeDruckerAgent)
    monkeypatch.setenv('DRUCKER_REPORT_DIR', str(tmp_path / 'store'))

    result = create_drucker_issue_check(
        'STL',
        ticket_key='STL-201',
        stale_days=21,
        persist=True,
    )

    assert result.is_success
    assert result.data['report']['report_id'] == 'rep-202'
    assert result.data['stored']['report_id'] == 'rep-202'
    assert (tmp_path / 'store' / 'STL' / 'rep-202' / 'report.json').exists()


def test_get_and_list_drucker_reports_tools(monkeypatch: pytest.MonkeyPatch, tmp_path):
    from state.drucker_report_store import DruckerReportStore

    store = DruckerReportStore(storage_dir=str(tmp_path / 'store'))
    store.save_report({
        'report_id': 'rep-301',
        'project_key': 'STL',
        'created_at': '2026-03-16T12:00:00+00:00',
        'summary': {'finding_count': 2, 'action_count': 1, 'tickets_with_findings': 1},
        'summary_markdown': '# Stored',
    }, summary_markdown='# Stored')

    monkeypatch.setenv('DRUCKER_REPORT_DIR', str(tmp_path / 'store'))

    get_result = get_drucker_report('rep-301', project_key='STL')
    list_result = list_drucker_reports(project_key='STL', limit=5)

    assert get_result.is_success
    assert get_result.data['report']['report_id'] == 'rep-301'
    assert list_result.is_success
    assert list_result.data[0]['report_id'] == 'rep-301'


def test_drucker_tools_collection_registers_methods():
    tools = DruckerTools()

    assert tools.get_tool('create_drucker_issue_check') is not None
    assert tools.get_tool('create_drucker_hygiene_report') is not None
    assert tools.get_tool('get_drucker_report') is not None
    assert tools.get_tool('list_drucker_reports') is not None
