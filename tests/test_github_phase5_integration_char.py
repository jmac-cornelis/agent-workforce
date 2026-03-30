##########################################################################################
#
# Module: tests/test_github_phase5_integration_char.py
#
# Description: Characterization tests for Phase 5 scan integration layer.
#              Covers tool wrappers (5), Shannon cards (10), API endpoints (5),
#              and polling dispatch (3) for the extended hygiene scan features.
#              Zero live API calls — all github_utils functions are monkeypatched.
#
# Author: Cornelis Networks
#
##########################################################################################

import sys
import types
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Card test helpers (same pattern as test_shannon_pr_cards_char.py)
# ---------------------------------------------------------------------------

def _card_schema_ok(card: dict) -> None:
    '''Assert the standard Adaptive Card envelope is present.'''
    assert card['$schema'] == 'http://adaptivecards.io/schemas/adaptive-card.json'
    assert card['type'] == 'AdaptiveCard'
    assert card['version'] == '1.5'
    assert isinstance(card['body'], list)


def _find_fact_set(card: dict) -> dict:
    '''Return the first FactSet element from the card body.'''
    for item in card['body']:
        if item.get('type') == 'FactSet':
            return item
    return {}


def _fact_value(fact_set: dict, title: str) -> str:
    '''Look up a fact value by its title inside a FactSet.'''
    for fact in fact_set.get('facts', []):
        if fact['title'] == title:
            return fact['value']
    return ''


def _body_texts(card: dict) -> list[str]:
    '''Collect all TextBlock text values from the card body.'''
    return [
        item['text']
        for item in card['body']
        if item.get('type') == 'TextBlock'
    ]


# ---------------------------------------------------------------------------
# Polling helpers (same pattern as test_drucker_github_polling_char.py)
# ---------------------------------------------------------------------------

def _stub_agent_init(monkeypatch):
    '''Patch DruckerCoordinatorAgent._load_prompt_file to avoid file I/O.'''
    from agents.drucker_agent import DruckerCoordinatorAgent
    monkeypatch.setattr(
        DruckerCoordinatorAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'drucker prompt'),
    )


def _inject_github_utils(monkeypatch, **attrs):
    '''Create a fake github_utils module with the given attributes.'''
    fake_module = types.ModuleType('github_utils')
    for name, fn in attrs.items():
        setattr(fake_module, name, fn)
    monkeypatch.setitem(sys.modules, 'github_utils', fake_module)


def _make_extended_report(repo, total_findings=4):
    '''Build a minimal extended hygiene report dict.'''
    return {
        'repo': repo,
        'total_open_prs': 10,
        'total_findings': total_findings,
        'stale_prs': [{'number': 1}],
        'missing_reviews': [{'number': 2}],
        'naming_findings': {'total_findings': 1},
        'merge_conflicts': {'total_conflicts': 0},
        'ci_failures': {'total_failures': 1},
        'stale_branches': {'total_findings': 1},
    }


# ****************************************************************************************
# A) Tool Wrappers — 5 tests
# ****************************************************************************************

def test_check_naming_compliance_returns_success(monkeypatch: pytest.MonkeyPatch):
    '''Stub _analyze_naming_compliance, verify ToolResult.is_success and metadata.'''
    from tools import github_tools

    fake_report = {
        'total_prs': 8,
        'title_compliant': 6,
        'title_noncompliant': 2,
        'no_jira_count': 1,
        'branch_compliant': 7,
        'branch_noncompliant': 1,
        'total_findings': 3,
    }

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_analyze_naming_compliance',
        lambda repo_name, ticket_patterns=None: fake_report,
    )

    result = github_tools.check_naming_compliance('cornelis/fabric')

    assert result.is_success
    assert result.data['total_prs'] == 8
    assert result.metadata['repo'] == 'cornelis/fabric'
    assert result.metadata['total_findings'] == 3
    assert result.metadata['title_noncompliant'] == 2
    assert result.metadata['branch_compliant'] == 7


