import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from agents.base import AgentResponse
from agents.drucker_models import DruckerAction, DruckerFinding, DruckerHygieneReport, DruckerRequest
from tools.base import ToolResult


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 3, 15, tzinfo=tz or timezone.utc)


def test_drucker_agent_builds_hygiene_report_and_actions(monkeypatch: pytest.MonkeyPatch):
    from agents import drucker_agent as drucker_agent_module
    from agents.drucker_agent import DruckerCoordinatorAgent

    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'drucker prompt'),
    )
    monkeypatch.setattr(drucker_agent_module, 'datetime', _FixedDateTime)
    monkeypatch.setattr(
        drucker_agent_module,
        'get_project_info',
        lambda project_key: ToolResult.success({
            'key': project_key,
            'name': 'Storage Team',
        }),
    )
    monkeypatch.setattr(
        drucker_agent_module,
        'search_tickets',
        lambda jql, limit=100, fields=None: ToolResult.success([
            {
                'key': 'STL-101',
                'summary': 'Old blocked story',
                'status': 'Blocked',
                'priority': 'High',
                'assignee': 'Unassigned',
                'assignee_display': '',
                'updated': '2026-01-15T10:00:00.000+0000',
                'updated_date': '2026-01-15',
                'fix_versions': [],
                'components': [],
                'labels': [],
                'issue_type': 'Story',
            },
            {
                'key': 'STL-102',
                'summary': 'Healthy story',
                'status': 'In Progress',
                'priority': 'Medium',
                'assignee': 'Jane Dev',
                'assignee_display': 'Jane Dev',
                'updated': '2026-03-10T10:00:00.000+0000',
                'updated_date': '2026-03-10',
                'fix_versions': ['12.1.0'],
                'components': ['Fabric'],
                'labels': ['in-flight'],
                'issue_type': 'Story',
            },
        ]),
    )

    agent = DruckerCoordinatorAgent(project_key='STL')
    report = agent.analyze_project_hygiene(
        DruckerRequest(project_key='STL', stale_days=21, limit=50)
    )

    categories = {finding.category for finding in report.findings}
    action_types = [action.action_type for action in report.proposed_actions]

    assert report.project_key == 'STL'
    assert report.summary['total_tickets'] == 2
    assert report.summary['tickets_with_findings'] == 2
    assert 'stale_ticket' in categories
    assert 'blocked_stale_ticket' in categories
    assert 'unassigned_ticket' in categories
    assert 'missing_fix_version' in categories
    assert 'missing_component' in categories
    assert 'missing_labels' in categories
    assert 'missing_recommended_fields' in categories
    assert action_types == ['update', 'comment', 'update', 'comment']
    assert report.proposed_actions[0].update_fields['labels'] == [
        'drucker-blocked',
        'drucker-needs-component',
        'drucker-needs-metadata-review',
        'drucker-needs-owner',
        'drucker-needs-release-target',
        'drucker-needs-triage',
        'drucker-stale',
    ]
    assert '## Ticket Remediation Suggestions' in report.summary_markdown
    assert 'STL-101' in report.summary_markdown


def test_drucker_agent_issue_check_builds_policy_findings_and_actions(
    monkeypatch: pytest.MonkeyPatch,
):
    from agents import drucker_agent as drucker_agent_module
    from agents.drucker_agent import DruckerCoordinatorAgent

    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'drucker prompt'),
    )
    monkeypatch.setattr(drucker_agent_module, 'datetime', _FixedDateTime)
    monkeypatch.setattr(
        drucker_agent_module,
        'get_project_info',
        lambda project_key: ToolResult.success({
            'key': project_key,
            'name': 'Storage Team',
        }),
    )
    monkeypatch.setattr(
        drucker_agent_module,
        'search_tickets',
        lambda jql, limit=100, fields=None: ToolResult.success([
            {
                'key': 'STL-201',
                'summary': 'New bug missing intake details',
                'description': '',
                'status': 'Open',
                'priority': '',
                'assignee': 'Jane Dev',
                'assignee_display': 'Jane Dev',
                'updated': '2026-03-15T10:00:00.000+0000',
                'updated_date': '2026-03-15',
                'fix_versions': ['12.1.0'],
                'components': ['Fabric'],
                'labels': ['triage'],
                'issue_type': 'Bug',
            },
        ]),
    )

    agent = DruckerCoordinatorAgent(project_key='STL')
    report = agent.analyze_ticket_hygiene(
        DruckerRequest(
            project_key='STL',
            ticket_key='STL-201',
            stale_days=21,
        )
    )

    categories = {finding.category for finding in report.findings}
    action_types = [action.action_type for action in report.proposed_actions]

    assert report.summary['monitor_scope'] == 'ticket'
    assert report.summary['ticket_key'] == 'STL-201'
    assert report.summary['tickets_with_findings'] == 1
    assert 'missing_required_fields' in categories
    assert 'missing_recommended_fields' in categories
    assert action_types == ['update', 'comment']
    assert report.proposed_actions[0].update_fields['labels'] == [
        'drucker-needs-metadata-review',
        'drucker-needs-required-fields',
        'triage',
    ]


