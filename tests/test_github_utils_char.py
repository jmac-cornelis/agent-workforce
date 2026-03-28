import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, Optional

import pytest

import github_utils


# ---------------------------------------------------------------------------
# Helpers — match jira_utils test pattern
# ---------------------------------------------------------------------------

def _silent_output(_message: str = '') -> None:
    return None


def _patch_common(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(github_utils, 'output', _silent_output)


def _make_fake_repo(
    full_name: str = 'cornelisnetworks/opa-psm2',
    name: str = 'opa-psm2',
    description: str = 'OPA PSM2 library',
    default_branch: str = 'main',
    private: bool = False,
    archived: bool = False,
    fork: bool = False,
    open_issues_count: int = 5,
    stargazers_count: int = 42,
    language: str = 'C',
    html_url: str = 'https://github.com/cornelisnetworks/opa-psm2',
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
    pushed_at: Optional[datetime] = None,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        full_name=full_name,
        name=name,
        description=description,
        default_branch=default_branch,
        private=private,
        archived=archived,
        fork=fork,
        open_issues_count=open_issues_count,
        stargazers_count=stargazers_count,
        language=language,
        html_url=html_url,
        created_at=created_at or now,
        updated_at=updated_at or now,
        pushed_at=pushed_at or now,
    )


def _make_fake_pr(
    number: int = 1,
    title: str = 'Fix buffer overflow',
    user_login: str = 'jdoe',
    state: str = 'open',
    draft: bool = False,
    mergeable: bool = True,
    html_url: str = 'https://github.com/cornelisnetworks/opa-psm2/pull/1',
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
    merged_at: Optional[datetime] = None,
    closed_at: Optional[datetime] = None,
    head_ref: str = 'fix-buffer',
    base_ref: str = 'main',
    requested_reviewers: Optional[list] = None,
    requested_teams: Optional[list] = None,
    labels: Optional[list] = None,
    review_count: int = 0,
    review_states: Optional[list] = None,
    user: Any = None,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)

    # Build user object
    if user is None:
        pr_user = SimpleNamespace(login=user_login) if user_login else None
    else:
        pr_user = user

    # Build reviewer list
    if requested_reviewers is None:
        requested_reviewers = []
    reviewer_objs = [SimpleNamespace(login=r) for r in requested_reviewers]

    # Build team list
    if requested_teams is None:
        requested_teams = []
    team_objs = [SimpleNamespace(slug=t) for t in requested_teams]

    # Build label list
    if labels is None:
        labels = []
    label_objs = [SimpleNamespace(name=l) for l in labels]

    # Build reviews iterable
    if review_states is None:
        review_states = []
    review_items = [SimpleNamespace(state=s) for s in review_states]

    class _ReviewList:
        def __init__(self, items, count):
            self._items = items
            self.totalCount = count

        def __iter__(self):
            return iter(self._items)

    reviews_obj = _ReviewList(review_items, review_count)

    return SimpleNamespace(
        number=number,
        title=title,
        user=pr_user,
        state=state,
        created_at=created_at or now,
        updated_at=updated_at or now,
        merged_at=merged_at,
        closed_at=closed_at,
        head=SimpleNamespace(ref=head_ref),
        base=SimpleNamespace(ref=base_ref),
        draft=draft,
        mergeable=mergeable,
        html_url=html_url,
        requested_reviewers=reviewer_objs,
        requested_teams=team_objs,
        labels=label_objs,
        get_reviews=lambda: reviews_obj,
    )


def _make_fake_review(
    review_id: int = 100,
    user_login: str = 'reviewer1',
    state: str = 'APPROVED',
    body: str = 'Looks good',
    submitted_at: Optional[datetime] = None,
    html_url: str = 'https://github.com/cornelisnetworks/opa-psm2/pull/1#pullrequestreview-100',
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=review_id,
        user=SimpleNamespace(login=user_login),
        state=state,
        body=body,
        submitted_at=submitted_at or now,
        html_url=html_url,
    )


# ---------------------------------------------------------------------------
# Autouse fixture — reset github_utils state before/after each test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_github_utils_state():
    github_utils.reset_connection()
    github_utils._quiet_mode = False
    yield
    github_utils.reset_connection()
    github_utils._quiet_mode = False


# =========================================================================
# A) Credentials & Connection
# =========================================================================

def test_get_github_credentials_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'ghp_test_token_123')

    token = github_utils.get_github_credentials()

    assert token == 'ghp_test_token_123'


