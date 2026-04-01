##########################################################################################
#
# Module: tests/test_github_tools_char.py
#
# Description: Characterization tests for tools/github_tools.py.
#              Validates all 11 tool functions and the GitHubTools collection class.
#              Zero live API calls — all github_utils functions are monkeypatched.
#
# Author: Cornelis Networks
#
##########################################################################################

import pytest

from tools.github_tools import GitHubTools


# ****************************************************************************************
# A) Repository tools
# ****************************************************************************************

def test_list_repos_returns_success(monkeypatch: pytest.MonkeyPatch):
    '''Stub _list_repos, verify ToolResult.is_success and data.'''
    from tools import github_tools

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_list_repos',
        lambda org: [
            {'full_name': 'cornelisnetworks/opa-psm2', 'name': 'opa-psm2'},
            {'full_name': 'cornelisnetworks/opa-ff', 'name': 'opa-ff'},
        ],
    )

    result = github_tools.list_repos('cornelisnetworks')

    assert result.is_success
    assert len(result.data) == 2
    assert result.data[0]['full_name'] == 'cornelisnetworks/opa-psm2'
    assert result.metadata['count'] == 2
    assert result.metadata['org'] == 'cornelisnetworks'


def test_get_repo_info_returns_success(monkeypatch: pytest.MonkeyPatch):
    '''Stub _get_repo_info, verify ToolResult with repo details.'''
    from tools import github_tools

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_get_repo_info',
        lambda repo_name: {
            'full_name': repo_name,
            'description': 'PSM2 user-space library',
            'default_branch': 'main',
            'open_issues_count': 7,
        },
    )

    result = github_tools.get_repo_info('cornelisnetworks/opa-psm2')

    assert result.is_success
    assert result.data['full_name'] == 'cornelisnetworks/opa-psm2'
    assert result.data['default_branch'] == 'main'
    assert result.data['open_issues_count'] == 7


def test_validate_repository_returns_validity(monkeypatch: pytest.MonkeyPatch):
    '''Stub validate_repo returning True, verify result.data['valid'] is True.'''
    from tools import github_tools

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(github_tools, 'validate_repo', lambda repo_name: True)

    result = github_tools.validate_repository('cornelisnetworks/opa-psm2')

    assert result.is_success
    assert result.data['valid'] is True
    assert result.data['repo_name'] == 'cornelisnetworks/opa-psm2'


# ****************************************************************************************
# B) PR tools
# ****************************************************************************************

def test_list_pull_requests_returns_success(monkeypatch: pytest.MonkeyPatch):
    '''Stub _list_pull_requests, verify count in metadata.'''
    from tools import github_tools

    fake_prs = [
        {'number': 101, 'title': 'Fix memory leak', 'state': 'open'},
        {'number': 102, 'title': 'Add unit tests', 'state': 'open'},
        {'number': 103, 'title': 'Update README', 'state': 'open'},
    ]

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_list_pull_requests',
        lambda repo_name, state='open', sort='created', direction='desc', limit=100: fake_prs,
    )

    result = github_tools.list_pull_requests('cornelisnetworks/opa-psm2')

    assert result.is_success
    assert len(result.data) == 3
    assert result.metadata['count'] == 3
    assert result.metadata['repo_name'] == 'cornelisnetworks/opa-psm2'
    assert result.metadata['state'] == 'open'


def test_get_pull_request_returns_single(monkeypatch: pytest.MonkeyPatch):
    '''Stub _get_pull_request, verify ToolResult with PR details.'''
    from tools import github_tools

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_get_pull_request',
        lambda repo_name, pr_number: {
            'number': pr_number,
            'title': 'Fix memory leak in PSM2',
            'state': 'open',
            'user': 'dev-engineer',
        },
    )

    result = github_tools.get_pull_request('cornelisnetworks/opa-psm2', 101)

    assert result.is_success
    assert result.data['number'] == 101
    assert result.data['title'] == 'Fix memory leak in PSM2'
    assert result.data['user'] == 'dev-engineer'


def test_get_pr_reviews_returns_list(monkeypatch: pytest.MonkeyPatch):
    '''Stub _get_pr_reviews, verify count in metadata.'''
    from tools import github_tools

    fake_reviews = [
        {'user': 'reviewer-a', 'state': 'APPROVED'},
        {'user': 'reviewer-b', 'state': 'CHANGES_REQUESTED'},
    ]

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_get_pr_reviews',
        lambda repo_name, pr_number: fake_reviews,
    )

    result = github_tools.get_pr_reviews('cornelisnetworks/opa-psm2', 101)

    assert result.is_success
    assert len(result.data) == 2
    assert result.metadata['count'] == 2
    assert result.metadata['pr_number'] == 101


# ****************************************************************************************
# C) Hygiene tools
# ****************************************************************************************

def test_find_stale_prs_returns_findings(monkeypatch: pytest.MonkeyPatch):
    '''Stub _analyze_pr_staleness returning list with one finding.'''
    from tools import github_tools

    stale_finding = [
        {'number': 55, 'title': 'Old PR', 'days_open': 30, 'last_updated': '2026-02-26'},
    ]

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_analyze_pr_staleness',
        lambda repo_name, stale_days=5: stale_finding,
    )

    result = github_tools.find_stale_prs('cornelisnetworks/opa-psm2', stale_days=7)

    assert result.is_success
    assert len(result.data) == 1
    assert result.data[0]['days_open'] == 30
    assert result.metadata['count'] == 1
    assert result.metadata['stale_days'] == 7