def test_drucker_agent_issue_check_promotes_learning_based_suggestions_to_review_actions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents import drucker_agent as drucker_agent_module
    from agents.drucker_agent import DruckerCoordinatorAgent

    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'drucker prompt'),
    )
    monkeypatch.setattr(drucker_agent_module, 'datetime', _FixedDateTime)
    monkeypatch.setenv('DRUCKER_LEARNING_DB', str(tmp_path / 'drucker_learning.db'))
    monkeypatch.setattr(
        drucker_agent_module,
        'get_project_info',
        lambda project_key: ToolResult.success({
            'key': project_key,
            'name': 'Storage Team',
        }),
    )
    monkeypatch.setattr(
        drucker_agent_module,
        'search_tickets',
        lambda jql, limit=100, fields=None: ToolResult.success([
            {
                'key': 'STL-220',
                'summary': 'Fabric issue missing metadata',
                'description': '',
                'status': 'Open',
                'priority': '',
                'assignee': 'Jane Dev',
                'assignee_display': 'Jane Dev',
                'reporter': 'alice',
                'updated': '2026-03-15T10:00:00.000+0000',
                'updated_date': '2026-03-15',
                'fix_versions': [],
                'components': [],
                'labels': [],
                'issue_type': 'Bug',
            },
        ]),
    )

    agent = DruckerCoordinatorAgent(project_key='STL')
    agent.monitor_config.min_observations = 2
    agent.monitor_config.confidence_thresholds['suggest'] = 0.40
    agent.monitor_config.confidence_thresholds['auto_fill'] = 0.80

    historical_tickets = [
        {
            'key': 'STL-210',
            'summary': 'Fabric issue regression',
            'reporter': 'alice',
            'components': ['Fabric'],
            'fix_versions': ['12.1.0'],
            'priority': 'P1-Critical',
        },
        {
            'key': 'STL-211',
            'summary': 'Fabric issue bring-up',
            'reporter': 'alice',
            'components': ['Fabric'],
            'fix_versions': ['12.1.0'],
            'priority': 'P1-Critical',
        },
    ]
    for ticket in historical_tickets:
        agent.learning_store.record_ticket(ticket)

    report = agent.analyze_ticket_hygiene(
        DruckerRequest(
            project_key='STL',
            ticket_key='STL-220',
            stale_days=21,
        )
    )

    suggestion_action = next(
        action for action in report.proposed_actions
        if action.title == 'Apply Drucker suggested metadata updates'
    )
    comment_action = next(
        action for action in report.proposed_actions
        if action.action_type == 'comment'
    )

    assert suggestion_action.update_fields == {
        'components': ['Fabric'],
        'fix_versions': ['12.1.0'],
        'priority': 'P1-Critical',
    }
    assert any(
        finding.category == 'suggested_field_update'
        for finding in report.findings
    )
    assert 'Suggested metadata updates for review:' in comment_action.comment
    assert 'priority: P1-Critical' in comment_action.comment


