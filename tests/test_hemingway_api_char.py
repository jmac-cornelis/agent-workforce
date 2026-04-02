##########
# Module:      test_hemingway_api_char.py
# Description: Characterization tests for the Hemingway Documentation Agent REST API.
#              Covers health, status, record retrieval, documentation generation,
#              impact detection, and publication endpoints in agents/hemingway/api.py.
# Author:      Cornelis Networks Engineering Tools
##########

import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers — lightweight fake objects that mirror model .to_dict() contracts
# ---------------------------------------------------------------------------

def _fake_documentation_record(**overrides):
    '''Return a SimpleNamespace mimicking DocumentationRecord with to_dict().'''
    defaults = {
        'doc_id': 'rec-001',
        'title': 'Fake Doc',
        'doc_type': 'engineering_reference',
        'project_key': 'STL',
        'created_at': '2026-03-31T00:00:00+00:00',
        'request': {},
        'impact': {},
        'source_refs': [],
        'evidence_summary': {},
        'content_markdown': '# Fake',
        'summary_markdown': 'Summary text',
        'patches': [],
        'validation': {},
        'warnings': [],
        'confidence': 'high',
        'metadata': {},
        'publication_records': [],
    }
    defaults.update(overrides)
    rec = SimpleNamespace(**defaults)
    rec.to_dict = lambda: {k: v for k, v in defaults.items()}
    return rec


def _fake_review_session(**overrides):
    '''Return a SimpleNamespace mimicking ReviewSession with to_dict().'''
    defaults = {
        'session_id': 'sess-001',
        'items': [],
        'created_at': '2026-03-31T00:00:00+00:00',
        'summary': {'total': 0, 'pending': 0, 'approved': 0, 'rejected': 0, 'executed': 0},
    }
    defaults.update(overrides)
    sess = SimpleNamespace(**defaults)
    sess.to_dict = lambda: {k: v for k, v in defaults.items()}
    return sess


def _fake_impact_record(**overrides):
    '''Return a SimpleNamespace mimicking DocumentationImpactRecord with to_dict().'''
    defaults = {
        'impact_id': 'imp-001',
        'created_at': '2026-03-31T00:00:00+00:00',
        'title': 'Impact Title',
        'doc_type': 'engineering_reference',
        'affected_targets': [{'target': 'docs/arch.md'}],
        'reasons': ['source changed'],
        'source_refs': ['src/main.c'],
        'warnings': [],
        'blocking_issues': [],
        'confidence': 'medium',
    }
    defaults.update(overrides)
    imp = SimpleNamespace(**defaults)
    imp.to_dict = lambda: {k: v for k, v in defaults.items()}
    return imp


def _fake_publication_record(**overrides):
    '''Return a SimpleNamespace mimicking PublicationRecord with to_dict().'''
    defaults = {
        'publication_id': 'pub-001',
        'doc_id': 'rec-001',
        'patch_id': 'p-001',
        'title': 'Published Patch',
        'target_type': 'repo_markdown',
        'operation': 'create',
        'target_ref': 'docs/new.md',
        'status': 'published',
        'published_at': '2026-03-31T01:00:00+00:00',
        'result': {},
        'error': '',
    }
    defaults.update(overrides)
    pub = SimpleNamespace(**defaults)
    pub.to_dict = lambda: {k: v for k, v in defaults.items()}
    return pub


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_record_store():
    '''Provide a MagicMock standing in for HemingwayRecordStore.'''
    return MagicMock()


@pytest.fixture
def client(monkeypatch, mock_record_store):
    '''
    Create a Starlette TestClient with record_store and agent stubbed out.

    We monkeypatch the module-level record_store in agents.hemingway.api so
    every endpoint uses our mock.  DRY_RUN defaults to '1' for safety.
    '''
    # Ensure DRY_RUN defaults to '1' unless a test overrides it
    monkeypatch.setenv('DRY_RUN', '1')

    # Import after env is set so load_env() picks up our value
    import agents.hemingway.api as api_mod
    monkeypatch.setattr(api_mod, 'record_store', mock_record_store)

    # Reset session counters so tests are isolated
    monkeypatch.setattr(api_mod, '_run_count', 0)
    monkeypatch.setattr(api_mod, '_total_docs_generated', 0)
    monkeypatch.setattr(api_mod, '_last_run_at', '')

    app = api_mod.create_app()

    from starlette.testclient import TestClient
    return TestClient(app)


# ---------------------------------------------------------------------------
# A) Health endpoint
# ---------------------------------------------------------------------------