def test_check_merge_conflicts_returns_success(monkeypatch: pytest.MonkeyPatch):
    '''Stub _analyze_merge_conflicts, verify ToolResult.is_success and metadata.'''
    from tools import github_tools

    fake_report = {
        'total_open_prs': 12,
        'total_conflicts': 2,
        'conflicting_prs': [{'number': 10}, {'number': 20}],
    }

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_analyze_merge_conflicts',
        lambda repo_name: fake_report,
    )

    result = github_tools.check_merge_conflicts('cornelis/fabric')

    assert result.is_success
    assert result.data['total_conflicts'] == 2
    assert result.metadata['repo'] == 'cornelis/fabric'
    assert result.metadata['total_open_prs'] == 12
    assert result.metadata['total_conflicts'] == 2


def test_check_ci_failures_returns_success(monkeypatch: pytest.MonkeyPatch):
    '''Stub _analyze_ci_failures, verify ToolResult.is_success and metadata.'''
    from tools import github_tools

    fake_report = {
        'total_open_prs': 15,
        'total_failures': 3,
        'failing_prs': [{'number': 5}, {'number': 6}, {'number': 7}],
    }

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_analyze_ci_failures',
        lambda repo_name: fake_report,
    )

    result = github_tools.check_ci_failures('cornelis/fabric')

    assert result.is_success
    assert result.data['total_failures'] == 3
    assert result.metadata['repo'] == 'cornelis/fabric'
    assert result.metadata['total_open_prs'] == 15
    assert result.metadata['total_failures'] == 3


def test_check_stale_branches_returns_success(monkeypatch: pytest.MonkeyPatch):
    '''Stub _analyze_stale_branches, verify ToolResult.is_success and metadata.'''
    from tools import github_tools

    fake_report = {
        'total_branches': 20,
        'stale_count': 4,
        'stale_branches': [
            {'name': 'feature/old', 'days_stale': 45},
        ],
    }

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_analyze_stale_branches',
        lambda repo_name, stale_days=30: fake_report,
    )

    result = github_tools.check_stale_branches('cornelis/fabric', stale_days=14)

    assert result.is_success
    assert result.data['stale_count'] == 4
    assert result.metadata['repo'] == 'cornelis/fabric'
    assert result.metadata['stale_days'] == 14
    assert result.metadata['total_branches'] == 20
    assert result.metadata['stale_count'] == 4


def test_analyze_extended_hygiene_returns_success(monkeypatch: pytest.MonkeyPatch):
    '''Stub _analyze_extended_hygiene, verify ToolResult.is_success and metadata.'''
    from tools import github_tools

    fake_report = {
        'total_open_prs': 18,
        'total_findings': 7,
        'stale_prs': [],
        'missing_reviews': [],
        'naming_findings': {},
        'merge_conflicts': {},
        'ci_failures': {},
        'stale_branches': {},
    }

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_analyze_extended_hygiene',
        lambda repo_name, stale_days=5, branch_stale_days=30: fake_report,
    )

    result = github_tools.analyze_extended_hygiene('cornelis/fabric')

    assert result.is_success
    assert result.data['total_findings'] == 7
    assert result.metadata['repo'] == 'cornelis/fabric'
    assert result.metadata['total_open_prs'] == 18
    assert result.metadata['total_findings'] == 7


# ****************************************************************************************
# B) Shannon Cards — 10 tests
# ****************************************************************************************

# --- build_naming_compliance_card (3 tests) ---

