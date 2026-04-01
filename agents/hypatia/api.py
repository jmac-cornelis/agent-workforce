##########################################################################################
#
# Module: agents/hypatia/api.py
#
# Description: Hypatia Documentation Agent REST API.
#              FastAPI service exposing documentation generation, impact analysis,
#              record retrieval, and review-gated publication.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.env_loader import load_env

load_env()

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from agents.hypatia.agent import HypatiaDocumentationAgent
from agents.hypatia.models import (
    DOC_TYPES,
    DocumentationImpactRecord,
    DocumentationRecord,
    DocumentationRequest,
    PublicationRecord,
)
from agents.hypatia.state.record_store import HypatiaRecordStore

import re

log = logging.getLogger(os.path.basename(sys.argv[0]))


def _parse_confluence_url(url: str) -> Dict[str, str]:
    '''
    Extract space_id and page_id from an Atlassian Confluence URL.

    Supported formats:
      https://DOMAIN/wiki/spaces/SPACE/pages/PAGE_ID/optional-title
      https://DOMAIN/wiki/spaces/SPACE/pages/PAGE_ID
    '''
    m = re.search(r'/wiki/spaces/([^/]+)/pages/(\d+)', url)
    if m:
        return {'space': m.group(1), 'page_id': m.group(2)}
    return {}

record_store = HypatiaRecordStore()

_run_count = 0
_total_docs_generated = 0
_last_run_at = ''


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class GenerateDocRequest(BaseModel):
    '''Request body for POST /v1/docs/generate.'''
    doc_title: str
    doc_type: str = 'engineering_reference'
    project_key: Optional[str] = None
    doc_summary: Optional[str] = None
    source_paths: List[str] = []
    source_refs: List[str] = []
    evidence_paths: List[str] = []
    target_file: Optional[str] = None
    confluence_title: Optional[str] = None
    confluence_page: Optional[str] = None
    confluence_space: Optional[str] = None
    confluence_parent_id: Optional[str] = None
    version_message: Optional[str] = None
    validation_profile: str = 'default'
    persist: bool = True
    dry_run: Optional[bool] = None


class ImpactDetectRequest(BaseModel):
    '''Request body for POST /v1/docs/impact.'''
    doc_title: str
    doc_type: str = 'engineering_reference'
    project_key: Optional[str] = None
    source_paths: List[str] = []
    target_file: Optional[str] = None
    confluence_title: Optional[str] = None
    confluence_page: Optional[str] = None


class SearchDocsRequest(BaseModel):
    '''Request body for POST /v1/docs/search.'''
    query: Optional[str] = None
    project_key: Optional[str] = None
    doc_type: Optional[str] = None
    source_ref: Optional[str] = None
    published_only: bool = False
    confidence: Optional[str] = None
    limit: Optional[int] = None


class PublishRequest(BaseModel):
    '''Request body for POST /v1/docs/publish.'''
    doc_id: str
    project_key: Optional[str] = None
    dry_run: Optional[bool] = None


