##########################################################################################
#
# Module: tests/test_mcp_server_github_char.py
#
# Description: Characterization tests for the 11 GitHub MCP tools in mcp_server.py.
#              Validates every GitHub tool function (Tools 26-36) by stubbing
#              github_utils via monkeypatch on the import_mcp_server fixture.
#              Zero live API calls — all github_utils functions are monkeypatched.
#
# Author: Cornelis Networks
#
##########################################################################################

import json
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Fake data factories
# ---------------------------------------------------------------------------

def _fake_repo(name: str = 'opa-psm2', org: str = 'cornelisnetworks') -> dict:
    '''Minimal repo dict matching github_utils.list_repos output shape.'''
    return {
        'full_name': f'{org}/{name}',
        'name': name,
        'private': False,
        'html_url': f'https://github.com/{org}/{name}',
        'description': 'Sample repo',
        'default_branch': 'main',
    }


def _fake_pr(number: int = 42, title: str = 'Fix widget') -> dict:
    '''Minimal PR dict matching github_utils.list_pull_requests output shape.'''
    return {
        'number': number,
        'title': title,
        'state': 'open',
        'user': 'dev-user',
        'created_at': '2026-03-01T00:00:00Z',
        'updated_at': '2026-03-02T00:00:00Z',
        'html_url': f'https://github.com/cornelisnetworks/opa-psm2/pull/{number}',
    }


def _fake_review(reviewer: str = 'reviewer-1', state: str = 'APPROVED') -> dict:
    '''Minimal review dict matching github_utils.get_pr_reviews output shape.'''
    return {
        'user': reviewer,
        'state': state,
        'submitted_at': '2026-03-03T00:00:00Z',
        'body': 'Looks good',
    }


# ---------------------------------------------------------------------------
# Helper: parse the MCP tool result list into Python data
# ---------------------------------------------------------------------------

def _parse_result(result: list[Any]) -> Any:
    '''Extract parsed JSON from an MCP tool result list.'''
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0].type == 'text'
    return json.loads(result[0].text)


