##########
# Module:      test_hemingway_confluence_publish_char.py
# Description: Characterization tests for Hemingway Confluence publish functionality.
#              Covers the POST /v1/docs/confluence/publish-page API endpoint,
#              the confluence-publish CLI subcommand, and the Shannon card builder.
# Author:      Cornelis Networks Engineering Tools
##########

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tools.base import ToolResult


# ---------------------------------------------------------------------------
# Helpers — card assertion utilities (mirrors test_hemingway_shannon_cards_char)
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(monkeypatch):
    '''
    Create a Starlette TestClient for the Hemingway API.

    The confluence tools are lazily imported inside the endpoint function,
    so we patch them on the tools.confluence_tools module which is where
    the endpoint's ``from tools.confluence_tools import ...`` resolves.
    '''
    # Ensure DRY_RUN defaults to '1' for safety
    monkeypatch.setenv('DRY_RUN', '1')

    import agents.hemingway.api as api_mod

    # Reset session counters for isolation
    monkeypatch.setattr(api_mod, '_run_count', 0)
    monkeypatch.setattr(api_mod, '_total_docs_generated', 0)
    monkeypatch.setattr(api_mod, '_last_run_at', '')

    app = api_mod.create_app()

    from starlette.testclient import TestClient
    return TestClient(app)


def _patch_confluence_tool(monkeypatch, tool_name, return_value):
    '''
    Patch a single confluence tool function on the tools.confluence_tools module.

    The API endpoint does ``from tools.confluence_tools import <fn>`` inside
    the request handler, so we must patch the attribute on the module itself.
    '''
    monkeypatch.setattr(f'tools.confluence_tools.{tool_name}', lambda **kw: return_value)


# ---------------------------------------------------------------------------
# A) API endpoint — POST /v1/docs/confluence/publish-page
# ---------------------------------------------------------------------------

