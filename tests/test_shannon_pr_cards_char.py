##########################################################################################
#
# Module: tests/test_shannon_pr_cards_char.py
#
# Description: Characterization tests for the 4 PR card builders in shannon/cards.py.
#
# Author: Cornelis Networks
#
##########################################################################################

from shannon.cards import (
    build_pr_hygiene_card,
    build_pr_list_card,
    build_pr_reviews_card,
    build_pr_stale_card,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _card_schema_ok(card: dict) -> None:
    '''Assert the standard Adaptive Card envelope is present.'''
    assert card['$schema'] == 'http://adaptivecards.io/schemas/adaptive-card.json'
    assert card['type'] == 'AdaptiveCard'
    assert card['version'] == '1.4'
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
# Fixtures — reusable data shapes
# ---------------------------------------------------------------------------

def _stale_item(number: int = 42, title: str = 'Add feature X',
                author: str = 'jdoe', days: int = 12,
                severity: str = 'high') -> dict:
    return {
        'pr': {
            'number': number,
            'title': title,
            'author': author,
            'state': 'open',
            'draft': False,
        },
        'days_stale': days,
        'severity': severity,
    }


def _review_item(number: int = 99, title: str = 'Fix bug Y',
                 author: str = 'jane',
                 reason: str = 'no_reviewers',
                 severity: str = 'medium') -> dict:
    return {
        'pr': {
            'number': number,
            'title': title,
            'author': author,
            'state': 'open',
        },
        'reason': reason,
        'severity': severity,
    }


def _pr_item(number: int = 1, title: str = 'Some PR',
             author: str = 'dev', draft: bool = False,
             review_count: int = 2, approved: bool = True) -> dict:
    return {
        'number': number,
        'title': title,
        'author': author,
        'state': 'open',
        'draft': draft,
        'review_count': review_count,
        'approved': approved,
    }


# ===========================================================================
# A) build_pr_hygiene_card
# ===========================================================================

def test_pr_hygiene_card_with_findings():
    '''Card with stale PRs and missing reviews shows expected structure.'''
    data = {
        'repo': 'cornelis/fabric',
        'total_open_prs': 15,
        'total_findings': 3,
        'stale_prs': [
            _stale_item(42, 'Add feature X', 'jdoe', 12, 'high'),
            _stale_item(55, 'Refactor Y', 'alice', 8, 'medium'),
        ],
        'missing_reviews': [
            _review_item(99, 'Fix bug Y', 'jane', 'no_reviewers'),
        ],
        'scan_time': '2026-03-28T10:00:00Z',
    }

    card = build_pr_hygiene_card(data)

    _card_schema_ok(card)

    texts = _body_texts(card)
    assert any('PR Hygiene' in t for t in texts)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Repository') == 'cornelis/fabric'
    assert _fact_value(fs, 'Open PRs') == '15'
    assert _fact_value(fs, 'Total Findings') == '3'
    assert _fact_value(fs, 'Stale PRs') == '2'
    assert _fact_value(fs, 'Missing Reviews') == '1'

    body = '\n'.join(texts)
    assert '**Stale PRs:**' in body
    assert '**Missing Reviews:**' in body
    assert '#42' in body
    assert '#55' in body
    assert '#99' in body


def test_pr_hygiene_card_no_findings():
    '''Card with no findings shows the clean message.'''
    data = {
        'repo': 'cornelis/fabric',
        'total_open_prs': 5,
        'total_findings': 0,
        'stale_prs': [],
        'missing_reviews': [],
    }

    card = build_pr_hygiene_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    assert any('No hygiene issues found.' in t for t in texts)


def test_pr_hygiene_card_truncates_at_five():
    '''Stale PRs list is capped at 5 with a "...and N more" trailer.'''
    stale = [_stale_item(i, f'PR {i}', 'dev', i) for i in range(1, 8)]
    data = {
        'repo': 'cornelis/fabric',
        'total_open_prs': 20,
        'total_findings': 7,
        'stale_prs': stale,
        'missing_reviews': [],
    }

    card = build_pr_hygiene_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    body = '\n'.join(texts)

    for i in range(1, 6):
        assert f'#{i} ' in body
    assert '#6 ' not in body
    assert '#7 ' not in body
    assert '...and 2 more' in body


# ===========================================================================
# B) build_pr_stale_card
# ===========================================================================

def test_pr_stale_card_with_stale_prs():
    '''Card lists stale PRs and shows threshold in facts.'''
    data = {
        'repo': 'cornelis/opa-psm',
        'stale_days': 7,
        'stale_prs': [
            _stale_item(10, 'Old PR A', 'alice', 14, 'high'),
            _stale_item(20, 'Old PR B', 'bob', 9, 'medium'),
            _stale_item(30, 'Old PR C', 'carol', 8, 'low'),
        ],
    }

    card = build_pr_stale_card(data)
    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Threshold') == '7 days'
    assert _fact_value(fs, 'Stale PRs') == '3'
    assert _fact_value(fs, 'Repository') == 'cornelis/opa-psm'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert '#10' in body
    assert '#20' in body
    assert '#30' in body


def test_pr_stale_card_empty():
    '''Card with no stale PRs shows the clean message.'''
    data = {
        'repo': 'cornelis/opa-psm',
        'stale_days': 5,
        'stale_prs': [],
    }

    card = build_pr_stale_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    assert any('No stale PRs found.' in t for t in texts)


# ===========================================================================
# C) build_pr_reviews_card
# ===========================================================================

def test_pr_reviews_card_mixed_reasons():
    '''Card with both no_reviewers and pending_reviews shows correct counts.'''
    data = {
        'repo': 'cornelis/eth-sw',
        'missing_reviews': [
            _review_item(100, 'PR Alpha', 'alice', 'no_reviewers'),
            _review_item(101, 'PR Beta', 'bob', 'pending_reviews'),
            _review_item(102, 'PR Gamma', 'carol', 'no_reviewers'),
        ],
    }

    card = build_pr_reviews_card(data)
    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Total Findings') == '3'
    assert _fact_value(fs, 'No Reviewers') == '2'
    assert _fact_value(fs, 'Pending Reviews') == '1'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert 'no reviewers' in body
    assert 'pending reviews' in body


def test_pr_reviews_card_empty():
    '''Card with no missing reviews shows the clean message.'''
    data = {
        'repo': 'cornelis/eth-sw',
        'missing_reviews': [],
    }

    card = build_pr_reviews_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    assert any('All PRs have active reviews.' in t for t in texts)


# ===========================================================================
# D) build_pr_list_card
# ===========================================================================

def test_pr_list_card_with_prs():
    '''Card lists PRs with review counts and author info.'''
    data = {
        'repo': 'cornelis/fabric',
        'state': 'open',
        'prs': [
            _pr_item(1, 'Feature A', 'alice', draft=False, review_count=2, approved=True),
            _pr_item(2, 'Feature B', 'bob', draft=True, review_count=0, approved=False),
            _pr_item(3, 'Feature C', 'carol', draft=False, review_count=1, approved=False),
        ],
    }

    card = build_pr_list_card(data)
    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Count') == '3'
    assert _fact_value(fs, 'State') == 'open'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert '#1' in body
    assert '#2' in body
    assert '#3' in body
    assert '(alice)' in body
    assert '2 review(s)' in body


def test_pr_list_card_draft_and_approved_indicators():
    '''Draft PRs show [DRAFT] and approved PRs show checkmark.'''
    data = {
        'repo': 'cornelis/fabric',
        'state': 'open',
        'prs': [
            _pr_item(10, 'Draft PR', 'dev', draft=True, review_count=0, approved=False),
            _pr_item(11, 'Approved PR', 'dev', draft=False, review_count=3, approved=True),
        ],
    }

    card = build_pr_list_card(data)
    texts = _body_texts(card)
    body = '\n'.join(texts)

    assert '[DRAFT]' in body
    assert '\u2713' in body


def test_pr_list_card_empty():
    '''Card with no PRs shows the clean message.'''
    data = {
        'repo': 'cornelis/fabric',
        'state': 'open',
        'prs': [],
    }

    card = build_pr_list_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    assert any('No open PRs found.' in t for t in texts)
