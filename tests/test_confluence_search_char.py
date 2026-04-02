##########
# Module:      test_confluence_search_char.py
# Description: Characterization tests for Confluence search capabilities.
#              Covers search_pages_fulltext(), search_pages_by_label() in
#              confluence_utils.py and their tool wrappers in tools/confluence_tools.py.
# Author:      Cornelis Networks Engineering Tools
##########

import json
import sys
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest

import confluence_utils


def _silent_output(_message: str = '') -> None:
    return None


def _patch_common(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(confluence_utils, 'output', _silent_output)


def _make_fake_confluence(monkeypatch: pytest.MonkeyPatch, response_payload: Dict[str, Any]):
    '''
    Build a fake ConfluenceConnection whose request() returns a fake response
    with the given JSON payload.  Patches get_connection and reset_connection.
    '''
    _patch_common(monkeypatch)

    fake_response = SimpleNamespace(
        status_code=200,
        text=json.dumps(response_payload),
    )
    fake_response.json = lambda: response_payload

    captured_requests: List[Dict[str, Any]] = []

    def _fake_request(method, path, **kwargs):
        captured_requests.append({
            'method': method,
            'path': path,
            'params': kwargs.get('params'),
        })
        return fake_response

    fake_conn = SimpleNamespace(
        base_url='https://cornelisnetworks.atlassian.net/wiki',
        site_url='https://cornelisnetworks.atlassian.net',
        request=_fake_request,
        session=MagicMock(),
    )

    monkeypatch.setattr(confluence_utils, 'get_connection', lambda: fake_conn)
    monkeypatch.setattr(confluence_utils, 'reset_connection', lambda: None)

    return fake_conn, captured_requests


def _search_result_payload(pages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    if pages is None:
        pages = [
            {
                'content': {
                    'id': '12345',
                    'title': 'PSM2 Architecture',
                    'space': {'key': 'ENG', 'name': 'Engineering'},
                    '_links': {'webui': '/wiki/spaces/ENG/pages/12345'},
                },
                'excerpt': 'The PSM2 hardware abstraction layer...',
            },
        ]
    return {'results': pages}


# ===========================================================================
# A) search_pages_fulltext()
# ===========================================================================

def test_search_fulltext_builds_correct_cql(monkeypatch: pytest.MonkeyPatch):
    _, captured = _make_fake_confluence(monkeypatch, _search_result_payload())

    confluence_utils.search_pages_fulltext(
        confluence_utils.get_connection(),
        query='PSM2 architecture',
    )

    assert len(captured) == 1
    cql = captured[0]['params']['cql']
    assert 'text ~' in cql
    assert 'PSM2 architecture' in cql


def test_search_fulltext_with_space_filter(monkeypatch: pytest.MonkeyPatch):
    _, captured = _make_fake_confluence(monkeypatch, _search_result_payload())

    # resolve_space_key returns the key as-is when it's not numeric
    monkeypatch.setattr(
        confluence_utils, 'resolve_space_key',
        lambda conn, space=None: space,
    )

    confluence_utils.search_pages_fulltext(
        confluence_utils.get_connection(),
        query='PSM2',
        space='ENG',
    )

    assert len(captured) == 1
    cql = captured[0]['params']['cql']
    assert 'space = "ENG"' in cql


def test_search_fulltext_returns_results(monkeypatch: pytest.MonkeyPatch):
    _make_fake_confluence(monkeypatch, _search_result_payload())

    pages = confluence_utils.search_pages_fulltext(
        confluence_utils.get_connection(),
        query='PSM2',
    )

    assert len(pages) == 1
    assert pages[0]['title'] == 'PSM2 Architecture'
    assert pages[0]['page_id'] == '12345'
    assert 'excerpt' in pages[0]


def test_search_fulltext_empty(monkeypatch: pytest.MonkeyPatch):
    _make_fake_confluence(monkeypatch, {'results': []})

    pages = confluence_utils.search_pages_fulltext(
        confluence_utils.get_connection(),
        query='nonexistent-xyz',
    )

    assert pages == []


# ===========================================================================
# B) search_pages_by_label()
# ===========================================================================

def test_search_by_label_builds_correct_cql(monkeypatch: pytest.MonkeyPatch):
    _, captured = _make_fake_confluence(monkeypatch, _search_result_payload())

    confluence_utils.search_pages_by_label(
        confluence_utils.get_connection(),
        label='architecture',
    )

    assert len(captured) == 1
    cql = captured[0]['params']['cql']
    assert 'label =' in cql
    assert 'architecture' in cql


def test_search_by_label_returns_results(monkeypatch: pytest.MonkeyPatch):
    _make_fake_confluence(monkeypatch, _search_result_payload())

    pages = confluence_utils.search_pages_by_label(
        confluence_utils.get_connection(),
        label='architecture',
    )

    assert len(pages) == 1
    assert pages[0]['title'] == 'PSM2 Architecture'
    assert pages[0]['page_id'] == '12345'


# ===========================================================================
# C) Tool wrappers — tools/confluence_tools.py
# ===========================================================================

def test_search_fulltext_tool(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    from tools.base import ToolStatus

    fake_pages = [
        {'page_id': '12345', 'title': 'PSM2 Architecture', 'link': 'http://example.com'},
    ]
    monkeypatch.setattr(
        'tools.confluence_tools._cu_search_pages_fulltext',
        lambda conn, query='', limit=25, space=None: fake_pages,
    )
    monkeypatch.setattr(
        'tools.confluence_tools.get_confluence',
        lambda: SimpleNamespace(),
    )

    from tools.confluence_tools import search_confluence_fulltext
    result = search_confluence_fulltext(query='PSM2')

    assert result.is_success
    assert result.status == ToolStatus.SUCCESS
    assert result.metadata.get('count') == 1


def test_search_by_label_tool(monkeypatch: pytest.MonkeyPatch):
    _patch_common(monkeypatch)
    from tools.base import ToolStatus

    fake_pages = [
        {'page_id': '12345', 'title': 'PSM2 Architecture', 'link': 'http://example.com'},
    ]
    monkeypatch.setattr(
        'tools.confluence_tools._cu_search_pages_by_label',
        lambda conn, label='', limit=25, space=None: fake_pages,
    )
    monkeypatch.setattr(
        'tools.confluence_tools.get_confluence',
        lambda: SimpleNamespace(),
    )

    from tools.confluence_tools import search_confluence_by_label
    result = search_confluence_by_label(label='architecture')

    assert result.is_success
    assert result.status == ToolStatus.SUCCESS
    assert result.metadata.get('count') == 1
