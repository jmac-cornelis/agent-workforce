##########
# Module:      test_drucker_api_github_char.py
# Description: Characterization tests for the 4 GitHub endpoints in drucker_api.py.
#              Covers POST /v1/github/pr-hygiene, POST /v1/github/pr-stale,
#              POST /v1/github/pr-reviews, and GET /v1/github/prs/{owner}/{repo}.
# Author:      Cornelis Networks Engineering Tools
##########

import sys
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_github_utils(monkeypatch):
    '''Provide a mock github_utils module injected into sys.modules.'''
    mock_mod = MagicMock()
    monkeypatch.setitem(sys.modules, 'github_utils', mock_mod)
    return mock_mod


@pytest.fixture
def client(mock_github_utils):
    '''Create a TestClient with mocked github_utils already in place.'''
    # Import AFTER the mock is registered so lazy imports inside endpoints
    # resolve to our mock.
    from agents.drucker.api import create_app
    from fastapi.testclient import TestClient

    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# A) POST /v1/github/pr-hygiene  (analyze_repo_pr_hygiene)
# ---------------------------------------------------------------------------

class TestPRHygiene:
    '''Tests for the /v1/github/pr-hygiene endpoint.'''

    def test_pr_hygiene_success(self, client, mock_github_utils):
        '''Happy-path: mock returns a report dict, endpoint wraps it.'''
        fake_report = {
            'repo': 'cornelisnetworks/opa-psm2',
            'stale_prs': [{'number': 42, 'title': 'old PR'}],
            'missing_reviews': [{'number': 99, 'title': 'needs review'}],
        }
        mock_github_utils.analyze_repo_pr_hygiene.return_value = fake_report

        resp = client.post(
            '/v1/github/pr-hygiene',
            json={'repo': 'cornelisnetworks/opa-psm2', 'stale_days': 5},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        data = body['data']
        assert data['repo'] == 'cornelisnetworks/opa-psm2'
        assert 'stale_prs' in data
        assert 'missing_reviews' in data

        mock_github_utils.analyze_repo_pr_hygiene.assert_called_once_with(
            'cornelisnetworks/opa-psm2',
            stale_days=5,
        )

    def test_pr_hygiene_error(self, client, mock_github_utils):
        '''When analyze_repo_pr_hygiene raises, endpoint returns ok=False.'''
        mock_github_utils.analyze_repo_pr_hygiene.side_effect = RuntimeError(
            'GitHub API rate limit exceeded'
        )

        resp = client.post(
            '/v1/github/pr-hygiene',
            json={'repo': 'cornelisnetworks/opa-psm2', 'stale_days': 3},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is False
        assert 'error' in body
        assert 'rate limit' in body['error']


# ---------------------------------------------------------------------------
# B) POST /v1/github/pr-stale  (analyze_pr_staleness)
# ---------------------------------------------------------------------------

class TestPRStale:
    '''Tests for the /v1/github/pr-stale endpoint.'''

    def test_pr_stale_success(self, client, mock_github_utils):
        '''Happy-path with explicit stale_days=7.'''
        fake_stale = [
            {'number': 10, 'title': 'stale PR', 'days_idle': 14},
            {'number': 20, 'title': 'another stale', 'days_idle': 9},
        ]
        mock_github_utils.analyze_pr_staleness.return_value = fake_stale

        resp = client.post(
            '/v1/github/pr-stale',
            json={'repo': 'cornelisnetworks/opa-psm2', 'stale_days': 7},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        data = body['data']
        assert data['repo'] == 'cornelisnetworks/opa-psm2'
        assert data['stale_days'] == 7
        assert data['stale_prs'] == fake_stale
        assert data['total_findings'] == 2

        mock_github_utils.analyze_pr_staleness.assert_called_once_with(
            'cornelisnetworks/opa-psm2',
            stale_days=7,
        )

    def test_pr_stale_default_days(self, client, mock_github_utils):
        '''Omitting stale_days should default to 5 (model default).'''
        mock_github_utils.analyze_pr_staleness.return_value = []

        resp = client.post(
            '/v1/github/pr-stale',
            json={'repo': 'cornelisnetworks/opa-psm2'},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['stale_days'] == 5

        mock_github_utils.analyze_pr_staleness.assert_called_once_with(
            'cornelisnetworks/opa-psm2',
            stale_days=5,
        )


# ---------------------------------------------------------------------------
# C) POST /v1/github/pr-reviews  (analyze_missing_reviews)
# ---------------------------------------------------------------------------

class TestPRReviews:
    '''Tests for the /v1/github/pr-reviews endpoint.'''

    def test_pr_reviews_success(self, client, mock_github_utils):
        '''Happy-path: findings list is returned under missing_reviews.'''
        fake_findings = [
            {'number': 55, 'title': 'no reviewers', 'reviewers': []},
        ]
        mock_github_utils.analyze_missing_reviews.return_value = fake_findings

        resp = client.post(
            '/v1/github/pr-reviews',
            json={'repo': 'cornelisnetworks/opa-psm2'},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        data = body['data']
        assert data['repo'] == 'cornelisnetworks/opa-psm2'
        assert data['missing_reviews'] == fake_findings
        assert data['total_findings'] == 1

        mock_github_utils.analyze_missing_reviews.assert_called_once_with(
            'cornelisnetworks/opa-psm2',
        )

    def test_pr_reviews_error(self, client, mock_github_utils):
        '''When analyze_missing_reviews raises, endpoint returns ok=False.'''
        mock_github_utils.analyze_missing_reviews.side_effect = ValueError(
            'repo not found'
        )

        resp = client.post(
            '/v1/github/pr-reviews',
            json={'repo': 'bad/repo'},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is False
        assert 'error' in body
        assert 'repo not found' in body['error']


# ---------------------------------------------------------------------------
# D) GET /v1/github/prs/{owner}/{repo}  (list_pull_requests)
# ---------------------------------------------------------------------------

class TestPRList:
    '''Tests for the /v1/github/prs/{owner}/{repo} endpoint.'''

    def test_pr_list_success(self, client, mock_github_utils):
        '''Happy-path: default state=open, limit=50.'''
        fake_prs = [
            {'number': 1, 'title': 'first PR', 'state': 'open'},
            {'number': 2, 'title': 'second PR', 'state': 'open'},
        ]
        mock_github_utils.list_pull_requests.return_value = fake_prs

        resp = client.get('/v1/github/prs/cornelisnetworks/opa-psm2')

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        data = body['data']
        assert data['repo'] == 'cornelisnetworks/opa-psm2'
        assert data['state'] == 'open'
        assert data['prs'] == fake_prs
        assert data['total'] == 2

        mock_github_utils.list_pull_requests.assert_called_once_with(
            'cornelisnetworks/opa-psm2',
            state='open',
            limit=50,
        )

    def test_pr_list_with_query_params(self, client, mock_github_utils):
        '''Explicit state=all and limit=10 are forwarded to the util.'''
        mock_github_utils.list_pull_requests.return_value = []

        resp = client.get(
            '/v1/github/prs/cornelisnetworks/opa-psm2',
            params={'state': 'all', 'limit': 10},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['state'] == 'all'
        assert body['data']['total'] == 0

        mock_github_utils.list_pull_requests.assert_called_once_with(
            'cornelisnetworks/opa-psm2',
            state='all',
            limit=10,
        )

    def test_pr_list_error(self, client, mock_github_utils):
        '''When list_pull_requests raises, endpoint returns ok=False.'''
        mock_github_utils.list_pull_requests.side_effect = ConnectionError(
            'network unreachable'
        )

        resp = client.get('/v1/github/prs/cornelisnetworks/opa-psm2')

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is False
        assert 'error' in body
        assert 'network unreachable' in body['error']
