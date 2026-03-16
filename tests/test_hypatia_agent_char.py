import json
from types import SimpleNamespace

import pytest

from agents.hypatia_models import (
    DocumentationPatch,
    DocumentationRecord,
    DocumentationRequest,
    PublicationRecord,
)
from agents.review_agent import ApprovalStatus, ReviewItem, ReviewSession, ReviewAgent
from tools.base import ToolResult


def test_hypatia_agent_builds_record_and_review_session(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents.hypatia_agent import HypatiaDocumentationAgent
    from agents import hypatia_agent as hypatia_agent_module

    source_path = tmp_path / 'inputs.md'
    source_path.write_text(
        '# Fabric bring-up\n\n- Enable secure boot path\n- Capture board revisions\n',
        encoding='utf-8',
    )

    monkeypatch.setattr(
        HypatiaDocumentationAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'hypatia prompt'),
    )
    monkeypatch.setattr(
        hypatia_agent_module,
        'create_confluence_page',
        lambda **kwargs: ToolResult.success({
            'mode': 'create',
            'title': kwargs['title'],
            'space': kwargs.get('space'),
            'preview_available': True,
        }),
    )

    agent = HypatiaDocumentationAgent(project_key='STL')
    record, session = agent.plan_documentation(DocumentationRequest(
        title='Fabric Bring-Up Guide',
        doc_type='how_to',
        project_key='STL',
        summary='Capture the current internal bring-up procedure.',
        source_paths=[str(source_path)],
        target_file=str(tmp_path / 'fabric-bring-up.md'),
        confluence_title='Fabric Bring-Up Guide',
        confluence_space='ENG',
        version_message='Initial draft',
    ))

    target_types = [patch.target_type for patch in record.patches]
    actions = [item.action for item in session.items]

    assert record.title == 'Fabric Bring-Up Guide'
    assert record.doc_type == 'how_to'
    assert record.project_key == 'STL'
    assert record.validation['valid'] is True
    assert record.confidence in ('medium', 'high')
    assert target_types == ['repo_markdown', 'confluence_page']
    assert actions == ['write', 'create']
    assert '## Key Facts' in record.content_markdown
    assert 'Fabric bring-up' in record.content_markdown
    assert '## Proposed Patches' in record.summary_markdown
    assert record.patches[1].preview['preview_available'] is True


def test_hypatia_record_store_save_load_list_and_publications(tmp_path):
    from state.hypatia_record_store import HypatiaRecordStore

    store = HypatiaRecordStore(storage_dir=str(tmp_path / 'hypatia'))

    store.save_record({
        'doc_id': 'doc-001',
        'title': 'First Guide',
        'doc_type': 'engineering_reference',
        'project_key': 'STL',
        'created_at': '2026-03-15T12:00:00+00:00',
        'patches': [{'patch_id': 'P1'}],
        'warnings': [],
        'publication_records': [],
        'summary_markdown': '# First',
    }, summary_markdown='# First')
    store.save_record({
        'doc_id': 'doc-002',
        'title': 'Second Guide',
        'doc_type': 'how_to',
        'project_key': 'STL',
        'created_at': '2026-03-16T12:00:00+00:00',
        'patches': [{'patch_id': 'P2'}, {'patch_id': 'P3'}],
        'warnings': ['needs review'],
        'publication_records': [],
        'summary_markdown': '# Second',
    }, summary_markdown='# Second')

    publication = PublicationRecord(
        doc_id='doc-002',
        patch_id='P2',
        title='Second Guide',
        target_type='repo_markdown',
        operation='write',
        target_ref='docs/second.md',
        status='published',
        published_at='2026-03-16T12:05:00+00:00',
        result={'path': 'docs/second.md'},
    )
    store.record_publications('doc-002', [publication])

    record = store.get_record('doc-002')
    listed = store.list_records(limit=5)

    assert record is not None
    assert record['summary']['publication_count'] == 1
    assert record['record']['publication_records'][0]['status'] == 'published'
    assert [row['doc_id'] for row in listed] == ['doc-002', 'doc-001']