# ---------------------------------------------------------------------------
# Tool 26: list_github_repos
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_github_repos_returns_repos(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''list_github_repos returns a JSON list of repo dicts.'''
    repos = [_fake_repo('opa-psm2'), _fake_repo('opa-fm')]

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(import_mcp_server.github_utils, 'list_repos', lambda org=None, limit=50: repos)

    result = await import_mcp_server.list_github_repos('cornelisnetworks', limit=10)
    data = _parse_result(result)

    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['full_name'] == 'cornelisnetworks/opa-psm2'
    assert data[1]['name'] == 'opa-fm'


@pytest.mark.asyncio
async def test_list_github_repos_no_org(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''list_github_repos with no org returns user repos.'''
    repos = [_fake_repo('my-repo', org='user')]

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(import_mcp_server.github_utils, 'list_repos', lambda org=None, limit=50: repos)

    result = await import_mcp_server.list_github_repos()
    data = _parse_result(result)

    assert len(data) == 1
    assert data[0]['full_name'] == 'user/my-repo'


# ---------------------------------------------------------------------------
# Tool 27: get_github_repo
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_github_repo_returns_info(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''get_github_repo returns detailed repo info dict.'''
    info = _fake_repo('opa-psm2')
    info['stargazers_count'] = 15
    info['open_issues_count'] = 3

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(import_mcp_server.github_utils, 'get_repo_info', lambda name: info)

    result = await import_mcp_server.get_github_repo('cornelisnetworks/opa-psm2')
    data = _parse_result(result)

    assert data['full_name'] == 'cornelisnetworks/opa-psm2'
    assert data['stargazers_count'] == 15


# ---------------------------------------------------------------------------
# Tool 28: validate_github_repo
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_github_repo_exists(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''validate_github_repo returns validation result for an existing repo.'''
    validation = {'valid': True, 'full_name': 'cornelisnetworks/opa-psm2', 'accessible': True}

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(import_mcp_server.github_utils, 'validate_repo', lambda name: validation)

    result = await import_mcp_server.validate_github_repo('cornelisnetworks/opa-psm2')
    data = _parse_result(result)

    assert data['valid'] is True
    assert data['full_name'] == 'cornelisnetworks/opa-psm2'


# ---------------------------------------------------------------------------
# Tool 29: list_github_pull_requests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_github_pull_requests_returns_prs(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''list_github_pull_requests returns a list of PR dicts.'''
    prs = [_fake_pr(42, 'Fix widget'), _fake_pr(43, 'Add feature')]

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(
        import_mcp_server.github_utils,
        'list_pull_requests',
        lambda repo, state='open', sort='created', direction='desc', limit=50: prs,
    )

    result = await import_mcp_server.list_github_pull_requests(
        'cornelisnetworks/opa-psm2', state='open', limit=10,
    )
    data = _parse_result(result)

    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['number'] == 42
    assert data[1]['title'] == 'Add feature'


# ---------------------------------------------------------------------------
# Tool 30: get_github_pull_request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_github_pull_request_returns_detail(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''get_github_pull_request returns a single PR detail dict.'''
    pr = _fake_pr(42, 'Fix widget')
    pr['body'] = 'Detailed description of the fix'
    pr['mergeable'] = True

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(
        import_mcp_server.github_utils,
        'get_pull_request',
        lambda repo, number: pr,
    )

    result = await import_mcp_server.get_github_pull_request('cornelisnetworks/opa-psm2', 42)
    data = _parse_result(result)

    assert data['number'] == 42
    assert data['body'] == 'Detailed description of the fix'
    assert data['mergeable'] is True


# ---------------------------------------------------------------------------
# Tool 31: get_github_pr_reviews
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_github_pr_reviews_returns_reviews(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''get_github_pr_reviews returns a list of review dicts.'''
    reviews = [_fake_review('reviewer-1', 'APPROVED'), _fake_review('reviewer-2', 'CHANGES_REQUESTED')]

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(
        import_mcp_server.github_utils,
        'get_pr_reviews',
        lambda repo, number: reviews,
    )

    result = await import_mcp_server.get_github_pr_reviews('cornelisnetworks/opa-psm2', 42)
    data = _parse_result(result)

    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['state'] == 'APPROVED'
    assert data[1]['state'] == 'CHANGES_REQUESTED'


# ---------------------------------------------------------------------------
# Tool 32: get_github_pr_review_requests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_github_pr_review_requests_returns_pending(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''get_github_pr_review_requests returns pending review request data.'''
    requests_data = {
        'users': ['user-a', 'user-b'],
        'teams': ['team-alpha'],
    }

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(
        import_mcp_server.github_utils,
        'get_pr_review_requests',
        lambda repo, number: requests_data,
    )

    result = await import_mcp_server.get_github_pr_review_requests('cornelisnetworks/opa-psm2', 42)
    data = _parse_result(result)

    assert data['users'] == ['user-a', 'user-b']
    assert data['teams'] == ['team-alpha']


# ---------------------------------------------------------------------------
# Tool 33: find_stale_github_prs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_find_stale_github_prs_returns_stale_list(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''find_stale_github_prs returns stale PR analysis results.'''
    stale = {
        'stale_prs': [_fake_pr(10, 'Old PR')],
        'total_open': 5,
        'stale_count': 1,
        'stale_days_threshold': 7,
    }

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(
        import_mcp_server.github_utils,
        'analyze_pr_staleness',
        lambda repo, stale_days=5: stale,
    )

    result = await import_mcp_server.find_stale_github_prs('cornelisnetworks/opa-psm2', stale_days=7)
    data = _parse_result(result)

    assert data['stale_count'] == 1
    assert data['total_open'] == 5
    assert len(data['stale_prs']) == 1
    assert data['stale_prs'][0]['number'] == 10


# ---------------------------------------------------------------------------
# Tool 34: find_github_prs_missing_reviews
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_find_github_prs_missing_reviews_returns_analysis(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''find_github_prs_missing_reviews returns PRs lacking reviews.'''
    missing = {
        'prs_missing_reviews': [_fake_pr(20, 'Needs review')],
        'total_open': 8,
        'missing_count': 1,
    }

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(
        import_mcp_server.github_utils,
        'analyze_missing_reviews',
        lambda repo: missing,
    )

    result = await import_mcp_server.find_github_prs_missing_reviews('cornelisnetworks/opa-psm2')
    data = _parse_result(result)

    assert data['missing_count'] == 1
    assert data['total_open'] == 8
    assert data['prs_missing_reviews'][0]['title'] == 'Needs review'


# ---------------------------------------------------------------------------
# Tool 35: analyze_github_pr_hygiene
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analyze_github_pr_hygiene_returns_report(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''analyze_github_pr_hygiene returns a full hygiene analysis dict.'''
    hygiene = {
        'repo': 'cornelisnetworks/opa-psm2',
        'total_open_prs': 12,
        'stale_prs': 2,
        'missing_reviews': 3,
        'summary': 'Needs attention',
    }

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(
        import_mcp_server.github_utils,
        'analyze_repo_pr_hygiene',
        lambda repo, stale_days=5: hygiene,
    )

    result = await import_mcp_server.analyze_github_pr_hygiene('cornelisnetworks/opa-psm2', stale_days=7)
    data = _parse_result(result)

    assert data['repo'] == 'cornelisnetworks/opa-psm2'
    assert data['total_open_prs'] == 12
    assert data['stale_prs'] == 2
    assert data['missing_reviews'] == 3


# ---------------------------------------------------------------------------
# Tool 36: get_github_rate_limit (no get_connection needed)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_github_rate_limit_returns_limits(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''get_github_rate_limit returns rate limit status without calling get_connection.'''
    rate = {
        'core': {'limit': 5000, 'remaining': 4990, 'reset': '2026-03-28T12:00:00Z'},
        'search': {'limit': 30, 'remaining': 28, 'reset': '2026-03-28T12:01:00Z'},
    }

    monkeypatch.setattr(import_mcp_server.github_utils, 'get_rate_limit', lambda: rate)

    result = await import_mcp_server.get_github_rate_limit()
    data = _parse_result(result)

    assert data['core']['limit'] == 5000
    assert data['core']['remaining'] == 4990
    assert data['search']['remaining'] == 28


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_github_repo_error_returns_error_result(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''When get_repo_info raises, get_github_repo returns an _error_result response.'''
    monkeypatch.setattr(import_mcp_server.github_utils, 'get_connection', lambda: None)
    monkeypatch.setattr(
        import_mcp_server.github_utils,
        'get_repo_info',
        _raise_not_found,
    )

    result = await import_mcp_server.get_github_repo('cornelisnetworks/nonexistent')
    data = _parse_result(result)

    assert 'error' in data
    assert 'not found' in data['error'].lower()


@pytest.mark.asyncio
async def test_list_github_repos_connection_error(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    '''When get_connection raises, list_github_repos returns an _error_result response.'''
    monkeypatch.setattr(
        import_mcp_server.github_utils,
        'get_connection',
        _raise_connection_error,
    )

    result = await import_mcp_server.list_github_repos('cornelisnetworks')
    data = _parse_result(result)

    assert 'error' in data
    assert 'github token' in data['error'].lower()


# ---------------------------------------------------------------------------
# Error-raising helpers (module-level for picklability)
# ---------------------------------------------------------------------------

def _raise_not_found(name: str) -> None:
    raise Exception('Repository not found: 404')


def _raise_connection_error() -> None:
    raise Exception('GITHUB_TOKEN not set or invalid GitHub token')