def test_drucker_report_store_save_load_and_list(tmp_path):
    from state.drucker_report_store import DruckerReportStore

    store = DruckerReportStore(storage_dir=str(tmp_path / 'drucker'))

    first_summary = store.save_report({
        'report_id': 'rep-001',
        'project_key': 'STL',
        'created_at': '2026-03-15T12:00:00+00:00',
        'summary': {
            'total_tickets': 5,
            'finding_count': 3,
            'action_count': 2,
            'tickets_with_findings': 2,
            'by_severity': {'high': 2},
        },
        'findings': [],
        'proposed_actions': [],
        'summary_markdown': '# Report 1',
    }, summary_markdown='# Report 1')
    store.save_report({
        'report_id': 'rep-002',
        'project_key': 'STL',
        'created_at': '2026-03-16T12:00:00+00:00',
        'summary': {
            'total_tickets': 8,
            'finding_count': 5,
            'action_count': 4,
            'tickets_with_findings': 4,
            'by_severity': {'high': 1},
        },
        'findings': [],
        'proposed_actions': [],
        'summary_markdown': '# Report 2',
    }, summary_markdown='# Report 2')

    record = store.get_report('rep-001', project_key='STL')
    listed = store.list_reports(project_key='STL')

    assert record is not None
    assert record['report']['project_key'] == 'STL'
    assert record['summary_markdown'] == '# Report 1'
    assert first_summary['storage_dir'].endswith('STL/rep-001')
    assert [row['report_id'] for row in listed] == ['rep-002', 'rep-001']


def test_drucker_agent_creates_review_session_and_executes_approved_actions(
    monkeypatch: pytest.MonkeyPatch,
):
    from agents.drucker_agent import DruckerCoordinatorAgent
    from agents.review_agent import ReviewAgent
    from tools import jira_tools as jira_tools_module

    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'drucker prompt'),
    )
    monkeypatch.setattr(
        ReviewAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'review prompt'),
    )

    update_calls = []
    comment_calls = []

    monkeypatch.setattr(
        jira_tools_module,
        'update_ticket',
        lambda **kwargs: (
            update_calls.append(kwargs)
            or ToolResult.success({'key': kwargs['ticket_key'], 'labels': kwargs.get('labels', [])})
        ),
    )
    monkeypatch.setattr(
        jira_tools_module,
        'add_ticket_comment',
        lambda **kwargs: (
            comment_calls.append(kwargs)
            or ToolResult.success({'ticket_key': kwargs['ticket_key'], 'comment': {'body': kwargs['body']}})
        ),
    )

    report = DruckerHygieneReport(
        project_key='STL',
        summary={'finding_count': 2, 'action_count': 2},
        findings=[
            DruckerFinding(
                finding_id='F001',
                ticket_key='STL-201',
                category='stale_ticket',
                severity='high',
                title='Active ticket is stale',
                description='STL-201 has not moved recently.',
                recommendation='Confirm status and owner.',
            )
        ],
        proposed_actions=[
            DruckerAction(
                action_id='D001',
                ticket_key='STL-201',
                action_type='update',
                title='Apply Drucker hygiene labels',
                update_fields={'labels': ['drucker-stale'], 'priority': 'P1-Critical'},
                finding_ids=['F001'],
            ),
            DruckerAction(
                action_id='D002',
                ticket_key='STL-201',
                action_type='comment',
                title='Post Drucker hygiene summary',
                comment='Drucker hygiene review\n\nSummary',
                finding_ids=['F001'],
            ),
        ],
        tickets=[{'key': 'STL-201', 'summary': 'Needs attention'}],
    )

    agent = DruckerCoordinatorAgent(project_key='STL')
    session = agent.create_review_session(report)

    assert [item.action for item in session.items] == ['update', 'comment']

    agent.review_agent.approve_all(session)
    results = agent.execute_approved_actions(session)

    assert [result['item_id'] for result in results] == ['D001', 'D002']
    assert update_calls[0]['ticket_key'] == 'STL-201'
    assert update_calls[0]['labels'] == ['drucker-stale']
    assert update_calls[0]['priority'] == 'P1-Critical'
    assert comment_calls[0]['ticket_key'] == 'STL-201'
    assert session.items[0].status.value == 'executed'
    assert session.items[1].status.value == 'executed'