def test_naming_compliance_card_shows_findings():
    '''Card with noncompliant titles and branches shows expected facts and body.'''
    from shannon.cards import build_naming_compliance_card

    data = {
        'repo': 'cornelis/fabric',
        'total_scanned': 10,
        'title_compliance': {
            'compliant': 7,
            'noncompliant': 3,
            'no_jira_count': 1,
            'noncompliant_items': [
                {'pr': {'number': 42, 'title': 'bad title', 'author': 'alice'}},
                {'pr': {'number': 55, 'title': 'no ticket ref', 'author': 'bob'}},
            ],
        },
        'branch_compliance': {
            'compliant': 8,
            'noncompliant': 2,
            'noncompliant_items': [
                {'branch': 'fix-stuff', 'pr_number': 42},
                {'branch': 'random-branch', 'pr_number': 55},
            ],
        },
    }

    card = build_naming_compliance_card(data)
    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Repository') == 'cornelis/fabric'
    assert _fact_value(fs, 'Total Scanned') == '10'
    assert _fact_value(fs, 'Title Non-compliant') == '3'
    assert _fact_value(fs, 'Branch Non-compliant') == '2'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert '**Non-compliant PR Titles:**' in body
    assert '#42' in body
    assert '#55' in body
    assert '**Non-compliant Branches:**' in body
    assert 'fix-stuff' in body


def test_naming_compliance_card_empty():
    '''Card with no findings shows the clean message.'''
    from shannon.cards import build_naming_compliance_card

    data = {
        'repo': 'cornelis/fabric',
        'total_scanned': 5,
        'title_compliance': {
            'compliant': 5,
            'noncompliant': 0,
            'no_jira_count': 0,
            'noncompliant_items': [],
        },
        'branch_compliance': {
            'compliant': 5,
            'noncompliant': 0,
            'noncompliant_items': [],
        },
    }

    card = build_naming_compliance_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    assert any('All PRs and branches follow naming conventions.' in t for t in texts)


def test_naming_compliance_card_truncates():
    '''More than 5 noncompliant titles triggers "...and N more" trailer.'''
    from shannon.cards import build_naming_compliance_card

    noncompliant_items = [
        {'pr': {'number': i, 'title': f'PR {i}', 'author': 'dev'}}
        for i in range(1, 9)
    ]

    data = {
        'repo': 'cornelis/fabric',
        'total_scanned': 20,
        'title_compliance': {
            'compliant': 12,
            'noncompliant': 8,
            'no_jira_count': 0,
            'noncompliant_items': noncompliant_items,
        },
        'branch_compliance': {
            'compliant': 20,
            'noncompliant': 0,
            'noncompliant_items': [],
        },
    }

    card = build_naming_compliance_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    body = '\n'.join(texts)

    # First 5 shown
    for i in range(1, 6):
        assert f'#{i} ' in body
    # 6-8 not shown
    assert '#6 ' not in body
    assert '...and 3 more' in body


# --- build_merge_conflicts_card (2 tests) ---

def test_merge_conflicts_card_shows_prs():
    '''Card with 3 conflicts lists PR numbers in body.'''
    from shannon.cards import build_merge_conflicts_card

    data = {
        'repo': 'cornelis/opa-psm2',
        'total_open_prs': 15,
        'total_conflicts': 3,
        'conflicting_prs': [
            {'pr': {'number': 10, 'title': 'Feature A', 'author': 'alice'}},
            {'pr': {'number': 20, 'title': 'Feature B', 'author': 'bob'}},
            {'pr': {'number': 30, 'title': 'Feature C', 'author': 'carol'}},
        ],
    }

    card = build_merge_conflicts_card(data)
    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Repository') == 'cornelis/opa-psm2'
    assert _fact_value(fs, 'Open PRs') == '15'
    assert _fact_value(fs, 'Total Conflicts') == '3'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert '#10' in body
    assert '#20' in body
    assert '#30' in body


def test_merge_conflicts_card_empty():
    '''Card with no conflicts shows the clean message.'''
    from shannon.cards import build_merge_conflicts_card

    data = {
        'repo': 'cornelis/opa-psm2',
        'total_open_prs': 5,
        'total_conflicts': 0,
        'conflicting_prs': [],
    }

    card = build_merge_conflicts_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    assert any('No merge conflicts found.' in t for t in texts)