class TestConfluencePublishAPI:
    '''Tests for POST /v1/docs/confluence/publish-page.'''

    # -- success paths -------------------------------------------------------

    def test_confluence_publish_create_success(self, client, monkeypatch):
        '''Create operation with markdown_content returns page metadata.'''
        mock_result = ToolResult.success({
            'page_id': '12345',
            'title': 'New Page',
            'link': 'https://wiki.example.com/pages/12345',
        })
        _patch_confluence_tool(monkeypatch, 'create_confluence_page', mock_result)
        # Also patch resolve_dry_run so it returns False for this test
        monkeypatch.setattr(
            'config.env_loader.resolve_dry_run', lambda v: False,
        )

        resp = client.post('/v1/docs/confluence/publish-page', json={
            'markdown_content': '# Hello\n\nWorld',
            'title': 'New Page',
            'operation': 'create',
            'space': 'ENG',
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['page_id'] == '12345'
        assert body['data']['title'] == 'New Page'
        assert body['data']['link'] == 'https://wiki.example.com/pages/12345'

    def test_confluence_publish_update_success(self, client, monkeypatch):
        '''Update operation with input_file and page_id_or_title succeeds.'''
        mock_result = ToolResult.success({
            'page_id': '67890',
            'title': 'Updated Page',
            'link': 'https://wiki.example.com/pages/67890',
        })
        _patch_confluence_tool(monkeypatch, 'update_confluence_page', mock_result)
        monkeypatch.setattr(
            'config.env_loader.resolve_dry_run', lambda v: False,
        )

        resp = client.post('/v1/docs/confluence/publish-page', json={
            'input_file': '/tmp/doc.md',
            'page_id_or_title': '67890',
            'operation': 'update',
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['page_id'] == '67890'

    def test_confluence_publish_append_success(self, client, monkeypatch):
        '''Append operation delegates to append_to_confluence_page.'''
        mock_result = ToolResult.success({
            'page_id': '11111',
            'title': 'Appended Page',
            'link': 'https://wiki.example.com/pages/11111',
        })
        _patch_confluence_tool(monkeypatch, 'append_to_confluence_page', mock_result)
        monkeypatch.setattr(
            'config.env_loader.resolve_dry_run', lambda v: False,
        )

        resp = client.post('/v1/docs/confluence/publish-page', json={
            'markdown_content': '## Appended section',
            'page_id_or_title': '11111',
            'operation': 'append',
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['page_id'] == '11111'

    def test_confluence_publish_section_success(self, client, monkeypatch):
        '''update_section operation requires heading and delegates correctly.'''
        mock_result = ToolResult.success({
            'page_id': '22222',
            'title': 'Section Page',
            'link': 'https://wiki.example.com/pages/22222',
        })
        _patch_confluence_tool(monkeypatch, 'update_confluence_section', mock_result)
        monkeypatch.setattr(
            'config.env_loader.resolve_dry_run', lambda v: False,
        )

        resp = client.post('/v1/docs/confluence/publish-page', json={
            'markdown_content': '## Updated content',
            'page_id_or_title': '22222',
            'heading': 'Architecture',
            'operation': 'update_section',
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['page_id'] == '22222'

    def test_confluence_publish_dry_run_returns_preview(self, client, monkeypatch):
        '''When dry_run=True, the tool is called with dry_run=True.'''
        captured_kwargs = {}

        def mock_create(**kwargs):
            captured_kwargs.update(kwargs)
            return ToolResult.success({
                'page_id': 'preview',
                'title': 'Preview Page',
                'link': '',
                'dry_run': True,
            })

        monkeypatch.setattr(
            'tools.confluence_tools.create_confluence_page', mock_create,
        )
        # resolve_dry_run returns True when body.dry_run is True
        monkeypatch.setattr(
            'config.env_loader.resolve_dry_run', lambda v: True,
        )

        resp = client.post('/v1/docs/confluence/publish-page', json={
            'markdown_content': '# Preview',
            'title': 'Preview Page',
            'operation': 'create',
            'dry_run': True,
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        # Verify the tool was called with dry_run=True
        assert captured_kwargs.get('dry_run') is True

    # -- validation errors ---------------------------------------------------

    def test_confluence_publish_missing_content_returns_400(self, client):
        '''No markdown_content or input_file → 400.'''
        resp = client.post('/v1/docs/confluence/publish-page', json={
            'title': 'No Content',
            'operation': 'create',
        })
        assert resp.status_code == 400
        assert 'markdown_content' in resp.json()['detail'].lower() or \
               'input_file' in resp.json()['detail'].lower()

    def test_confluence_publish_invalid_operation_returns_400(self, client):
        '''Invalid operation value → 400.'''
        resp = client.post('/v1/docs/confluence/publish-page', json={
            'markdown_content': '# Test',
            'operation': 'invalid',
        })
        assert resp.status_code == 400
        assert 'invalid' in resp.json()['detail'].lower()

    def test_confluence_publish_create_missing_title_returns_400(self, client):
        '''Create operation without title → 400.'''
        resp = client.post('/v1/docs/confluence/publish-page', json={
            'markdown_content': '# Test',
            'operation': 'create',
            # title is missing
        })
        assert resp.status_code == 400
        assert 'title' in resp.json()['detail'].lower()

    def test_confluence_publish_update_missing_page_returns_400(self, client):
        '''Update operation without page_id_or_title → 400.'''
        resp = client.post('/v1/docs/confluence/publish-page', json={
            'markdown_content': '# Test',
            'operation': 'update',
            # page_id_or_title is missing
        })
        assert resp.status_code == 400
        assert 'page_id_or_title' in resp.json()['detail'].lower()

    def test_confluence_publish_section_missing_heading_returns_400(self, client):
        '''update_section without heading → 400.'''
        resp = client.post('/v1/docs/confluence/publish-page', json={
            'markdown_content': '# Test',
            'page_id_or_title': '99999',
            'operation': 'update_section',
            # heading is missing
        })
        assert resp.status_code == 400
        assert 'heading' in resp.json()['detail'].lower()

    # -- tool failure --------------------------------------------------------

    def test_confluence_publish_tool_failure(self, client, monkeypatch):
        '''When the tool returns ToolResult.failure(), endpoint returns ok=False.'''
        mock_result = ToolResult.failure('Confluence API returned 403 Forbidden')
        _patch_confluence_tool(monkeypatch, 'create_confluence_page', mock_result)
        monkeypatch.setattr(
            'config.env_loader.resolve_dry_run', lambda v: False,
        )

        resp = client.post('/v1/docs/confluence/publish-page', json={
            'markdown_content': '# Fail',
            'title': 'Fail Page',
            'operation': 'create',
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is False
        assert '403' in body['error']


# ---------------------------------------------------------------------------
# B) CLI subcommand — confluence-publish
# ---------------------------------------------------------------------------

class TestConfluencePublishCLI:
    '''Tests for cmd_confluence_publish in agents/hemingway/cli.py.'''

    def test_cli_confluence_publish_create(self, monkeypatch, tmp_path):
        '''CLI create operation calls create_confluence_page and exits 0.'''
        # Create a temp markdown file for input
        md_file = tmp_path / 'test.md'
        md_file.write_text('# CLI Test\n\nContent here.')

        mock_result = ToolResult.success({
            'page_id': 'cli-001',
            'title': 'CLI Page',
            'link': 'https://wiki.example.com/pages/cli-001',
        })

        # Patch the tool at the module level where the CLI imports it
        monkeypatch.setattr(
            'tools.confluence_tools.create_confluence_page',
            lambda **kw: mock_result,
        )
        # Prevent dotenv from loading real .env
        monkeypatch.setattr('dotenv.load_dotenv', lambda *a, **kw: None)

        from agents.hemingway.cli import cmd_confluence_publish

        args = SimpleNamespace(
            input_file=str(md_file),
            title='CLI Page',
            operation='create',
            space='ENG',
            parent_id=None,
            page_id=None,
            heading=None,
            version_message=None,
            no_diagrams=False,
            execute=True,
            json=True,
            env=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_confluence_publish(args)
        assert exc_info.value.code == 0

    def test_cli_confluence_publish_dry_run(self, monkeypatch, tmp_path):
        '''CLI defaults to dry_run=True when --execute is not set.'''
        md_file = tmp_path / 'test.md'
        md_file.write_text('# Dry Run Test')

        captured_kwargs = {}

        def mock_create(**kwargs):
            captured_kwargs.update(kwargs)
            return ToolResult.success({
                'page_id': 'dry-001',
                'title': 'Dry Page',
                'link': '',
            })

        monkeypatch.setattr(
            'tools.confluence_tools.create_confluence_page', mock_create,
        )
        monkeypatch.setattr('dotenv.load_dotenv', lambda *a, **kw: None)

        from agents.hemingway.cli import cmd_confluence_publish

        args = SimpleNamespace(
            input_file=str(md_file),
            title='Dry Page',
            operation='create',
            space=None,
            parent_id=None,
            page_id=None,
            heading=None,
            version_message=None,
            no_diagrams=False,
            execute=False,   # dry-run (default)
            json=True,
            env=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_confluence_publish(args)
        assert exc_info.value.code == 0
        # Verify the tool was called with dry_run=True
        assert captured_kwargs.get('dry_run') is True


# ---------------------------------------------------------------------------
# C) Shannon card builder — build_hemingway_confluence_publish_card
# ---------------------------------------------------------------------------

class TestConfluencePublishCard:
    '''Tests for build_hemingway_confluence_publish_card in shannon/cards.py.'''

    def test_confluence_publish_card_success(self):
        '''Success data produces a valid card with page facts.'''
        from shannon.cards import build_hemingway_confluence_publish_card

        data = {
            'page_id': '12345',
            'title': 'Architecture Guide',
            'operation': 'create',
            'space': 'ENG',
            'link': 'https://wiki.example.com/pages/12345',
            'dry_run': False,
        }

        card = build_hemingway_confluence_publish_card(data)

        _card_schema_ok(card)

        # Title should NOT contain dry-run indicator
        texts = _body_texts(card)
        title_text = texts[0] if texts else ''
        assert 'Confluence Publication' in title_text
        assert 'Dry-Run' not in title_text

        # Facts
        fs = _find_fact_set(card)
        assert _fact_value(fs, 'Page ID') == '12345'
        assert _fact_value(fs, 'Title') == 'Architecture Guide'
        assert _fact_value(fs, 'Operation') == 'create'
        assert _fact_value(fs, 'Space') == 'ENG'
        assert _fact_value(fs, 'Link') == 'https://wiki.example.com/pages/12345'

        # Body should say publication complete
        body = '\n'.join(texts)
        assert 'Publication complete.' in body

    def test_confluence_publish_card_dry_run(self):
        '''Dry-run data shows preview indicator in title and body.'''
        from shannon.cards import build_hemingway_confluence_publish_card

        data = {
            'page_id': '99999',
            'title': 'Preview Doc',
            'operation': 'update',
            'space': 'DEV',
            'dry_run': True,
        }

        card = build_hemingway_confluence_publish_card(data)

        _card_schema_ok(card)

        texts = _body_texts(card)
        title_text = texts[0] if texts else ''
        assert 'Dry-Run Preview' in title_text

        body = '\n'.join(texts)
        assert 'Preview' in body or 'no changes made' in body.lower()

    def test_confluence_publish_card_empty_data(self):
        '''Empty dict produces a valid card without crashing.'''
        from shannon.cards import build_hemingway_confluence_publish_card

        card = build_hemingway_confluence_publish_card({})

        _card_schema_ok(card)

        # Should still have a title
        texts = _body_texts(card)
        assert len(texts) >= 1
        assert 'Confluence Publication' in texts[0]