def test_drucker_agent_recent_ticket_intake_uses_checkpoint_and_processed_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents import drucker_agent as drucker_agent_module
    from agents.drucker_agent import DruckerCoordinatorAgent

    search_calls = []

    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'drucker prompt'),
    )
    monkeypatch.setattr(drucker_agent_module, 'datetime', _FixedDateTime)
    monkeypatch.setenv(
        'DRUCKER_MONITOR_STATE_DB',
        str(tmp_path / 'drucker_monitor_state.db'),
    )
    monkeypatch.setattr(
        drucker_agent_module,
        'get_project_info',
        lambda project_key: ToolResult.success({
            'key': project_key,
            'name': 'Storage Team',
        }),
    )
    monkeypatch.setattr(
        drucker_agent_module,
        'search_tickets',
        lambda jql, limit=100, fields=None: (
            search_calls.append(jql)
            or ToolResult.success([
                {
                    'key': 'STL-301',
                    'summary': 'Recent bug missing priority',
                    'description': '',
                    'status': 'Open',
                    'priority': '',
                    'assignee': 'Jane Dev',
                    'assignee_display': 'Jane Dev',
                    'updated': '2026-03-15T10:00:00.000+0000',
                    'updated_date': '2026-03-15',
                    'fix_versions': ['12.1.0'],
                    'components': ['Fabric'],
                    'labels': ['triage'],
                    'issue_type': 'Bug',
                },
                {
                    'key': 'STL-302',
                    'summary': 'Healthy recent story',
                    'description': 'ready',
                    'status': 'Open',
                    'priority': 'Medium',
                    'assignee': 'Jane Dev',
                    'assignee_display': 'Jane Dev',
                    'updated': '2026-03-15T10:00:00.000+0000',
                    'updated_date': '2026-03-15',
                    'fix_versions': ['12.1.0'],
                    'components': ['Fabric'],
                    'labels': ['triage'],
                    'issue_type': 'Story',
                },
            ])
        ),
    )

    agent = DruckerCoordinatorAgent(project_key='STL')
    request = DruckerRequest(
        project_key='STL',
        recent_only=True,
        since='2026-03-14 00:00',
        stale_days=21,
        limit=50,
    )

    first_report = agent.analyze_recent_ticket_intake(request)
    second_report = agent.analyze_recent_ticket_intake(request)

    assert 'created >=' in search_calls[0]
    assert first_report.summary['monitor_scope'] == 'recent_ticket_intake'
    assert first_report.summary['source_ticket_count'] == 2
    assert first_report.summary['tickets_with_findings'] == 1
    assert second_report.summary['source_ticket_count'] == 0
    assert agent.monitor_state.get_last_checked('STL') is not None


def test_drucker_agent_analyzes_bug_activity(monkeypatch: pytest.MonkeyPatch):
    from agents import drucker_agent as drucker_agent_module
    from agents.drucker_agent import DruckerCoordinatorAgent

    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'drucker prompt'),
    )
    monkeypatch.setattr(
        drucker_agent_module,
        'connect_to_jira',
        lambda: object(),
    )
    monkeypatch.setattr(
        drucker_agent_module,
        'bug_activity_today',
        lambda jira, project, target_date=None: {
            'project': project,
            'date': target_date,
            'summary': {
                'bugs_opened': 1,
                'status_transitions': 2,
                'bugs_with_comments': 1,
                'total_active_bugs': 3,
            },
            'opened': [],
            'status_changed': [],
            'commented': [],
        },
    )

    agent = DruckerCoordinatorAgent(project_key='STL')
    activity = agent.analyze_bug_activity(
        project_key='STL',
        target_date='2026-03-25',
    )
    markdown = agent.format_bug_activity_report(activity)

    assert activity['task_type'] == 'bug_activity'
    assert activity['project'] == 'STL'
    assert activity['summary']['status_transitions'] == 2
    assert '# DRUCKER BUG ACTIVITY: STL' in markdown
    assert '- Bugs Opened: 1' in markdown


