##########################################################################################
#
# Module: agents/hemingway/api.py
#
# Description: Hemingway Documentation Agent REST API.
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
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.env_loader import load_env

load_env()

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from agents.hemingway.agent import HemingwayDocumentationAgent
from agents.hemingway.models import (
    DOC_TYPES,
    DocumentationImpactRecord,
    DocumentationRecord,
    DocumentationRequest,
    PublicationRecord,
)
from agents.hemingway.state.record_store import HemingwayRecordStore

import re
from pathlib import Path

import yaml

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

record_store = HemingwayRecordStore()


# ---------------------------------------------------------------------------
# Human-friendly record formatting helpers
# ---------------------------------------------------------------------------

_DOC_TYPE_DISPLAY = {
    'as_built': 'As-Built Reference',
    'engineering_reference': 'Engineering Reference',
    'how_to': 'How-To Guide',
    'user_guide': 'User Guide',
    'release_note_support': 'Release Notes',
}


def _classify_source(record: Dict[str, Any]) -> str:
    """Classify the origin of a documentation record for display."""
    req = record.get('request', {})
    if isinstance(req, dict):
        if req.get('pr_number'):
            return f"PR #{req['pr_number']}"
        if req.get('confluence_title') or req.get('confluence_page'):
            return 'Confluence'
        if req.get('target_file'):
            return 'Repository'
    return 'One-off'


def _build_record_link(record: Dict[str, Any]) -> str:
    """Build a live link to the documentation artifact."""
    req = record.get('request', {})
    if not isinstance(req, dict):
        doc_id = record.get('doc_id', '')
        return f'https://hemingway.cn-agents.com/v1/docs/record/{doc_id}'
    repo = req.get('repo_name', '')
    target = req.get('target_file', '')
    branch = req.get('branch', 'main')
    if repo and target:
        return f'https://github.com/{repo}/blob/{branch}/{target}'
    pr = req.get('pr_number')
    if repo and pr:
        return f'https://github.com/{repo}/pull/{pr}'
    confluence_page = req.get('confluence_page')
    if confluence_page:
        return str(confluence_page)
    doc_id = record.get('doc_id', '')
    return f'https://hemingway.cn-agents.com/v1/docs/record/{doc_id}'


