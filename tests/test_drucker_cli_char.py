##########################################################################################
#
# Module: tests/test_drucker_cli_char.py
#
# Description: Characterization tests for agents/drucker/cli.py command handlers.
#              Covers all 6 subcommands: cmd_hygiene, cmd_issue_check,
#              cmd_intake_report, cmd_bug_activity, cmd_github_hygiene, cmd_poll.
#              Uses monkeypatch to stub agent and store dependencies — no live
#              API calls.
#
# Author: Cornelis Networks
#
##########################################################################################

import json
import os
import sys
from types import SimpleNamespace

import pytest

from agents.base import AgentResponse


# ------------------------------------------------------------------
# Shared fake fixtures
# ------------------------------------------------------------------

_FAKE_HYGIENE_REPORT = {
    'project_key': 'STL',
    'summary': {
        'finding_count': 3,
        'action_count': 2,
        'tickets_with_findings': 1,
        'total_tickets': 10,
    },
    'findings': [],
    'proposed_actions': [],
}

_FAKE_REVIEW_SESSION = {
    'session_id': 'sess-001',
    'reviewed_tickets': ['STL-101'],
}

_FAKE_STORED_SUMMARY = {
    'report_id': 'test-id',
    'storage_dir': '/tmp/test',
    'json_path': '/tmp/test.json',
    'markdown_path': '/tmp/test.md',
}

_FAKE_BUG_ACTIVITY = {
    'project': 'STL',
    'date': '2026-03-30',
    'summary': {
        'bugs_opened': 5,
        'status_transitions': 12,
        'bugs_with_comments': 3,
    },
    'bugs': [],
}

_FAKE_GITHUB_REPORT = {
    'repo': 'cornelisnetworks/ifs-all',
    'total_open_prs': 15,
    'total_findings': 4,
    'summary': '## PR Hygiene\n4 findings across 15 open PRs.',
}

_FAKE_EXTENDED_GITHUB_REPORT = {
    'repo': 'cornelisnetworks/ifs-all',
    'total_open_prs': 15,
    'total_findings': 7,
    'stale_branch_count': 3,
    'summary': '## Extended Hygiene\n7 findings, 3 stale branches.',
}


