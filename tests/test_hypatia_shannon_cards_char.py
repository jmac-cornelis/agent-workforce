##########################################################################################
#
# Module: tests/test_hypatia_shannon_cards_char.py
#
# Description: Characterization tests for the 4 Hypatia card builders in shannon/cards.py.
#
# Author: Cornelis Networks
#
##########################################################################################

from shannon.cards import (
    build_hypatia_doc_card,
    build_hypatia_impact_card,
    build_hypatia_records_card,
    build_hypatia_publication_card,
)


# ---------------------------------------------------------------------------
# Helpers
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


# ===========================================================================
# A) build_hypatia_doc_card
# ===========================================================================

def test_hypatia_doc_card_typical():
    '''Card with typical data shows facts, patches, validation, and warnings.'''
    data = {
        'doc_id': 'DOC-001',
        'title': 'OPA PSM Architecture',
        'doc_type': 'architecture',
        'confidence': '0.92',
        'created_at': '2026-03-28T10:00:00Z',
        'patches': ['patch-a', 'patch-b', 'patch-c'],
        'validation': {'valid': True, 'errors': []},
        'warnings': ['Missing diagram ref', 'Stale link in section 3'],
        'content_markdown': '# Architecture\n\nThis document describes...',
    }

    card = build_hypatia_doc_card(data)

    _card_schema_ok(card)

    # -- facts
    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Doc ID') == 'DOC-001'
    assert _fact_value(fs, 'Title') == 'OPA PSM Architecture'
    assert _fact_value(fs, 'Type') == 'architecture'
    assert _fact_value(fs, 'Confidence') == '0.92'
    assert _fact_value(fs, 'Created') == '2026-03-28T10:00:00Z'

    # -- body lines
    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert 'Patches: 3' in body
    assert 'Validation: valid' in body
    assert 'Warnings: 2' in body
    assert 'Missing diagram ref' in body
    assert 'Stale link in section 3' in body
    assert '**Preview:**' in body


def test_hypatia_doc_card_empty_minimal():
    '''Card with empty/minimal data still produces valid schema.'''
    data = {}

    card = build_hypatia_doc_card(data)

    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Doc ID') == ''
    assert _fact_value(fs, 'Title') == ''

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert 'Patches: 0' in body
    assert 'Validation: invalid' in body
    assert 'Warnings: 0' in body
    # No preview when content_markdown is empty
    assert '**Preview:**' not in body


def test_hypatia_doc_card_long_content_truncated():
    '''Content preview is truncated at 200 chars with ellipsis.'''
    long_content = 'A' * 300
    data = {
        'doc_id': 'DOC-002',
        'title': 'Long Doc',
        'content_markdown': long_content,
    }

    card = build_hypatia_doc_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert '**Preview:**' in body
    # Preview should be 200 chars + '...'
    assert '...' in body
    # Full 300-char string should NOT appear
    assert long_content not in body


# ===========================================================================
# B) build_hypatia_impact_card
# ===========================================================================

def test_hypatia_impact_card_with_targets_and_blockers():
    '''Card with affected targets and blocking issues shows both sections.'''
    data = {
        'impact_id': 'IMP-101',
        'title': 'PSM API Change',
        'doc_type': 'api-change',
        'confidence': '0.85',
        'affected_targets': ['libfabric', 'psm3', 'opa-fm'],
        'reasons': ['API signature changed', 'Deprecated endpoint removed'],
        'blocking_issues': ['STL-1234', 'STL-5678'],
    }

    card = build_hypatia_impact_card(data)

    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Impact ID') == 'IMP-101'
    assert _fact_value(fs, 'Title') == 'PSM API Change'
    assert _fact_value(fs, 'Type') == 'api-change'
    assert _fact_value(fs, 'Confidence') == '0.85'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert '**Affected Targets:**' in body
    assert 'libfabric' in body
    assert 'psm3' in body
    assert 'opa-fm' in body
    assert '**Reasons:**' in body
    assert 'API signature changed' in body
    assert '**Blocking Issues:**' in body
    assert 'STL-1234' in body
    assert 'STL-5678' in body