def test_get_github_credentials_missing_token(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv('GITHUB_TOKEN', raising=False)

    with pytest.raises(github_utils.GitHubCredentialsError):
        github_utils.get_github_credentials()


def test_get_connection_caches_and_reset(monkeypatch: pytest.MonkeyPatch):
    sentinel = object()
    call_count = {'count': 0}

    def _fake_connect():
        call_count['count'] += 1
        return sentinel

    monkeypatch.setattr(github_utils, 'connect_to_github', _fake_connect)
    github_utils.reset_connection()

    conn1 = github_utils.get_connection()
    conn2 = github_utils.get_connection()

    assert conn1 is sentinel
    assert conn2 is sentinel
    assert call_count['count'] == 1

    github_utils.reset_connection()
    _ = github_utils.get_connection()
    assert call_count['count'] == 2


def test_connect_to_github_ghe_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'ghp_test_token_123')
    monkeypatch.setattr(github_utils, 'GITHUB_URL', 'https://github.example.com/api/v3')
    monkeypatch.setattr(github_utils, 'DEFAULT_GITHUB_URL', 'https://api.github.com')

    captured = {}

    class FakeGithub:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def get_user(self):
            return SimpleNamespace(login='testuser')

    monkeypatch.setattr(github_utils, 'Github', FakeGithub)

    gh = github_utils.connect_to_github()

    assert 'base_url' in captured
    assert captured['base_url'] == 'https://github.example.com/api/v3'


# =========================================================================
# B) Normalization helpers
# =========================================================================

def test_normalize_repo_extracts_fields():
    now = datetime.now(timezone.utc)
    repo = _make_fake_repo(
        full_name='cornelisnetworks/opa-psm2',
        name='opa-psm2',
        description='OPA PSM2 library',
        default_branch='main',
        private=True,
        archived=False,
        fork=False,
        open_issues_count=5,
        stargazers_count=42,
        language='C',
        html_url='https://github.com/cornelisnetworks/opa-psm2',
        created_at=now,
        updated_at=now,
        pushed_at=now,
    )

    result = github_utils._normalize_repo(repo)

    assert result['full_name'] == 'cornelisnetworks/opa-psm2'
    assert result['name'] == 'opa-psm2'
    assert result['description'] == 'OPA PSM2 library'
    assert result['default_branch'] == 'main'
    assert result['visibility'] == 'private'
    assert result['archived'] is False
    assert result['fork'] is False
    assert result['open_issues_count'] == 5
    assert result['stargazers_count'] == 42
    assert result['language'] == 'C'
    assert result['html_url'] == 'https://github.com/cornelisnetworks/opa-psm2'
    assert result['created_at'] == now.isoformat()
    assert result['updated_at'] == now.isoformat()
    assert result['pushed_at'] == now.isoformat()


def test_normalize_pr_extracts_fields():
    now = datetime.now(timezone.utc)
    pr = _make_fake_pr(
        number=42,
        title='Fix buffer overflow',
        user_login='jdoe',
        state='open',
        draft=False,
        mergeable=True,
        created_at=now,
        updated_at=now,
        head_ref='fix-buffer',
        base_ref='main',
        requested_reviewers=['reviewer1', 'reviewer2'],
        requested_teams=['core-team'],
        labels=['bug', 'urgent'],
        review_count=2,
        review_states=['APPROVED', 'COMMENTED'],
    )

    result = github_utils._normalize_pr(pr)

    assert result['number'] == 42
    assert result['title'] == 'Fix buffer overflow'
    assert result['author'] == 'jdoe'
    assert result['state'] == 'open'
    assert result['draft'] is False
    assert result['mergeable'] is True
    assert result['head_branch'] == 'fix-buffer'
    assert result['base_branch'] == 'main'
    assert result['requested_reviewers'] == ['reviewer1', 'reviewer2']
    assert result['requested_teams'] == ['core-team']
    assert result['labels'] == ['bug', 'urgent']
    assert result['review_count'] == 2
    assert result['approved'] is True
    assert result['created_at'] == now.isoformat()
    assert result['updated_at'] == now.isoformat()
    assert result['html_url'] == 'https://github.com/cornelisnetworks/opa-psm2/pull/1'


