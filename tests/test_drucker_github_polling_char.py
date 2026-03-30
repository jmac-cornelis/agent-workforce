##########################################################################################
#
# Module: tests/test_drucker_github_polling_char.py
#
# Description: Characterization tests for the GitHub PR hygiene polling loop
#              in DruckerCoordinatorAgent.tick().  Covers the scan_type='github'
#              branch: single/multi repo analysis, error handling, notification
#              gating, parameter pass-through, and mixed-job scenarios.
#
# Author: Cornelis Networks
#
##########################################################################################

import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def _make_github_report(repo, open_pr_count=3, stale_count=1,
                        missing_review_count=1, findings=None):
    return {
        'repo': repo,
        'open_pr_count': open_pr_count,
        'stale_count': stale_count,
        'missing_review_count': missing_review_count,
        'findings': findings or [{'type': 'stale_pr', 'pr_number': 42}],
    }


def _stub_agent_init(monkeypatch):
    from agents.drucker.agent import DruckerCoordinatorAgent
    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'drucker prompt'),
    )


def _inject_github_utils(monkeypatch, analyze_fn):
    fake_module = types.ModuleType('github_utils')
    fake_module.analyze_repo_pr_hygiene = analyze_fn  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, 'github_utils', fake_module)


def test_tick_github_single_repo_success(monkeypatch):
    _stub_agent_init(monkeypatch)

    calls = []

    def _analyze(repo, stale_days=5):
        calls.append({'repo': repo, 'stale_days': stale_days})
        return _make_github_report(repo)

    _inject_github_utils(monkeypatch, _analyze)

    from agents.drucker import agent as mod
    monkeypatch.setattr(mod, 'notify_shannon', lambda **kw: {'ok': True})

    from agents.drucker.agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    result = agent.tick({
        'scan_type': 'github',
        'github_repos': ['cornelis/fabric'],
        'github_stale_days': 7,
    })

    assert result['ok'] is True
    assert len(result['tasks']) == 1
    task = result['tasks'][0]
    assert task['task_type'] == 'github_pr_hygiene'
    assert task['repo'] == 'cornelis/fabric'
    assert task['report']['open_pr_count'] == 3
    assert len(result['errors']) == 0
    assert calls[0]['stale_days'] == 7


def test_tick_github_multiple_repos(monkeypatch):
    _stub_agent_init(monkeypatch)

    def _analyze(repo, stale_days=5):
        return _make_github_report(repo)

    _inject_github_utils(monkeypatch, _analyze)

    from agents.drucker import agent as mod
    monkeypatch.setattr(mod, 'notify_shannon', lambda **kw: {'ok': True})

    from agents.drucker.agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    repos = ['cornelis/fabric', 'cornelis/opa-psm2', 'cornelis/libfabric']
    result = agent.tick({
        'scan_type': 'github',
        'github_repos': repos,
    })

    assert result['ok'] is True
    assert len(result['tasks']) == 3
    assert [t['repo'] for t in result['tasks']] == repos
    assert all(t['task_type'] == 'github_pr_hygiene' for t in result['tasks'])


def test_tick_github_repo_exception_captured(monkeypatch):
    _stub_agent_init(monkeypatch)

    def _analyze(repo, stale_days=5):
        if repo == 'cornelis/broken':
            raise RuntimeError('API rate limit exceeded')
        return _make_github_report(repo)

    _inject_github_utils(monkeypatch, _analyze)

    from agents.drucker import agent as mod
    monkeypatch.setattr(mod, 'notify_shannon', lambda **kw: {'ok': True})

    from agents.drucker.agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    result = agent.tick({
        'job_id': 'gh-scan',
        'scan_type': 'github',
        'github_repos': ['cornelis/fabric', 'cornelis/broken', 'cornelis/libfabric'],
    })

    assert result['ok'] is False
    assert len(result['tasks']) == 2
    assert len(result['errors']) == 1
    assert 'cornelis/broken' in result['errors'][0]
    assert 'API rate limit exceeded' in result['errors'][0]