def test_drucker_agent_tick_persists_results_and_posts_notifications(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents import pm_runtime
    from agents.drucker_agent import DruckerCoordinatorAgent

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {'ok': True}

    notification_calls = []

    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'drucker prompt'),
    )
    monkeypatch.setenv('DRUCKER_REPORT_DIR', str(tmp_path / 'reports'))
    monkeypatch.setenv('DRY_RUN', 'false')
    monkeypatch.setattr(
        pm_runtime.requests,
        'post',
        lambda url, json=None, timeout=15: (
            notification_calls.append({'url': url, 'json': json, 'timeout': timeout})
            or _FakeResponse()
        ),
    )

    report = DruckerHygieneReport(
        project_key='STL',
        report_id='rep-poll',
        summary={
            'total_tickets': 5,
            'finding_count': 3,
            'action_count': 2,
            'tickets_with_findings': 2,
        },
        summary_markdown='# Report',
    )

    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        'analyze_project_hygiene',
        lambda self, request: report,
    )
    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        'create_review_session',
        lambda self, report: SimpleNamespace(
            to_dict=lambda: {'session_id': report.report_id, 'items': []}
        ),
    )

    agent = DruckerCoordinatorAgent(project_key='STL')
    result = agent.tick({
        'project_key': 'STL',
        'stale_days': 21,
        'notify_shannon': True,
        'shannon_base_url': 'http://shannon.test',
    })

    assert result['ok'] is True
    assert len(result['tasks']) == 1
    assert len(result['notifications']) == 1
    assert (tmp_path / 'reports' / 'STL' / 'rep-poll' / 'report.json').exists()
    assert notification_calls[0]['url'] == 'http://shannon.test/v1/bot/notify'


def test_drucker_agent_tick_recent_only_persists_recent_intake_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents import pm_runtime
    from agents.drucker_agent import DruckerCoordinatorAgent

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {'ok': True}

    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'drucker prompt'),
    )
    monkeypatch.setenv('DRUCKER_REPORT_DIR', str(tmp_path / 'reports'))
    monkeypatch.setattr(pm_runtime.requests, 'post', lambda *args, **kwargs: _FakeResponse())

    report = DruckerHygieneReport(
        project_key='STL',
        report_id='rep-intake',
        summary={
            'total_tickets': 2,
            'finding_count': 2,
            'action_count': 2,
            'tickets_with_findings': 1,
            'monitor_scope': 'recent_ticket_intake',
        },
        summary_markdown='# Intake Report',
    )

    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        'analyze_recent_ticket_intake',
        lambda self, request: report,
    )
    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        'create_review_session',
        lambda self, report: SimpleNamespace(
            to_dict=lambda: {'session_id': report.report_id, 'items': []}
        ),
    )

    agent = DruckerCoordinatorAgent(project_key='STL')
    result = agent.tick({
        'project_key': 'STL',
        'stale_days': 21,
        'recent_only': True,
    })

    assert result['ok'] is True
    assert result['tasks'][0]['task_type'] == 'ticket_intake_report'
    assert (tmp_path / 'reports' / 'STL' / 'rep-intake' / 'report.json').exists()


def test_drucker_agent_tick_uses_configured_polling_jobs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents.drucker_agent import DruckerCoordinatorAgent

    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'drucker prompt'),
    )

    config_path = tmp_path / 'drucker_polling.yaml'
    config_path.write_text(
        '\n'.join([
            'defaults:',
            '  project_key: STL',
            '  persist: true',
            'jobs:',
            '  - job_id: hygiene-scan',
            '    stale_days: 21',
            '    recent_only: false',
            '  - job_id: recent-ticket-intake',
            '    stale_days: 21',
            '    recent_only: true',
        ]),
        encoding='utf-8',
    )

    call_order = []

    def _fake_run_once(self, request, persist=True):
        call_order.append({
            'recent_only': request.recent_only,
            'project_key': request.project_key,
            'persist': persist,
        })
        report_id = 'rep-intake' if request.recent_only else 'rep-hygiene'
        return {
            'ok': True,
            'task_type': (
                'ticket_intake_report' if request.recent_only else 'hygiene_report'
            ),
            'project_key': request.project_key,
            'report': {'report_id': report_id, 'project_key': request.project_key},
            'stored': {'report_id': report_id},
        }

    monkeypatch.setattr(DruckerCoordinatorAgent, 'run_once', _fake_run_once)

    agent = DruckerCoordinatorAgent(project_key='STL')
    result = agent.tick({
        'config_path': str(config_path),
        'project_key': 'STL',
    })

    assert result['ok'] is True
    assert [task['job_id'] for task in result['tasks']] == [
        'hygiene-scan',
        'recent-ticket-intake',
    ]
    assert [task['task_type'] for task in result['tasks']] == [
        'hygiene_report',
        'ticket_intake_report',
    ]
    assert call_order == [
        {'recent_only': False, 'project_key': 'STL', 'persist': True},
        {'recent_only': True, 'project_key': 'STL', 'persist': True},
    ]