def test_normalize_review_extracts_fields():
    now = datetime.now(timezone.utc)
    review = _make_fake_review(
        review_id=200,
        user_login='reviewer1',
        state='APPROVED',
        body='LGTM',
        submitted_at=now,
        html_url='https://github.com/cornelisnetworks/opa-psm2/pull/1#pullrequestreview-200',
    )

    result = github_utils._normalize_review(review)

    assert result['id'] == 200
    assert result['user'] == 'reviewer1'
    assert result['state'] == 'APPROVED'
    assert result['body'] == 'LGTM'
    assert result['submitted_at'] == now.isoformat()
    assert result['html_url'] == 'https://github.com/cornelisnetworks/opa-psm2/pull/1#pullrequestreview-200'


def test_normalize_pr_handles_none_user():
    pr = _make_fake_pr(user_login=None, user=None)
    # Override user to None explicitly (the helper sets it to None when user_login is None)
    pr.user = None

    result = github_utils._normalize_pr(pr)

    assert result['author'] == 'unknown'


# =========================================================================
# C) Repository operations
# =========================================================================

def test_list_repos_returns_list(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    fake_repo = _make_fake_repo()

    fake_org = SimpleNamespace(get_repos=lambda: [fake_repo])
    fake_gh = SimpleNamespace(get_organization=lambda org: fake_org)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    repos = github_utils.list_repos('cornelisnetworks')

    assert isinstance(repos, list)
    assert len(repos) == 1
    assert repos[0]['full_name'] == 'cornelisnetworks/opa-psm2'


def test_get_repo_info_returns_dict(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    fake_repo = _make_fake_repo(full_name='cornelisnetworks/opa-psm2')

    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    result = github_utils.get_repo_info('cornelisnetworks/opa-psm2')

    assert isinstance(result, dict)
    assert result['full_name'] == 'cornelisnetworks/opa-psm2'
    assert result['name'] == 'opa-psm2'


def test_validate_repo_true_and_false(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    # Case 1: repo exists
    fake_repo = _make_fake_repo()
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    assert github_utils.validate_repo('cornelisnetworks/opa-psm2') is True

    # Case 2: repo does not exist — get_repo_info raises GitHubRepoError
    def _raise_repo_error(name):
        raise github_utils.GitHubRepoError(f'not found: {name}')

    monkeypatch.setattr(github_utils, 'get_repo_info', _raise_repo_error)

    assert github_utils.validate_repo('cornelisnetworks/nonexistent') is False


# =========================================================================
# D) Pull Request operations
# =========================================================================

def test_list_pull_requests_returns_normalized(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    fake_pr = _make_fake_pr(number=10, title='Add feature X')

    fake_repo = SimpleNamespace(
        get_pulls=lambda state='open', sort='created', direction='desc': [fake_pr],
    )
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    prs = github_utils.list_pull_requests('cornelisnetworks/opa-psm2')

    assert isinstance(prs, list)
    assert len(prs) == 1
    assert prs[0]['number'] == 10
    assert prs[0]['title'] == 'Add feature X'


def test_get_pull_request_returns_single(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    fake_pr = _make_fake_pr(number=42, title='Fix segfault')

    fake_repo = SimpleNamespace(get_pull=lambda n: fake_pr)
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    result = github_utils.get_pull_request('cornelisnetworks/opa-psm2', 42)

    assert result['number'] == 42
    assert result['title'] == 'Fix segfault'


def test_get_pr_reviews_returns_list(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    fake_review = _make_fake_review(review_id=300, user_login='reviewer1', state='APPROVED')

    fake_pr = SimpleNamespace(get_reviews=lambda: [fake_review])
    fake_repo = SimpleNamespace(get_pull=lambda n: fake_pr)
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    reviews = github_utils.get_pr_reviews('cornelisnetworks/opa-psm2', 42)

    assert isinstance(reviews, list)
    assert len(reviews) == 1
    assert reviews[0]['id'] == 300
    assert reviews[0]['state'] == 'APPROVED'


# =========================================================================
# E) Hygiene analysis
# =========================================================================

def test_analyze_pr_staleness_finds_stale(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    now = datetime.now(timezone.utc)
    old_date = (now - timedelta(days=8)).isoformat()

    stale_pr = {
        'number': 1,
        'title': 'Old PR',
        'author': 'jdoe',
        'state': 'open',
        'updated_at': old_date,
        'draft': False,
    }

    monkeypatch.setattr(github_utils, 'list_pull_requests', lambda *a, **kw: [stale_pr])

    results = github_utils.analyze_pr_staleness('cornelisnetworks/opa-psm2', stale_days=5)

    assert len(results) == 1
    assert results[0]['days_stale'] >= 7
    assert results[0]['severity'] == 'medium'


def test_analyze_pr_staleness_draft_grace_period(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    now = datetime.now(timezone.utc)
    # 6 days old — within draft grace period (5 * 2 = 10 days)
    six_days_ago = (now - timedelta(days=6)).isoformat()

    draft_pr = {
        'number': 2,
        'title': 'Draft PR',
        'author': 'jdoe',
        'state': 'open',
        'updated_at': six_days_ago,
        'draft': True,
    }

    monkeypatch.setattr(github_utils, 'list_pull_requests', lambda *a, **kw: [draft_pr])

    results = github_utils.analyze_pr_staleness('cornelisnetworks/opa-psm2', stale_days=5)

    # Draft with 6 days should NOT be stale (threshold is 10 for drafts)
    assert len(results) == 0


def test_analyze_pr_staleness_non_draft_is_stale_at_6(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    now = datetime.now(timezone.utc)
    six_days_ago = (now - timedelta(days=6)).isoformat()

    non_draft_pr = {
        'number': 3,
        'title': 'Non-draft PR',
        'author': 'jdoe',
        'state': 'open',
        'updated_at': six_days_ago,
        'draft': False,
    }

    monkeypatch.setattr(github_utils, 'list_pull_requests', lambda *a, **kw: [non_draft_pr])

    results = github_utils.analyze_pr_staleness('cornelisnetworks/opa-psm2', stale_days=5)

    # Non-draft with 6 days SHOULD be stale (threshold is 5)
    assert len(results) == 1
    assert results[0]['days_stale'] >= 5
    assert results[0]['severity'] == 'medium'


def test_analyze_missing_reviews_no_reviewers(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    pr_no_reviews = {
        'number': 10,
        'title': 'Lonely PR',
        'author': 'jdoe',
        'state': 'open',
        'draft': False,
        'review_count': 0,
        'requested_reviewers': [],
        'requested_teams': [],
        'approved': False,
    }

    monkeypatch.setattr(github_utils, 'list_pull_requests', lambda *a, **kw: [pr_no_reviews])

    results = github_utils.analyze_missing_reviews('cornelisnetworks/opa-psm2')

    assert len(results) == 1
    assert results[0]['reason'] == 'no_reviewers'
    assert results[0]['severity'] == 'medium'


def test_analyze_missing_reviews_skips_drafts(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    draft_pr = {
        'number': 11,
        'title': 'Draft with no reviews',
        'author': 'jdoe',
        'state': 'open',
        'draft': True,
        'review_count': 0,
        'requested_reviewers': [],
        'requested_teams': [],
        'approved': False,
    }

    monkeypatch.setattr(github_utils, 'list_pull_requests', lambda *a, **kw: [draft_pr])

    results = github_utils.analyze_missing_reviews('cornelisnetworks/opa-psm2')

    # Draft PRs should be excluded
    assert len(results) == 0


def test_analyze_repo_pr_hygiene_returns_report(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    stale_finding = {
        'pr': {'number': 1, 'title': 'Stale PR', 'author': 'jdoe'},
        'days_stale': 12,
        'severity': 'high',
    }
    review_finding = {
        'pr': {'number': 2, 'title': 'No reviews', 'author': 'jane'},
        'reason': 'no_reviewers',
        'severity': 'medium',
    }

    monkeypatch.setattr(github_utils, 'analyze_pr_staleness', lambda *a, **kw: [stale_finding])
    monkeypatch.setattr(github_utils, 'analyze_missing_reviews', lambda *a, **kw: [review_finding])
    monkeypatch.setattr(github_utils, 'list_pull_requests', lambda *a, **kw: [
        {'number': 1}, {'number': 2}, {'number': 3},
    ])

    report = github_utils.analyze_repo_pr_hygiene('cornelisnetworks/opa-psm2', stale_days=5)

    assert report['repo'] == 'cornelisnetworks/opa-psm2'
    assert 'scan_time' in report
    assert len(report['stale_prs']) == 1
    assert len(report['missing_reviews']) == 1
    assert report['total_open_prs'] == 3
    assert report['total_findings'] == 2
    assert 'summary' in report


# =========================================================================
# F) Rate limit
# =========================================================================

def test_get_rate_limit_returns_dict(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    reset_time = datetime(2026, 3, 28, 12, 0, 0)

    fake_core = SimpleNamespace(limit=5000, remaining=4500, reset=reset_time)
    fake_rate = SimpleNamespace(core=fake_core)
    fake_gh = SimpleNamespace(get_rate_limit=lambda: fake_rate)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    result = github_utils.get_rate_limit()

    assert result['limit'] == 5000
    assert result['remaining'] == 4500
    assert result['used'] == 500
    assert 'reset' in result


def test_check_rate_limit_returns_bool(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    monkeypatch.setattr(github_utils, 'get_rate_limit', lambda: {
        'limit': 5000,
        'remaining': 50,
        'reset': '2026-03-28T12:00:00+00:00',
        'used': 4950,
    })

    # 50 remaining < 100 minimum → should return False
    assert github_utils.check_rate_limit(minimum=100) is False

    # 50 remaining >= 10 minimum → should return True
    assert github_utils.check_rate_limit(minimum=10) is True


# =========================================================================
# G) Output & CLI
# =========================================================================

def test_output_respects_quiet_mode(monkeypatch: pytest.MonkeyPatch, capsys):
    monkeypatch.setattr(github_utils, '_quiet_mode', False)
    github_utils.output('visible message')
    out_visible = capsys.readouterr().out

    monkeypatch.setattr(github_utils, '_quiet_mode', True)
    github_utils.output('hidden message')
    out_hidden = capsys.readouterr().out

    assert 'visible message' in out_visible
    assert out_hidden == ''


def test_handle_args_list_prs(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, 'argv', [
        'github_utils.py', '--list-prs', 'cornelisnetworks/opa-psm2',
    ])

    args = github_utils.handle_args()

    assert args.list_prs == 'cornelisnetworks/opa-psm2'


# =========================================================================
# H) Exceptions
# =========================================================================

def test_exception_hierarchy():
    assert issubclass(github_utils.GitHubConnectionError, github_utils.Error)
    assert issubclass(github_utils.GitHubCredentialsError, github_utils.Error)
    assert issubclass(github_utils.GitHubRepoError, github_utils.Error)
    assert issubclass(github_utils.GitHubPRError, github_utils.Error)

    # Verify they are all subclasses of Exception too
    assert issubclass(github_utils.Error, Exception)


def test_list_repos_unknown_org_raises(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)

    def _raise_unknown(org):
        raise github_utils.UnknownObjectException(404, 'Not Found', None)

    fake_gh = SimpleNamespace(get_organization=_raise_unknown)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    with pytest.raises(github_utils.GitHubRepoError):
        github_utils.list_repos('nonexistent-org')