def test_tick_github_empty_repos_list(monkeypatch):
    _stub_agent_init(monkeypatch)

    analyze_calls = []

    def _analyze(repo, stale_days=5):
        analyze_calls.append(repo)
        return _make_github_report(repo)

    _inject_github_utils(monkeypatch, _analyze)

    from agents.drucker import agent as mod
    monkeypatch.setattr(mod, 'notify_shannon', lambda **kw: {'ok': True})

    from agents.drucker.agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    result = agent.tick({
        'scan_type': 'github',
        'github_repos': [],
    })

    assert result['ok'] is True
    assert len(result['tasks']) == 0
    assert len(result['errors']) == 0
    assert len(analyze_calls) == 0


def test_tick_github_string_repos_coerced_to_list(monkeypatch):
    _stub_agent_init(monkeypatch)

    calls = []

    def _analyze(repo, stale_days=5):
        calls.append(repo)
        return _make_github_report(repo)

    _inject_github_utils(monkeypatch, _analyze)

    from agents.drucker import agent as mod
    monkeypatch.setattr(mod, 'notify_shannon', lambda **kw: {'ok': True})

    from agents.drucker.agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    result = agent.tick({
        'scan_type': 'github',
        'github_repos': 'cornelis/fabric',
    })

    assert result['ok'] is True
    assert len(result['tasks']) == 1
    assert result['tasks'][0]['repo'] == 'cornelis/fabric'
    assert calls == ['cornelis/fabric']


def test_tick_github_notify_shannon_enabled(monkeypatch):
    _stub_agent_init(monkeypatch)

    def _analyze(repo, stale_days=5):
        return _make_github_report(
            repo,
            open_pr_count=5,
            stale_count=2,
            missing_review_count=3,
            findings=[
                {'type': 'stale_pr', 'pr_number': 10},
                {'type': 'missing_review', 'pr_number': 11},
            ],
        )

    _inject_github_utils(monkeypatch, _analyze)

    notification_calls = []

    from agents.drucker import agent as mod
    monkeypatch.setattr(
        mod,
        'notify_shannon',
        lambda **kw: (notification_calls.append(kw) or {'ok': True}),
    )

    from agents.drucker.agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    result = agent.tick({
        'scan_type': 'github',
        'github_repos': ['cornelis/fabric'],
        'github_stale_days': 5,
        'notify_shannon': True,
        'shannon_base_url': 'http://shannon.test',
    })

    assert result['ok'] is True
    assert len(result['notifications']) == 1
    assert len(notification_calls) == 1

    call = notification_calls[0]
    assert call['agent_id'] == 'drucker'
    assert call['shannon_base_url'] == 'http://shannon.test'
    assert 'cornelis/fabric' in call['title']
    assert '2 finding(s)' in call['text']
    body_text = ' '.join(call['body_lines'])
    assert '2' in body_text
    assert '3' in body_text
    assert '5' in body_text


def test_tick_github_notify_shannon_disabled(monkeypatch):
    _stub_agent_init(monkeypatch)

    def _analyze(repo, stale_days=5):
        return _make_github_report(repo)

    _inject_github_utils(monkeypatch, _analyze)

    notification_calls = []

    from agents.drucker import agent as mod
    monkeypatch.setattr(
        mod,
        'notify_shannon',
        lambda **kw: (notification_calls.append(kw) or {'ok': True}),
    )

    from agents.drucker.agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    result = agent.tick({
        'scan_type': 'github',
        'github_repos': ['cornelis/fabric'],
        'notify_shannon': False,
    })

    assert result['ok'] is True
    assert len(result['tasks']) == 1
    assert len(result['notifications']) == 0
    assert len(notification_calls) == 0