class ConfluencePublishPageRequest(BaseModel):
    '''Request body for POST /v1/docs/confluence/publish-page.'''
    title: Optional[str] = None
    markdown_content: Optional[str] = None
    input_file: Optional[str] = None
    space: Optional[str] = None
    parent_id: Optional[str] = None
    parent_url: Optional[str] = None
    page_id_or_title: Optional[str] = None
    heading: Optional[str] = None
    version_message: Optional[str] = None
    operation: str = 'create'
    render_diagrams: bool = True
    dry_run: Optional[bool] = None


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    '''Build and return the Hypatia FastAPI application.'''
    app = FastAPI(title='Hypatia Documentation Agent API', version='1.0.0')

    # ------------------------------------------------------------------
    # Health & status endpoints (match Shannon expected contract)
    # ------------------------------------------------------------------

    @app.get('/v1/health')
    def health() -> Dict[str, Any]:
        return {'service': 'hypatia', 'ok': True}

    @app.get('/v1/status/stats')
    def status_stats() -> Dict[str, Any]:
        records = record_store.list_records(limit=100)
        type_counts: Dict[str, int] = {}
        for r in records:
            dt = str(r.get('doc_type') or 'unknown')
            type_counts[dt] = type_counts.get(dt, 0) + 1
        return {
            'ok': True,
            'data': {
                'records_count': len(records),
                'runs_this_session': _run_count,
                'doc_types': type_counts,
            },
        }

    @app.get('/v1/status/load')
    def status_load() -> Dict[str, Any]:
        return {
            'ok': True,
            'data': {
                'state': 'idle',
                'runs_this_session': _run_count,
                'last_run_at': _last_run_at,
            },
        }

    @app.get('/v1/status/work-summary')
    def status_work_summary() -> Dict[str, Any]:
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        records = record_store.list_records(limit=50)
        today_records = [
            r for r in records
            if str(r.get('created_at', '')).startswith(today)
        ]
        return {
            'ok': True,
            'data': {
                'docs_today': len(today_records),
                'last_run_at': _last_run_at or 'none',
            },
        }

    @app.get('/v1/status/tokens')
    def status_tokens() -> Dict[str, Any]:
        return {
            'ok': True,
            'data': {
                'llm_enabled': True,
                'token_usage_today': 0,
                'token_usage_cumulative': 0,
                'notes': 'Hypatia uses LLM for content generation; token tracking is placeholder.',
            },
        }

    @app.get('/v1/status/decisions')
    def status_decisions(
        limit: int = Query(default=10, ge=1, le=100),
    ) -> Dict[str, Any]:
        records = record_store.list_records(limit=limit)
        decisions = []
        for r in records:
            decisions.append({
                'record_id': r.get('doc_id', ''),
                'title': r.get('title', ''),
                'doc_type': r.get('doc_type', ''),
                'project_key': r.get('project_key', ''),
                'created_at': r.get('created_at', ''),
                'patch_count': r.get('patch_count', 0),
                'warning_count': r.get('warning_count', 0),
            })
        return {'ok': True, 'data': decisions}

    @app.get('/v1/status/decisions/{record_id}')
    def status_decision_detail(record_id: str) -> Dict[str, Any]:
        result = record_store.get_record(record_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f'Documentation record {record_id} not found',
            )
        record_data = result.get('record', {})
        return {
            'ok': True,
            'data': {
                'doc_id': record_data.get('doc_id', ''),
                'title': record_data.get('title', ''),
                'doc_type': record_data.get('doc_type', ''),
                'project_key': record_data.get('project_key', ''),
                'created_at': record_data.get('created_at', ''),
                'patch_count': len(record_data.get('patches', [])),
                'warning_count': len(record_data.get('warnings', [])),
                'confidence': record_data.get('confidence', ''),
                'summary_markdown': record_data.get('summary_markdown', ''),
            },
        }

    # ------------------------------------------------------------------
    # Domain endpoints
    # ------------------------------------------------------------------

    @app.post('/v1/docs/generate')
    def docs_generate(body: GenerateDocRequest) -> Dict[str, Any]:
        '''
        Generate a documentation record from source materials.

        When dry_run is active, returns a preview of what would be generated
        without invoking the LLM or persisting anything.
        '''
        global _run_count, _total_docs_generated, _last_run_at

        from config.env_loader import resolve_dry_run

        dry_run = resolve_dry_run(body.dry_run)

        request = DocumentationRequest(
            title=body.doc_title,
            doc_type=body.doc_type,
            project_key=body.project_key or '',
            summary=body.doc_summary or '',
            source_paths=body.source_paths,
            source_refs=body.source_refs,
            evidence_paths=body.evidence_paths,
            target_file=body.target_file,
            confluence_title=body.confluence_title,
            confluence_page=body.confluence_page,
            confluence_space=body.confluence_space,
            confluence_parent_id=body.confluence_parent_id,
            version_message=body.version_message,
            validation_profile=body.validation_profile,
        )

        if dry_run:
            return {
                'ok': True,
                'data': {
                    'dry_run': True,
                    'message': 'Dry-run preview — no LLM invocation or persistence.',
                    'request': request.to_dict(),
                    'doc_type': body.doc_type,
                    'project_key': body.project_key or '',
                },
            }

        agent = HypatiaDocumentationAgent(project_key=body.project_key)

        try:
            record, review_session = agent.plan_documentation(request)
        except Exception as e:
            log.error(f'Hypatia documentation generation failed: {e}')
            return {'ok': False, 'error': str(e)}

        save_result = None
        if body.persist:
            save_result = record_store.save_record(record)

        _run_count += 1
        _total_docs_generated += 1
        _last_run_at = datetime.now(timezone.utc).isoformat()

        return {
            'ok': True,
            'data': {
                'record': record.to_dict(),
                'review_session': review_session.to_dict(),
                'stored': save_result,
            },
        }

    @app.get('/v1/docs/records')
    def docs_records(
        doc_type: Optional[str] = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> Dict[str, Any]:
        '''List stored documentation records.'''
        records = record_store.list_records(doc_type=doc_type, limit=limit)
        return {'ok': True, 'data': records}

    @app.get('/v1/docs/record/{doc_id}')
    def docs_record_detail(doc_id: str) -> Dict[str, Any]:
        '''Load a single stored documentation record by ID.'''
        result = record_store.get_record(doc_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f'Documentation record {doc_id} not found',
            )
        return {'ok': True, 'data': result}

    @app.post('/v1/docs/search')
    def docs_search(body: SearchDocsRequest) -> Dict[str, Any]:
        '''Search stored documentation records with multi-field filtering.'''
        results = record_store.search_records(
            query=body.query,
            project_key=body.project_key,
            doc_type=body.doc_type,
            source_ref=body.source_ref,
            published_only=body.published_only,
            confidence=body.confidence,
            limit=body.limit,
        )
        return {
            'ok': True,
            'data': {
                'results': results,
                'count': len(results),
                'query': body.query or '',
            },
        }

    @app.post('/v1/docs/impact')
    def docs_impact(body: ImpactDetectRequest) -> Dict[str, Any]:
        '''
        Detect documentation impact for the given request parameters.
        No persistence needed — returns the impact analysis directly.
        '''
        global _run_count, _last_run_at

        request = DocumentationRequest(
            title=body.doc_title,
            doc_type=body.doc_type,
            project_key=body.project_key or '',
            source_paths=body.source_paths,
            target_file=body.target_file,
            confluence_title=body.confluence_title,
            confluence_page=body.confluence_page,
        )

        agent = HypatiaDocumentationAgent(project_key=body.project_key)

        try:
            impact = agent.detect_documentation_impact(request)
        except Exception as e:
            log.error(f'Hypatia impact detection failed: {e}')
            return {'ok': False, 'error': str(e)}

        _run_count += 1
        _last_run_at = datetime.now(timezone.utc).isoformat()

        return {'ok': True, 'data': impact.to_dict()}

    @app.post('/v1/docs/publish')
    def docs_publish(body: PublishRequest) -> Dict[str, Any]:
        '''
        Publish approved documentation patches for a stored record.

        This is a mutation endpoint — dry_run gate applies.
        '''
        global _run_count, _last_run_at

        from config.env_loader import resolve_dry_run

        dry_run = resolve_dry_run(body.dry_run)

        stored = record_store.get_record(body.doc_id)
        if stored is None:
            raise HTTPException(
                status_code=404,
                detail=f'Documentation record {body.doc_id} not found',
            )

        if dry_run:
            record_data = stored.get('record', {})
            patches = record_data.get('patches', [])
            return {
                'ok': True,
                'data': {
                    'dry_run': True,
                    'message': 'Dry-run preview — no publication executed.',
                    'doc_id': body.doc_id,
                    'patch_count': len(patches),
                    'patches': [
                        {
                            'patch_id': p.get('patch_id', ''),
                            'target_type': p.get('target_type', ''),
                            'operation': p.get('operation', ''),
                            'target_ref': p.get('target_ref', ''),
                        }
                        for p in patches
                    ],
                },
            }

        agent = HypatiaDocumentationAgent(project_key=body.project_key)
        record_data = stored.get('record', {})
        record = DocumentationRecord(
            title=record_data.get('title', ''),
            doc_type=record_data.get('doc_type', ''),
            project_key=record_data.get('project_key', ''),
            doc_id=record_data.get('doc_id', ''),
            created_at=record_data.get('created_at', ''),
            request=record_data.get('request', {}),
            impact=record_data.get('impact', {}),
            source_refs=record_data.get('source_refs', []),
            evidence_summary=record_data.get('evidence_summary', {}),
            content_markdown=record_data.get('content_markdown', ''),
            summary_markdown=record_data.get('summary_markdown', ''),
            validation=record_data.get('validation', {}),
            warnings=record_data.get('warnings', []),
            confidence=record_data.get('confidence', 'medium'),
            metadata=record_data.get('metadata', {}),
        )

        review_session = agent.create_review_session(record)

        try:
            publications = agent.publish_approved(review_session)
        except Exception as e:
            log.error(f'Hypatia publication failed: {e}')
            return {'ok': False, 'error': str(e)}

        record_store.record_publications(
            body.doc_id,
            publications,
        )

        _run_count += 1
        _last_run_at = datetime.now(timezone.utc).isoformat()

        return {
            'ok': True,
            'data': {
                'doc_id': body.doc_id,
                'publications': [pub.to_dict() for pub in publications],
                'publication_count': len(publications),
            },
        }

    # ------------------------------------------------------------------
    # Direct Confluence publish endpoint
    # ------------------------------------------------------------------

    @app.post('/v1/docs/confluence/publish-page')
    def docs_confluence_publish_page(
        body: ConfluencePublishPageRequest,
    ) -> Dict[str, Any]:
        '''
        Publish markdown content directly to Confluence as a page.

        Supports create, update, append, and update_section operations.
        Handles Mermaid and draw.io diagram rendering when render_diagrams
        is enabled.  This is a mutation endpoint — dry_run gate applies.
        '''
        from config.env_loader import resolve_dry_run
        from tools.confluence_tools import (
            append_to_confluence_page,
            create_confluence_page,
            update_confluence_page,
            update_confluence_section,
        )

        # --- validation ---------------------------------------------------
        valid_operations = ('create', 'update', 'append', 'update_section')
        if body.operation not in valid_operations:
            raise HTTPException(
                status_code=400,
                detail=(
                    f'Invalid operation {body.operation!r}. '
                    f'Must be one of: {", ".join(valid_operations)}'
                ),
            )

        if body.parent_url and not body.parent_id:
            parsed = _parse_confluence_url(body.parent_url)
            if parsed.get('page_id'):
                body.parent_id = parsed['page_id']
            if parsed.get('space') and not body.space:
                body.space = parsed['space']

        if not body.markdown_content and not body.input_file:
            raise HTTPException(
                status_code=400,
                detail='Either markdown_content or input_file must be provided.',
            )

        if body.operation == 'create' and not body.title:
            raise HTTPException(
                status_code=400,
                detail='title is required for create operations.',
            )

        if body.operation in ('update', 'append', 'update_section') and not body.page_id_or_title:
            raise HTTPException(
                status_code=400,
                detail='page_id_or_title is required for update/append/update_section operations.',
            )

        if body.operation == 'update_section' and not body.heading:
            raise HTTPException(
                status_code=400,
                detail='heading is required for update_section operations.',
            )

        dry_run = resolve_dry_run(body.dry_run)

        # --- resolve input file -------------------------------------------
        # When raw markdown is provided, write it to a temp file so the
        # confluence_tools functions (which expect a file path) can consume it.
        temp_path: Optional[str] = None
        input_file = body.input_file

        if body.markdown_content:
            handle = tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                suffix='.md',
                delete=False,
            )
            handle.write(body.markdown_content)
            handle.close()
            temp_path = handle.name
            input_file = temp_path

        try:
            # --- dispatch to correct tool ---------------------------------
            if body.operation == 'create':
                result = create_confluence_page(
                    title=body.title or '',
                    input_file=input_file or '',
                    space=body.space,
                    parent_id=body.parent_id,
                    version_message=body.version_message,
                    dry_run=dry_run,
                )
            elif body.operation == 'update':
                result = update_confluence_page(
                    page_id_or_title=body.page_id_or_title or '',
                    input_file=input_file or '',
                    space=body.space,
                    version_message=body.version_message,
                    dry_run=dry_run,
                )
            elif body.operation == 'append':
                result = append_to_confluence_page(
                    page_id_or_title=body.page_id_or_title or '',
                    input_file=input_file or '',
                    space=body.space,
                    version_message=body.version_message,
                    dry_run=dry_run,
                )
            else:
                result = update_confluence_section(
                    page_id_or_title=body.page_id_or_title or '',
                    heading=body.heading or '',
                    input_file=input_file or '',
                    space=body.space,
                    version_message=body.version_message,
                    dry_run=dry_run,
                )

            if result.is_success:
                return {'ok': True, 'data': result.data}

            return {'ok': False, 'error': result.error}

        except Exception as e:
            log.error(f'Confluence publish-page failed: {e}')
            return {'ok': False, 'error': str(e)}

        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    return app


# ---------------------------------------------------------------------------
# Module-level app + CLI runner
# ---------------------------------------------------------------------------

app = create_app()


def run() -> None:
    import uvicorn
    host = str(os.getenv('HYPATIA_HOST', '0.0.0.0') or '0.0.0.0').strip()
    port = int(os.getenv('HYPATIA_PORT', '8203') or '8203')
    uvicorn.run('agents.hypatia.api:app', host=host, port=port, log_level='info')


if __name__ == '__main__':
    run()
