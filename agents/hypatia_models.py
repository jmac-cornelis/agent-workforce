##########################################################################################
#
# Module: agents/hypatia_models.py
#
# Description: Data models for the Hypatia Documentation agent.
#              Defines documentation requests, impact records, candidate patches,
#              durable document records, and publication records.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


DOC_TYPES = {
    'as_built',
    'engineering_reference',
    'how_to',
    'release_note_support',
    'user_guide',
}


@dataclass
class DocumentationRequest:
    '''
    Input request for generating a Hypatia documentation record.
    '''
    title: str = ''
    doc_type: str = 'engineering_reference'
    project_key: str = ''
    summary: str = ''
    source_paths: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)
    target_file: Optional[str] = None
    confluence_title: Optional[str] = None
    confluence_page: Optional[str] = None
    confluence_space: Optional[str] = None
    confluence_parent_id: Optional[str] = None
    version_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'doc_type': self.doc_type,
            'project_key': self.project_key,
            'summary': self.summary,
            'source_paths': self.source_paths,
            'source_refs': self.source_refs,
            'target_file': self.target_file,
            'confluence_title': self.confluence_title,
            'confluence_page': self.confluence_page,
            'confluence_space': self.confluence_space,
            'confluence_parent_id': self.confluence_parent_id,
            'version_message': self.version_message,
        }


@dataclass
class DocumentationImpactRecord:
    '''
    Documentation-impact summary describing affected targets and blockers.
    '''
    impact_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    title: str = ''
    doc_type: str = 'engineering_reference'
    affected_targets: List[Dict[str, Any]] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    confidence: str = 'medium'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'impact_id': self.impact_id,
            'created_at': self.created_at,
            'title': self.title,
            'doc_type': self.doc_type,
            'affected_targets': self.affected_targets,
            'reasons': self.reasons,
            'source_refs': self.source_refs,
            'warnings': self.warnings,
            'blocking_issues': self.blocking_issues,
            'confidence': self.confidence,
        }


@dataclass
class DocumentationPatch:
    '''
    Candidate documentation patch for an internal publication target.
    '''
    patch_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    target_type: str = 'repo_markdown'
    operation: str = 'create'
    title: str = ''
    target_ref: str = ''
    content_markdown: str = ''
    preview: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    source_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'patch_id': self.patch_id,
            'target_type': self.target_type,
            'operation': self.operation,
            'title': self.title,
            'target_ref': self.target_ref,
            'content_markdown': self.content_markdown,
            'preview': self.preview,
            'validation': self.validation,
            'source_refs': self.source_refs,
            'metadata': self.metadata,
        }


@dataclass
class PublicationRecord:
    '''
    Result of publishing an approved documentation patch.
    '''
    publication_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    doc_id: str = ''
    patch_id: str = ''
    title: str = ''
    target_type: str = ''
    operation: str = ''
    target_ref: str = ''
    status: str = 'pending'
    published_at: str = ''
    result: Dict[str, Any] = field(default_factory=dict)
    error: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'publication_id': self.publication_id,
            'doc_id': self.doc_id,
            'patch_id': self.patch_id,
            'title': self.title,
            'target_type': self.target_type,
            'operation': self.operation,
            'target_ref': self.target_ref,
            'status': self.status,
            'published_at': self.published_at,
            'result': self.result,
            'error': self.error,
        }


@dataclass
class DocumentationRecord:
    '''
    Durable documentation record produced by Hypatia.
    '''
    title: str = ''
    doc_type: str = 'engineering_reference'
    project_key: str = ''
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    request: Dict[str, Any] = field(default_factory=dict)
    impact: Dict[str, Any] = field(default_factory=dict)
    source_refs: List[str] = field(default_factory=list)
    content_markdown: str = ''
    summary_markdown: str = ''
    patches: List[DocumentationPatch] = field(default_factory=list)
    validation: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    confidence: str = 'medium'
    metadata: Dict[str, Any] = field(default_factory=dict)
    publication_records: List[PublicationRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'doc_id': self.doc_id,
            'title': self.title,
            'doc_type': self.doc_type,
            'project_key': self.project_key,
            'created_at': self.created_at,
            'request': self.request,
            'impact': self.impact,
            'source_refs': self.source_refs,
            'content_markdown': self.content_markdown,
            'summary_markdown': self.summary_markdown,
            'patches': [patch.to_dict() for patch in self.patches],
            'validation': self.validation,
            'warnings': self.warnings,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'publication_records': [
                publication.to_dict() for publication in self.publication_records
            ],
        }
