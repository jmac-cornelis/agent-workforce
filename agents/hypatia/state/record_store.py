##########################################################################################
#
# Module: state/hypatia_record_store.py
#
# Description: Persistence helpers for Hypatia documentation records.
#              Stores durable JSON + Markdown artifacts plus publication history.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.hypatia.models import DocumentationRecord, PublicationRecord

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class HypatiaRecordStore:
    '''
    JSON + Markdown persistence for Hypatia documentation records.

    Records are stored at:
        data/hypatia_docs/<DOC_ID>/record.json
        data/hypatia_docs/<DOC_ID>/summary.md
    '''

    def __init__(self, storage_dir: Optional[str] = None):
        env_dir = os.getenv('HYPATIA_DOC_DIR')
        resolved_dir = storage_dir or env_dir or 'data/hypatia_docs'
        self.storage_dir = Path(resolved_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        log.debug(f'HypatiaRecordStore initialized: {self.storage_dir}')

    def save_record(
        self,
        record: DocumentationRecord | Dict[str, Any],
        summary_markdown: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Persist a documentation record and return a summary record.
        '''
        if isinstance(record, DocumentationRecord):
            record_data = record.to_dict()
            if summary_markdown is None:
                summary_markdown = record.summary_markdown
        else:
            record_data = dict(record)

        doc_id = str(record_data.get('doc_id') or '').strip()
        if not doc_id:
            raise ValueError('Documentation record is missing doc_id')

        record_dir = self.storage_dir / doc_id
        record_dir.mkdir(parents=True, exist_ok=True)

        json_path = record_dir / 'record.json'
        markdown_path = record_dir / 'summary.md'

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(record_data, f, indent=2, default=str)

        markdown_text = summary_markdown
        if markdown_text is None:
            markdown_text = str(record_data.get('summary_markdown') or '')

        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        summary = self._build_summary(record_data, json_path, markdown_path)
        log.info(f'Saved Hypatia documentation record {doc_id} to {record_dir}')
        return summary

    def get_record(self, doc_id: str) -> Optional[Dict[str, Any]]:
        '''
        Load a stored documentation record by ID.
        '''
        json_path = self.storage_dir / str(doc_id).strip() / 'record.json'
        if not json_path.exists():
            return None

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                record_data = json.load(f)
        except Exception as e:
            log.error(f'Failed to load Hypatia record {doc_id}: {e}')
            return None

        markdown_path = json_path.parent / 'summary.md'
        summary_markdown = ''
        if markdown_path.exists():
            try:
                summary_markdown = markdown_path.read_text(encoding='utf-8')
            except Exception as e:
                log.warning(f'Failed to read Hypatia summary markdown {markdown_path}: {e}')

        return {
            'record': record_data,
            'summary_markdown': summary_markdown,
            'summary': self._build_summary(record_data, json_path, markdown_path),
        }

    def list_records(
        self,
        doc_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        '''
        List stored documentation records, optionally filtered by doc type.
        '''
        summaries: List[Dict[str, Any]] = []

        for json_path in sorted(self.storage_dir.glob('*/record.json')):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    record_data = json.load(f)
            except Exception as e:
                log.warning(f'Skipping unreadable Hypatia record {json_path}: {e}')
                continue

            if doc_type and str(record_data.get('doc_type') or '') != doc_type:
                continue

            summaries.append(
                self._build_summary(
                    record_data,
                    json_path,
                    json_path.parent / 'summary.md',
                )
            )

        summaries.sort(
            key=lambda item: (
                self._sort_timestamp(item.get('created_at')),
                str(item.get('doc_id') or ''),
            ),
            reverse=True,
        )

        if limit is not None and limit >= 0:
            summaries = summaries[:limit]

        return summaries

    def search_records(
        self,
        query: Optional[str] = None,
        project_key: Optional[str] = None,
        doc_type: Optional[str] = None,
        source_ref: Optional[str] = None,
        published_only: bool = False,
        confidence: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        '''
        Search stored documentation records with multi-field filtering.

        Filters:
          - query: case-insensitive substring match on title, content_markdown,
                   and summary_markdown
          - project_key: exact match
          - doc_type: exact match
          - source_ref: substring match against any item in source_refs list
          - published_only: requires at least one publication with status='published'
          - confidence: exact match
        '''
        results: List[Dict[str, Any]] = []

        for json_path in sorted(self.storage_dir.glob('*/record.json')):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    record_data = json.load(f)
            except Exception as e:
                log.warning(f'Skipping unreadable Hypatia record {json_path}: {e}')
                continue

            if project_key and str(record_data.get('project_key') or '') != project_key:
                continue
            if doc_type and str(record_data.get('doc_type') or '') != doc_type:
                continue
            if confidence and str(record_data.get('confidence') or '') != confidence:
                continue

            if source_ref:
                refs = record_data.get('source_refs') or []
                if not any(source_ref in str(ref) for ref in refs):
                    continue

            if published_only:
                publications = record_data.get('publication_records') or []
                if not any(
                    str(pub.get('status') or '') == 'published'
                    for pub in publications
                ):
                    continue

            match_context = ''
            if query:
                q_lower = query.lower()
                title_text = str(record_data.get('title') or '')
                content_text = str(record_data.get('content_markdown') or '')
                summary_text = str(record_data.get('summary_markdown') or '')
                combined = f'{title_text} {content_text} {summary_text}'
                if q_lower not in combined.lower():
                    continue
                for field_text in (title_text, content_text, summary_text):
                    if q_lower in field_text.lower():
                        match_context = field_text[:200]
                        break

            summary = self._build_summary(
                record_data,
                json_path,
                json_path.parent / 'summary.md',
            )
            if query:
                summary['match_context'] = match_context
            results.append(summary)

        results.sort(
            key=lambda item: (
                self._sort_timestamp(item.get('created_at')),
                str(item.get('doc_id') or ''),
            ),
            reverse=True,
        )

        if limit is not None and limit >= 0:
            results = results[:limit]

        return results

    def record_publications(
        self,
        doc_id: str,
        publications: List[PublicationRecord | Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        '''
        Append publication records to an existing stored documentation record.
        '''
        stored = self.get_record(doc_id)
        if stored is None:
            return None

        record_data = stored['record']
        existing = list(record_data.get('publication_records') or [])
        for publication in publications:
            if isinstance(publication, PublicationRecord):
                existing.append(publication.to_dict())
            else:
                existing.append(dict(publication))

        record_data['publication_records'] = existing
        return self.save_record(record_data, summary_markdown=stored['summary_markdown'])

    @staticmethod
    def _build_summary(
        record_data: Dict[str, Any],
        json_path: Path,
        markdown_path: Path,
    ) -> Dict[str, Any]:
        patches = record_data.get('patches') or []
        publications = record_data.get('publication_records') or []

        return {
            'doc_id': str(record_data.get('doc_id') or ''),
            'title': str(record_data.get('title') or ''),
            'doc_type': str(record_data.get('doc_type') or ''),
            'project_key': str(record_data.get('project_key') or ''),
            'created_at': str(record_data.get('created_at') or ''),
            'patch_count': len(patches),
            'warning_count': len(record_data.get('warnings') or []),
            'publication_count': len(publications),
            'published_count': sum(
                1 for publication in publications
                if str(publication.get('status') or '') == 'published'
            ),
            'storage_dir': str(json_path.parent),
            'json_path': str(json_path),
            'markdown_path': str(markdown_path),
        }

    @staticmethod
    def _sort_timestamp(value: Any) -> datetime:
        raw = str(value or '').strip()
        if not raw:
            return datetime.min

        try:
            if raw.endswith('Z'):
                raw = raw[:-1] + '+00:00'
            return datetime.fromisoformat(raw)
        except ValueError:
            return datetime.min