def test_workflow_drucker_hygiene_writes_report_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    import pm_agent
    from agents import drucker_agent as drucker_agent_module

    class _FakeDruckerAgent:
        def __init__(self, project_key=None, **kwargs):
            self.project_key = project_key

        def run(self, input_data):
            return AgentResponse.success_response(
                content='# Drucker Hygiene Report\n\nSummary',
                metadata={
                    'hygiene_report': {
                        'report_id': 'rep-101',
                        'project_key': input_data['project_key'],
                        'created_at': '2026-03-15T12:00:00+00:00',
                        'summary': {
                            'total_tickets': 4,
                            'finding_count': 3,
                            'action_count': 2,
                            'tickets_with_findings': 2,
                            'by_severity': {'high': 1},
                        },
                        'findings': [],
                        'proposed_actions': [],
                    },
                    'review_session': {
                        'session_id': 'rep-101',
                        'items': [{'id': 'D001', 'action': 'update'}],
                    },
                },
            )

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeDruckerAgent)
    monkeypatch.setattr(pm_agent, 'output', lambda *args, **kwargs: None)
    monkeypatch.setenv('DRUCKER_REPORT_DIR', str(tmp_path / 'store'))

    output_path = tmp_path / 'drucker_report.json'
    args = SimpleNamespace(
        project='STL',
        limit=25,
        include_done=False,
        stale_days=21,
        output=str(output_path),
    )

    exit_code = pm_agent._workflow_drucker_hygiene(args)

    assert exit_code == 0
    assert output_path.exists()
    assert (tmp_path / 'drucker_report.md').exists()
    assert (tmp_path / 'drucker_report_review.json').exists()
    assert (tmp_path / 'store' / 'STL' / 'rep-101' / 'report.json').exists()

    exported = json.loads(output_path.read_text(encoding='utf-8'))
    review_payload = json.loads(
        (tmp_path / 'drucker_report_review.json').read_text(encoding='utf-8')
    )

    assert exported['project_key'] == 'STL'
    assert review_payload['session_id'] == 'rep-101'


def test_workflow_drucker_intake_report_writes_report_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    import pm_agent
    from agents import drucker_agent as drucker_agent_module

    class _FakeDruckerAgent:
        def __init__(self, project_key=None, **kwargs):
            self.project_key = project_key

        def run(self, input_data):
            assert input_data['recent_only'] is True
            assert input_data['since'] == '2026-03-24 00:00'
            return AgentResponse.success_response(
                content='# Drucker Intake Report\n\nSummary',
                metadata={
                    'task_type': 'ticket_intake_report',
                    'hygiene_report': {
                        'report_id': 'rep-intake-101',
                        'project_key': input_data['project_key'],
                        'created_at': '2026-03-15T12:00:00+00:00',
                        'summary': {
                            'total_tickets': 2,
                            'finding_count': 2,
                            'action_count': 1,
                            'tickets_with_findings': 1,
                            'monitor_scope': 'recent_ticket_intake',
                            'source_ticket_count': 2,
                        },
                        'findings': [],
                        'proposed_actions': [],
                    },
                    'review_session': {
                        'session_id': 'rep-intake-101',
                        'items': [{'id': 'D001', 'action': 'comment'}],
                    },
                },
            )

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeDruckerAgent)
    monkeypatch.setattr(pm_agent, 'output', lambda *args, **kwargs: None)
    monkeypatch.setenv('DRUCKER_REPORT_DIR', str(tmp_path / 'store'))

    output_path = tmp_path / 'drucker_intake_report.json'
    args = SimpleNamespace(
        project='STL',
        limit=25,
        stale_days=21,
        since='2026-03-24 00:00',
        output=str(output_path),
    )

    exit_code = pm_agent._workflow_drucker_intake_report(args)

    assert exit_code == 0
    assert output_path.exists()
    assert (tmp_path / 'drucker_intake_report.md').exists()
    assert (tmp_path / 'drucker_intake_report_review.json').exists()
    assert (tmp_path / 'store' / 'STL' / 'rep-intake-101' / 'report.json').exists()


