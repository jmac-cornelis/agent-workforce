##########################################################################################
#
# Module: tests/test_github_integration_char.py
#
# Description: Integration smoke tests for the GitHub PR hygiene pipeline.
#              Validates analyze_repo_pr_hygiene() → card builder end-to-end.
#
# Author: Cornelis Networks
#
##########################################################################################

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import github_utils
from shannon.cards import (
    build_pr_hygiene_card,
    build_pr_list_card,
    build_pr_reviews_card,
    build_pr_stale_card,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pr(number, title, author, days_old, draft=False,
             requested_reviewers=None, requested_teams=None,
             review_count=0, approved=False, labels=None):
    now = datetime.now(timezone.utc)
    user = SimpleNamespace(login=author)
    reviewer_objs = [SimpleNamespace(login=r) for r in (requested_reviewers or [])]
    team_objs = [SimpleNamespace(slug=t) for t in (requested_teams or [])]
    label_objs = [SimpleNamespace(name=l) for l in (labels or [])]

    class ReviewList:
        def __init__(self, count):
            self.totalCount = count
            self._items = []
        def __iter__(self):
            return iter(self._items)

    return SimpleNamespace(
        number=number,
        title=title,
        user=user,
        state='open',
        draft=draft,
        mergeable=True,
        html_url=f'https://github.com/cornelisnetworks/opa-psm2/pull/{number}',
        created_at=now - timedelta(days=days_old),
        updated_at=now - timedelta(days=days_old),
        merged_at=None,
        closed_at=None,
        head=SimpleNamespace(ref=f'feature/pr-{number}'),
        base=SimpleNamespace(ref='main'),
        requested_reviewers=reviewer_objs,
        requested_teams=team_objs,
        labels=label_objs,
        get_reviews=lambda: ReviewList(review_count),
    )


@pytest.fixture(autouse=True)
def reset_state():
    github_utils.reset_connection()
    yield
    github_utils.reset_connection()


# ---------------------------------------------------------------------------
# A) Full pipeline: analyze_repo_pr_hygiene → build_pr_hygiene_card
# ---------------------------------------------------------------------------

def test_hygiene_report_to_card_pipeline(monkeypatch):
    monkeypatch.setattr(github_utils, 'output', lambda msg='': None)

    stale_pr = _make_pr(10, 'Old feature', 'dev1', days_old=8)
    no_review_pr = _make_pr(20, 'Needs eyes', 'dev2', days_old=2,
                            requested_reviewers=[], review_count=0)
    healthy_pr = _make_pr(30, 'Looking good', 'dev3', days_old=1,
                          requested_reviewers=['reviewer1'], review_count=1,
                          approved=True)

    fake_repo = SimpleNamespace(
        get_pulls=lambda state, sort, direction: [stale_pr, no_review_pr, healthy_pr],
    )
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    report = github_utils.analyze_repo_pr_hygiene(
        'cornelisnetworks/opa-psm2', stale_days=5,
    )

    assert report['repo'] == 'cornelisnetworks/opa-psm2'
    assert report['total_open_prs'] == 3
    assert len(report['stale_prs']) >= 1
    assert len(report['missing_reviews']) >= 1
    assert report['total_findings'] == len(report['stale_prs']) + len(report['missing_reviews'])

    card = build_pr_hygiene_card(report)

    assert card['type'] == 'AdaptiveCard'
    assert card['version'] == '1.5'
    assert isinstance(card['body'], list)
    assert len(card['body']) > 0

    fact_set = next((b for b in card['body'] if b.get('type') == 'FactSet'), None)
    assert fact_set is not None
    fact_titles = [f['title'] for f in fact_set['facts']]
    assert 'Repository' in fact_titles
    assert 'Total Findings' in fact_titles


# ---------------------------------------------------------------------------
# B) Staleness pipeline: analyze_pr_staleness → build_pr_stale_card
# ---------------------------------------------------------------------------

def test_staleness_to_card_pipeline(monkeypatch):
    monkeypatch.setattr(github_utils, 'output', lambda msg='': None)

    stale_pr = _make_pr(10, 'Very old PR', 'dev1', days_old=12)
    fresh_pr = _make_pr(20, 'Fresh PR', 'dev2', days_old=1)

    fake_repo = SimpleNamespace(
        get_pulls=lambda state, sort, direction: [stale_pr, fresh_pr],
    )
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    findings = github_utils.analyze_pr_staleness('cornelisnetworks/opa-psm2', stale_days=5)

    assert len(findings) == 1
    assert findings[0]['pr']['number'] == 10

    card_data = {
        'repo': 'cornelisnetworks/opa-psm2',
        'stale_prs': findings,
        'stale_days': 5,
    }
    card = build_pr_stale_card(card_data)

    assert card['type'] == 'AdaptiveCard'
    body_texts = [b.get('text', '') for b in card['body'] if b.get('type') == 'TextBlock']
    assert any('Very old PR' in t or '#10' in t for t in body_texts)


# ---------------------------------------------------------------------------
# C) Missing reviews pipeline: analyze_missing_reviews → build_pr_reviews_card
# ---------------------------------------------------------------------------

def test_missing_reviews_to_card_pipeline(monkeypatch):
    monkeypatch.setattr(github_utils, 'output', lambda msg='': None)

    no_reviewer = _make_pr(15, 'Lonely PR', 'dev1', days_old=3,
                           requested_reviewers=[], review_count=0)
    draft_pr = _make_pr(25, 'WIP draft', 'dev2', days_old=3,
                        draft=True, requested_reviewers=[], review_count=0)

    fake_repo = SimpleNamespace(
        get_pulls=lambda state, sort, direction: [no_reviewer, draft_pr],
    )
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    findings = github_utils.analyze_missing_reviews('cornelisnetworks/opa-psm2')

    assert len(findings) == 1
    assert findings[0]['pr']['number'] == 15

    card_data = {
        'repo': 'cornelisnetworks/opa-psm2',
        'findings': findings,
    }
    card = build_pr_reviews_card(card_data)

    assert card['type'] == 'AdaptiveCard'


# ---------------------------------------------------------------------------
# D) PR list pipeline: list_pull_requests → build_pr_list_card
# ---------------------------------------------------------------------------

def test_list_prs_to_card_pipeline(monkeypatch):
    monkeypatch.setattr(github_utils, 'output', lambda msg='': None)

    pr1 = _make_pr(5, 'Feature A', 'dev1', days_old=2, draft=True)
    pr2 = _make_pr(6, 'Feature B', 'dev2', days_old=1, review_count=2, approved=True)

    fake_repo = SimpleNamespace(
        get_pulls=lambda state, sort, direction: [pr1, pr2],
    )
    fake_gh = SimpleNamespace(get_repo=lambda name: fake_repo)
    monkeypatch.setattr(github_utils, 'get_connection', lambda: fake_gh)

    prs = github_utils.list_pull_requests('cornelisnetworks/opa-psm2')

    assert len(prs) == 2

    card_data = {
        'repo': 'cornelisnetworks/opa-psm2',
        'prs': prs,
        'state': 'open',
    }
    card = build_pr_list_card(card_data)

    assert card['type'] == 'AdaptiveCard'
    body_texts = [b.get('text', '') for b in card['body'] if b.get('type') == 'TextBlock']
    assert any('Feature A' in t or 'Feature B' in t or '#5' in t or '#6' in t for t in body_texts)