class TestHealth:
    '''Tests for GET /v1/health.'''

    def test_health_returns_ok(self, client):
        '''Health endpoint returns service name and ok flag.'''
        resp = client.get('/v1/health')
        assert resp.status_code == 200
        body = resp.json()
        assert body['service'] == 'hemingway'
        assert body['ok'] is True


# ---------------------------------------------------------------------------
# B) Status endpoints
# ---------------------------------------------------------------------------

class TestStatus:
    '''Tests for the /v1/status/* family.'''

    def test_status_stats(self, client, mock_record_store):
        '''Stats endpoint returns record counts and doc-type breakdown.'''
        mock_record_store.list_records.return_value = [
            {'doc_type': 'engineering_reference'},
            {'doc_type': 'engineering_reference'},
            {'doc_type': 'how_to'},
        ]
        resp = client.get('/v1/status/stats')
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        data = body['data']
        assert data['records_count'] == 3
        assert data['doc_types']['engineering_reference'] == 2
        assert data['doc_types']['how_to'] == 1

    def test_status_load(self, client):
        '''Load endpoint returns idle state and session counters.'''
        resp = client.get('/v1/status/load')
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['state'] == 'idle'
        assert body['data']['runs_this_session'] == 0

    def test_status_work_summary(self, client, mock_record_store):
        '''Work-summary endpoint returns docs_today count.'''
        mock_record_store.list_records.return_value = []
        resp = client.get('/v1/status/work-summary')
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert 'docs_today' in body['data']

    def test_status_tokens(self, client):
        '''Tokens endpoint returns placeholder token info.'''
        resp = client.get('/v1/status/tokens')
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['llm_enabled'] is True

    def test_status_decisions(self, client, mock_record_store):
        '''Decisions endpoint returns list of decision summaries.'''
        mock_record_store.list_records.return_value = [
            {
                'doc_id': 'rec-001',
                'title': 'Test Doc',
                'doc_type': 'how_to',
                'project_key': 'STL',
                'created_at': '2026-03-31T00:00:00+00:00',
                'patch_count': 2,
                'warning_count': 1,
            },
        ]
        resp = client.get('/v1/status/decisions', params={'limit': 5})
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert len(body['data']) == 1
        assert body['data'][0]['record_id'] == 'rec-001'


# ---------------------------------------------------------------------------
# C) Record retrieval endpoints
# ---------------------------------------------------------------------------

class TestRecordRetrieval:
    '''Tests for GET /v1/docs/records and GET /v1/docs/record/{doc_id}.'''

    def test_list_records(self, client, mock_record_store):
        '''List records returns ok with data array.'''
        mock_record_store.list_records.return_value = [
            {'doc_id': 'a', 'title': 'Alpha'},
            {'doc_id': 'b', 'title': 'Beta'},
        ]
        resp = client.get('/v1/docs/records', params={'limit': 10})
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert len(body['data']) == 2
        mock_record_store.list_records.assert_called_once_with(
            doc_type=None, limit=10,
        )

    def test_get_record_found(self, client, mock_record_store):
        '''Get record by ID returns the stored record envelope.'''
        mock_record_store.get_record.return_value = {
            'record': {'doc_id': 'rec-001', 'title': 'Found'},
            'summary_markdown': '# Found',
            'summary': {},
        }
        resp = client.get('/v1/docs/record/rec-001')
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['record']['doc_id'] == 'rec-001'

    def test_get_record_not_found(self, client, mock_record_store):
        '''Get record returns 404 when doc_id does not exist.'''
        mock_record_store.get_record.return_value = None
        resp = client.get('/v1/docs/record/nonexistent')
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# D) POST /v1/docs/generate
# ---------------------------------------------------------------------------

