import pytest

from tools.hypatia_tools import (
    HypatiaTools,
    generate_hypatia_documentation,
    get_hypatia_record,
    list_hypatia_records,
)


def test_generate_hypatia_documentation_tool_persists_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    from agents import hypatia_agent as hypatia_agent_module
    from agents.hypatia_models import DocumentationPatch, DocumentationRecord
    from agents.review_agent import ReviewItem, ReviewSession

    class _FakeHypatiaAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def plan_documentation(self, request):
            assert request.validation_profile == 'strict'
            assert request.evidence_paths == ['release.json']
            record = DocumentationRecord(
                doc_id='doc-201',
                title=request.title,
                doc_type=request.doc_type,
                project_key=request.project_key,
                summary_markdown='# Hypatia\n\nSummary',
                validation={'valid': True},
                evidence_summary={'record_count': 1, 'by_type': {'release': 1}},
                patches=[
                    DocumentationPatch(
                        patch_id='H001',
                        target_type='repo_markdown',
                        operation='create',
                        title=request.title,
                        target_ref=request.target_file or 'docs/output.md',
                        content_markdown='# Draft\n',
                    )
                ],
            )
            session = ReviewSession(
                session_id='doc-201',
                created_at='2026-03-16T12:00:00+00:00',
                items=[ReviewItem(id='H001', item_type='document', action='write', data={})],
            )
            return record, session

    monkeypatch.setattr(hypatia_agent_module, 'HypatiaDocumentationAgent', _FakeHypatiaAgent)
    monkeypatch.setenv('HYPATIA_DOC_DIR', str(tmp_path / 'store'))

    result = generate_hypatia_documentation(
        title='Release Notes Support',
        doc_type='release_note_support',
        project_key='STL',
        evidence_paths=['release.json'],
        target_file='docs/release-notes.md',
        validation_profile='strict',
        persist=True,
    )

    assert result.is_success
    assert result.data['record']['doc_id'] == 'doc-201'
    assert result.data['record']['evidence_summary']['record_count'] == 1
    assert result.data['stored']['doc_id'] == 'doc-201'
    assert (tmp_path / 'store' / 'doc-201' / 'record.json').exists()


def test_get_and_list_hypatia_records_tools(monkeypatch: pytest.MonkeyPatch, tmp_path):
    from state.hypatia_record_store import HypatiaRecordStore

    store = HypatiaRecordStore(storage_dir=str(tmp_path / 'store'))
    store.save_record({
        'doc_id': 'doc-301',
        'title': 'Guide',
        'doc_type': 'engineering_reference',
        'project_key': 'STL',
        'created_at': '2026-03-16T12:00:00+00:00',
        'patches': [{'patch_id': 'H1'}],
        'summary_markdown': '# Guide',
    }, summary_markdown='# Guide')

    monkeypatch.setenv('HYPATIA_DOC_DIR', str(tmp_path / 'store'))

    get_result = get_hypatia_record('doc-301')
    list_result = list_hypatia_records(doc_type='engineering_reference', limit=5)

    assert get_result.is_success
    assert get_result.data['record']['doc_id'] == 'doc-301'
    assert list_result.is_success
    assert list_result.data[0]['doc_id'] == 'doc-301'


def test_hypatia_tools_collection_registers_methods():
    tools = HypatiaTools()

    assert tools.get_tool('generate_hypatia_documentation') is not None
    assert tools.get_tool('get_hypatia_record') is not None
    assert tools.get_tool('list_hypatia_records') is not None