def test_tick_mixed_jira_and_github_jobs(monkeypatch, tmp_path):
    _stub_agent_init(monkeypatch)

    config_path = tmp_path / 'mixed_polling.yaml'
    config_path.write_text(
        '\n'.join([
            'defaults:',
            '  project_key: STL',
            '  persist: true',
            'jobs:',
            '  - job_id: jira-hygiene',
            '    scan_type: jira',
            '    stale_days: 21',
            '    recent_only: false',
            '  - job_id: github-pr-scan',
            '    scan_type: github',
            '    github_repos:',
            '      - cornelis/fabric',
            '    github_stale_days: 7',
        ]),
        encoding='utf-8',
    )

    github_calls = []

    def _analyze(repo, stale_days=5):
        github_calls.append({'repo': repo, 'stale_days': stale_days})
        return _make_github_report(repo)

    _inject_github_utils(monkeypatch, _analyze)

    jira_calls = []

    from agents.drucker.agent import DruckerCoordinatorAgent

    def _fake_run_once(self, request, persist=True):
        jira_calls.append({
            'project_key': request.project_key,
            'recent_only': request.recent_only,
            'persist': persist,
        })
        return {
            'ok': True,
            'task_type': 'hygiene_report',
            'project_key': request.project_key,
            'report': {'report_id': 'rep-jira-001'},
            'stored': {'report_id': 'rep-jira-001'},
        }

    monkeypatch.setattr(DruckerCoordinatorAgent, 'run_once', _fake_run_once)

    from agents.drucker import agent as mod
    monkeypatch.setattr(mod, 'notify_shannon', lambda **kw: {'ok': True})

    agent = DruckerCoordinatorAgent(project_key='STL')
    result = agent.tick({
        'config_path': str(config_path),
        'project_key': 'STL',
    })

    assert result['ok'] is True
    assert len(result['tasks']) == 2
    task_types = [t['task_type'] for t in result['tasks']]
    assert 'hygiene_report' in task_types
    assert 'github_pr_hygiene' in task_types
    assert len(jira_calls) == 1
    assert jira_calls[0]['project_key'] == 'STL'
    assert len(github_calls) == 1
    assert github_calls[0]['repo'] == 'cornelis/fabric'
    assert github_calls[0]['stale_days'] == 7


def test_tick_github_stale_days_parameter_passthrough(monkeypatch):
    _stub_agent_init(monkeypatch)

    received_stale_days = []

    def _analyze(repo, stale_days=5):
        received_stale_days.append(stale_days)
        return _make_github_report(repo)

    _inject_github_utils(monkeypatch, _analyze)

    from agents.drucker import agent as mod
    monkeypatch.setattr(mod, 'notify_shannon', lambda **kw: {'ok': True})

    from agents.drucker.agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    result = agent.tick({
        'scan_type': 'github',
        'github_repos': ['cornelis/fabric'],
        'github_stale_days': 14,
    })

    assert result['ok'] is True
    assert received_stale_days == [14]


def test_tick_github_default_stale_days(monkeypatch):
    _stub_agent_init(monkeypatch)

    received_stale_days = []

    def _analyze(repo, stale_days=5):
        received_stale_days.append(stale_days)
        return _make_github_report(repo)

    _inject_github_utils(monkeypatch, _analyze)

    from agents.drucker import agent as mod
    monkeypatch.setattr(mod, 'notify_shannon', lambda **kw: {'ok': True})

    from agents.drucker.agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    result = agent.tick({
        'scan_type': 'github',
        'github_repos': ['cornelis/fabric'],
    })

    assert result['ok'] is True
    assert received_stale_days == [5]


def test_tick_github_none_repos_treated_as_empty(monkeypatch):
    _stub_agent_init(monkeypatch)

    analyze_calls = []

    def _analyze(repo, stale_days=5):
        analyze_calls.append(repo)
        return _make_github_report(repo)

    _inject_github_utils(monkeypatch, _analyze)

    from agents.drucker import agent as mod
    monkeypatch.setattr(mod, 'notify_shannon', lambda **kw: {'ok': True})

    from agents.drucker.agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    result = agent.tick({
        'scan_type': 'github',
        'github_repos': None,
    })

    assert result['ok'] is True
    assert len(result['tasks']) == 0
    assert len(result['errors']) == 0
    assert len(analyze_calls) == 0