class TestDocsGenerate:
    '''Tests for POST /v1/docs/generate.'''

    def test_generate_dry_run(self, client):
        '''Dry-run returns preview without invoking agent.'''
        resp = client.post('/v1/docs/generate', json={
            'doc_title': 'Test Doc',
            'doc_type': 'how_to',
            'dry_run': True,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        data = body['data']
        assert data['dry_run'] is True
        assert 'request' in data
        assert data['doc_type'] == 'how_to'

    def test_generate_execute(self, client, monkeypatch, mock_record_store):
        '''Execute path calls agent.plan_documentation and persists record.'''
        fake_record = _fake_documentation_record()
        fake_session = _fake_review_session()

        mock_agent = MagicMock()
        mock_agent.plan_documentation.return_value = (fake_record, fake_session)

        # Patch the agent constructor to return our mock
        monkeypatch.setattr(
            'agents.hemingway.api.HemingwayDocumentationAgent',
            lambda **kwargs: mock_agent,
        )

        mock_record_store.save_record.return_value = {'doc_id': 'rec-001', 'stored': True}

        resp = client.post('/v1/docs/generate', json={
            'doc_title': 'Execute Doc',
            'doc_type': 'engineering_reference',
            'dry_run': False,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        data = body['data']
        assert data['record']['doc_id'] == 'rec-001'
        assert 'review_session' in data
        assert data['stored'] is not None

    def test_generate_agent_error(self, client, monkeypatch):
        '''When agent raises, endpoint returns ok=False with error message.'''
        mock_agent = MagicMock()
        mock_agent.plan_documentation.side_effect = RuntimeError('LLM unavailable')

        monkeypatch.setattr(
            'agents.hemingway.api.HemingwayDocumentationAgent',
            lambda **kwargs: mock_agent,
        )

        resp = client.post('/v1/docs/generate', json={
            'doc_title': 'Failing Doc',
            'dry_run': False,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is False
        assert 'LLM unavailable' in body['error']


# ---------------------------------------------------------------------------
# E) POST /v1/docs/impact
# ---------------------------------------------------------------------------

class TestDocsImpact:
    '''Tests for POST /v1/docs/impact.'''

    def test_impact_success(self, client, monkeypatch):
        '''Impact detection returns impact record data.'''
        fake_impact = _fake_impact_record()

        mock_agent = MagicMock()
        mock_agent.detect_documentation_impact.return_value = fake_impact

        monkeypatch.setattr(
            'agents.hemingway.api.HemingwayDocumentationAgent',
            lambda **kwargs: mock_agent,
        )

        resp = client.post('/v1/docs/impact', json={
            'doc_title': 'Impact Test',
            'doc_type': 'engineering_reference',
            'source_paths': ['src/main.c'],
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        assert body['data']['impact_id'] == 'imp-001'
        assert len(body['data']['affected_targets']) == 1


# ---------------------------------------------------------------------------
# F) POST /v1/docs/publish
# ---------------------------------------------------------------------------

class TestDocsPublish:
    '''Tests for POST /v1/docs/publish.'''

    def test_publish_dry_run(self, client, mock_record_store):
        '''Dry-run publish returns preview with patch list.'''
        mock_record_store.get_record.return_value = {
            'record': {
                'doc_id': 'rec-001',
                'title': 'Pub Doc',
                'patches': [
                    {
                        'patch_id': 'p-001',
                        'target_type': 'repo_markdown',
                        'operation': 'create',
                        'target_ref': 'docs/new.md',
                    },
                ],
            },
            'summary_markdown': '',
            'summary': {},
        }

        resp = client.post('/v1/docs/publish', json={
            'doc_id': 'rec-001',
            'dry_run': True,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        data = body['data']
        assert data['dry_run'] is True
        assert data['patch_count'] == 1
        assert data['patches'][0]['patch_id'] == 'p-001'

    def test_publish_not_found(self, client, mock_record_store):
        '''Publish returns 404 when doc_id does not exist.'''
        mock_record_store.get_record.return_value = None

        resp = client.post('/v1/docs/publish', json={
            'doc_id': 'nonexistent',
            'dry_run': True,
        })
        assert resp.status_code == 404

    def test_publish_execute(self, client, monkeypatch, mock_record_store):
        '''Execute publish calls agent.publish_approved and records publications.'''
        mock_record_store.get_record.return_value = {
            'record': {
                'doc_id': 'rec-001',
                'title': 'Pub Doc',
                'doc_type': 'engineering_reference',
                'project_key': 'STL',
                'created_at': '2026-03-31T00:00:00+00:00',
                'request': {},
                'impact': {},
                'source_refs': [],
                'evidence_summary': {},
                'content_markdown': '',
                'summary_markdown': '',
                'patches': [],
                'validation': {},
                'warnings': [],
                'confidence': 'medium',
                'metadata': {},
            },
            'summary_markdown': '',
            'summary': {},
        }

        fake_pub = _fake_publication_record()
        mock_agent = MagicMock()
        mock_agent.create_review_session.return_value = MagicMock()
        mock_agent.publish_approved.return_value = [fake_pub]

        monkeypatch.setattr(
            'agents.hemingway.api.HemingwayDocumentationAgent',
            lambda **kwargs: mock_agent,
        )
        mock_record_store.record_publications.return_value = None

        resp = client.post('/v1/docs/publish', json={
            'doc_id': 'rec-001',
            'dry_run': False,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body['ok'] is True
        data = body['data']
        assert data['doc_id'] == 'rec-001'
        assert data['publication_count'] == 1
        assert data['publications'][0]['publication_id'] == 'pub-001'