def _make_hygiene_args(tmp_path, **overrides):
    '''Build a SimpleNamespace mimicking argparse output for cmd_hygiene.'''
    defaults = dict(
        project='STL',
        limit=200,
        include_done=False,
        stale_days=14,
        quiet=True,
        json=False,
        env=None,
        output=str(tmp_path / 'hygiene_out.json'),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_issue_check_args(tmp_path, **overrides):
    '''Build a SimpleNamespace mimicking argparse output for cmd_issue_check.'''
    defaults = dict(
        project='STL',
        ticket_key='STL-1234',
        stale_days=14,
        quiet=True,
        json=False,
        env=None,
        output=str(tmp_path / 'issue_check_out.json'),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_intake_args(tmp_path, **overrides):
    '''Build a SimpleNamespace mimicking argparse output for cmd_intake_report.'''
    defaults = dict(
        project='STL',
        limit=200,
        stale_days=14,
        since=None,
        quiet=True,
        json=False,
        env=None,
        output=str(tmp_path / 'intake_out.json'),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_bug_activity_args(tmp_path, **overrides):
    '''Build a SimpleNamespace mimicking argparse output for cmd_bug_activity.'''
    defaults = dict(
        project='STL',
        target_date=None,
        quiet=True,
        json=False,
        env=None,
        output=str(tmp_path / 'bug_activity_out.json'),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_github_hygiene_args(tmp_path, **overrides):
    '''Build a SimpleNamespace mimicking argparse output for cmd_github_hygiene.'''
    defaults = dict(
        repo='cornelisnetworks/ifs-all',
        stale_days=5,
        branch_stale_days=30,
        extended=False,
        quiet=True,
        json=False,
        env=None,
        output=str(tmp_path / 'github_hygiene_out.json'),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_poll_args(**overrides):
    '''Build a SimpleNamespace mimicking argparse output for cmd_poll.'''
    defaults = dict(
        project='STL',
        limit=200,
        include_done=False,
        stale_days=14,
        poll_config=None,
        poll_job=None,
        notify_shannon=False,
        shannon_url='http://localhost:8200',
        poll_interval=300,
        max_cycles=1,
        recent_only=False,
        since=None,
        quiet=True,
        json=False,
        env=None,
        output=None,
        github_repos=None,
        github_stale_days=5,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ------------------------------------------------------------------
# cmd_hygiene tests
# ------------------------------------------------------------------

def test_cmd_hygiene_success(monkeypatch, tmp_path):
    '''cmd_hygiene exits 0 when agent returns success with hygiene_report.'''
    from agents.drucker.cli import cmd_hygiene
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            self.project_key = project_key

        def run(self, request_dict):
            return AgentResponse(
                content='# Hygiene Report\nAll good.',
                success=True,
                metadata={
                    'hygiene_report': _FAKE_HYGIENE_REPORT,
                    'review_session': _FAKE_REVIEW_SESSION,
                },
            )

    class _FakeStore:
        def __init__(self, **_kw):
            pass

        def save_report(self, report, summary_markdown=''):
            return _FAKE_STORED_SUMMARY

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)
    monkeypatch.setattr(
        'agents.drucker.state.report_store.DruckerReportStore', _FakeStore,
    )

    args = _make_hygiene_args(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        cmd_hygiene(args)
    assert exc_info.value.code == 0

    json_path = str(tmp_path / 'hygiene_out.json')
    assert os.path.exists(json_path)
    with open(json_path) as f:
        data = json.load(f)
    assert data['project_key'] == 'STL'


def test_cmd_hygiene_agent_failure(monkeypatch, tmp_path):
    '''cmd_hygiene exits 1 when agent returns success=False.'''
    from agents.drucker.cli import cmd_hygiene
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def run(self, request_dict):
            return AgentResponse(
                content='',
                success=False,
                error='Jira connection failed',
            )

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)

    args = _make_hygiene_args(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        cmd_hygiene(args)
    assert exc_info.value.code == 1


def test_cmd_hygiene_json_output(monkeypatch, tmp_path, capsys):
    '''cmd_hygiene with --json prints JSON to stdout and exits 0.'''
    from agents.drucker.cli import cmd_hygiene
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def run(self, request_dict):
            return AgentResponse(
                content='markdown content',
                success=True,
                metadata={
                    'hygiene_report': _FAKE_HYGIENE_REPORT,
                    'review_session': _FAKE_REVIEW_SESSION,
                },
            )

    class _FakeStore:
        def __init__(self, **_kw):
            pass

        def save_report(self, report, summary_markdown=''):
            return _FAKE_STORED_SUMMARY

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)
    monkeypatch.setattr(
        'agents.drucker.state.report_store.DruckerReportStore', _FakeStore,
    )

    args = _make_hygiene_args(tmp_path, json=True)

    with pytest.raises(SystemExit) as exc_info:
        cmd_hygiene(args)
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed['project_key'] == 'STL'
    assert parsed['summary']['finding_count'] == 3


def test_cmd_hygiene_missing_report(monkeypatch, tmp_path):
    '''cmd_hygiene exits 1 when agent returns success but no hygiene_report.'''
    from agents.drucker.cli import cmd_hygiene
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def run(self, request_dict):
            return AgentResponse(
                content='',
                success=True,
                metadata={},
            )

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)

    args = _make_hygiene_args(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        cmd_hygiene(args)
    assert exc_info.value.code == 1


# ------------------------------------------------------------------
# cmd_issue_check tests
# ------------------------------------------------------------------

def test_cmd_issue_check_success(monkeypatch, tmp_path):
    '''cmd_issue_check exits 0 for a valid single-ticket check.'''
    from agents.drucker.cli import cmd_issue_check
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def run(self, request_dict):
            assert request_dict['ticket_key'] == 'STL-1234'
            return AgentResponse(
                content='# Issue Check\nFindings for STL-1234.',
                success=True,
                metadata={
                    'hygiene_report': _FAKE_HYGIENE_REPORT,
                    'review_session': _FAKE_REVIEW_SESSION,
                },
            )

    class _FakeStore:
        def __init__(self, **_kw):
            pass

        def save_report(self, report, summary_markdown=''):
            return _FAKE_STORED_SUMMARY

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)
    monkeypatch.setattr(
        'agents.drucker.state.report_store.DruckerReportStore', _FakeStore,
    )

    args = _make_issue_check_args(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        cmd_issue_check(args)
    assert exc_info.value.code == 0

    json_path = str(tmp_path / 'issue_check_out.json')
    assert os.path.exists(json_path)


def test_cmd_issue_check_agent_failure(monkeypatch, tmp_path):
    '''cmd_issue_check exits 1 when agent returns success=False.'''
    from agents.drucker.cli import cmd_issue_check
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def run(self, request_dict):
            return AgentResponse(
                content='',
                success=False,
                error='Ticket not found',
            )

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)

    args = _make_issue_check_args(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        cmd_issue_check(args)
    assert exc_info.value.code == 1


# ------------------------------------------------------------------
# cmd_intake_report tests
# ------------------------------------------------------------------

def test_cmd_intake_report_success(monkeypatch, tmp_path):
    '''cmd_intake_report exits 0 with valid report and since parameter.'''
    from agents.drucker.cli import cmd_intake_report
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def run(self, request_dict):
            assert request_dict['recent_only'] is True
            assert request_dict['since'] == '2026-03-01'
            return AgentResponse(
                content='# Intake Report',
                success=True,
                metadata={
                    'hygiene_report': _FAKE_HYGIENE_REPORT,
                    'review_session': _FAKE_REVIEW_SESSION,
                },
            )

    class _FakeStore:
        def __init__(self, **_kw):
            pass

        def save_report(self, report, summary_markdown=''):
            return _FAKE_STORED_SUMMARY

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)
    monkeypatch.setattr(
        'agents.drucker.state.report_store.DruckerReportStore', _FakeStore,
    )

    args = _make_intake_args(tmp_path, since='2026-03-01')

    with pytest.raises(SystemExit) as exc_info:
        cmd_intake_report(args)
    assert exc_info.value.code == 0

    json_path = str(tmp_path / 'intake_out.json')
    assert os.path.exists(json_path)


def test_cmd_intake_report_agent_failure(monkeypatch, tmp_path):
    '''cmd_intake_report exits 1 when agent returns success=False.'''
    from agents.drucker.cli import cmd_intake_report
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def run(self, request_dict):
            return AgentResponse(
                content='',
                success=False,
                error='Query timeout',
            )

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)

    args = _make_intake_args(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        cmd_intake_report(args)
    assert exc_info.value.code == 1


# ------------------------------------------------------------------
# cmd_bug_activity tests
# ------------------------------------------------------------------

def test_cmd_bug_activity_success(monkeypatch, tmp_path):
    '''cmd_bug_activity exits 0 and writes activity files.'''
    from agents.drucker.cli import cmd_bug_activity
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def analyze_bug_activity(self, project_key, target_date):
            assert project_key == 'STL'
            assert target_date == '2026-03-30'
            return _FAKE_BUG_ACTIVITY

        def format_bug_activity_report(self, activity):
            return '## Bug Activity\n5 bugs opened.'

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)

    args = _make_bug_activity_args(tmp_path, target_date='2026-03-30')

    with pytest.raises(SystemExit) as exc_info:
        cmd_bug_activity(args)
    assert exc_info.value.code == 0

    json_path = str(tmp_path / 'bug_activity_out.json')
    assert os.path.exists(json_path)
    with open(json_path) as f:
        data = json.load(f)
    assert data['summary']['bugs_opened'] == 5


def test_cmd_bug_activity_json_output(monkeypatch, tmp_path, capsys):
    '''cmd_bug_activity with --json prints JSON to stdout and exits 0.'''
    from agents.drucker.cli import cmd_bug_activity
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def analyze_bug_activity(self, project_key, target_date):
            return _FAKE_BUG_ACTIVITY

        def format_bug_activity_report(self, activity):
            return '## Bug Activity'

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)

    args = _make_bug_activity_args(tmp_path, json=True)

    with pytest.raises(SystemExit) as exc_info:
        cmd_bug_activity(args)
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed['project'] == 'STL'
    assert parsed['summary']['bugs_opened'] == 5


# ------------------------------------------------------------------
# cmd_github_hygiene tests
# ------------------------------------------------------------------

def test_cmd_github_hygiene_basic(monkeypatch, tmp_path):
    '''cmd_github_hygiene basic (non-extended) exits 0 and writes files.'''
    from agents.drucker.cli import cmd_github_hygiene

    fake_github = SimpleNamespace(
        analyze_repo_pr_hygiene=lambda repo_name, stale_days: _FAKE_GITHUB_REPORT,
        analyze_extended_hygiene=lambda **kw: _FAKE_EXTENDED_GITHUB_REPORT,
    )
    monkeypatch.setitem(sys.modules, 'github_utils', fake_github)

    args = _make_github_hygiene_args(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        cmd_github_hygiene(args)
    assert exc_info.value.code == 0

    json_path = str(tmp_path / 'github_hygiene_out.json')
    assert os.path.exists(json_path)
    with open(json_path) as f:
        data = json.load(f)
    assert data['total_open_prs'] == 15
    assert data['total_findings'] == 4


def test_cmd_github_hygiene_extended(monkeypatch, tmp_path):
    '''cmd_github_hygiene with --extended calls analyze_extended_hygiene.'''
    from agents.drucker.cli import cmd_github_hygiene

    extended_called = {}

    def _fake_extended(repo_name, stale_days, branch_stale_days):
        extended_called['repo'] = repo_name
        extended_called['stale_days'] = stale_days
        extended_called['branch_stale_days'] = branch_stale_days
        return _FAKE_EXTENDED_GITHUB_REPORT

    fake_github = SimpleNamespace(
        analyze_repo_pr_hygiene=lambda repo_name, stale_days: _FAKE_GITHUB_REPORT,
        analyze_extended_hygiene=_fake_extended,
    )
    monkeypatch.setitem(sys.modules, 'github_utils', fake_github)

    args = _make_github_hygiene_args(tmp_path, extended=True, branch_stale_days=60)

    with pytest.raises(SystemExit) as exc_info:
        cmd_github_hygiene(args)
    assert exc_info.value.code == 0

    assert extended_called['repo'] == 'cornelisnetworks/ifs-all'
    assert extended_called['branch_stale_days'] == 60

    json_path = str(tmp_path / 'github_hygiene_out.json')
    with open(json_path) as f:
        data = json.load(f)
    assert data['stale_branch_count'] == 3


def test_cmd_github_hygiene_json_output(monkeypatch, tmp_path, capsys):
    '''cmd_github_hygiene with --json prints JSON to stdout and exits 0.'''
    from agents.drucker.cli import cmd_github_hygiene

    fake_github = SimpleNamespace(
        analyze_repo_pr_hygiene=lambda repo_name, stale_days: _FAKE_GITHUB_REPORT,
    )
    monkeypatch.setitem(sys.modules, 'github_utils', fake_github)

    args = _make_github_hygiene_args(tmp_path, json=True)

    with pytest.raises(SystemExit) as exc_info:
        cmd_github_hygiene(args)
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed['total_findings'] == 4


# ------------------------------------------------------------------
# cmd_poll tests
# ------------------------------------------------------------------

def test_cmd_poll_success(monkeypatch):
    '''cmd_poll exits 0 when poller returns ok=True.'''
    from agents.drucker.cli import cmd_poll
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def run_poller(self, spec):
            assert spec['project_key'] == 'STL'
            assert spec['max_cycles'] == 1
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
                            'task_type': 'hygiene_report',
                            'stored': {'report_id': 'rep-900'},
                        }
                    ]
                },
            }

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)

    args = _make_poll_args()

    with pytest.raises(SystemExit) as exc_info:
        cmd_poll(args)
    assert exc_info.value.code == 0


