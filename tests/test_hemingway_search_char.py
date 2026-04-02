##########
# Module:      test_hemingway_search_char.py
# Description: Characterization tests for Hemingway search capabilities.
#              Covers HemingwayRecordStore.search_records(), the POST /v1/docs/search
#              API endpoint, and the search_hemingway_records() tool wrapper.
# Author:      Cornelis Networks Engineering Tools
##########

import json
import os
import sys
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from agents.hemingway.state.record_store import HemingwayRecordStore


# ---------------------------------------------------------------------------
# Helpers — reusable record data builders
# ---------------------------------------------------------------------------

def _make_record(
    doc_id: str = 'test-1',
    title: str = 'PSM2 Architecture',
    doc_type: str = 'as_built',
    project_key: str = 'STL',
    created_at: str = '2026-03-30T10:00:00Z',
    content_markdown: str = '# PSM2\nHardware abstraction layer...',
    summary_markdown: str = 'Summary of PSM2',
    confidence: str = 'high',
    source_refs: Optional[List[str]] = None,
    patches: Optional[List[Dict]] = None,
    warnings: Optional[List[str]] = None,
    publication_records: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    '''Build a record dict suitable for HemingwayRecordStore.save_record().'''
    return {
        'doc_id': doc_id,
        'title': title,
        'doc_type': doc_type,
        'project_key': project_key,
        'created_at': created_at,
        'content_markdown': content_markdown,
        'summary_markdown': summary_markdown,
        'confidence': confidence,
        'source_refs': source_refs or ['src/psm2_hal.c', 'src/psm2_ep.c'],
        'patches': patches or [],
        'warnings': warnings or [],
        'publication_records': publication_records or [],
    }


def _store_with_records(tmp_path, records: List[Dict[str, Any]]) -> HemingwayRecordStore:
    '''Create a HemingwayRecordStore in tmp_path and save the given records.'''
    store = HemingwayRecordStore(storage_dir=str(tmp_path))
    for rec in records:
        store.save_record(rec)
    return store


# ===========================================================================
# A) HemingwayRecordStore.search_records() — direct store tests
# ===========================================================================

class TestSearchRecordsByQuery:
    '''Tests for query-based text matching in search_records().'''

    def test_search_records_by_query_matches_title(self, tmp_path):
        '''Query substring found in title returns that record.'''
        rec_a = _make_record(doc_id='a', title='PSM2 Architecture Guide')
        rec_b = _make_record(
            doc_id='b', title='CN5000 User Manual',
            content_markdown='# CN5000\nSwitch management overview...',
            summary_markdown='Summary of CN5000',
        )
        store = _store_with_records(tmp_path, [rec_a, rec_b])

        results = store.search_records(query='PSM2')

        assert len(results) == 1
        assert results[0]['doc_id'] == 'a'

    def test_search_records_by_query_matches_content(self, tmp_path):
        '''Query substring found in content_markdown returns that record.'''
        rec_a = _make_record(
            doc_id='a',
            title='Generic Title',
            content_markdown='# Overview\nThe OPA fabric manager handles...',
        )
        rec_b = _make_record(
            doc_id='b',
            title='Another Title',
            content_markdown='# Build\nCompile instructions...',
        )
        store = _store_with_records(tmp_path, [rec_a, rec_b])

        results = store.search_records(query='fabric manager')

        assert len(results) == 1
        assert results[0]['doc_id'] == 'a'

    def test_search_records_query_is_case_insensitive(self, tmp_path):
        '''Query matching is case-insensitive.'''
        rec = _make_record(doc_id='a', title='PSM2 Architecture')
        store = _store_with_records(tmp_path, [rec])

        results = store.search_records(query='psm2 architecture')

        assert len(results) == 1


class TestSearchRecordsByFilter:
    '''Tests for exact-match and substring filter fields.'''

    def test_search_records_by_project_key(self, tmp_path):
        '''Filter by project_key returns only matching records.'''
        rec_stl = _make_record(doc_id='stl-1', project_key='STL')
        rec_opa = _make_record(doc_id='opa-1', project_key='OPA')
        store = _store_with_records(tmp_path, [rec_stl, rec_opa])

        results = store.search_records(project_key='STL')

        assert len(results) == 1
        assert results[0]['doc_id'] == 'stl-1'

    def test_search_records_by_doc_type(self, tmp_path):
        '''Filter by doc_type returns only matching records.'''
        rec_ab = _make_record(doc_id='ab-1', doc_type='as_built')
        rec_ug = _make_record(doc_id='ug-1', doc_type='user_guide')
        store = _store_with_records(tmp_path, [rec_ab, rec_ug])

        results = store.search_records(doc_type='as_built')

        assert len(results) == 1
        assert results[0]['doc_id'] == 'ab-1'

    def test_search_records_by_source_ref(self, tmp_path):
        '''Filter by source_ref substring matches against source_refs list items.'''
        rec_a = _make_record(
            doc_id='a',
            source_refs=['src/psm2_hal.c', 'src/psm2_ep.c'],
        )
        rec_b = _make_record(
            doc_id='b',
            source_refs=['src/cn5000_init.c'],
        )
        store = _store_with_records(tmp_path, [rec_a, rec_b])

        results = store.search_records(source_ref='psm2_hal')

        assert len(results) == 1
        assert results[0]['doc_id'] == 'a'

    def test_search_records_by_confidence(self, tmp_path):
        '''Filter by confidence level returns only matching records.'''
        rec_high = _make_record(doc_id='h', confidence='high')
        rec_med = _make_record(doc_id='m', confidence='medium')
        store = _store_with_records(tmp_path, [rec_high, rec_med])

        results = store.search_records(confidence='high')

        assert len(results) == 1
        assert results[0]['doc_id'] == 'h'

    def test_search_records_published_only(self, tmp_path):
        '''published_only=True returns only records with a published publication.'''
        rec_published = _make_record(
            doc_id='pub',
            publication_records=[{
                'publication_id': 'pub-001',
                'status': 'published',
                'published_at': '2026-03-30T12:00:00Z',
            }],
        )
        rec_unpublished = _make_record(
            doc_id='unpub',
            publication_records=[],
        )
        store = _store_with_records(tmp_path, [rec_published, rec_unpublished])

        results = store.search_records(published_only=True)

        assert len(results) == 1
        assert results[0]['doc_id'] == 'pub'


class TestSearchRecordsCombinedAndEdge:
    '''Tests for combined filters, empty results, limit, and match_context.'''

    def test_search_records_combined_filters(self, tmp_path):
        '''Multiple filters applied together narrow results correctly.'''
        rec_match = _make_record(
            doc_id='match',
            title='PSM2 Architecture',
            project_key='STL',
            doc_type='as_built',
        )
        rec_wrong_project = _make_record(
            doc_id='wrong-proj',
            title='PSM2 Architecture',
            project_key='OPA',
            doc_type='as_built',
        )
        rec_wrong_type = _make_record(
            doc_id='wrong-type',
            title='PSM2 Architecture',
            project_key='STL',
            doc_type='user_guide',
        )
        store = _store_with_records(
            tmp_path, [rec_match, rec_wrong_project, rec_wrong_type],
        )

        results = store.search_records(
            query='PSM2',
            project_key='STL',
            doc_type='as_built',
        )

        assert len(results) == 1
        assert results[0]['doc_id'] == 'match'

    def test_search_records_empty_results(self, tmp_path):
        '''No matching records returns an empty list.'''
        rec = _make_record(doc_id='a', title='PSM2 Architecture')
        store = _store_with_records(tmp_path, [rec])

        results = store.search_records(query='nonexistent-term-xyz')

        assert results == []

    def test_search_records_limit(self, tmp_path):
        '''Limit parameter caps the number of returned results.'''
        records = [
            _make_record(
                doc_id=f'rec-{i}',
                title='Common Title',
                created_at=f'2026-03-{10 + i:02d}T10:00:00Z',
            )
            for i in range(5)
        ]
        store = _store_with_records(tmp_path, records)

        results = store.search_records(query='Common', limit=2)

        assert len(results) == 2

    def test_search_records_match_context(self, tmp_path):
        '''When query matches, match_context field is present in results.'''
        rec = _make_record(
            doc_id='ctx',
            title='PSM2 Architecture',
            content_markdown='# PSM2\nDetailed hardware abstraction layer docs...',
        )
        store = _store_with_records(tmp_path, [rec])

        results = store.search_records(query='PSM2')

        assert len(results) == 1
        assert 'match_context' in results[0]
        assert len(results[0]['match_context']) > 0

    def test_search_records_no_query_omits_match_context(self, tmp_path):
        '''When no query is provided, match_context is not in results.'''
        rec = _make_record(doc_id='no-q', title='Some Doc')
        store = _store_with_records(tmp_path, [rec])

        results = store.search_records(project_key='STL')

        assert len(results) == 1
        assert 'match_context' not in results[0]


# ===========================================================================
# B) API endpoint — POST /v1/docs/search
# ===========================================================================

class TestSearchApiEndpoint:
    '''Tests for the POST /v1/docs/search FastAPI endpoint.'''

    @pytest.fixture
    def mock_record_store(self):
        '''Provide a MagicMock standing in for HemingwayRecordStore.'''
        return MagicMock()

    @pytest.fixture
    def client(self, monkeypatch, mock_record_store):
        '''Create a Starlette TestClient with record_store stubbed.'''
        monkeypatch.setenv('DRY_RUN', '1')

        import agents.hemingway.api as api_mod
        monkeypatch.setattr(api_mod, 'record_store', mock_record_store)
        monkeypatch.setattr(api_mod, '_run_count', 0)
        monkeypatch.setattr(api_mod, '_total_docs_generated', 0)
        monkeypatch.setattr(api_mod, '_last_run_at', '')

        app = api_mod.create_app()

        from starlette.testclient import TestClient
        return TestClient(app)

    def test_search_api_endpoint(self, client, mock_record_store):
        '''POST /v1/docs/search returns ok with results and count.'''
        mock_record_store.search_records.return_value = [
            {
                'doc_id': 'test-1',
                'title': 'PSM2 Architecture',
                'doc_type': 'as_built',
                'project_key': 'STL',
                'created_at': '2026-03-30T10:00:00Z',
                'match_context': 'PSM2 Architecture',
            },
        ]

        resp = client.post('/v1/docs/search', json={
            'query': 'PSM2',
            'project_key': 'STL',
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['count'] == 1
        assert body['data']['query'] == 'PSM2'
        assert len(body['data']['results']) == 1

        # Verify the store was called with correct params
        mock_record_store.search_records.assert_called_once_with(
            query='PSM2',
            project_key='STL',
            doc_type=None,
            source_ref=None,
            published_only=False,
            confidence=None,
            limit=None,
        )

    def test_search_api_empty_body(self, client, mock_record_store):
        '''POST /v1/docs/search with empty body returns all records.'''
        mock_record_store.search_records.return_value = []

        resp = client.post('/v1/docs/search', json={})

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['count'] == 0
        assert body['data']['query'] == ''


# ===========================================================================
# C) Tool wrapper — search_hemingway_records()
# ===========================================================================

class TestSearchTool:
    '''Tests for the search_hemingway_records() tool function.'''

    def test_search_tool_returns_success(self, tmp_path, monkeypatch):
        '''search_hemingway_records() returns ToolResult with success status.'''
        rec = _make_record(doc_id='tool-1', title='PSM2 Architecture')
        store = _store_with_records(tmp_path, [rec])

        monkeypatch.setattr(
            'agents.hemingway.state.record_store.HemingwayRecordStore',
            lambda **kw: store,
        )

        from agents.hemingway.tools import search_hemingway_records
        from tools.base import ToolStatus

        result = search_hemingway_records(query='PSM2')

        assert result.is_success
        assert result.status == ToolStatus.SUCCESS
        assert isinstance(result.data, list)
        assert len(result.data) == 1
        assert result.metadata.get('count') == 1
        assert result.metadata.get('query') == 'PSM2'

    def test_search_tool_returns_empty_on_no_match(self, tmp_path, monkeypatch):
        '''search_hemingway_records() returns empty list when nothing matches.'''
        rec = _make_record(
            doc_id='tool-2', title='CN5000 Guide',
            content_markdown='# CN5000\nSwitch management...',
            summary_markdown='Summary of CN5000',
        )
        store = _store_with_records(tmp_path, [rec])

        monkeypatch.setattr(
            'agents.hemingway.state.record_store.HemingwayRecordStore',
            lambda **kw: store,
        )

        from agents.hemingway.tools import search_hemingway_records

        result = search_hemingway_records(query='nonexistent-xyz')

        assert result.is_success
        assert result.data == []
        assert result.metadata.get('count') == 0
