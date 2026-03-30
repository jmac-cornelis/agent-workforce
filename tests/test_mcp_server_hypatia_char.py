import json

import pytest


def _payload(result):
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].type == 'text'
    return json.loads(result[0].text)


@pytest.mark.asyncio
async def test_generate_hypatia_documentation_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    from agents.hypatia.models import DocumentationPatch, DocumentationRecord
    from agents.review_agent import ReviewItem, ReviewSession

    class _FakeHypatiaAgent:
        def __init__(self, project_key=None, **_kwargs):
            self.project_key = project_key

        def plan_documentation(self, request):
            assert request.validation_profile == 'strict'
            assert request.evidence_paths == ['release.json']
            record = DocumentationRecord(
                doc_id='doc-401',
                title=request.title,
                doc_type=request.doc_type,
                project_key=request.project_key,
                summary_markdown='# Hypatia',
                validation={'valid': True},
                evidence_summary={'record_count': 1, 'by_type': {'release': 1}},
                patches=[
                    DocumentationPatch(
                        patch_id='H001',
                        target_type='repo_markdown',
                        operation='create',
                        title=request.title,
                        target_ref='docs/output.md',
                        content_markdown='# Draft\n',
                    )
                ],
            )
            session = ReviewSession(
                session_id='doc-401',
                items=[ReviewItem(id='H001', item_type='document', action='write', data={})],
            )
            return record, session

    class _FakeStore:
        def save_record(self, record, summary_markdown=None):
            return {'doc_id': record.doc_id, 'storage_dir': '/tmp/hypatia/doc-401'}

    monkeypatch.setattr(import_mcp_server, 'HypatiaDocumentationAgent', _FakeHypatiaAgent)
    monkeypatch.setattr(import_mcp_server, 'HypatiaRecordStore', _FakeStore)

    result = await import_mcp_server.generate_hypatia_documentation(
        title='Release Notes Support',
        doc_type='release_note_support',
        project_key='STL',
        evidence_paths=['release.json'],
        validation_profile='strict',
        persist=True,
    )
    data = _payload(result)

    assert data['record']['doc_id'] == 'doc-401'
    assert data['stored']['doc_id'] == 'doc-401'


@pytest.mark.asyncio
async def test_get_and_list_hypatia_records_tools(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
    class _FakeStore:
        def get_record(self, doc_id):
            assert doc_id == 'doc-501'
            return {'record': {'doc_id': doc_id}, 'summary_markdown': '# Stored'}

        def list_records(self, doc_type=None, limit=20):
            assert doc_type == 'engineering_reference'
            assert limit == 5
            return [{'doc_id': 'doc-501', 'doc_type': doc_type}]

    monkeypatch.setattr(import_mcp_server, 'HypatiaRecordStore', _FakeStore)

    get_result = await import_mcp_server.get_hypatia_record('doc-501')
    list_result = await import_mcp_server.list_hypatia_records(
        doc_type='engineering_reference',
        limit=5,
    )

    assert _payload(get_result)['record']['doc_id'] == 'doc-501'
    assert _payload(list_result)[0]['doc_id'] == 'doc-501'
