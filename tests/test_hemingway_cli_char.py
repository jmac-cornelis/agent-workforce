##########################################################################################
#
# Module: tests/test_hemingway_cli_char.py
#
# Description: Characterization tests for agents/hemingway/cli.py.
#              Covers all three subcommands (cmd_generate, cmd_list, cmd_get)
#              with monkeypatched agent and store stubs — no live API calls.
#
# Author: Cornelis Networks
#
##########################################################################################

import json
from types import SimpleNamespace

import pytest

from agents.hemingway.models import (
    DocumentationPatch,
    DocumentationRecord,
    PublicationRecord,
)
from agents.review_agent import ApprovalStatus, ReviewItem, ReviewSession


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_record(doc_id='doc-cli-001', title='CLI Test Doc', execute=False):
    '''Build a minimal DocumentationRecord for CLI tests.'''
    return DocumentationRecord(
        doc_id=doc_id,
        title=title,
        doc_type='engineering_reference',
        project_key='STL',
        summary_markdown='# CLI Test\n\nSummary text.',
        content_markdown='## Key Facts\n\n- Item one\n',
        validation={'valid': True},
        warnings=['minor style note'],
        patches=[
            DocumentationPatch(
                patch_id='P001',
                target_type='repo_markdown',
                operation='create',
                title=title,
                target_ref='docs/cli-test.md',
                content_markdown='# Patch content\n',
            ),
        ],
    )


def _make_review_session(doc_id='doc-cli-001', title='CLI Test Doc'):
    '''Build a minimal ReviewSession matching the record.'''
    return ReviewSession(
        session_id=doc_id,
        created_at='2026-03-30T12:00:00+00:00',
        items=[
            ReviewItem(
                id='P001',
                item_type='document',
                action='write',
                data={
                    'doc_id': doc_id,
                    'patch_id': 'P001',
                    'title': title,
                    'file_path': 'docs/cli-test.md',
                    'content': '# Patch content\n',
                },
            ),
        ],
    )