def test_workflow_drucker_issue_check_writes_report_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    import pm_agent
    from agents import drucker_agent as drucker_agent_module

    class _FakeDruckerAgent:
        def __init__(self, project_key=None, **kwargs):
            self.project_key = project_key

        def run(self, input_data):
            return AgentResponse.success_response(
                content='# Drucker Issue Check\n\nSummary',
                metadata={
                    'task_type': 'issue_check',
                    'hygiene_report': {
                        'report_id': 'rep-issue-101',
                        'project_key': input_data['project_key'],
                        'created_at': '2026-03-15T12:00:00+00:00',
                        'summary': {
                            'total_tickets': 1,
                            'finding_count': 2,
                            'action_count': 2,
                            'tickets_with_findings': 1,
                            'monitor_scope': 'ticket',
                            'ticket_key': input_data['ticket_key'],
                        },
                        'findings': [],
                        'proposed_actions': [],
                    },
                    'review_session': {
                        'session_id': 'rep-issue-101',
                        'items': [{'id': 'D001', 'action': 'comment'}],
                    },
                },
            )

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeDruckerAgent)
    monkeypatch.setattr(pm_agent, 'output', lambda *args, **kwargs: None)
    monkeypatch.setenv('DRUCKER_REPORT_DIR', str(tmp_path / 'store'))

    output_path = tmp_path / 'drucker_issue_check.json'
    args = SimpleNamespace(
        project='STL',
        ticket_key='STL-201',
        stale_days=21,
        output=str(output_path),
    )

    exit_code = pm_agent._workflow_drucker_issue_check(args)

    assert exit_code == 0
    assert output_path.exists()
    assert (tmp_path / 'drucker_issue_check.md').exists()
    assert (tmp_path / 'drucker_issue_check_review.json').exists()
    assert (tmp_path / 'store' / 'STL' / 'rep-issue-101' / 'report.json').exists()


def test_workflow_drucker_bug_activity_writes_report_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    import pm_agent
    from agents import drucker_agent as drucker_agent_module

    class _FakeDruckerAgent:
        def __init__(self, project_key=None, **kwargs):
            self.project_key = project_key

        def analyze_bug_activity(self, project_key=None, target_date=None):
            assert project_key == 'STL'
            assert target_date == '2026-03-25'
            return {
                'project': 'STL',
                'date': '2026-03-25',
                'generated_at': '2026-03-25T12:00:00+00:00',
                'summary': {
                    'bugs_opened': 1,
                    'status_transitions': 2,
                    'bugs_with_comments': 1,
                    'total_active_bugs': 3,
                },
                'opened': [],
                'status_changed': [],
                'commented': [],
            }

        @staticmethod
        def format_bug_activity_report(activity):
            return '# DRUCKER BUG ACTIVITY: STL\n\nSummary'

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeDruckerAgent)
    monkeypatch.setattr(pm_agent, 'output', lambda *args, **kwargs: None)

    output_path = tmp_path / 'drucker_bug_activity.json'
    args = SimpleNamespace(
        project='STL',
        target_date='2026-03-25',
        output=str(output_path),
    )

    exit_code = pm_agent._workflow_drucker_bug_activity(args)

    assert exit_code == 0
    assert output_path.exists()
    assert (tmp_path / 'drucker_bug_activity.md').exists()