def _format_record_for_humans(record: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a raw record summary into a human-friendly representation."""
    return {
        'title': record.get('title', ''),
        'author': 'Hemingway',
        'doc_type': record.get('doc_type', ''),
        'doc_type_display': _DOC_TYPE_DISPLAY.get(
            record.get('doc_type', ''), record.get('doc_type', ''),
        ),
        'source': _classify_source(record),
        'link': _build_record_link(record),
        'created_at': record.get('created_at', ''),
        'doc_id': record.get('doc_id', ''),
        'project_key': record.get('project_key', ''),
    }

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
    repo_name: Optional[str] = None
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


class FindRequest(BaseModel):
    '''Request body for POST /v1/docs/find -- free-text search.'''
    text: str
    limit: int = 10


class PublishRequest(BaseModel):
    '''Request body for POST /v1/docs/publish.'''
    doc_id: str
    project_key: Optional[str] = None
    dry_run: Optional[bool] = None


class PRReviewRequest(BaseModel):
    '''Request body for POST /v1/docs/pr-review.'''
    repo: str
    pr_number: int
    doc_types: Optional[List[str]] = None
    target_dir: Optional[str] = 'docs'
    dry_run: Optional[bool] = None
    branch: Optional[str] = None


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


class VoiceConfigRequest(BaseModel):
    '''Request body for POST /v1/config/voice.'''
    profile_name: Optional[str] = None
    tone: Optional[str] = None
    audience: Optional[str] = None
    purpose: Optional[str] = None
    style_notes: Optional[str] = None


class VoiceConfigFromFileRequest(BaseModel):
    '''Request body for POST /v1/config/voice/from-file.'''
    file_url: Optional[str] = None
    file_path: Optional[str] = None
    profile_name: str = 'custom'


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

class NLQueryRequest(BaseModel):
    query: str


class ReindexRequest(BaseModel):
    """Request body for POST /v1/docs/reindex."""
    repo: str
    docs_dir: str = 'docs'
    branch: str = 'main'
    project_key: Optional[str] = None


def create_app() -> FastAPI:
    '''Build and return the Hemingway FastAPI application.'''
    app = FastAPI(title='Hemingway Documentation Agent API', version='1.0.0')

    # ------------------------------------------------------------------
    # Health & status endpoints (match Shannon expected contract)
    # ------------------------------------------------------------------

    @app.get('/v1/health')
    def health() -> Dict[str, Any]:
        return {'service': 'hemingway', 'ok': True}

    @app.get('/v1/info')
    def info() -> Dict[str, Any]:
        return {
            'agent_id': 'hemingway',
            'name': 'Hemingway Documentation Agent',
            'version': '1.1.0',
            'description': (
                'Source-grounded documentation generation, impact analysis, '
                'and review-gated publication. Supports voice/tone configuration.'
            ),
            'capabilities': [
                'Documentation generation from source files (as_built, engineering_reference, how_to, user_guide, release_note_support)',
                'Documentation impact analysis for source changes',
                'Record storage, search, and retrieval',
                'Review-gated publication to repo Markdown and Confluence',
                'PR-driven documentation generation with auto-commit',
                'Voice/tone configuration for documentation style control',
            ],
            'endpoints': [
                {'method': 'GET', 'path': '/v1/health', 'description': 'Service liveness check'},
                {'method': 'GET', 'path': '/v1/info', 'description': 'Agent identity and capabilities'},
                {'method': 'GET', 'path': '/v1/status/stats', 'description': 'Record counts and doc types'},
                {'method': 'GET', 'path': '/v1/status/load', 'description': 'Current load state'},
                {'method': 'GET', 'path': '/v1/status/work-summary', 'description': 'Docs generated today'},
                {'method': 'GET', 'path': '/v1/status/tokens', 'description': 'Token usage summary'},
                {'method': 'GET', 'path': '/v1/status/decisions', 'description': 'Recent documentation records'},
                {'method': 'GET', 'path': '/v1/status/decisions/{record_id}', 'description': 'Detail for one record'},
                {'method': 'POST', 'path': '/v1/docs/generate', 'description': 'Generate documentation from source files'},
                {'method': 'GET', 'path': '/v1/docs/records', 'description': 'List stored documentation records'},
                {'method': 'GET', 'path': '/v1/docs/record/{doc_id}', 'description': 'Get a specific record'},
                {'method': 'POST', 'path': '/v1/docs/search', 'description': 'Search documentation records'},
                {'method': 'POST', 'path': '/v1/docs/impact', 'description': 'Detect documentation impact'},
                {'method': 'POST', 'path': '/v1/docs/publish', 'description': 'Publish approved documentation'},
                {'method': 'POST', 'path': '/v1/docs/pr-review', 'description': 'PR documentation review (async)'},
                {'method': 'GET', 'path': '/v1/docs/pr-review/{job_id}', 'description': 'Poll PR review job status'},
                {'method': 'POST', 'path': '/v1/docs/confluence/publish-page', 'description': 'Publish markdown to Confluence'},
                {'method': 'GET', 'path': '/v1/config/voice', 'description': 'Get current voice configuration'},
                {'method': 'POST', 'path': '/v1/config/voice', 'description': 'Update voice configuration'},
                {'method': 'POST', 'path': '/v1/config/voice/from-file', 'description': 'Load voice personality from file/URL'},
            ],
            'shannon_commands': [
                '/generate-doc', '/impact-detect', '/doc-records', '/doc-record',
                '/publish-doc', '/search-docs', '/pr-review', '/confluence-publish',
                '/voice-config',
            ],
        }

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
                'notes': 'Hemingway uses LLM for content generation; token tracking is placeholder.',
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


    _VOICE_CONFIG_PATH = Path(os.getenv('CONFIG_DIR', 'config')) / 'hemingway' / 'voice_config.yaml'

    def _load_voice_config() -> dict:
        try:
            with open(_VOICE_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {
                'active_profile': 'default',
                'profiles': {
                    'default': {
                        'name': 'Default Engineering Voice',
                        'tone': 'professional',
                        'audience': 'engineers',
                        'purpose': 'internal engineering documentation',
                        'style_notes': 'Write clear, precise technical documentation.',
                        'personality_file': None,
                    }
                }
            }

    def _save_voice_config(config: dict) -> None:
        _VOICE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_VOICE_CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def get_active_voice_profile() -> dict:
        config = _load_voice_config()
        active = config.get('active_profile', 'default')
        return config.get('profiles', {}).get(active, {})



    # ------------------------------------------------------------------
    # Voice configuration endpoints
    # ------------------------------------------------------------------

    @app.get('/v1/config/voice')
    def get_voice_config() -> Dict[str, Any]:
        '''Get current voice configuration and available profiles.'''
        config = _load_voice_config()
        active = config.get('active_profile', 'default')
        profiles = config.get('profiles', {})
        return {
            'ok': True,
            'data': {
                'active_profile': active,
                'active_config': profiles.get(active, {}),
                'available_profiles': list(profiles.keys()),
            },
        }

    @app.post('/v1/config/voice')
    def set_voice_config(body: VoiceConfigRequest) -> Dict[str, Any]:
        '''Update voice configuration — switch profile or modify active profile fields.'''
        config = _load_voice_config()

        if body.profile_name:
            if body.profile_name not in config.get('profiles', {}):
                return {'ok': False, 'error': f'Profile not found: {body.profile_name}'}
            config['active_profile'] = body.profile_name

        active = config.get('active_profile', 'default')
        profile = config.setdefault('profiles', {}).setdefault(active, {})

        if body.tone is not None:
            profile['tone'] = body.tone
        if body.audience is not None:
            profile['audience'] = body.audience
        if body.purpose is not None:
            profile['purpose'] = body.purpose
        if body.style_notes is not None:
            profile['style_notes'] = body.style_notes

        _save_voice_config(config)
        return {'ok': True, 'data': {'active_profile': active, 'config': profile}}

    @app.post('/v1/config/voice/from-file')
    def load_voice_from_file(body: VoiceConfigFromFileRequest) -> Dict[str, Any]:
        '''Load voice personality from a file URL or local path into a new profile.'''
        content_text = ''
        source_ref = ''
        if body.file_url:
            import requests as _requests
            try:
                resp = _requests.get(body.file_url, timeout=15)
                resp.raise_for_status()
                content_text = resp.text
                source_ref = body.file_url
            except Exception as exc:
                return {'ok': False, 'error': f'Failed to fetch URL: {exc}'}
        elif body.file_path:
            try:
                with open(body.file_path, 'r', encoding='utf-8') as fh:
                    content_text = fh.read()
                source_ref = body.file_path
            except Exception as exc:
                return {'ok': False, 'error': f'Failed to read file: {exc}'}
        else:
            return {'ok': False, 'error': 'Provide file_url or file_path'}

        config = _load_voice_config()
        config.setdefault('profiles', {})[body.profile_name] = {
            'name': f'Custom: {body.profile_name}',
            'tone': 'custom',
            'audience': 'as specified in personality file',
            'purpose': 'as specified in personality file',
            'style_notes': content_text,
            'personality_file': source_ref,
        }
        config['active_profile'] = body.profile_name
        _save_voice_config(config)
        return {
            'ok': True,
            'data': {
                'profile': body.profile_name,
                'content_length': len(content_text),
                'source': source_ref,
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
            repo_name=body.repo_name,
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

        agent = HemingwayDocumentationAgent(project_key=body.project_key)

        try:
            record, review_session = agent.plan_documentation(request)
        except Exception as e:
            log.error(f'Hemingway documentation generation failed: {e}')
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
        '''List stored documentation records with human-friendly formatting.'''
        records = record_store.list_records(doc_type=doc_type, limit=limit)
        return {
            'ok': True,
            'data': records,
            'records': [_format_record_for_humans(r) for r in records],
            'total': len(records),
        }

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


    @app.post('/v1/docs/find')
    def docs_find(body: FindRequest) -> Dict[str, Any]:
        """
        Free-form search. Text can be a query, PR number, or doc type.

        Convenience wrapper around the search infrastructure that interprets
        a single text string and routes to the appropriate filter.
        """
        text = body.text.strip()

        # Detect PR reference (e.g. "#42" or "42")
        pr_match = re.match(r'#?(\d+)$', text)
        if pr_match:
            pr_num = pr_match.group(1)
            # Search all records for PR number in request metadata
            all_records = record_store.list_records(limit=200)
            matched = []
            for r in all_records:
                req = r.get('request', {})
                if isinstance(req, dict) and str(req.get('pr_number', '')) == pr_num:
                    matched.append(r)
            matched = matched[:body.limit]
            return {
                'ok': True,
                'data': {
                    'results': matched,
                    'count': len(matched),
                    'query': text,
                    'interpreted_as': f'PR #{pr_num}',
                },
                'records': [_format_record_for_humans(r) for r in matched],
                'total': len(matched),
            }

        # Detect doc type keyword
        doc_type_aliases = {
            'as_built': 'as_built',
            'as-built': 'as_built',
            'engineering_reference': 'engineering_reference',
            'engineering-reference': 'engineering_reference',
            'how_to': 'how_to',
            'how-to': 'how_to',
            'user_guide': 'user_guide',
            'user-guide': 'user_guide',
            'release_note_support': 'release_note_support',
            'release-notes': 'release_note_support',
        }
        text_lower = text.lower().replace(' ', '_')
        if text_lower in doc_type_aliases:
            doc_type_val = doc_type_aliases[text_lower]
            results = record_store.search_records(
                doc_type=doc_type_val,
                limit=body.limit,
            )
            return {
                'ok': True,
                'data': {
                    'results': results,
                    'count': len(results),
                    'query': text,
                    'interpreted_as': f'doc_type={doc_type_val}',
                },
                'records': [_format_record_for_humans(r) for r in results],
                'total': len(results),
            }

        # Default: free-text search across title, content, summary
        results = record_store.search_records(
            query=text,
            limit=body.limit,
        )
        return {
            'ok': True,
            'data': {
                'results': results,
                'count': len(results),
                'query': text,
            },
            'records': [_format_record_for_humans(r) for r in results],
            'total': len(results),
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

        agent = HemingwayDocumentationAgent(project_key=body.project_key)

        try:
            impact = agent.detect_documentation_impact(request)
        except Exception as e:
            log.error(f'Hemingway impact detection failed: {e}')
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

        agent = HemingwayDocumentationAgent(project_key=body.project_key)
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
            log.error(f'Hemingway publication failed: {e}')
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
    # PR review → doc generation → commit pipeline
    # ------------------------------------------------------------------

    # Binary / generated extensions to SKIP — everything else is doc-worthy.
    # Intent: any source code change should get documentation generated.
    _BINARY_EXTENSIONS = {
        '.o', '.so', '.a', '.dylib', '.dll', '.exe', '.bin', '.elf',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
        '.pdf', '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.jar', '.war',
        '.whl', '.egg', '.pyc', '.pyo', '.class', '.obj',
        '.ttf', '.otf', '.woff', '.woff2', '.eot',
        '.mp3', '.mp4', '.wav', '.avi', '.mov',
        '.lock',
    }
    # Files/directories to always skip regardless of extension.
    _SKIP_PATTERNS = (
        '.gitignore', '.gitattributes', '.git/',
        '.github/', '.github\\',
        'node_modules/', '__pycache__/', '.tox/',
    )

    def _is_doc_relevant(filename: str) -> bool:
        '''Return True unless the file is binary, generated, or trivial.'''
        import posixpath
        lower = filename.lower()
        # Skip known non-doc patterns
        if any(lower.endswith(p) or (p.endswith('/') and p in lower)
               for p in _SKIP_PATTERNS):
            return False
        ext = posixpath.splitext(lower)[1]
        # Skip binary / generated extensions
        return ext not in _BINARY_EXTENSIONS

    def _extract_filename(entry) -> str:
        '''Extract filename from a changed-file entry (dict or plain str).'''
        if isinstance(entry, dict):
            return str(entry.get('filename', ''))
        return str(entry)

    # ------------------------------------------------------------------
    # Async PR review — job store
    # ------------------------------------------------------------------

    _pr_review_jobs: Dict[str, Dict[str, Any]] = {}
    _pr_review_lock = threading.Lock()

    def _run_pr_review_job(job_id: str, body: PRReviewRequest) -> None:
        '''Background thread for PR doc generation.'''
        def _set_result(result: Dict[str, Any]) -> None:
            with _pr_review_lock:
                _pr_review_jobs[job_id].update({
                    'status': 'completed' if result.get('ok') else 'failed',
                    'completed_at': datetime.now(timezone.utc).isoformat(),
                    **result,
                })

        global _run_count, _last_run_at
        import posixpath
        from config.env_loader import resolve_dry_run

        dry_run = resolve_dry_run(body.dry_run)

        if '/' not in body.repo:
            _set_result({'ok': False, 'error': 'repo must be in "owner/repo" format.'})
            return
        if body.pr_number < 1:
            _set_result({'ok': False, 'error': 'pr_number must be a positive integer.'})
            return

        try:
            import github_utils
        except ImportError:
            _set_result({
                'ok': False,
                'error': (
                    'github_utils is not available. '
                    'Install the github integration package to use /pr-review.'
                ),
            })
            return

        # --- fetch PR changed files ---
        try:
            changed_files = github_utils.get_pr_changed_files(
                body.repo, body.pr_number,
            )
        except Exception as exc:
            log.error(f'GitHub API error fetching PR files: {exc}')
            _set_result({'ok': False, 'error': f'GitHub API error: {exc}'})
            return

        target_dir = body.target_dir or 'docs'
        relevant_files = [
            f for f in changed_files
            if _is_doc_relevant(_extract_filename(f))
            and not _extract_filename(f).startswith(f'{target_dir}/')
        ]

        if not relevant_files:
            _set_result({
                'ok': True,
                'data': {
                    'pr_number': body.pr_number,
                    'repo': body.repo,
                    'impact_summary': 'No doc-relevant files detected in this PR.',
                    'files_generated': [],
                    'files_committed': False,
                    'commit_sha': None,
                    'record_id': None,
                    'dry_run': dry_run,
                },
            })
            return

        # --- resolve PR head branch early (needed for source fetch) ---
        head_branch = body.branch
        if not head_branch:
            try:
                pr_info = github_utils.get_pull_request(
                    body.repo, body.pr_number,
                )
                head_branch = str(pr_info.get('head_branch', '') or '')
            except Exception as exc:
                log.error(f'GitHub API error fetching PR info: {exc}')
                _set_result({'ok': False, 'error': f'GitHub API error: {exc}'})
                return
        if not head_branch:
            _set_result({'ok': False, 'error': 'Could not determine PR head branch.'})
            return

        # --- build impact details ---
        target_dir = body.target_dir or 'docs'
        impact_details: List[Dict[str, Any]] = []
        files_planned: List[Dict[str, Any]] = []

        module_map: Dict[str, List[Dict[str, Any]]] = {}
        for entry in relevant_files:
            fname = _extract_filename(entry)
            parent = posixpath.dirname(fname) or '.'
            module_map.setdefault(parent, []).append(entry)

        for module_dir, entries in module_map.items():
            if module_dir == '.':
                repo_short = body.repo.split('/')[-1] if '/' in body.repo else body.repo
                slug = repo_short.lower().replace('_', '-').replace(' ', '-')
            else:
                slug = module_dir.lower().replace('/', '-').replace('_', '-').replace(' ', '-')
            target = f'{target_dir}/{slug}.md'
            first_entry = entries[0]
            is_readme = any(
                posixpath.basename(_extract_filename(e)).upper().startswith('README')
                for e in entries
            )
            doc_type = 'user_guide' if is_readme else 'as_built'

            source_names = [_extract_filename(e) for e in entries]
            detail = {
                'source': ', '.join(source_names),
                'status': first_entry.get('status', 'unknown') if isinstance(first_entry, dict) else 'unknown',
                'additions': sum(e.get('additions', 0) for e in entries if isinstance(e, dict)),
                'deletions': sum(e.get('deletions', 0) for e in entries if isinstance(e, dict)),
                'doc_type': doc_type,
                'target': target,
            }
            impact_details.append(detail)
            files_planned.append({
                'source': ', '.join(source_names),
                'target': target,
                'doc_type': doc_type,
            })

        # --- Phase 1 & 2: generate one doc per module directory ---
        all_generated: List[Dict[str, Any]] = []
        generated_docs: List[Dict[str, Any]] = []
        files_to_commit: Dict[str, str] = {}
        record_ids: List[str] = []

        for module_dir, entries in module_map.items():
            if module_dir == '.':
                repo_short = body.repo.split('/')[-1] if '/' in body.repo else body.repo
                slug = repo_short.lower().replace('_', '-').replace(' ', '-')
                title_label = repo_short.replace('_', ' ').replace('-', ' ').title()
            else:
                slug = module_dir.lower().replace('/', '-').replace('_', '-').replace(' ', '-')
                title_label = posixpath.basename(module_dir).replace('_', ' ').replace('-', ' ').title()

            is_readme = any(
                posixpath.basename(_extract_filename(e)).upper().startswith('README')
                for e in entries
            )
            doc_type = 'user_guide' if is_readme else 'as_built'
            target_file = f'{target_dir}/{slug}.md'

            if body.doc_types and doc_type not in body.doc_types:
                continue

            changed_names = [_extract_filename(e) for e in entries]
            if module_dir == '.':
                source_paths_for_agent = ['/']
            else:
                source_paths_for_agent = [module_dir + '/']

            patch_parts = []
            for e in entries:
                if isinstance(e, dict) and e.get('patch'):
                    patch_parts.append(f'--- {_extract_filename(e)} ---\n{e["patch"]}')
            patch_text = '\n'.join(patch_parts)

            doc_request = DocumentationRequest(
                title=f'{title_label} — Design Reference',
                doc_type=doc_type,
                repo_name=body.repo,
                source_paths=source_paths_for_agent,
                target_file=target_file,
                diff_context=patch_text,
                branch=head_branch,
                pr_number=body.pr_number,
            )

            agent = HemingwayDocumentationAgent()
            try:
                result = agent.run(doc_request)
            except Exception as exc:
                log.error(f'Hemingway agent run failed for {module_dir}: {exc}')
                continue

            if not result.success:
                log.warning(f'Hemingway agent returned error for {module_dir}: {result.error}')
                continue

            doc_record_dict = (result.metadata or {}).get('documentation_record', {})
            patches = doc_record_dict.get('patches', [])
            for patch in patches:
                if patch.get('target_type') == 'repo_markdown':
                    p_target = patch.get('target_ref', target_file)
                    p_content = patch.get('content_markdown', '')
                    if p_content:
                        files_to_commit[p_target] = p_content
                        all_generated.append({
                            'path': p_target,
                            'operation': patch.get('operation', 'create'),
                        })
                        record_id = doc_record_dict.get('doc_id', '')
                        generated_docs.append({
                            'path': p_target,
                            'title': doc_record_dict.get('title', ''),
                            'content': p_content,
                            'content_preview': p_content[:500],
                            'content_length': len(p_content),
                            'record_id': record_id,
                        })

            record_id = doc_record_dict.get('doc_id', '')
            if doc_record_dict:
                try:
                    record_obj = DocumentationRecord(
                        title=doc_record_dict.get('title', ''),
                        doc_type=doc_record_dict.get('doc_type', ''),
                        project_key=doc_record_dict.get('project_key', ''),
                        doc_id=record_id,
                        created_at=doc_record_dict.get('created_at', ''),
                        request=doc_record_dict.get('request', {}),
                        impact=doc_record_dict.get('impact', {}),
                        source_refs=doc_record_dict.get('source_refs', []),
                        evidence_summary=doc_record_dict.get('evidence_summary', {}),
                        content_markdown=doc_record_dict.get('content_markdown', ''),
                        summary_markdown=doc_record_dict.get('summary_markdown', ''),
                        validation=doc_record_dict.get('validation', {}),
                        warnings=doc_record_dict.get('warnings', []),
                        confidence=doc_record_dict.get('confidence', 'medium'),
                        metadata=doc_record_dict.get('metadata', {}),
                    )
                    record_store.save_record(record_obj)
                    if record_id:
                        record_ids.append(record_id)
                except Exception as exc:
                    log.warning(f'Failed to save Hemingway record for {fname}: {exc}')

        # --- Phase 2 only: commit generated files to PR branch ---
        commit_sha: Optional[str] = None
        files_committed = False

        if not dry_run and files_to_commit:
            try:
                commit_result = github_utils.batch_commit_files(
                    body.repo,
                    files_to_commit,
                    f'docs: auto-generate documentation for PR #{body.pr_number} [skip ci]',
                    head_branch,
                    dry_run=False,
                )
                commit_sha = str(commit_result.get('commit_sha', '')) if isinstance(commit_result, dict) else str(commit_result)
                files_committed = True
            except Exception as exc:
                log.error(f'GitHub commit failed: {exc}')
                _set_result({'ok': False, 'error': f'GitHub commit failed: {exc}'})
                return

            if commit_sha and files_committed:
                try:
                    github_utils.post_commit_status(
                        body.repo, commit_sha, 'pending',
                        context='hemingway/documentation',
                        description=f'{len(all_generated)} doc(s) generated — review required',
                    )
                except Exception as exc:
                    log.warning(f'Failed to set commit status: {exc}')

        # --- Persist lightweight metadata records post-commit ---
        # Update existing records with commit destination metadata so they
        # are discoverable by PR URL, file URL, and commit SHA.
        if commit_sha and files_committed:
            pr_url = f'https://github.com/{body.repo}/pull/{body.pr_number}'
            for doc in generated_docs:
                rec_id = doc.get('record_id', '')
                doc_path = doc.get('path', '')
                if rec_id:
                    try:
                        stored = record_store.get_record(rec_id)
                        if stored and stored.get('record'):
                            rec_data = stored['record']
                            # Enrich metadata with destination info
                            meta = dict(rec_data.get('metadata', {}) or {})
                            meta['source_type'] = 'pr_review'
                            meta['pr_url'] = pr_url
                            meta['file_url'] = f'https://github.com/{body.repo}/blob/{head_branch}/{doc_path}'
                            meta['commit_sha'] = commit_sha
                            meta['generated_at'] = datetime.now(timezone.utc).isoformat()
                            rec_data['metadata'] = meta
                            # Tag the request with source origin
                            req = dict(rec_data.get('request', {}) or {})
                            req['source'] = f'PR #{body.pr_number}'
                            req['pr_number'] = body.pr_number
                            req['repo_name'] = body.repo
                            req['branch'] = head_branch
                            req['target_file'] = doc_path
                            rec_data['request'] = req
                            # Clear full content — doc lives in git now
                            rec_data['content_markdown'] = ''
                            record_store.save_record(rec_data, summary_markdown=stored.get('summary_markdown', ''))
                            log.info(f'Updated record {rec_id} with commit metadata (sha={commit_sha[:8]})')
                    except Exception as exc:
                        log.warning(f'Failed to update record {rec_id} with commit metadata: {exc}')

        for doc in generated_docs:
            rec_id = doc.get('record_id', '')
            if rec_id:
                try:
                    rec = record_store.get_record(rec_id)
                    if rec:
                        doc['content'] = rec.get('record', {}).get('content_markdown', '')
                except Exception:
                    pass

        _run_count += 1
        _last_run_at = datetime.now(timezone.utc).isoformat()

        impact_summary = (
            f'{len(relevant_files)} doc-relevant file(s) detected, '
            f'{len(all_generated)} doc(s) generated'
        )

        _set_result({
            'ok': True,
            'data': {
                'pr_number': body.pr_number,
                'repo': body.repo,
                'head_branch': head_branch,
                'dry_run': dry_run,
                'impact_summary': impact_summary,
                'impact_details': impact_details,
                'generated_docs': generated_docs,
                'files_generated': all_generated,
                'files_planned': files_planned,
                'files_committed': files_committed,
                'commit_sha': commit_sha,
                'record_ids': record_ids,
                'record_id': record_ids[-1] if record_ids else None,
            },
        })

    @app.post('/v1/docs/pr-review')
    def docs_pr_review_submit(body: PRReviewRequest) -> Dict[str, Any]:
        job_id = uuid.uuid4().hex[:12]
        with _pr_review_lock:
            _pr_review_jobs[job_id] = {
                'status': 'running',
                'started_at': datetime.now(timezone.utc).isoformat(),
            }
        t = threading.Thread(target=_run_pr_review_job, args=(job_id, body), daemon=True)
        t.start()
        return {
            'ok': True,
            'job_id': job_id,
            'status': 'running',
            'poll_url': f'/v1/docs/pr-review/{job_id}',
        }

    @app.get('/v1/docs/pr-review/{job_id}')
    def docs_pr_review_status(job_id: str) -> Dict[str, Any]:
        with _pr_review_lock:
            job = _pr_review_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f'Job {job_id} not found.')
        return {
            'ok': job.get('ok', True),
            'job_id': job_id,
            'status': job.get('status', 'unknown'),
            'started_at': job.get('started_at'),
            'completed_at': job.get('completed_at'),
            'data': job.get('data'),
            'error': job.get('error'),
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


    # ------------------------------------------------------------------
    # Natural language query endpoint
    # ------------------------------------------------------------------

    @app.post("/v1/nl/query")
    def nl_query(body: NLQueryRequest) -> Dict[str, Any]:
        try:
            from agents.hemingway.nl_query import run_nl_query
            result = run_nl_query(query=body.query)
            return result
        except Exception as e:
            log.error(f"NL query failed: {e}")
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Re-index existing docs from a GitHub repo
    # ------------------------------------------------------------------

    @app.post('/v1/docs/reindex')
    def docs_reindex(body: ReindexRequest) -> Dict[str, Any]:
        """
        Scan a GitHub repo's docs/ folder and create lightweight metadata
        records for each .md file.  Skips files already indexed (matched by
        target_file path in the request field).

        Does NOT store full content — only metadata for discovery.
        """
        import requests as http_requests

        gh_token = os.getenv('GITHUB_TOKEN', '')
        if not gh_token:
            # Fallback: try github_utils credential loader (same as PR review)
            try:
                import github_utils
                gh_token = github_utils.get_github_credentials()
            except Exception:
                pass
        # Token is optional — public repos work without auth

        if '/' not in body.repo:
            raise HTTPException(status_code=400, detail='repo must be in "owner/repo" format.')

        headers = {'Accept': 'application/vnd.github.v3+json'}
        if gh_token:
            headers['Authorization'] = f'token {gh_token}'

        # --- List files in docs_dir via GitHub Contents API ---
        api_url = f'https://api.github.com/repos/{body.repo}/contents/{body.docs_dir}'
        params = {'ref': body.branch}
        try:
            resp = http_requests.get(api_url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
        except Exception as exc:
            return {'ok': False, 'error': f'GitHub API error listing {body.docs_dir}/: {exc}'}

        entries = resp.json()
        if not isinstance(entries, list):
            return {'ok': False, 'error': f'{body.docs_dir}/ is not a directory or is empty.'}

        md_files = [e for e in entries if isinstance(e, dict) and str(e.get('name', '')).endswith('.md')]

        # --- Check which files are already indexed ---
        existing_records = record_store.search_records(limit=500)
        indexed_paths: set = set()
        for rec in existing_records:
            stored = record_store.get_record(rec.get('doc_id', ''))
            if stored and stored.get('record'):
                req = stored['record'].get('request', {})
                tf = req.get('target_file', '')
                if tf:
                    indexed_paths.add(tf)

        indexed_count = 0
        skipped_count = 0
        errors: List[str] = []

        for entry in md_files:
            file_path = entry.get('path', '')
            file_name = entry.get('name', '')
            download_url = entry.get('download_url', '')

            # Skip if already indexed
            if file_path in indexed_paths:
                skipped_count += 1
                continue

            # Fetch first 2KB to extract H1 title
            title = file_name.replace('.md', '').replace('-', ' ').replace('_', ' ').title()
            summary_text = ''
            if download_url:
                try:
                    dl_resp = http_requests.get(download_url, headers=headers, timeout=15)
                    dl_resp.raise_for_status()
                    raw_text = dl_resp.text[:2048]
                    # Extract H1 title
                    h1_match = re.match(r'^#\s+(.+)', raw_text, re.MULTILINE)
                    if h1_match:
                        title = h1_match.group(1).strip()
                    # Extract first paragraph as summary
                    lines = raw_text.split('\n')
                    para_lines = []
                    started = False
                    for line in lines:
                        stripped = line.strip()
                        if not started and stripped and not stripped.startswith('#'):
                            started = True
                        if started:
                            if not stripped:
                                break
                            para_lines.append(stripped)
                    summary_text = ' '.join(para_lines)[:300]
                except Exception:
                    pass

            file_url = f'https://github.com/{body.repo}/blob/{body.branch}/{file_path}'

            record = DocumentationRecord(
                doc_id=str(uuid.uuid4())[:8],
                title=title,
                doc_type='as_built',
                project_key=body.project_key or '',
                created_at=datetime.now(timezone.utc).isoformat(),
                request={
                    'repo_name': body.repo,
                    'branch': body.branch,
                    'target_file': file_path,
                    'source': 'Repository',
                },
                impact={},
                source_refs=[],
                evidence_summary={},
                content_markdown='',
                summary_markdown=summary_text,
                patches=[],
                validation={},
                warnings=[],
                confidence='high',
                metadata={
                    'source_type': 'reindex',
                    'file_url': file_url,
                    'indexed_at': datetime.now(timezone.utc).isoformat(),
                },
            )
            try:
                record_store.save_record(record)
                indexed_count += 1
            except Exception as exc:
                errors.append(f'{file_path}: {exc}')

        return {
            'ok': True,
            'data': {
                'repo': body.repo,
                'branch': body.branch,
                'docs_dir': body.docs_dir,
                'files_found': len(md_files),
                'indexed': indexed_count,
                'skipped': skipped_count,
                'errors': errors,
            },
        }

    return app


# ---------------------------------------------------------------------------
# Module-level app + CLI runner
# ---------------------------------------------------------------------------

app = create_app()


def run() -> None:
    import uvicorn
    host = str(os.getenv('HEMINGWAY_HOST', '0.0.0.0') or '0.0.0.0').strip()
    port = int(os.getenv('HEMINGWAY_PORT', '8203') or '8203')
    uvicorn.run('agents.hemingway.api:app', host=host, port=port, log_level='info')


if __name__ == '__main__':
    run()