def test_hypatia_impact_card_no_impacts():
    '''Card with no targets, reasons, or blockers shows fallback message.'''
    data = {
        'impact_id': 'IMP-102',
        'title': 'No-op Change',
        'doc_type': 'minor',
        'confidence': '0.10',
        'affected_targets': [],
        'reasons': [],
        'blocking_issues': [],
    }

    card = build_hypatia_impact_card(data)

    _card_schema_ok(card)

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert 'No impact detected.' in body
    assert '**Affected Targets:**' not in body


def test_hypatia_impact_card_truncates_targets_at_five():
    '''Affected targets list is capped at 5 with a "...and N more" trailer.'''
    targets = [f'target-{i}' for i in range(1, 9)]
    data = {
        'impact_id': 'IMP-103',
        'title': 'Wide Impact',
        'doc_type': 'refactor',
        'confidence': '0.70',
        'affected_targets': targets,
    }

    card = build_hypatia_impact_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    body = '\n'.join(texts)

    for i in range(1, 6):
        assert f'target-{i}' in body
    assert 'target-6' not in body
    assert '...and 3 more' in body


# ===========================================================================
# C) build_hypatia_records_card
# ===========================================================================

def _record_item(doc_id: str = 'DOC-001', title: str = 'Some Doc',
                 doc_type: str = 'guide',
                 created_at: str = '2026-03-01') -> dict:
    return {
        'doc_id': doc_id,
        'title': title,
        'doc_type': doc_type,
        'created_at': created_at,
    }


def test_hypatia_records_card_multiple():
    '''Card with multiple records shows each record line.'''
    data = {
        'total': 3,
        'records': [
            _record_item('DOC-001', 'Architecture Guide', 'architecture', '2026-03-01'),
            _record_item('DOC-002', 'API Reference', 'api-ref', '2026-03-10'),
            _record_item('DOC-003', 'Release Notes', 'release', '2026-03-15'),
        ],
    }

    card = build_hypatia_records_card(data)

    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Total Records') == '3'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert '**DOC-001**' in body
    assert 'Architecture Guide' in body
    assert '[architecture]' in body
    assert '**DOC-002**' in body
    assert '**DOC-003**' in body


def test_hypatia_records_card_empty():
    '''Card with no records shows fallback message.'''
    data = {
        'total': 0,
        'records': [],
    }

    card = build_hypatia_records_card(data)

    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Total Records') == '0'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert 'No documentation records found.' in body


def test_hypatia_records_card_truncates_at_ten():
    '''Records list is capped at 10 with a "...and N more" trailer.'''
    records = [_record_item(f'DOC-{i:03d}', f'Doc {i}') for i in range(1, 15)]
    data = {
        'total': 14,
        'records': records,
    }

    card = build_hypatia_records_card(data)
    _card_schema_ok(card)

    texts = _body_texts(card)
    body = '\n'.join(texts)

    # First 10 should appear
    for i in range(1, 11):
        assert f'DOC-{i:03d}' in body
    # 11th and beyond should not
    assert 'DOC-011' not in body
    assert '...and 4 more' in body


# ===========================================================================
# D) build_hypatia_publication_card
# ===========================================================================

def test_hypatia_publication_card_with_publications():
    '''Card with successful publications shows each target line.'''
    data = {
        'doc_id': 'DOC-050',
        'title': 'PSM3 User Guide',
        'publications': [
            {'target_type': 'confluence', 'status': 'published', 'target_ref': 'SPACE/page-123'},
            {'target_type': 'markdown', 'status': 'written', 'target_ref': 'docs/psm3-guide.md'},
        ],
    }

    card = build_hypatia_publication_card(data)

    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Doc ID') == 'DOC-050'
    assert _fact_value(fs, 'Title') == 'PSM3 User Guide'
    assert _fact_value(fs, 'Publications') == '2'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert 'confluence: published (SPACE/page-123)' in body
    assert 'markdown: written (docs/psm3-guide.md)' in body


def test_hypatia_publication_card_no_publications():
    '''Card with no publications shows fallback message.'''
    data = {
        'doc_id': 'DOC-051',
        'title': 'Unpublished Draft',
        'publications': [],
    }

    card = build_hypatia_publication_card(data)

    _card_schema_ok(card)

    fs = _find_fact_set(card)
    assert _fact_value(fs, 'Publications') == '0'

    texts = _body_texts(card)
    body = '\n'.join(texts)
    assert 'No publication results.' in body