def test_find_missing_reviews_returns_findings(monkeypatch: pytest.MonkeyPatch):
    '''Stub _analyze_missing_reviews, verify count.'''
    from tools import github_tools

    missing = [
        {'number': 88, 'title': 'Needs review', 'review_count': 0},
    ]

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_analyze_missing_reviews',
        lambda repo_name: missing,
    )

    result = github_tools.find_missing_reviews('cornelisnetworks/opa-psm2')

    assert result.is_success
    assert len(result.data) == 1
    assert result.metadata['count'] == 1
    assert result.metadata['repo_name'] == 'cornelisnetworks/opa-psm2'


def test_analyze_pr_hygiene_returns_report(monkeypatch: pytest.MonkeyPatch):
    '''Stub _analyze_repo_pr_hygiene returning full report dict.'''
    from tools import github_tools

    report = {
        'repo_name': 'cornelisnetworks/opa-psm2',
        'total_open_prs': 12,
        'stale_prs': 3,
        'missing_reviews': 2,
        'health_score': 75,
    }

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_analyze_repo_pr_hygiene',
        lambda repo_name, stale_days=5: report,
    )

    result = github_tools.analyze_pr_hygiene('cornelisnetworks/opa-psm2')

    assert result.is_success
    assert result.data['total_open_prs'] == 12
    assert result.data['health_score'] == 75
    assert result.metadata['repo_name'] == 'cornelisnetworks/opa-psm2'
    assert result.metadata['stale_days'] == 5


# ****************************************************************************************
# D) Rate limit
# ****************************************************************************************

def test_get_rate_limit_status_returns_info(monkeypatch: pytest.MonkeyPatch):
    '''Stub _get_rate_limit returning dict with rate info.'''
    from tools import github_tools

    rate_info = {
        'core': {'limit': 5000, 'remaining': 4832, 'reset': '2026-03-28T12:00:00Z'},
        'search': {'limit': 30, 'remaining': 28, 'reset': '2026-03-28T11:31:00Z'},
    }

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(github_tools, '_get_rate_limit', lambda: rate_info)

    result = github_tools.get_rate_limit_status()

    assert result.is_success
    assert result.data['core']['remaining'] == 4832
    assert result.data['search']['limit'] == 30


# ****************************************************************************************
# E) Error handling
# ****************************************************************************************

def test_get_pr_review_requests_returns_success(monkeypatch: pytest.MonkeyPatch):
    from tools import github_tools

    monkeypatch.setattr(github_tools, 'get_github', lambda: object())
    monkeypatch.setattr(
        github_tools,
        '_get_pr_review_requests',
        lambda repo, pr: {'users': ['reviewer1'], 'teams': ['firmware-team']},
    )

    result = github_tools.get_pr_review_requests('cornelisnetworks/opa-psm2', 42)

    assert result.is_success
    assert result.data['users'] == ['reviewer1']
    assert result.data['teams'] == ['firmware-team']


def test_tool_returns_failure_on_exception(monkeypatch: pytest.MonkeyPatch):
    from tools import github_tools

    monkeypatch.setattr(
        github_tools,
        'get_github',
        lambda: (_ for _ in ()).throw(RuntimeError('Connection refused')),
    )

    result = github_tools.list_repos('cornelisnetworks')

    assert not result.is_success
    assert result.is_error
    assert 'Connection refused' in (result.error or '')


def test_tool_returns_failure_when_github_utils_unavailable(monkeypatch: pytest.MonkeyPatch):
    '''Stub get_github to raise RuntimeError about missing utils, verify failure message.'''
    from tools import github_tools

    monkeypatch.setattr(
        github_tools,
        'get_github',
        lambda: (_ for _ in ()).throw(
            RuntimeError('github_utils.py is required but not available')
        ),
    )

    result = github_tools.get_repo_info('cornelisnetworks/opa-psm2')

    assert not result.is_success
    assert 'github_utils.py is required' in (result.error or '')


# ****************************************************************************************
# F) Collection class
# ****************************************************************************************

def test_github_tools_collection_registers_methods():
    '''Instantiate GitHubTools(), verify key tools are registered.'''
    tools = GitHubTools()

    assert tools.get_tool('list_repos') is not None
    assert tools.get_tool('get_repo_info') is not None
    assert tools.get_tool('validate_repository') is not None
    assert tools.get_tool('list_pull_requests') is not None
    assert tools.get_tool('get_pull_request') is not None
    assert tools.get_tool('get_pr_reviews') is not None
    assert tools.get_tool('get_pr_review_requests') is not None
    assert tools.get_tool('find_stale_prs') is not None
    assert tools.get_tool('find_missing_reviews') is not None
    assert tools.get_tool('analyze_pr_hygiene') is not None
    assert tools.get_tool('get_rate_limit_status') is not None


def test_github_tools_collection_lists_all_tools():
    '''Verify len(tools.get_tools()) == 11 — one for each tool function.'''
    tools = GitHubTools()

    all_tools = tools.get_tools()
    assert len(all_tools) == 24

    tool_names = {t.name for t in all_tools}
    expected = {
        'list_repos',
        'get_repo_info',
        'validate_repository',
        'list_pull_requests',
        'get_pull_request',
        'get_pr_reviews',
        'get_pr_review_requests',
        'find_stale_prs',
        'find_missing_reviews',
        'analyze_pr_hygiene',
        'get_rate_limit_status',
        'check_naming_compliance',
        'check_merge_conflicts',
        'check_ci_failures',
        'check_stale_branches',
        'analyze_extended_hygiene',
        'get_repo_readme',
        'list_repo_docs',
        'search_repo_docs',
        'get_pr_changed_files',
        'get_file_content',
        'create_or_update_file',
        'batch_commit_files',
        'post_pr_comment',
    }
    assert tool_names == expected