def test_cmd_poll_failure(monkeypatch):
    '''cmd_poll exits 1 when poller returns ok=False.'''
    from agents.drucker.cli import cmd_poll
    from agents.drucker import agent as drucker_agent_module

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def run_poller(self, spec):
            return {
                'ok': False,
                'cycles_run': 1,
                'cycle_summaries': [
                    {
                        'cycle_number': 1,
                        'ok': False,
                        'task_count': 0,
                        'notification_count': 0,
                        'errors': ['Connection refused'],
                    },
                ],
                'last_tick': {'tasks': []},
            }

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)

    args = _make_poll_args()

    with pytest.raises(SystemExit) as exc_info:
        cmd_poll(args)
    assert exc_info.value.code == 1


def test_cmd_poll_with_github_repos(monkeypatch):
    '''cmd_poll passes github_repos and github_stale_days into poller spec.'''
    from agents.drucker.cli import cmd_poll
    from agents.drucker import agent as drucker_agent_module

    captured_spec = {}

    class _FakeAgent:
        def __init__(self, project_key=None, **_kw):
            pass

        def run_poller(self, spec):
            captured_spec.update(spec)
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
                            'task_type': 'github_pr_hygiene',
                            'repo': 'cornelisnetworks/ifs-all',
                            'report': {
                                'stale_count': 2,
                                'missing_review_count': 1,
                            },
                        }
                    ]
                },
            }

    monkeypatch.setattr(drucker_agent_module, 'DruckerCoordinatorAgent', _FakeAgent)

    args = _make_poll_args(
        github_repos=['cornelisnetworks/ifs-all', 'cornelisnetworks/opa-psm2'],
        github_stale_days=7,
    )

    with pytest.raises(SystemExit) as exc_info:
        cmd_poll(args)
    assert exc_info.value.code == 0

    assert captured_spec['github_repos'] == [
        'cornelisnetworks/ifs-all',
        'cornelisnetworks/opa-psm2',
    ]
    assert captured_spec['github_stale_days'] == 7
