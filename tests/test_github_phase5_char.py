from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import github_utils


# ---------------------------------------------------------------------------
# Helpers — reuse patterns from test_github_utils_char.py
# ---------------------------------------------------------------------------

def _silent_output(_message: str = '') -> None:
    return None


def _patch_common(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(github_utils, 'output', _silent_output)


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


# ---------------------------------------------------------------------------
# Fake PR builder — returns normalised dict (not SimpleNamespace)
# ---------------------------------------------------------------------------

def _make_pr_dict(
    number=1,
    title='Fix buffer overflow',
    author='jdoe',
    state='open',
    draft=False,
    head_branch='fix-buffer',
    base_branch='main',
    html_url='https://github.com/cornelisnetworks/opa-psm2/pull/1',
    updated_at=None,
    **extra,
):
    now = datetime.now(timezone.utc)
    d = {
        'number': number,
        'title': title,
        'author': author,
        'state': state,
        'draft': draft,
        'head_branch': head_branch,
        'base_branch': base_branch,
        'html_url': html_url,
        'created_at': (updated_at or now.isoformat()),
        'updated_at': (updated_at or now.isoformat()),
        'merged_at': None,
        'closed_at': None,
        'mergeable': None,
        'requested_reviewers': [],
        'requested_teams': [],
        'labels': [],
        'review_count': 0,
        'approved': False,
    }
    d.update(extra)
    return d


# =========================================================================
# A) analyze_naming_compliance
# =========================================================================

class TestAnalyzeNamingCompliance:
    '''Characterization tests for analyze_naming_compliance().'''

    def test_naming_all_compliant(self, monkeypatch):
        '''3 PRs with STL-12345 in title → 0 pr_findings, 3 title_compliant.'''
        _patch_common(monkeypatch)
        prs = [
            _make_pr_dict(number=1, title='STL-1001 Add feature A', head_branch='STL-1001-feature-a'),
            _make_pr_dict(number=2, title='STL-1002 Fix bug B', head_branch='STL-1002-fix-b'),
            _make_pr_dict(number=3, title='STLSW-999 Refactor C', head_branch='STLSW-999-refactor'),
        ]

        result = github_utils.analyze_naming_compliance(
            'cornelisnetworks/opa-psm2', _prefetched_prs=prs)

        assert result['pr_findings'] == []
        assert result['summary']['title_compliant'] == 3
        assert result['summary']['title_noncompliant'] == 0
        assert result['total_findings'] == 0

    def test_naming_noncompliant_title(self, monkeypatch):
        '''PR without ticket ref targeting main → severity high, in pr_findings.'''
        _patch_common(monkeypatch)
        prs = [
            _make_pr_dict(number=10, title='Quick fix no ticket', base_branch='main',
                          head_branch='quick-fix'),
        ]

        result = github_utils.analyze_naming_compliance(
            'cornelisnetworks/opa-psm2', _prefetched_prs=prs)

        assert len(result['pr_findings']) == 1
        finding = result['pr_findings'][0]
        assert finding['severity'] == 'high'
        assert finding['pr']['number'] == 10
        assert finding['title_compliant'] is False

    def test_naming_no_jira_tag_accepted(self, monkeypatch):
        '''PR title with [NO-JIRA] → title_compliant, has_no_jira=True, no_jira_count=1.'''
        _patch_common(monkeypatch)
        prs = [
            _make_pr_dict(number=20, title='[NO-JIRA] Update README',
                          head_branch='update-readme'),
        ]

        result = github_utils.analyze_naming_compliance(
            'cornelisnetworks/opa-psm2', _prefetched_prs=prs)

        # Title is compliant (no pr_findings for title), but branch is noncompliant
        assert len(result['pr_findings']) == 0
        assert result['summary']['title_compliant'] == 1
        assert result['summary']['no_jira_count'] == 1

    def test_naming_noncompliant_branch(self, monkeypatch):
        '''Branch without ticket ref → in branch_findings with branch_name, pr_number, author.'''
        _patch_common(monkeypatch)
        prs = [
            _make_pr_dict(number=30, title='STL-5000 Good title',
                          head_branch='my-random-branch', author='alice'),
        ]

        result = github_utils.analyze_naming_compliance(
            'cornelisnetworks/opa-psm2', _prefetched_prs=prs)

        assert len(result['branch_findings']) == 1
        bf = result['branch_findings'][0]
        assert bf['branch_name'] == 'my-random-branch'
        assert bf['pr_number'] == 30
        assert bf['author'] == 'alice'

    def test_naming_custom_patterns(self, monkeypatch):
        '''Custom ticket_patterns=['(?i)CUSTOM-\\d+'] works.'''
        _patch_common(monkeypatch)
        prs = [
            _make_pr_dict(number=40, title='CUSTOM-100 New feature',
                          head_branch='CUSTOM-100-new'),
        ]

        result = github_utils.analyze_naming_compliance(
            'cornelisnetworks/opa-psm2',
            ticket_patterns=[r'(?i)CUSTOM-\d+'],
            _prefetched_prs=prs,
        )

        assert result['pr_findings'] == []
        assert result['summary']['title_compliant'] == 1
        assert result['ticket_patterns'] == [r'(?i)CUSTOM-\d+']

    def test_naming_uses_prefetched_prs(self, monkeypatch):
        '''Passes _prefetched_prs directly, never calls list_pull_requests.'''
        _patch_common(monkeypatch)
        called = {'list_prs': False}

        def _track_list(*a, **kw):
            called['list_prs'] = True
            return []

        monkeypatch.setattr(github_utils, 'list_pull_requests', _track_list)

        prs = [_make_pr_dict(number=50, title='STL-1 test', head_branch='STL-1-test')]
        github_utils.analyze_naming_compliance(
            'cornelisnetworks/opa-psm2', _prefetched_prs=prs)

        assert called['list_prs'] is False


# =========================================================================
# B) analyze_merge_conflicts
# =========================================================================

class TestAnalyzeMergeConflicts:
    '''Characterization tests for analyze_merge_conflicts().'''

    def test_merge_conflicts_graphql_path(self, monkeypatch):
        '''Stub _graphql_pr_mergeability → only CONFLICTING in conflicts, severity=high.'''
        _patch_common(monkeypatch)
        gql_prs = [
            {'number': 1, 'title': 'PR A', 'author': 'alice', 'url': 'http://x/1',
             'head_ref': 'a', 'base_ref': 'main', 'draft': False, 'mergeable': 'CONFLICTING'},
            {'number': 2, 'title': 'PR B', 'author': 'bob', 'url': 'http://x/2',
             'head_ref': 'b', 'base_ref': 'main', 'draft': False, 'mergeable': 'MERGEABLE'},
        ]
        monkeypatch.setattr(github_utils, '_graphql_pr_mergeability', lambda o, n: gql_prs)

        result = github_utils.analyze_merge_conflicts('cornelisnetworks/opa-psm2')

        assert result['total_conflicts'] == 1
        assert result['total_open_prs'] == 2
        assert result['conflicts'][0]['pr']['number'] == 1
        assert result['conflicts'][0]['severity'] == 'high'

    def test_merge_conflicts_no_conflicts(self, monkeypatch):
        '''All MERGEABLE → empty conflicts list.'''
        _patch_common(monkeypatch)
        gql_prs = [
            {'number': 1, 'title': 'PR A', 'author': 'alice', 'url': 'http://x/1',
             'head_ref': 'a', 'base_ref': 'main', 'draft': False, 'mergeable': 'MERGEABLE'},
        ]
        monkeypatch.setattr(github_utils, '_graphql_pr_mergeability', lambda o, n: gql_prs)

        result = github_utils.analyze_merge_conflicts('cornelisnetworks/opa-psm2')

        assert result['conflicts'] == []
        assert result['total_conflicts'] == 0

    def test_merge_conflicts_rest_fallback(self, monkeypatch):
        '''GraphQL raises → REST fallback with pr.mergeable=False → found in conflicts.'''
        _patch_common(monkeypatch)

        def _raise_gql(*a, **kw):
            raise RuntimeError('GraphQL unavailable')

        monkeypatch.setattr(github_utils, '_graphql_pr_mergeability', _raise_gql)

        # Stub list_pull_requests for REST fallback
        prs = [_make_pr_dict(number=5, title='Conflict PR', author='carol',
                             head_branch='feat-x', base_branch='main')]
        monkeypatch.setattr(github_utils, 'list_pull_requests', lambda *a, **kw: prs)

        # Stub get_connection → repo.get_pull → pr_obj.mergeable=False
        fake_pr_obj = SimpleNamespace(mergeable=False)
        fake_repo = SimpleNamespace(get_pull=lambda n: fake_pr_obj)
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

        result = github_utils.analyze_merge_conflicts('cornelisnetworks/opa-psm2')

        assert result['total_conflicts'] == 1
        assert result['conflicts'][0]['pr']['number'] == 5
        assert result['conflicts'][0]['mergeable_state'] == 'dirty'

    def test_merge_conflicts_summary_format(self, monkeypatch):
        '''Summary string: "N of M open PRs have merge conflicts".'''
        _patch_common(monkeypatch)
        gql_prs = [
            {'number': 1, 'title': 'A', 'author': 'a', 'url': '', 'head_ref': 'x',
             'base_ref': 'main', 'draft': False, 'mergeable': 'CONFLICTING'},
            {'number': 2, 'title': 'B', 'author': 'b', 'url': '', 'head_ref': 'y',
             'base_ref': 'main', 'draft': False, 'mergeable': 'MERGEABLE'},
            {'number': 3, 'title': 'C', 'author': 'c', 'url': '', 'head_ref': 'z',
             'base_ref': 'main', 'draft': False, 'mergeable': 'CONFLICTING'},
        ]
        monkeypatch.setattr(github_utils, '_graphql_pr_mergeability', lambda o, n: gql_prs)

        result = github_utils.analyze_merge_conflicts('cornelisnetworks/opa-psm2')

        assert result['summary'] == '2 of 3 open PRs have merge conflicts'


# =========================================================================
# C) analyze_ci_failures
# =========================================================================

class TestAnalyzeCiFailures:
    '''Characterization tests for analyze_ci_failures().'''

    def test_ci_failures_graphql_path(self, monkeypatch):
        '''Stub _graphql_pr_ci_status → PRs with FAILURE rollup + failed_checks → in failures.'''
        _patch_common(monkeypatch)
        gql_prs = [
            {'number': 1, 'title': 'Failing PR', 'author': 'alice', 'url': 'http://x/1',
             'head_ref': 'a', 'base_ref': 'main', 'draft': False,
             'rollup_state': 'FAILURE',
             'failed_checks': [{'name': 'ci/build', 'conclusion': 'FAILURE'}]},
            {'number': 2, 'title': 'Good PR', 'author': 'bob', 'url': 'http://x/2',
             'head_ref': 'b', 'base_ref': 'main', 'draft': False,
             'rollup_state': 'SUCCESS', 'failed_checks': []},
        ]
        monkeypatch.setattr(github_utils, '_graphql_pr_ci_status', lambda o, n: gql_prs)

        result = github_utils.analyze_ci_failures('cornelisnetworks/opa-psm2')

        assert result['total_failures'] == 1
        assert result['failures'][0]['pr']['number'] == 1
        assert result['failures'][0]['failed_checks'] == [{'name': 'ci/build', 'conclusion': 'FAILURE'}]

    def test_ci_failures_no_failures(self, monkeypatch):
        '''All SUCCESS → empty failures list.'''
        _patch_common(monkeypatch)
        gql_prs = [
            {'number': 1, 'title': 'Good PR', 'author': 'alice', 'url': 'http://x/1',
             'head_ref': 'a', 'base_ref': 'main', 'draft': False,
             'rollup_state': 'SUCCESS', 'failed_checks': []},
        ]
        monkeypatch.setattr(github_utils, '_graphql_pr_ci_status', lambda o, n: gql_prs)

        result = github_utils.analyze_ci_failures('cornelisnetworks/opa-psm2')

        assert result['failures'] == []
        assert result['total_failures'] == 0

    def test_ci_failures_rest_fallback(self, monkeypatch):
        '''GraphQL raises → REST fallback with check_runs returning failure → found in failures.'''
        _patch_common(monkeypatch)

        def _raise_gql(*a, **kw):
            raise RuntimeError('GraphQL unavailable')

        monkeypatch.setattr(github_utils, '_graphql_pr_ci_status', _raise_gql)

        # Stub list_pull_requests for REST fallback
        prs = [_make_pr_dict(number=7, title='CI Fail PR', author='dave',
                             head_branch='feat-y', base_branch='main')]
        monkeypatch.setattr(github_utils, 'list_pull_requests', lambda *a, **kw: prs)

        # Build REST chain: get_connection → repo → get_pull → head.sha → get_commit → check_runs
        fake_check = SimpleNamespace(name='ci/lint', conclusion='failure')
        fake_commit = SimpleNamespace(
            get_check_runs=lambda: [fake_check],
            get_statuses=lambda: [],
        )
        fake_pr_obj = SimpleNamespace(head=SimpleNamespace(sha='abc123'))
        fake_repo = SimpleNamespace(
            get_pull=lambda n: fake_pr_obj,
            get_commit=lambda sha: fake_commit,
        )
        fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
        monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

        result = github_utils.analyze_ci_failures('cornelisnetworks/opa-psm2')

        assert result['total_failures'] == 1
        assert result['failures'][0]['pr']['number'] == 7
        assert result['failures'][0]['failed_checks'][0]['name'] == 'ci/lint'

    def test_ci_failures_draft_pr_severity(self, monkeypatch):
        '''Draft PR with CI failure → severity=medium (non-draft=high).'''
        _patch_common(monkeypatch)
        gql_prs = [
            {'number': 1, 'title': 'Draft fail', 'author': 'alice', 'url': 'http://x/1',
             'head_ref': 'a', 'base_ref': 'main', 'draft': True,
             'rollup_state': 'FAILURE', 'failed_checks': [{'name': 'ci/build', 'conclusion': 'FAILURE'}]},
            {'number': 2, 'title': 'Non-draft fail', 'author': 'bob', 'url': 'http://x/2',
             'head_ref': 'b', 'base_ref': 'main', 'draft': False,
             'rollup_state': 'FAILURE', 'failed_checks': [{'name': 'ci/test', 'conclusion': 'FAILURE'}]},
        ]
        monkeypatch.setattr(github_utils, '_graphql_pr_ci_status', lambda o, n: gql_prs)

        result = github_utils.analyze_ci_failures('cornelisnetworks/opa-psm2')

        assert result['total_failures'] == 2
        # Draft → medium
        draft_failure = [f for f in result['failures'] if f['pr']['number'] == 1][0]
        assert draft_failure['severity'] == 'medium'
        # Non-draft → high
        nondraft_failure = [f for f in result['failures'] if f['pr']['number'] == 2][0]
        assert nondraft_failure['severity'] == 'high'


# =========================================================================
# D) analyze_stale_branches
# =========================================================================

class TestAnalyzeStaleBranches:
    '''Characterization tests for analyze_stale_branches().'''

    def _make_branch(self, name, days_ago, open_pr_count=0, is_protected=False):
        '''Helper to build a branch dict as returned by _graphql_stale_branches.'''
        commit_date = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
        return {
            'name': name,
            'last_commit_date': commit_date,
            'last_commit_author': 'dev1',
            'is_protected': is_protected,
            'open_pr_count': open_pr_count,
        }

    def test_stale_branches_finds_stale(self, monkeypatch):
        '''Branch older than threshold, no open PRs → in stale_branches.'''
        _patch_common(monkeypatch)
        branches = [self._make_branch('old-feature', days_ago=45)]
        monkeypatch.setattr(github_utils, '_graphql_stale_branches',
                            lambda o, n, c: (branches, 1, []))

        result = github_utils.analyze_stale_branches(
            'cornelisnetworks/opa-psm2', stale_days=30)

        assert len(result['stale_branches']) == 1
        assert result['stale_branches'][0]['name'] == 'old-feature'
        assert result['stale_branches'][0]['days_stale'] >= 44

    def test_stale_branches_skips_with_open_prs(self, monkeypatch):
        '''Branch with open_pr_count=1 → excluded.'''
        _patch_common(monkeypatch)
        branches = [self._make_branch('has-pr', days_ago=60, open_pr_count=1)]
        monkeypatch.setattr(github_utils, '_graphql_stale_branches',
                            lambda o, n, c: (branches, 1, []))

        result = github_utils.analyze_stale_branches(
            'cornelisnetworks/opa-psm2', stale_days=30)

        assert result['stale_branches'] == []
        assert result['summary']['with_open_prs'] == 1

    def test_stale_branches_skips_protected(self, monkeypatch):
        '''Protected branch → excluded when exclude_protected=True.'''
        _patch_common(monkeypatch)
        branches = [self._make_branch('main', days_ago=90, is_protected=True)]
        monkeypatch.setattr(github_utils, '_graphql_stale_branches',
                            lambda o, n, c: (branches, 1, ['main']))

        result = github_utils.analyze_stale_branches(
            'cornelisnetworks/opa-psm2', stale_days=30, exclude_protected=True)

        assert result['stale_branches'] == []
        assert result['summary']['protected_excluded'] == 1

    def test_stale_branches_includes_protected_when_disabled(self, monkeypatch):
        '''exclude_protected=False → protected branches included.'''
        _patch_common(monkeypatch)
        branches = [self._make_branch('main', days_ago=90, is_protected=True)]
        monkeypatch.setattr(github_utils, '_graphql_stale_branches',
                            lambda o, n, c: (branches, 1, ['main']))

        result = github_utils.analyze_stale_branches(
            'cornelisnetworks/opa-psm2', stale_days=30, exclude_protected=False)

        assert len(result['stale_branches']) == 1
        assert result['stale_branches'][0]['name'] == 'main'

    def test_stale_branches_severity_tiers(self, monkeypatch):
        '''<60 days = low, 60-179 = medium, 180+ = high.'''
        _patch_common(monkeypatch)
        branches = [
            self._make_branch('low-stale', days_ago=45),
            self._make_branch('med-stale', days_ago=100),
            self._make_branch('high-stale', days_ago=200),
        ]
        monkeypatch.setattr(github_utils, '_graphql_stale_branches',
                            lambda o, n, c: (branches, 3, []))

        result = github_utils.analyze_stale_branches(
            'cornelisnetworks/opa-psm2', stale_days=30)

        # Build a name→severity map
        sev_map = {b['name']: b['severity'] for b in result['stale_branches']}
        assert sev_map['low-stale'] == 'low'
        assert sev_map['med-stale'] == 'medium'
        assert sev_map['high-stale'] == 'high'


# =========================================================================
# E) analyze_extended_hygiene
# =========================================================================

class TestAnalyzeExtendedHygiene:
    '''Characterization tests for analyze_extended_hygiene().'''

    def test_extended_hygiene_combines_all_scans(self, monkeypatch):
        '''Stub all 6 sub-functions, verify result has all 6 keys + total_findings is sum.'''
        _patch_common(monkeypatch)

        # Stub GraphQL PR fetch
        monkeypatch.setattr(github_utils, '_graphql_list_open_prs',
                            lambda o, n: [_make_pr_dict(number=1)])

        # Stub each scan
        monkeypatch.setattr(github_utils, 'analyze_pr_staleness',
                            lambda *a, **kw: [{'pr': {}, 'days_stale': 10, 'severity': 'high'}])
        monkeypatch.setattr(github_utils, 'analyze_missing_reviews',
                            lambda *a, **kw: [{'pr': {}, 'reason': 'no_reviewers', 'severity': 'medium'}])
        monkeypatch.setattr(github_utils, 'analyze_naming_compliance',
                            lambda *a, **kw: {'total_findings': 2, 'pr_findings': [{}, {}],
                                              'branch_findings': [], 'summary': {}})
        monkeypatch.setattr(github_utils, 'analyze_merge_conflicts',
                            lambda *a, **kw: {'total_conflicts': 1, 'conflicts': [{}],
                                              'total_open_prs': 1, 'summary': ''})
        monkeypatch.setattr(github_utils, 'analyze_ci_failures',
                            lambda *a, **kw: {'total_failures': 1, 'failures': [{}],
                                              'total_open_prs': 1, 'summary': ''})
        monkeypatch.setattr(github_utils, 'analyze_stale_branches',
                            lambda *a, **kw: {'total_findings': 3, 'stale_branches': [{}, {}, {}],
                                              'summary': {}})

        result = github_utils.analyze_extended_hygiene('cornelisnetworks/opa-psm2')

        # All 6 keys present
        assert 'stale_prs' in result
        assert 'missing_reviews' in result
        assert 'naming_findings' in result
        assert 'merge_conflicts' in result
        assert 'ci_failures' in result
        assert 'stale_branches' in result

        # total_findings = 1 stale + 1 review + 2 naming + 1 conflict + 1 ci + 3 branch = 9
        assert result['total_findings'] == 9

    def test_extended_hygiene_stale_branch_failure_graceful(self, monkeypatch):
        '''Stub analyze_stale_branches to raise → result still has empty stale_branches entry.'''
        _patch_common(monkeypatch)

        monkeypatch.setattr(github_utils, '_graphql_list_open_prs',
                            lambda o, n: [])
        monkeypatch.setattr(github_utils, 'analyze_pr_staleness',
                            lambda *a, **kw: [])
        monkeypatch.setattr(github_utils, 'analyze_missing_reviews',
                            lambda *a, **kw: [])
        monkeypatch.setattr(github_utils, 'analyze_naming_compliance',
                            lambda *a, **kw: {'total_findings': 0, 'pr_findings': [],
                                              'branch_findings': [], 'summary': {}})
        monkeypatch.setattr(github_utils, 'analyze_merge_conflicts',
                            lambda *a, **kw: {'total_conflicts': 0, 'conflicts': [],
                                              'total_open_prs': 0, 'summary': ''})
        monkeypatch.setattr(github_utils, 'analyze_ci_failures',
                            lambda *a, **kw: {'total_failures': 0, 'failures': [],
                                              'total_open_prs': 0, 'summary': ''})

        def _raise_branch(*a, **kw):
            raise RuntimeError('Branch scan exploded')

        monkeypatch.setattr(github_utils, 'analyze_stale_branches', _raise_branch)

        result = github_utils.analyze_extended_hygiene('cornelisnetworks/opa-psm2')

        assert result['stale_branches']['stale_branches'] == []
        assert result['stale_branches']['total_findings'] == 0

    def test_extended_hygiene_passes_prefetched_prs(self, monkeypatch):
        '''Verify PR-based scans receive _prefetched_prs (use monkeypatch to track calls).'''
        _patch_common(monkeypatch)

        captured_kw = {'staleness': None, 'reviews': None, 'naming': None}

        fake_prs = [_make_pr_dict(number=99)]
        monkeypatch.setattr(github_utils, '_graphql_list_open_prs',
                            lambda o, n: fake_prs)

        def _track_staleness(*a, **kw):
            captured_kw['staleness'] = kw.get('_prefetched_prs')
            return []

        def _track_reviews(*a, **kw):
            captured_kw['reviews'] = kw.get('_prefetched_prs')
            return []

        def _track_naming(*a, **kw):
            captured_kw['naming'] = kw.get('_prefetched_prs')
            return {'total_findings': 0, 'pr_findings': [], 'branch_findings': [],
                    'summary': {}}

        monkeypatch.setattr(github_utils, 'analyze_pr_staleness', _track_staleness)
        monkeypatch.setattr(github_utils, 'analyze_missing_reviews', _track_reviews)
        monkeypatch.setattr(github_utils, 'analyze_naming_compliance', _track_naming)
        monkeypatch.setattr(github_utils, 'analyze_merge_conflicts',
                            lambda *a, **kw: {'total_conflicts': 0, 'conflicts': [],
                                              'total_open_prs': 0, 'summary': ''})
        monkeypatch.setattr(github_utils, 'analyze_ci_failures',
                            lambda *a, **kw: {'total_failures': 0, 'failures': [],
                                              'total_open_prs': 0, 'summary': ''})
        monkeypatch.setattr(github_utils, 'analyze_stale_branches',
                            lambda *a, **kw: {'total_findings': 0, 'stale_branches': [],
                                              'summary': {}})

        github_utils.analyze_extended_hygiene('cornelisnetworks/opa-psm2')

        # All three PR-based scans should have received the same prefetched list
        assert captured_kw['staleness'] is fake_prs
        assert captured_kw['reviews'] is fake_prs
        assert captured_kw['naming'] is fake_prs

    def test_extended_hygiene_graphql_fallback(self, monkeypatch):
        '''Stub _graphql_list_open_prs to raise, verify list_pull_requests called as fallback.'''
        _patch_common(monkeypatch)
        called = {'list_prs': False}

        def _raise_gql(*a, **kw):
            raise RuntimeError('GraphQL down')

        monkeypatch.setattr(github_utils, '_graphql_list_open_prs', _raise_gql)

        def _track_list(*a, **kw):
            called['list_prs'] = True
            return []

        monkeypatch.setattr(github_utils, 'list_pull_requests', _track_list)
        monkeypatch.setattr(github_utils, 'analyze_pr_staleness', lambda *a, **kw: [])
        monkeypatch.setattr(github_utils, 'analyze_missing_reviews', lambda *a, **kw: [])
        monkeypatch.setattr(github_utils, 'analyze_naming_compliance',
                            lambda *a, **kw: {'total_findings': 0, 'pr_findings': [],
                                              'branch_findings': [], 'summary': {}})
        monkeypatch.setattr(github_utils, 'analyze_merge_conflicts',
                            lambda *a, **kw: {'total_conflicts': 0, 'conflicts': [],
                                              'total_open_prs': 0, 'summary': ''})
        monkeypatch.setattr(github_utils, 'analyze_ci_failures',
                            lambda *a, **kw: {'total_failures': 0, 'failures': [],
                                              'total_open_prs': 0, 'summary': ''})
        monkeypatch.setattr(github_utils, 'analyze_stale_branches',
                            lambda *a, **kw: {'total_findings': 0, 'stale_branches': [],
                                              'summary': {}})

        github_utils.analyze_extended_hygiene('cornelisnetworks/opa-psm2')

        assert called['list_prs'] is True


# =========================================================================
# F) GraphQL helpers
# =========================================================================

class TestGraphQLHelpers:
    '''Characterization tests for the 3 GraphQL helper functions.'''

    def _make_fake_session(self, monkeypatch, response_json):
        '''Stub _get_graphql_session to return a session whose post() returns response_json.'''
        fake_resp = SimpleNamespace(json=lambda: response_json)
        fake_session = SimpleNamespace(post=lambda url, json=None: fake_resp)
        monkeypatch.setattr(github_utils, '_get_graphql_session', lambda: fake_session)

    def test_graphql_pr_mergeability_parses_response(self, monkeypatch):
        '''Stub _get_graphql_session + requests.post response → correct list returned.'''
        _patch_common(monkeypatch)
        response = {
            'data': {
                'repository': {
                    'pullRequests': {
                        'pageInfo': {'hasNextPage': False, 'endCursor': None},
                        'nodes': [
                            {
                                'number': 10,
                                'title': 'Test PR',
                                'isDraft': False,
                                'url': 'https://github.com/o/r/pull/10',
                                'headRefName': 'feat-x',
                                'baseRefName': 'main',
                                'author': {'login': 'alice'},
                                'mergeable': 'CONFLICTING',
                            },
                        ],
                    },
                },
            },
        }
        self._make_fake_session(monkeypatch, response)

        result = github_utils._graphql_pr_mergeability('cornelisnetworks', 'opa-psm2')

        assert len(result) == 1
        assert result[0]['number'] == 10
        assert result[0]['mergeable'] == 'CONFLICTING'
        assert result[0]['author'] == 'alice'
        assert result[0]['head_ref'] == 'feat-x'

    def test_graphql_pr_ci_status_parses_checks(self, monkeypatch):
        '''Stub GraphQL response with CheckRun + StatusContext nodes → correct parsing.'''
        _patch_common(monkeypatch)
        response = {
            'data': {
                'repository': {
                    'pullRequests': {
                        'pageInfo': {'hasNextPage': False, 'endCursor': None},
                        'nodes': [
                            {
                                'number': 20,
                                'title': 'CI PR',
                                'isDraft': False,
                                'url': 'https://github.com/o/r/pull/20',
                                'headRefName': 'feat-ci',
                                'baseRefName': 'main',
                                'author': {'login': 'bob'},
                                'commits': {
                                    'nodes': [{
                                        'commit': {
                                            'statusCheckRollup': {
                                                'state': 'FAILURE',
                                                'contexts': {
                                                    'nodes': [
                                                        # CheckRun node
                                                        {'name': 'ci/build', 'conclusion': 'FAILURE',
                                                         'status': 'COMPLETED'},
                                                        # StatusContext node
                                                        {'context': 'ci/deploy', 'state': 'ERROR'},
                                                        # Passing CheckRun — should NOT appear in failed
                                                        {'name': 'ci/lint', 'conclusion': 'SUCCESS',
                                                         'status': 'COMPLETED'},
                                                    ],
                                                },
                                            },
                                        },
                                    }],
                                },
                            },
                        ],
                    },
                },
            },
        }
        self._make_fake_session(monkeypatch, response)

        result = github_utils._graphql_pr_ci_status('cornelisnetworks', 'opa-psm2')

        assert len(result) == 1
        pr = result[0]
        assert pr['rollup_state'] == 'FAILURE'
        assert len(pr['failed_checks']) == 2
        names = [c['name'] for c in pr['failed_checks']]
        assert 'ci/build' in names
        assert 'ci/deploy' in names

    def test_graphql_stale_branches_parses_refs(self, monkeypatch):
        '''Stub GraphQL response with refs, protection rules → correct branch list + patterns.'''
        _patch_common(monkeypatch)
        response = {
            'data': {
                'repository': {
                    'refs': {
                        'pageInfo': {'hasNextPage': False, 'endCursor': None},
                        'totalCount': 2,
                        'nodes': [
                            {
                                'name': 'old-feature',
                                'target': {
                                    'committedDate': '2025-01-01T00:00:00Z',
                                    'author': {'name': 'dev1'},
                                },
                                'associatedPullRequests': {'totalCount': 0},
                            },
                            {
                                'name': 'main',
                                'target': {
                                    'committedDate': '2026-03-29T00:00:00Z',
                                    'author': {'name': 'dev2'},
                                },
                                'associatedPullRequests': {'totalCount': 1},
                            },
                        ],
                    },
                    'branchProtectionRules': {
                        'nodes': [
                            {'pattern': 'main'},
                            {'pattern': 'release-*'},
                        ],
                    },
                },
            },
        }
        self._make_fake_session(monkeypatch, response)

        branches, total_count, protection_patterns = github_utils._graphql_stale_branches(
            'cornelisnetworks', 'opa-psm2', '2026-01-01T00:00:00Z')

        assert total_count == 2
        assert len(branches) == 2
        assert branches[0]['name'] == 'old-feature'
        assert branches[0]['last_commit_date'] == '2025-01-01T00:00:00Z'
        assert branches[0]['last_commit_author'] == 'dev1'
        assert branches[0]['open_pr_count'] == 0
        # main matches protection pattern 'main'
        assert branches[1]['is_protected'] is True
        assert protection_patterns == ['main', 'release-*']