def test_workflow_drucker_poll_runs_poller(monkeypatch: pytest.MonkeyPatch):
    import pm_agent
    from agents import drucker_agent as drucker_agent_module

    class _FakeDruckerAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def run_poller(self, spec):
            assert spec['project_key'] == 'STL'
            assert spec['notify_shannon'] is True
            assert spec['stale_days'] == 21
            assert spec['max_cycles'] == 2
            return {
                'ok': True,
                'cycles_run': 2,
                'cycle_summaries': [
                    {
                        'cycle_number': 1,
                        'ok': True,
                        'task_count': 1,
                        'notification_count': 1,
                        'errors': [],
                    },
                    {
                        'cycle_number': 2,
                        'ok': True,
                        'task_count': 1,
                        'notification_count': 1,
                        'errors': [],
                    },
                ],
                'last_tick': {
                    'tasks': [
                        {
                            'task_type': 'hygiene_report',
                            'stored': {'report_id': 'rep-702'},
                        }
                    ]
                },
            }

    monkeypatch.setattr(
        drucker_agent_module,
        'DruckerCoordinatorAgent',
        _FakeDruckerAgent,
    )
    monkeypatch.setattr(pm_agent, 'output', lambda *args, **kwargs: None)

    args = SimpleNamespace(
        project='STL',
        limit=50,
        include_done=False,
        stale_days=21,
        poll_config=None,
        poll_job=None,
        recent_only=False,
        since=None,
        notify_shannon=True,
        shannon_url='http://shannon.test',
        poll_interval=300,
        max_cycles=2,
    )

    assert pm_agent._workflow_drucker_poll(args) == 0


def test_workflow_drucker_poll_passes_recent_only_options(
    monkeypatch: pytest.MonkeyPatch,
):
    import pm_agent
    from agents import drucker_agent as drucker_agent_module

    class _FakeDruckerAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def run_poller(self, spec):
            assert spec['project_key'] == 'STL'
            assert spec['recent_only'] is True
            assert spec['since'] == '2026-03-14 00:00'
            return {
                'ok': True,
                'cycles_run': 1,
                'cycle_summaries': [
                    {
                        'cycle_number': 1,
                        'ok': True,
                        'task_count': 1,
                        'notification_count': 0,
                        'errors': [],
                    },
                ],
                'last_tick': {
                    'tasks': [
                        {
                            'task_type': 'ticket_intake_report',
                            'stored': {'report_id': 'rep-703'},
                        }
                    ]
                },
            }

    monkeypatch.setattr(
        drucker_agent_module,
        'DruckerCoordinatorAgent',
        _FakeDruckerAgent,
    )
    monkeypatch.setattr(pm_agent, 'output', lambda *args, **kwargs: None)

    args = SimpleNamespace(
        project='STL',
        limit=50,
        include_done=False,
        stale_days=21,
        poll_config=None,
        poll_job=None,
        notify_shannon=False,
        shannon_url=None,
        poll_interval=300,
        max_cycles=1,
        recent_only=True,
        since='2026-03-14 00:00',
    )

    assert pm_agent._workflow_drucker_poll(args) == 0


def test_workflow_drucker_poll_passes_configured_job_options(
    monkeypatch: pytest.MonkeyPatch,
):
    import pm_agent
    from agents import drucker_agent as drucker_agent_module

    class _FakeDruckerAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def run_poller(self, spec):
            assert spec['config_path'] == 'config/drucker_polling.yaml'
            assert spec['job_name'] == 'recent-ticket-intake'
            assert spec['project_key'] == 'STL'
            assert spec['notify_shannon'] is False
            return {
                'ok': True,
                'cycles_run': 1,
                'cycle_summaries': [
                    {
                        'cycle_number': 1,
                        'ok': True,
                        'task_count': 2,
                        'notification_count': 0,
                        'errors': [],
                    },
                ],
                'last_tick': {
                    'tasks': [
                        {
                            'job_id': 'recent-ticket-intake',
                            'task_type': 'ticket_intake_report',
                            'stored': {'report_id': 'rep-704'},
                        }
                    ]
                },
            }

    monkeypatch.setattr(
        drucker_agent_module,
        'DruckerCoordinatorAgent',
        _FakeDruckerAgent,
    )
    monkeypatch.setattr(pm_agent, 'output', lambda *args, **kwargs: None)

    args = SimpleNamespace(
        project='STL',
        limit=50,
        include_done=False,
        stale_days=21,
        poll_config='config/drucker_polling.yaml',
        poll_job='recent-ticket-intake',
        notify_shannon=False,
        shannon_url=None,
        poll_interval=300,
        max_cycles=1,
        recent_only=False,
        since=None,
    )

    assert pm_agent._workflow_drucker_poll(args) == 0