# --- build_ci_failures_card (2 tests) ---

def test_ci_failures_card_shows_checks():
    '''Card with 2 failures shows PR numbers and check names.'''
    from shannon.cards import build_ci_failures_card

    data = {
        'repo': 'cornelis/fabric',
        'total_open_prs': 20,
        'total_failures': 2,
        'failing_prs': [
            {
                'pr': {'number': 100, 'title': 'Add feature', 'author': 'alice'},
                'failed_checks': ['lint', 'unit-tests'],
            },
            {
                'pr': {'number': 101, 'title': 'Fix bug', 'author': 'bob'},
                'failed_checks': ['integration-tests'],
            },
        ],
    }

    card = build_ci_failures_card(data)
    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Repository') == 'cornelis/fabric'
    assert _fact_value(fs, 'Total Failures') == '2'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert '#100' in body
    assert '#101' in body
    assert 'lint' in body
    assert 'unit-tests' in body
    assert 'integration-tests' in body


def test_ci_failures_card_empty():
    '''Card with no failures shows the clean message.'''
    from shannon.cards import build_ci_failures_card

    data = {
        'repo': 'cornelis/fabric',
        'total_open_prs': 10,
        'total_failures': 0,
        'failing_prs': [],
    }

    card = build_ci_failures_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    assert any('No CI failures found.' in t for t in texts)


# --- build_stale_branches_card (3 tests) ---

def test_stale_branches_card_shows_branches():
    '''Card with 5 stale branches shows name, days, and author.'''
    from shannon.cards import build_stale_branches_card

    branches = [
        {'name': f'feature/old-{i}', 'days_stale': 30 + i, 'last_author': f'dev{i}'}
        for i in range(1, 6)
    ]

    data = {
        'repo': 'cornelis/fabric',
        'stale_days': 30,
        'total_branches': 25,
        'stale_count': 5,
        'stale_branches': branches,
    }

    card = build_stale_branches_card(data)
    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Repository') == 'cornelis/fabric'
    assert _fact_value(fs, 'Threshold') == '30 days'
    assert _fact_value(fs, 'Total Branches') == '25'
    assert _fact_value(fs, 'Stale Branches') == '5'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert 'feature/old-1' in body
    assert 'feature/old-5' in body
    assert 'dev1' in body
    assert '31d stale' in body


def test_stale_branches_card_empty():
    '''Card with no stale branches shows the clean message.'''
    from shannon.cards import build_stale_branches_card

    data = {
        'repo': 'cornelis/fabric',
        'stale_days': 30,
        'total_branches': 10,
        'stale_count': 0,
        'stale_branches': [],
    }

    card = build_stale_branches_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    assert any('No stale branches found.' in t for t in texts)


def test_stale_branches_card_truncates():
    '''More than 10 stale branches triggers "...and N more" trailer.'''
    from shannon.cards import build_stale_branches_card

    branches = [
        {'name': f'branch-{i}', 'days_stale': 40 + i, 'last_author': f'dev{i}'}
        for i in range(1, 14)
    ]

    data = {
        'repo': 'cornelis/fabric',
        'stale_days': 30,
        'total_branches': 50,
        'stale_count': 13,
        'stale_branches': branches,
    }

    card = build_stale_branches_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    body = '\n'.join(texts)

    # First 10 shown
    for i in range(1, 11):
        assert f'branch-{i}' in body
    # 11-13 not shown individually
    assert 'branch-11' not in body
    assert '...and 3 more' in body


# ****************************************************************************************
# C) API Endpoints — 5 tests
# ****************************************************************************************

@pytest.fixture
def mock_github_utils(monkeypatch):
    '''Provide a mock github_utils module injected into sys.modules.'''
    mock_mod = MagicMock()
    monkeypatch.setitem(sys.modules, 'github_utils', mock_mod)
    return mock_mod