def test_hypatia_publish_approved_executes_repo_and_confluence_targets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents.hypatia_agent import HypatiaDocumentationAgent
    from agents import hypatia_agent as hypatia_agent_module
    from tools import file_tools as file_tools_module
    from tools import confluence_tools as confluence_tools_module

    source_path = tmp_path / 'summary.md'
    source_path.write_text('# System\n\n- Secure link required\n', encoding='utf-8')

    monkeypatch.setattr(
        HypatiaDocumentationAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'hypatia prompt'),
    )
    monkeypatch.setattr(
        ReviewAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'review prompt'),
    )
    monkeypatch.setattr(
        hypatia_agent_module,
        'create_confluence_page',
        lambda **kwargs: ToolResult.success({
            'mode': 'create',
            'title': kwargs['title'],
            'preview_available': True,
        }),
    )

    file_calls = []
    confluence_calls = []

    monkeypatch.setattr(
        file_tools_module,
        'write_file',
        lambda **kwargs: (
            file_calls.append(kwargs)
            or ToolResult.success({'path': kwargs['file_path'], 'size_bytes': len(kwargs['content'])})
        ),
    )
    monkeypatch.setattr(
        confluence_tools_module,
        'create_confluence_page',
        lambda **kwargs: (
            confluence_calls.append(kwargs)
            or ToolResult.success({'page_id': '9001', 'title': kwargs['title']})
        ),
    )

    agent = HypatiaDocumentationAgent(project_key='STL')
    record, session = agent.plan_documentation(DocumentationRequest(
        title='Secure Link Notes',
        doc_type='engineering_reference',
        project_key='STL',
        source_paths=[str(source_path)],
        target_file=str(tmp_path / 'secure-link.md'),
        confluence_title='Secure Link Notes',
        confluence_space='ENG',
    ))

    agent.review_agent.approve_all(session)
    publications = agent.publish_approved(session)

    assert len(file_calls) == 1
    assert file_calls[0]['file_path'].endswith('secure-link.md')
    assert len(confluence_calls) == 1
    assert confluence_calls[0]['title'] == 'Secure Link Notes'
    assert [publication.status for publication in publications] == ['published', 'published']
    assert session.items[0].status.value == 'executed'
    assert session.items[1].status.value == 'executed'


def test_hypatia_strict_validation_requires_source_refs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents.hypatia_agent import HypatiaDocumentationAgent

    monkeypatch.setattr(
        HypatiaDocumentationAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'hypatia prompt'),
    )

    agent = HypatiaDocumentationAgent(project_key='STL')
    record, _session = agent.plan_documentation(DocumentationRequest(
        title='Ungrounded Draft',
        doc_type='engineering_reference',
        project_key='STL',
        summary='This draft has no authoritative sources.',
        target_file=str(tmp_path / 'ungrounded.md'),
        validation_profile='strict',
    ))

    assert record.validation['valid'] is False
    assert any('source references' in issue.casefold() for issue in record.validation['blocking_issues'])


def test_hypatia_sphinx_validation_runs_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents.hypatia_agent import HypatiaDocumentationAgent
    from agents import hypatia_agent as hypatia_agent_module

    docs_source = tmp_path / 'docs' / 'source'
    docs_source.mkdir(parents=True)
    (docs_source / 'conf.py').write_text("project = 'Demo'\n", encoding='utf-8')
    source_path = tmp_path / 'facts.md'
    source_path.write_text('# Facts\n\n- One\n', encoding='utf-8')

    run_calls = []

    monkeypatch.setattr(
        HypatiaDocumentationAgent,
        '_load_prompt_file',
        staticmethod(lambda: 'hypatia prompt'),
    )
    monkeypatch.setattr(hypatia_agent_module.shutil, 'which', lambda name: '/usr/bin/sphinx-build')
    monkeypatch.setattr(
        hypatia_agent_module.subprocess,
        'run',
        lambda args, capture_output, text, check: (
            run_calls.append(args) or SimpleNamespace(returncode=0, stdout='', stderr='')
        ),
    )

    agent = HypatiaDocumentationAgent(project_key='STL')
    record, _session = agent.plan_documentation(DocumentationRequest(
        title='Sphinx Draft',
        doc_type='engineering_reference',
        project_key='STL',
        source_paths=[str(source_path)],
        target_file=str(docs_source / 'guide.md'),
        validation_profile='sphinx',
    ))

    assert record.validation['valid'] is True
    assert run_calls
    assert record.patches[0].metadata['sphinx_validation']['validated'] is True


