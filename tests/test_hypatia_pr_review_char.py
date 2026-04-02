##########
# Module:      test_hypatia_pr_review_char.py
# Description: Characterization tests for the Hypatia POST /v1/docs/pr-review endpoint.
#              Covers input validation, dry-run, doc-relevant filtering, agent run,
#              batch commit, and record persistence. Updated for async job pattern.
# Author:      Cornelis Networks Engineering Tools
##########

import sys
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_github_utils(monkeypatch):
    mock_mod = MagicMock()
    monkeypatch.setitem(sys.modules, 'github_utils', mock_mod)
    return mock_mod


@pytest.fixture
def mock_agent(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(
        'agents.hypatia.agent.HypatiaDocumentationAgent', mock_cls,
    )
    return mock_cls


@pytest.fixture
def mock_record_store(monkeypatch):
    mock_store = MagicMock()
    mock_store.list_records.return_value = []
    mock_store.get_record.return_value = None
    monkeypatch.setattr(
        'agents.hypatia.state.record_store.HypatiaRecordStore',
        lambda: mock_store,
    )
    return mock_store


@pytest.fixture
def client(mock_github_utils, monkeypatch):
    monkeypatch.setenv('DRY_RUN', 'false')
    # Ensure fresh import with mocked github_utils
    for mod_name in list(sys.modules):
        if mod_name.startswith('agents.hypatia.api'):
            del sys.modules[mod_name]

    from agents.hypatia.api import create_app
    from fastapi.testclient import TestClient

    app = create_app()
    return TestClient(app)


def _submit_and_poll(client, payload, max_wait=5.0):
    '''Submit a pr-review job and poll until completion.'''
    resp = client.post('/v1/docs/pr-review', json=payload)
    assert resp.status_code == 200
    submit_body = resp.json()
    assert submit_body.get('ok') is True
    job_id = submit_body.get('job_id')
    assert job_id

    poll_url = f'/v1/docs/pr-review/{job_id}'
    deadline = time.time() + max_wait
    while time.time() < deadline:
        poll_resp = client.get(poll_url)
        assert poll_resp.status_code == 200
        poll_body = poll_resp.json()
        if poll_body.get('status') in ('completed', 'failed'):
            return poll_body
        time.sleep(0.05)

    # Final attempt
    poll_resp = client.get(poll_url)
    return poll_resp.json()


def _make_changed_files(*filenames):
    '''Return a list of filename strings.

    The pr-review endpoint passes each element to _is_doc_relevant() which
    expects a plain string (filename), so the mock must match that contract.
    '''
    return list(filenames)


class TestPRReviewValidation:

    def test_pr_review_validates_repo_format(self, client, mock_github_utils):
        body = _submit_and_poll(
            client,
            {'repo': 'no-slash', 'pr_number': 1},
        )
        assert body['ok'] is False
        assert 'owner/repo' in body.get('error', '')

    def test_pr_review_validates_pr_number(self, client, mock_github_utils):
        body = _submit_and_poll(
            client,
            {'repo': 'org/repo', 'pr_number': 0},
        )
        assert body['ok'] is False
        assert 'positive' in body.get('error', '')


class TestPRReviewDryRun:

    def test_pr_review_dry_run_returns_preview(self, client, mock_github_utils, monkeypatch):
        monkeypatch.setenv('DRY_RUN', 'true')
        # Re-import to pick up DRY_RUN=true
        for mod_name in list(sys.modules):
            if mod_name.startswith('agents.hypatia.api'):
                del sys.modules[mod_name]
        from agents.hypatia.api import create_app
        from fastapi.testclient import TestClient
        app = create_app()
        dry_client = TestClient(app)

        mock_github_utils.get_pr_changed_files.return_value = _make_changed_files(
            'src/main.py', 'docs/guide.md',
        )

        body = _submit_and_poll(
            dry_client,
            {'repo': 'org/repo', 'pr_number': 5, 'dry_run': True},
        )

        assert body['ok'] is True
        data = body['data']
        assert data['dry_run'] is True
        assert data['files_committed'] is False
        assert 'files_planned' in data
        mock_github_utils.batch_commit_files.assert_not_called()


class TestPRReviewFiltering:

    def test_pr_review_no_relevant_files(self, client, mock_github_utils):
        mock_github_utils.get_pr_changed_files.return_value = _make_changed_files(
            'build/output.o', 'dist/app.bin', 'image.png',
        )

        body = _submit_and_poll(
            client,
            {'repo': 'org/repo', 'pr_number': 3},
        )

        assert body['ok'] is True
        data = body['data']
        assert data['files_generated'] == []
        assert 'No doc-relevant' in data['impact_summary']


class TestPRReviewGitHubErrors:

    def test_pr_review_github_unavailable(self, monkeypatch):
        monkeypatch.setenv('DRY_RUN', 'false')
        monkeypatch.delitem(sys.modules, 'github_utils', raising=False)
        monkeypatch.setattr(
            'builtins.__import__',
            _make_import_blocker('github_utils'),
        )

        for mod_name in list(sys.modules):
            if mod_name.startswith('agents.hypatia.api'):
                del sys.modules[mod_name]

        from agents.hypatia.api import create_app
        from fastapi.testclient import TestClient
        app = create_app()
        err_client = TestClient(app)

        body = _submit_and_poll(
            err_client,
            {'repo': 'org/repo', 'pr_number': 1},
        )

        assert body['ok'] is False
        assert 'not available' in body.get('error', '')

    def test_pr_review_github_api_error(self, client, mock_github_utils):
        mock_github_utils.get_pr_changed_files.side_effect = RuntimeError(
            'API rate limit exceeded'
        )

        body = _submit_and_poll(
            client,
            {'repo': 'org/repo', 'pr_number': 10},
        )

        assert body['ok'] is False
        assert 'GitHub API error' in body.get('error', '')


class TestPRReviewFullFlow:

    def _setup_full_flow(self, mock_github_utils):
        mock_github_utils.get_pr_changed_files.return_value = _make_changed_files(
            'src/main.py',
        )
        mock_github_utils.get_pull_request.return_value = {
            'head_branch': 'feature-branch',
            'number': 42,
        }
        mock_github_utils.batch_commit_files.return_value = {
            'commit_sha': 'commit_sha_abc',
            'file_count': 1,
        }

    def _make_agent_result(self, target_file='docs/main.md'):
        return SimpleNamespace(
            success=True,
            error=None,
            metadata={
                'documentation_record': {
                    'doc_id': 'hyp_001',
                    'title': 'Main Documentation',
                    'doc_type': 'as_built',
                    'project_key': '',
                    'created_at': '2026-04-01T00:00:00Z',
                    'request': {},
                    'impact': {},
                    'source_refs': [],
                    'evidence_summary': {},
                    'content_markdown': '# Main\n\nGenerated doc.',
                    'summary_markdown': 'Auto-generated.',
                    'validation': {},
                    'warnings': [],
                    'confidence': 'medium',
                    'metadata': {},
                    'patches': [
                        {
                            'target_type': 'repo_markdown',
                            'target_ref': target_file,
                            'content_markdown': '# Main\n\nGenerated doc.',
                            'operation': 'create',
                        },
                    ],
                },
            },
        )

    def test_pr_review_returns_200_with_impact(self, client, mock_github_utils, monkeypatch):
        self._setup_full_flow(mock_github_utils)

        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = self._make_agent_result()
        monkeypatch.setattr(
            'agents.hypatia.api.HypatiaDocumentationAgent',
            lambda **kw: mock_agent_instance,
        )

        body = _submit_and_poll(
            client,
            {'repo': 'org/repo', 'pr_number': 42},
        )

        assert body['ok'] is True
        data = body['data']
        assert len(data['files_generated']) > 0
        assert data['files_committed'] is True

    def test_pr_review_commits_to_branch(self, client, mock_github_utils, monkeypatch):
        self._setup_full_flow(mock_github_utils)

        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = self._make_agent_result()
        monkeypatch.setattr(
            'agents.hypatia.api.HypatiaDocumentationAgent',
            lambda **kw: mock_agent_instance,
        )

        _submit_and_poll(
            client,
            {'repo': 'org/repo', 'pr_number': 42},
        )

        mock_github_utils.batch_commit_files.assert_called_once()
        call_args = mock_github_utils.batch_commit_files.call_args
        assert call_args[0][0] == 'org/repo'  # repo_name
        assert call_args[0][3] == 'feature-branch'  # branch

    def test_pr_review_skip_ci_in_commit_message(self, client, mock_github_utils, monkeypatch):
        self._setup_full_flow(mock_github_utils)

        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = self._make_agent_result()
        monkeypatch.setattr(
            'agents.hypatia.api.HypatiaDocumentationAgent',
            lambda **kw: mock_agent_instance,
        )

        _submit_and_poll(
            client,
            {'repo': 'org/repo', 'pr_number': 42},
        )

        call_args = mock_github_utils.batch_commit_files.call_args
        commit_message = call_args[0][2]
        assert '[skip ci]' in commit_message

    def test_pr_review_saves_record(self, client, mock_github_utils, monkeypatch):
        self._setup_full_flow(mock_github_utils)

        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = self._make_agent_result()
        monkeypatch.setattr(
            'agents.hypatia.api.HypatiaDocumentationAgent',
            lambda **kw: mock_agent_instance,
        )

        mock_store = MagicMock()
        mock_store.list_records.return_value = []
        mock_store.get_record.return_value = None
        monkeypatch.setattr(
            'agents.hypatia.api.record_store', mock_store,
        )

        body = _submit_and_poll(
            client,
            {'repo': 'org/repo', 'pr_number': 42},
        )

        assert body['ok'] is True
        mock_store.save_record.assert_called_once()
        saved_record = mock_store.save_record.call_args[0][0]
        assert saved_record.doc_id == 'hyp_001'


def _make_import_blocker(blocked_module):
    original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

    def _blocked_import(name, *args, **kwargs):
        if name == blocked_module:
            raise ImportError(f'{blocked_module} is not available')
        return original_import(name, *args, **kwargs)

    return _blocked_import