@pytest.fixture
def client(mock_github_utils):
    '''Create a TestClient with mocked github_utils already in place.'''
    from agents.drucker_api import create_app
    from fastapi.testclient import TestClient

    app = create_app()
    return TestClient(app)


def test_naming_compliance_endpoint_success(client, mock_github_utils):
    '''POST /v1/github/naming-compliance returns 200 with ok=True.'''
    fake_report = {
        'repo': 'cornelis/fabric',
        'total_findings': 2,
        'title_compliance': {'compliant': 8, 'noncompliant': 2},
    }
    mock_github_utils.analyze_naming_compliance.return_value = fake_report

    resp = client.post(
        '/v1/github/naming-compliance',
        json={'repo': 'cornelis/fabric'},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body['ok'] is True
    assert body['data']['total_findings'] == 2

    mock_github_utils.analyze_naming_compliance.assert_called_once_with(
        'cornelis/fabric',
        ticket_patterns=None,
    )


def test_merge_conflicts_endpoint_success(client, mock_github_utils):
    '''POST /v1/github/merge-conflicts returns 200 with ok=True.'''
    fake_report = {
        'repo': 'cornelis/fabric',
        'total_conflicts': 1,
        'conflicting_prs': [{'number': 42}],
    }
    mock_github_utils.analyze_merge_conflicts.return_value = fake_report

    resp = client.post(
        '/v1/github/merge-conflicts',
        json={'repo': 'cornelis/fabric'},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body['ok'] is True
    assert body['data']['total_conflicts'] == 1

    mock_github_utils.analyze_merge_conflicts.assert_called_once_with(
        'cornelis/fabric',
    )


def test_ci_failures_endpoint_success(client, mock_github_utils):
    '''POST /v1/github/ci-failures returns 200 with ok=True.'''
    fake_report = {
        'repo': 'cornelis/fabric',
        'total_failures': 3,
        'failing_prs': [],
    }
    mock_github_utils.analyze_ci_failures.return_value = fake_report

    resp = client.post(
        '/v1/github/ci-failures',
        json={'repo': 'cornelis/fabric'},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body['ok'] is True
    assert body['data']['total_failures'] == 3

    mock_github_utils.analyze_ci_failures.assert_called_once_with(
        'cornelis/fabric',
    )


def test_stale_branches_endpoint_success(client, mock_github_utils):
    '''POST /v1/github/stale-branches returns 200 with ok=True.'''
    fake_report = {
        'repo': 'cornelis/fabric',
        'stale_count': 5,
        'stale_branches': [],
    }
    mock_github_utils.analyze_stale_branches.return_value = fake_report

    resp = client.post(
        '/v1/github/stale-branches',
        json={'repo': 'cornelis/fabric', 'stale_days': 14},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body['ok'] is True
    assert body['data']['stale_count'] == 5

    mock_github_utils.analyze_stale_branches.assert_called_once_with(
        'cornelis/fabric',
        stale_days=14,
    )


def test_extended_hygiene_endpoint_success(client, mock_github_utils):
    '''POST /v1/github/extended-hygiene returns 200 with ok=True.'''
    fake_report = {
        'repo': 'cornelis/fabric',
        'total_findings': 9,
        'total_open_prs': 20,
    }
    mock_github_utils.analyze_extended_hygiene.return_value = fake_report

    resp = client.post(
        '/v1/github/extended-hygiene',
        json={'repo': 'cornelis/fabric', 'stale_days': 7, 'branch_stale_days': 21},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body['ok'] is True
    assert body['data']['total_findings'] == 9

    mock_github_utils.analyze_extended_hygiene.assert_called_once_with(
        'cornelis/fabric',
        stale_days=7,
        branch_stale_days=21,
    )


# ****************************************************************************************
# D) Polling Dispatch — 3 tests
# ****************************************************************************************

def test_github_extended_tick_single_repo(monkeypatch):
    '''One repo in github_repos calls analyze_extended_hygiene, returns result.'''
    _stub_agent_init(monkeypatch)

    calls = []

    def _analyze(repo, stale_days=5, branch_stale_days=30):
        calls.append({'repo': repo, 'stale_days': stale_days, 'branch_stale_days': branch_stale_days})
        return _make_extended_report(repo)

    _inject_github_utils(monkeypatch, analyze_extended_hygiene=_analyze)

    from agents import drucker_agent as mod
    monkeypatch.setattr(mod, 'notify_shannon', lambda **kw: {'ok': True})

    from agents.drucker_agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    result = agent.tick({
        'scan_type': 'github-extended',
        'github_repos': ['cornelis/fabric'],
        'github_stale_days': 7,
        'branch_stale_days': 14,
    })

    assert result['ok'] is True
    assert len(result['tasks']) == 1
    task = result['tasks'][0]
    assert task['task_type'] == 'github_extended_hygiene'
    assert task['repo'] == 'cornelis/fabric'
    assert task['report']['total_findings'] == 4
    assert len(result['errors']) == 0
    assert calls[0]['stale_days'] == 7
    assert calls[0]['branch_stale_days'] == 14


def test_github_extended_tick_multi_repo(monkeypatch):
    '''Two repos in github_repos produces two task results.'''
    _stub_agent_init(monkeypatch)

    def _analyze(repo, stale_days=5, branch_stale_days=30):
        return _make_extended_report(repo)

    _inject_github_utils(monkeypatch, analyze_extended_hygiene=_analyze)

    from agents import drucker_agent as mod
    monkeypatch.setattr(mod, 'notify_shannon', lambda **kw: {'ok': True})

    from agents.drucker_agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    repos = ['cornelis/fabric', 'cornelis/opa-psm2']
    result = agent.tick({
        'scan_type': 'github-extended',
        'github_repos': repos,
    })

    assert result['ok'] is True
    assert len(result['tasks']) == 2
    assert [t['repo'] for t in result['tasks']] == repos
    assert all(t['task_type'] == 'github_extended_hygiene' for t in result['tasks'])


def test_github_extended_tick_notify_shannon(monkeypatch):
    '''notify_shannon=true sends notification with all 6 finding counts.'''
    _stub_agent_init(monkeypatch)

    def _analyze(repo, stale_days=5, branch_stale_days=30):
        return {
            'repo': repo,
            'total_open_prs': 10,
            'total_findings': 6,
            'stale_prs': [{'number': 1}, {'number': 2}],
            'missing_reviews': [{'number': 3}],
            'naming_findings': {'total_findings': 1},
            'merge_conflicts': {'total_conflicts': 1},
            'ci_failures': {'total_failures': 1},
            'stale_branches': {'total_findings': 0},
        }

    _inject_github_utils(monkeypatch, analyze_extended_hygiene=_analyze)

    notification_calls = []

    from agents import drucker_agent as mod
    monkeypatch.setattr(
        mod,
        'notify_shannon',
        lambda **kw: (notification_calls.append(kw) or {'ok': True}),
    )

    from agents.drucker_agent import DruckerCoordinatorAgent
    agent = DruckerCoordinatorAgent(project_key='STL')

    result = agent.tick({
        'scan_type': 'github-extended',
        'github_repos': ['cornelis/fabric'],
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
    assert '6 finding(s)' in call['text']

    # Verify all 6 body_lines are present with correct counts
    body_text = ' '.join(call['body_lines'])
    assert 'Stale PRs: 2' in body_text
    assert 'Missing reviews: 1' in body_text
    assert 'Naming findings: 1' in body_text
    assert 'Merge conflicts: 1' in body_text
    assert 'CI failures: 1' in body_text
    assert 'Stale branches: 0' in body_text