def test_workflow_hypatia_generate_writes_record_and_publications(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    import pm_agent
    from agents import hypatia_agent as hypatia_agent_module

    class _FakeReviewAgent:
        def approve_all(self, session):
            for item in session.items:
                item.status = ApprovalStatus.APPROVED
            return len(session.items)

    class _FakeHypatiaAgent:
        def __init__(self, project_key=None, **kwargs):
            self.project_key = project_key
            self.review_agent = _FakeReviewAgent()

        def _normalize_request(self, request):
            return request

        def plan_documentation(self, request):
            record = DocumentationRecord(
                doc_id='doc-101',
                title=request['title'],
                doc_type=request['doc_type'],
                project_key=request['project_key'],
                summary_markdown='# Hypatia\n\nSummary',
                validation={'valid': True},
                patches=[
                    DocumentationPatch(
                        patch_id='H001',
                        target_type='repo_markdown',
                        operation='create',
                        title=request['title'],
                        target_ref=request['target_file'],
                        content_markdown='# Patch 1\n',
                    ),
                ],
            )
            session = ReviewSession(
                session_id='doc-101',
                created_at='2026-03-16T12:00:00+00:00',
                items=[
                    ReviewItem(
                        id='H001',
                        item_type='document',
                        action='write',
                        data={
                            'doc_id': 'doc-101',
                            'patch_id': 'H001',
                            'title': request['title'],
                            'file_path': request['target_file'],
                            'content': '# Patch 1\n',
                        },
                    ),
                ],
            )
            return record, session

        def publish_approved(self, session):
            return [
                PublicationRecord(
                    doc_id='doc-101',
                    patch_id='H001',
                    title='Draft',
                    target_type='document',
                    operation='write',
                    target_ref='docs/hypatia.md',
                    status='published',
                    published_at='2026-03-16T12:05:00+00:00',
                    result={'path': 'docs/hypatia.md'},
                )
            ]

    monkeypatch.setattr(hypatia_agent_module, 'HypatiaDocumentationAgent', _FakeHypatiaAgent)
    monkeypatch.setattr(pm_agent, 'output', lambda *args, **kwargs: None)
    monkeypatch.setenv('HYPATIA_DOC_DIR', str(tmp_path / 'store'))

    output_path = tmp_path / 'hypatia_record.json'
    args = SimpleNamespace(
        project='STL',
        doc_title='Draft',
        doc_type='engineering_reference',
        doc_summary='Build summary',
        docs=[],
        target_file=str(tmp_path / 'docs' / 'hypatia.md'),
        confluence_title=None,
        confluence_page=None,
        confluence_space=None,
        confluence_parent_id=None,
        version_message=None,
        output=str(output_path),
        execute=True,
    )

    exit_code = pm_agent._workflow_hypatia_generate(args)

    assert exit_code == 0
    assert output_path.exists()
    assert (tmp_path / 'hypatia_record.md').exists()
    assert (tmp_path / 'hypatia_record_review.json').exists()
    assert (tmp_path / 'hypatia_record_publications.json').exists()
    assert (tmp_path / 'store' / 'doc-101' / 'record.json').exists()

    exported = json.loads(output_path.read_text(encoding='utf-8'))
    publications = json.loads(
        (tmp_path / 'hypatia_record_publications.json').read_text(encoding='utf-8')
    )

    assert exported['doc_id'] == 'doc-101'
    assert publications[0]['status'] == 'published'