def _base_generate_args(tmp_path, **overrides):
    '''Return a SimpleNamespace mimicking argparse output for cmd_generate.'''
    defaults = dict(
        project='STL',
        doc_title='CLI Test Doc',
        doc_type='engineering_reference',
        doc_summary='Test summary',
        docs=[],
        evidence=[],
        target_file=str(tmp_path / 'docs' / 'cli-test.md'),
        confluence_title=None,
        confluence_page=None,
        confluence_space=None,
        confluence_parent_id=None,
        version_message=None,
        doc_validation='default',
        output=str(tmp_path / 'cli_record.json'),
        execute=False,
        env=None,
        json=False,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Fake agent / store classes
# ---------------------------------------------------------------------------

class _FakeReviewAgent:
    def approve_all(self, session):
        for item in session.items:
            item.status = ApprovalStatus.APPROVED
        return len(session.items)


class _FakeHemingwayAgent:
    '''Stub that returns a canned record + review session.'''

    def __init__(self, project_key=None, **kwargs):
        self.project_key = project_key
        self.review_agent = _FakeReviewAgent()

    def _normalize_request(self, request):
        return request

    def plan_documentation(self, request):
        record = _make_record()
        session = _make_review_session()
        return record, session

    def publish_approved(self, session):
        return [
            PublicationRecord(
                doc_id='doc-cli-001',
                patch_id='P001',
                title='CLI Test Doc',
                target_type='repo_markdown',
                operation='write',
                target_ref='docs/cli-test.md',
                status='published',
                published_at='2026-03-30T12:05:00+00:00',
                result={'path': 'docs/cli-test.md'},
            ),
        ]


# ---------------------------------------------------------------------------
# cmd_generate tests
# ---------------------------------------------------------------------------

class TestCmdGenerate:
    '''Tests for the generate subcommand.'''

    def _patch_agent(self, monkeypatch):
        '''Monkeypatch HemingwayDocumentationAgent in the cli module's import target.'''
        from agents.hemingway import agent as hemingway_agent_module
        monkeypatch.setattr(
            hemingway_agent_module,
            'HemingwayDocumentationAgent',
            _FakeHemingwayAgent,
        )

    def test_generate_dry_run_writes_artifacts(self, monkeypatch, tmp_path):
        '''Dry-run generate writes record JSON, markdown, and review files.'''
        self._patch_agent(monkeypatch)
        monkeypatch.setenv('HEMINGWAY_DOC_DIR', str(tmp_path / 'store'))

        from agents.hemingway.cli import cmd_generate

        args = _base_generate_args(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            cmd_generate(args)

        assert exc_info.value.code == 0

        output_path = tmp_path / 'cli_record.json'
        assert output_path.exists()
        exported = json.loads(output_path.read_text(encoding='utf-8'))
        assert exported['doc_id'] == 'doc-cli-001'
        assert (tmp_path / 'cli_record.md').exists()
        assert (tmp_path / 'cli_record_review.json').exists()
        assert (tmp_path / 'cli_record_patches').is_dir()
        assert (tmp_path / 'store' / 'doc-cli-001' / 'record.json').exists()

    def test_generate_execute_publishes_and_writes_publications(
        self, monkeypatch, tmp_path,
    ):
        '''--execute path approves, publishes, and writes publications file.'''
        self._patch_agent(monkeypatch)
        monkeypatch.setenv('HEMINGWAY_DOC_DIR', str(tmp_path / 'store'))

        from agents.hemingway.cli import cmd_generate

        args = _base_generate_args(tmp_path, execute=True)

        with pytest.raises(SystemExit) as exc_info:
            cmd_generate(args)

        assert exc_info.value.code == 0

        pub_path = tmp_path / 'cli_record_publications.json'
        assert pub_path.exists()
        publications = json.loads(pub_path.read_text(encoding='utf-8'))
        assert len(publications) == 1
        assert publications[0]['status'] == 'published'

    def test_generate_json_output(self, monkeypatch, tmp_path, capsys):
        '''--json flag produces structured JSON summary to stdout.'''
        self._patch_agent(monkeypatch)
        monkeypatch.setenv('HEMINGWAY_DOC_DIR', str(tmp_path / 'store'))

        from agents.hemingway.cli import cmd_generate

        args = _base_generate_args(tmp_path, json=True)

        with pytest.raises(SystemExit) as exc_info:
            cmd_generate(args)

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload['doc_id'] == 'doc-cli-001'
        assert payload['title'] == 'CLI Test Doc'
        assert payload['patch_count'] == 1
        assert payload['warning_count'] == 1
        assert payload['validation_valid'] is True
        assert payload['execute'] is False
        assert isinstance(payload['created_files'], list)
        assert len(payload['created_files']) >= 5

    def test_generate_execute_blocked_by_invalid_validation(
        self, monkeypatch, tmp_path,
    ):
        '''--execute with invalid validation exits 1 and refuses to publish.'''
        from agents.hemingway import agent as hemingway_agent_module

        class _BlockedAgent(_FakeHemingwayAgent):
            def plan_documentation(self, request):
                record = _make_record()
                record.validation = {'valid': False, 'blocking_issues': ['missing refs']}
                session = _make_review_session()
                return record, session

        monkeypatch.setattr(
            hemingway_agent_module,
            'HemingwayDocumentationAgent',
            _BlockedAgent,
        )
        monkeypatch.setenv('HEMINGWAY_DOC_DIR', str(tmp_path / 'store'))

        from agents.hemingway.cli import cmd_generate

        args = _base_generate_args(tmp_path, execute=True)

        with pytest.raises(SystemExit) as exc_info:
            cmd_generate(args)

        assert exc_info.value.code == 1
        assert not (tmp_path / 'cli_record_publications.json').exists()

    def test_generate_execute_blocked_json_output(
        self, monkeypatch, tmp_path, capsys,
    ):
        '''--execute + --json with invalid validation emits error JSON and exits 1.'''
        from agents.hemingway import agent as hemingway_agent_module

        class _BlockedAgent(_FakeHemingwayAgent):
            def plan_documentation(self, request):
                record = _make_record()
                record.validation = {'valid': False, 'blocking_issues': ['missing refs']}
                session = _make_review_session()
                return record, session

        monkeypatch.setattr(
            hemingway_agent_module,
            'HemingwayDocumentationAgent',
            _BlockedAgent,
        )
        monkeypatch.setenv('HEMINGWAY_DOC_DIR', str(tmp_path / 'store'))

        from agents.hemingway.cli import cmd_generate

        args = _base_generate_args(tmp_path, execute=True, json=True)

        with pytest.raises(SystemExit) as exc_info:
            cmd_generate(args)

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert 'error' in payload
        assert 'blocking validation' in payload['error'].lower()


# ---------------------------------------------------------------------------
# cmd_list tests
# ---------------------------------------------------------------------------

class TestCmdList:
    '''Tests for the list subcommand.'''

    def test_list_returns_records(self, monkeypatch, capsys):
        '''cmd_list prints tabular output for stored records.'''
        from agents.hemingway.state import record_store as rs_module

        class _FakeStore:
            def __init__(self, **kwargs):
                pass

            def list_records(self, **kwargs):
                return [
                    {
                        'doc_id': 'doc-001',
                        'doc_type': 'engineering_reference',
                        'title': 'First Guide',
                        'project_key': 'STL',
                        'created_at': '2026-03-15T12:00:00+00:00',
                    },
                    {
                        'doc_id': 'doc-002',
                        'doc_type': 'how_to',
                        'title': 'Second Guide',
                        'project_key': 'STL',
                        'created_at': '2026-03-16T12:00:00+00:00',
                    },
                ]

        monkeypatch.setattr(rs_module, 'HemingwayRecordStore', _FakeStore)

        from agents.hemingway.cli import cmd_list

        args = SimpleNamespace(project=None, limit=20, json=False)

        with pytest.raises(SystemExit) as exc_info:
            cmd_list(args)

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert 'doc-001' in captured.out
        assert 'doc-002' in captured.out
        assert 'First Guide' in captured.out

    def test_list_json_output(self, monkeypatch, capsys):
        '''cmd_list --json emits structured JSON with count.'''
        from agents.hemingway.state import record_store as rs_module

        class _FakeStore:
            def __init__(self, **kwargs):
                pass

            def list_records(self, **kwargs):
                return [
                    {
                        'doc_id': 'doc-001',
                        'doc_type': 'engineering_reference',
                        'title': 'First Guide',
                        'project_key': 'STL',
                        'created_at': '2026-03-15T12:00:00+00:00',
                    },
                ]

        monkeypatch.setattr(rs_module, 'HemingwayRecordStore', _FakeStore)

        from agents.hemingway.cli import cmd_list

        args = SimpleNamespace(project=None, limit=20, json=True)

        with pytest.raises(SystemExit) as exc_info:
            cmd_list(args)

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload['count'] == 1
        assert payload['records'][0]['doc_id'] == 'doc-001'

    def test_list_empty_records(self, monkeypatch, capsys):
        '''cmd_list with no stored records prints informational message.'''
        from agents.hemingway.state import record_store as rs_module

        class _FakeStore:
            def __init__(self, **kwargs):
                pass

            def list_records(self, **kwargs):
                return []

        monkeypatch.setattr(rs_module, 'HemingwayRecordStore', _FakeStore)

        from agents.hemingway.cli import cmd_list

        args = SimpleNamespace(project=None, limit=20, json=False)

        with pytest.raises(SystemExit) as exc_info:
            cmd_list(args)

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert 'No stored documentation records found' in captured.out

    def test_list_project_filter(self, monkeypatch, capsys):
        '''cmd_list --project filters records by project_key.'''
        from agents.hemingway.state import record_store as rs_module

        class _FakeStore:
            def __init__(self, **kwargs):
                pass

            def list_records(self, **kwargs):
                return [
                    {
                        'doc_id': 'doc-001',
                        'doc_type': 'engineering_reference',
                        'title': 'STL Guide',
                        'project_key': 'STL',
                        'created_at': '2026-03-15T12:00:00+00:00',
                    },
                    {
                        'doc_id': 'doc-002',
                        'doc_type': 'how_to',
                        'title': 'OPA Guide',
                        'project_key': 'OPA',
                        'created_at': '2026-03-16T12:00:00+00:00',
                    },
                ]

        monkeypatch.setattr(rs_module, 'HemingwayRecordStore', _FakeStore)

        from agents.hemingway.cli import cmd_list

        args = SimpleNamespace(project='STL', limit=20, json=True)

        with pytest.raises(SystemExit) as exc_info:
            cmd_list(args)

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload['count'] == 1
        assert payload['records'][0]['doc_id'] == 'doc-001'


# ---------------------------------------------------------------------------
# cmd_get tests
# ---------------------------------------------------------------------------

class TestCmdGet:
    '''Tests for the get subcommand.'''

    def test_get_returns_record(self, monkeypatch, capsys):
        '''cmd_get prints summary markdown for an existing record.'''
        from agents.hemingway.state import record_store as rs_module

        class _FakeStore:
            def __init__(self, **kwargs):
                pass

            def get_record(self, doc_id):
                return {
                    'record': {
                        'doc_id': doc_id,
                        'title': 'Test Doc',
                        'doc_type': 'engineering_reference',
                        'project_key': 'STL',
                    },
                    'summary_markdown': '# Test Doc\n\nSummary content.',
                    'summary': {'doc_id': doc_id},
                }

        monkeypatch.setattr(rs_module, 'HemingwayRecordStore', _FakeStore)

        from agents.hemingway.cli import cmd_get

        args = SimpleNamespace(
            doc_id='doc-001', project=None, output=None, json=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_get(args)

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert '# Test Doc' in captured.out
        assert 'Summary content' in captured.out

    def test_get_not_found_exits_1(self, monkeypatch, capsys):
        '''cmd_get with unknown doc_id exits 1 with error message.'''
        from agents.hemingway.state import record_store as rs_module

        class _FakeStore:
            def __init__(self, **kwargs):
                pass

            def get_record(self, doc_id):
                return None

        monkeypatch.setattr(rs_module, 'HemingwayRecordStore', _FakeStore)

        from agents.hemingway.cli import cmd_get

        args = SimpleNamespace(
            doc_id='nonexistent', project=None, output=None, json=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_get(args)

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert 'No documentation record found' in captured.out

    def test_get_json_output(self, monkeypatch, capsys):
        '''cmd_get --json emits the record dict as JSON.'''
        from agents.hemingway.state import record_store as rs_module

        class _FakeStore:
            def __init__(self, **kwargs):
                pass

            def get_record(self, doc_id):
                return {
                    'record': {
                        'doc_id': doc_id,
                        'title': 'JSON Doc',
                        'doc_type': 'how_to',
                        'project_key': 'STL',
                    },
                    'summary_markdown': '# JSON Doc',
                    'summary': {'doc_id': doc_id},
                }

        monkeypatch.setattr(rs_module, 'HemingwayRecordStore', _FakeStore)

        from agents.hemingway.cli import cmd_get

        args = SimpleNamespace(
            doc_id='doc-json', project=None, output=None, json=True,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_get(args)

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload['doc_id'] == 'doc-json'
        assert payload['title'] == 'JSON Doc'

    def test_get_export_to_file(self, monkeypatch, tmp_path):
        '''cmd_get --output exports the record JSON to a file.'''
        from agents.hemingway.state import record_store as rs_module

        class _FakeStore:
            def __init__(self, **kwargs):
                pass

            def get_record(self, doc_id):
                return {
                    'record': {
                        'doc_id': doc_id,
                        'title': 'Export Doc',
                        'doc_type': 'engineering_reference',
                        'project_key': 'STL',
                    },
                    'summary_markdown': '# Export Doc',
                    'summary': {'doc_id': doc_id},
                }

        monkeypatch.setattr(rs_module, 'HemingwayRecordStore', _FakeStore)

        from agents.hemingway.cli import cmd_get

        output_file = tmp_path / 'exported.json'
        args = SimpleNamespace(
            doc_id='doc-export', project=None, output=str(output_file), json=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_get(args)

        assert exc_info.value.code == 0
        assert output_file.exists()

        exported = json.loads(output_file.read_text(encoding='utf-8'))
        assert exported['doc_id'] == 'doc-export'
        assert exported['title'] == 'Export Doc'

    def test_get_project_mismatch_exits_1(self, monkeypatch, capsys):
        '''cmd_get --project with mismatched project_key exits 1.'''
        from agents.hemingway.state import record_store as rs_module

        class _FakeStore:
            def __init__(self, **kwargs):
                pass

            def get_record(self, doc_id):
                return {
                    'record': {
                        'doc_id': doc_id,
                        'title': 'Wrong Project',
                        'doc_type': 'engineering_reference',
                        'project_key': 'OPA',
                    },
                    'summary_markdown': '',
                    'summary': {'doc_id': doc_id},
                }

        monkeypatch.setattr(rs_module, 'HemingwayRecordStore', _FakeStore)

        from agents.hemingway.cli import cmd_get

        args = SimpleNamespace(
            doc_id='doc-wrong', project='STL', output=None, json=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_get(args)

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert 'OPA' in captured.out
        assert 'STL' in captured.out
