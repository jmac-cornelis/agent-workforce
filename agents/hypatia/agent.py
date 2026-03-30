##########################################################################################
#
# Module: agents/hypatia_agent.py
#
# Description: Hypatia Documentation agent.
#              Produces documentation-impact analysis, source-grounded internal
#              documentation records, and review-gated publication plans for
#              repo Markdown and Confluence targets.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agents.base import BaseAgent, AgentConfig, AgentResponse
from agents.hypatia.models import (
    DOC_TYPES,
    DocumentationImpactRecord,
    DocumentationPatch,
    DocumentationRecord,
    DocumentationRequest,
    PublicationRecord,
)
from agents.review_agent import ReviewAgent, ReviewItem, ReviewSession
from core.evidence import EvidenceBundle, load_evidence_bundle
from tools.confluence_tools import (
    create_confluence_page,
    get_confluence_page,
    update_confluence_page,
)
from tools.file_tools import read_file

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


VALIDATION_PROFILES = {'default', 'strict', 'sphinx'}


class HypatiaDocumentationAgent(BaseAgent):
    '''
    Deterministic-first documentation coordinator.

    Hypatia analyzes documentation impact, synthesizes source-backed internal
    documentation, stages repo/Confluence publication patches, and hands
    publication off through review-gated execution paths.
    '''

    def __init__(self, project_key: Optional[str] = None, **kwargs):
        instruction = self._load_prompt_file()
        if not instruction:
            raise FileNotFoundError(
                'agents/hypatia/prompts/system.md is required but not found. '
                'The Hypatia Documentation Agent has no hardcoded fallback prompt.'
            )

        config = AgentConfig(
            name='hypatia_documentation',
            description='Coordinates source-grounded documentation generation and publication',
            instruction=instruction,
            max_iterations=12,
        )

        super().__init__(config=config, tools=[], **kwargs)
        self.project_key = project_key
        self._review_agent: Optional[ReviewAgent] = None

    @staticmethod
    def _load_prompt_file() -> Optional[str]:
        prompt_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'prompts', 'system.md'
        )
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                log.warning(f'Failed to load Hypatia agent prompt: {e}')
        return None

    @property
    def review_agent(self) -> ReviewAgent:
        if self._review_agent is None:
            self._review_agent = ReviewAgent()
        return self._review_agent

    def run(self, input_data: Any) -> AgentResponse:
        '''
        Build a documentation record and corresponding review session.
        '''
        log.debug(f'HypatiaDocumentationAgent.run(input_data={input_data})')

        try:
            request = self._normalize_request(input_data)
        except Exception as e:
            return AgentResponse.error_response(str(e))

        try:
            record, review_session = self.plan_documentation(request)
        except Exception as e:
            log.error(f'Hypatia documentation generation failed: {e}')
            return AgentResponse.error_response(str(e))

        return AgentResponse.success_response(
            content=record.summary_markdown,
            metadata={
                'documentation_record': record.to_dict(),
                'review_session': review_session.to_dict(),
            },
        )

    def plan_documentation(
        self,
        request: DocumentationRequest,
    ) -> Tuple[DocumentationRecord, ReviewSession]:
        '''
        Produce a documentation record and review-gated publication session.
        '''
        impact = self.detect_documentation_impact(request)
        evidence_bundle = load_evidence_bundle(request.evidence_paths)
        source_materials, existing_targets = self._load_authoritative_inputs(request)
        source_refs = self._merge_source_refs(request, source_materials, evidence_bundle)
        content_markdown = self._generate_content(
            request,
            impact,
            source_materials,
            existing_targets,
            evidence_bundle,
        )
        patches = self._build_patches(request, impact, content_markdown, source_refs)
        validation, validation_warnings, confidence = self._validate_patches(
            request,
            patches,
            evidence_bundle,
            source_refs,
        )
        warnings = list(impact.warnings) + [
            warning for warning in validation_warnings
            if warning not in impact.warnings
        ]
        warnings.extend(
            warning for warning in evidence_bundle.warnings
            if warning not in warnings
        )
        if impact.blocking_issues:
            validation['blocking_issues'] = list(validation.get('blocking_issues') or []) + [
                blocker for blocker in impact.blocking_issues
                if blocker not in (validation.get('blocking_issues') or [])
            ]
            validation['valid'] = False
            if confidence != 'low':
                confidence = 'low'
        summary_markdown = self._format_record_summary(
            request,
            impact,
            patches,
            validation,
            warnings,
            confidence,
        )

        record = DocumentationRecord(
            title=request.title or self._derive_title(request),
            doc_type=request.doc_type,
            project_key=request.project_key,
            request=request.to_dict(),
            impact=impact.to_dict(),
            source_refs=source_refs,
            evidence_summary=evidence_bundle.to_summary(),
            content_markdown=content_markdown,
            summary_markdown=summary_markdown,
            patches=patches,
            validation=validation,
            warnings=warnings,
            confidence=confidence,
            metadata={
                'source_materials': source_materials,
                'existing_targets': existing_targets,
                'evidence_bundle': evidence_bundle.to_dict(),
            },
        )
        review_session = self.create_review_session(record)
        return record, review_session

    def detect_documentation_impact(
        self,
        request: DocumentationRequest,
    ) -> DocumentationImpactRecord:
        '''
        Determine which internal documentation targets are affected.
        '''
        affected_targets: List[Dict[str, Any]] = []
        reasons: List[str] = []
        warnings: List[str] = []
        blocking_issues: List[str] = []

        title = request.title or self._derive_title(request)

        repo_target = request.target_file or self._default_target_file(title)
        repo_operation = 'update' if Path(repo_target).exists() else 'create'
        affected_targets.append({
            'target_type': 'repo_markdown',
            'operation': repo_operation,
            'target_ref': repo_target,
        })
        reasons.append(
            f'Repo-owned internal documentation target resolved to {repo_target}.'
        )

        confluence_operation = ''
        confluence_target_ref = ''
        if request.confluence_page or request.confluence_title:
            if request.confluence_page:
                confluence_operation = 'update'
                confluence_target_ref = request.confluence_page
                reasons.append(
                    f'Confluence update target resolved to {request.confluence_page}.'
                )
            else:
                confluence_operation = 'create'
                confluence_target_ref = request.confluence_title or title
                reasons.append(
                    f'Confluence create target resolved to title "{confluence_target_ref}".'
                )

            affected_targets.append({
                'target_type': 'confluence_page',
                'operation': confluence_operation,
                'target_ref': confluence_target_ref,
                'space': request.confluence_space or '',
            })

            if confluence_operation == 'create' and not request.confluence_space:
                blocking_issues.append(
                    'Confluence page creation requires --confluence-space.'
                )

        if not request.source_paths and not request.source_refs and not request.summary:
            warnings.append(
                'No source files or source references were supplied; output will be low confidence.'
            )

        confidence = 'low' if warnings else 'medium'
        if blocking_issues:
            confidence = 'low'

        return DocumentationImpactRecord(
            title=title,
            doc_type=request.doc_type,
            affected_targets=affected_targets,
            reasons=reasons,
            source_refs=self._merge_source_refs(request, []),
            warnings=warnings,
            blocking_issues=blocking_issues,
            confidence=confidence,
        )

    def create_review_session(self, record: DocumentationRecord) -> ReviewSession:
        '''
        Convert Hypatia patches into a review-gated publication session.
        '''
        session = ReviewSession(
            session_id=record.doc_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        for patch in record.patches:
            if patch.target_type == 'repo_markdown':
                session.add_item(ReviewItem(
                    id=patch.patch_id,
                    item_type='document',
                    action='write',
                    data={
                        'doc_id': record.doc_id,
                        'patch_id': patch.patch_id,
                        'title': patch.title,
                        'doc_type': record.doc_type,
                        'file_path': patch.target_ref,
                        'content': patch.content_markdown,
                        'source_refs': patch.source_refs,
                        'preview': patch.preview,
                    },
                ))
                continue

            if patch.target_type == 'confluence_page':
                session.add_item(ReviewItem(
                    id=patch.patch_id,
                    item_type='confluence_page',
                    action=patch.operation,
                    data={
                        'doc_id': record.doc_id,
                        'patch_id': patch.patch_id,
                        'title': patch.title,
                        'page_id_or_title': patch.metadata.get('page_id_or_title', ''),
                        'space': patch.metadata.get('space'),
                        'parent_id': patch.metadata.get('parent_id'),
                        'version_message': patch.metadata.get('version_message'),
                        'content': patch.content_markdown,
                        'preview': patch.preview,
                        'source_refs': patch.source_refs,
                    },
                ))

        return session

    def publish_approved(
        self,
        session: ReviewSession,
    ) -> List[PublicationRecord]:
        '''
        Publish already-approved Hypatia actions through the shared ReviewAgent.
        '''
        item_lookup = {item.id: item for item in session.items}
        results = self.review_agent.execute_approved(session)
        publications: List[PublicationRecord] = []

        for result in results:
            item_id = str(result.get('item_id') or '')
            item = item_lookup.get(item_id)
            effective_data = item.get_effective_data() if item else {}
            success = bool(result.get('success'))
            publications.append(PublicationRecord(
                doc_id=str(effective_data.get('doc_id') or session.session_id),
                patch_id=str(effective_data.get('patch_id') or item_id),
                title=str(effective_data.get('title') or ''),
                target_type=str(item.item_type if item else ''),
                operation=str(item.action if item else ''),
                target_ref=str(
                    effective_data.get('file_path')
                    or effective_data.get('page_id_or_title')
                    or effective_data.get('title')
                    or ''
                ),
                status='published' if success else 'failed',
                published_at=datetime.now(timezone.utc).isoformat(),
                result=result.get('data') or {},
                error='' if success else str(result.get('error') or ''),
            ))

        return publications

    def _normalize_request(self, input_data: Any) -> DocumentationRequest:
        if isinstance(input_data, DocumentationRequest):
            request = input_data
        elif isinstance(input_data, dict):
            request = DocumentationRequest(
                title=str(input_data.get('title') or '').strip(),
                doc_type=str(
                    input_data.get('doc_type') or 'engineering_reference'
                ).strip() or 'engineering_reference',
                project_key=str(
                    input_data.get('project_key') or self.project_key or ''
                ).strip(),
                summary=str(input_data.get('summary') or '').strip(),
                source_paths=[
                    str(path) for path in (input_data.get('source_paths') or [])
                ],
                source_refs=[
                    str(ref) for ref in (input_data.get('source_refs') or [])
                ],
                evidence_paths=[
                    str(path) for path in (input_data.get('evidence_paths') or [])
                ],
                target_file=input_data.get('target_file'),
                confluence_title=input_data.get('confluence_title'),
                confluence_page=input_data.get('confluence_page'),
                confluence_space=input_data.get('confluence_space'),
                confluence_parent_id=input_data.get('confluence_parent_id'),
                version_message=input_data.get('version_message'),
                validation_profile=str(
                    input_data.get('validation_profile') or 'default'
                ).strip() or 'default',
            )
        elif isinstance(input_data, str):
            request = DocumentationRequest(
                title=input_data.strip(),
                project_key=self.project_key or '',
            )
        else:
            raise ValueError(
                'Invalid input: expected DocumentationRequest, dict, or title string'
            )

        if request.doc_type not in DOC_TYPES:
            raise ValueError(
                f'Unsupported doc_type "{request.doc_type}". '
                f'Expected one of: {", ".join(sorted(DOC_TYPES))}'
            )

        if not request.title:
            request.title = self._derive_title(request)

        if request.validation_profile not in VALIDATION_PROFILES:
            raise ValueError(
                f'Unsupported validation_profile "{request.validation_profile}". '
                f'Expected one of: {", ".join(sorted(VALIDATION_PROFILES))}'
            )

        return request

    def _derive_title(self, request: DocumentationRequest) -> str:
        if request.title:
            return request.title

        if request.confluence_title:
            return request.confluence_title

        if request.target_file:
            return Path(request.target_file).stem.replace('-', ' ').replace('_', ' ').title()

        if request.project_key:
            return f'{request.project_key} Documentation Update'

        return 'Hypatia Documentation Draft'

    def _default_target_file(self, title: str) -> str:
        slug = re.sub(r'[^a-z0-9]+', '-', title.casefold()).strip('-') or 'hypatia-doc'
        return str(Path('docs') / f'{slug}.md')

    def _load_authoritative_inputs(
        self,
        request: DocumentationRequest,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        '''
        Load source material and existing target context.
        '''
        source_materials: List[Dict[str, Any]] = []
        existing_targets: Dict[str, Any] = {}

        for source_path in request.source_paths:
            material = self._read_source_file(source_path)
            if material is not None:
                source_materials.append(material)

        if request.target_file and Path(request.target_file).exists():
            existing_doc = self._read_source_file(request.target_file, role='existing_repo_doc')
            if existing_doc is not None:
                existing_targets['repo_markdown'] = {
                    'target_ref': request.target_file,
                    'facts': existing_doc.get('facts', []),
                    'excerpt': existing_doc.get('excerpt', ''),
                }

        if request.confluence_page:
            confluence_result = get_confluence_page(
                request.confluence_page,
                space=request.confluence_space,
                include_body=True,
            )
            if confluence_result.is_success:
                page = confluence_result.data
                existing_targets['confluence_page'] = {
                    'target_ref': request.confluence_page,
                    'title': page.get('title'),
                    'link': page.get('link'),
                    'facts': self._extract_fact_lines(
                        str(page.get('body_markdown') or ''),
                        limit=8,
                    ),
                }
            else:
                existing_targets['confluence_warning'] = confluence_result.error

        return source_materials, existing_targets

    def _read_source_file(
        self,
        source_path: str,
        role: str = 'source',
    ) -> Optional[Dict[str, Any]]:
        result = read_file(source_path, max_chars=20000)
        if result.is_error:
            log.warning(f'Failed to read Hypatia source file {source_path}: {result.error}')
            return None

        content = str((result.data or {}).get('content') or '')
        absolute_path = str((result.data or {}).get('path') or source_path)
        return {
            'path': absolute_path,
            'role': role,
            'facts': self._extract_fact_lines(content, limit=10),
            'excerpt': self._build_excerpt(content, max_lines=6),
            'lines': int((result.data or {}).get('lines') or 0),
        }

    def _generate_content(
        self,
        request: DocumentationRequest,
        impact: DocumentationImpactRecord,
        source_materials: List[Dict[str, Any]],
        existing_targets: Dict[str, Any],
        evidence_bundle: EvidenceBundle,
    ) -> str:
        '''
        Generate a source-grounded Markdown documentation candidate.
        '''
        title = request.title or self._derive_title(request)
        now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

        lines = [
            f'# {title}',
            '',
            '## Purpose',
        ]

        if request.summary:
            lines.append(request.summary)
        else:
            lines.append(
                'This internal document candidate was generated from authoritative '
                'source artifacts for review before publication.'
            )

        lines.extend([
            '',
            '## Metadata',
            f'- Documentation class: `{request.doc_type}`',
            f'- Generated: `{now_utc}`',
        ])
        if request.project_key:
            lines.append(f'- Project: `{request.project_key}`')
        lines.append(f'- Confidence: `{impact.confidence}`')

        lines.extend([
            '',
            '## Authoritative Inputs',
        ])
        if source_materials:
            for material in source_materials:
                lines.append(
                    f'- `{material["path"]}` ({material.get("role", "source")})'
                )
        else:
            lines.append('- No source files were supplied.')

        if request.source_refs:
            lines.append('- Additional references:')
            for ref in request.source_refs:
                lines.append(f'  - `{ref}`')

        if evidence_bundle.records:
            lines.extend([
                '',
                '## Evidence Inputs',
            ])
            for record in evidence_bundle.records:
                lines.append(
                    f'- `{record.evidence_type}`: {record.title} (`{record.source_ref}`)'
                )
                if record.summary:
                    lines.append(f'  - {record.summary}')

        lines.extend([
            '',
            '## Key Facts',
        ])
        if source_materials:
            for material in source_materials:
                lines.append('')
                lines.append(f'### Source: `{material["path"]}`')
                facts = material.get('facts') or []
                if facts:
                    for fact in facts:
                        lines.append(f'- {fact}')
                elif material.get('excerpt'):
                    lines.append(material['excerpt'])
                else:
                    lines.append('- No extractable facts found.')

        if evidence_bundle.records:
            lines.extend([
                '',
                '## Evidence Highlights',
            ])
            for record in evidence_bundle.records:
                lines.append('')
                lines.append(f'### Evidence: {record.title}')
                if record.summary:
                    lines.append(f'- Summary: {record.summary}')
                for fact in record.facts[:6]:
                    lines.append(f'- {fact}')
        else:
            lines.append('- No authoritative source facts were available.')

        if existing_targets:
            lines.extend([
                '',
                '## Existing Target Context',
            ])
            if existing_targets.get('repo_markdown'):
                repo_target = existing_targets['repo_markdown']
                lines.append(f'- Existing repo doc: `{repo_target["target_ref"]}`')
                for fact in repo_target.get('facts') or []:
                    lines.append(f'  - {fact}')
            if existing_targets.get('confluence_page'):
                confluence_target = existing_targets['confluence_page']
                lines.append(
                    f'- Existing Confluence page: `{confluence_target.get("title")}`'
                )
                if confluence_target.get('link'):
                    lines.append(f'  - Link: {confluence_target["link"]}')
                for fact in confluence_target.get('facts') or []:
                    lines.append(f'  - {fact}')
            if existing_targets.get('confluence_warning'):
                lines.append(
                    f'- Warning: {existing_targets["confluence_warning"]}'
                )

        lines.extend([
            '',
            '## Publication Targets',
        ])
        for target in impact.affected_targets:
            target_line = (
                f'- `{target["target_type"]}` -> `{target["target_ref"]}` '
                f'({target["operation"]})'
            )
            if target.get('space'):
                target_line += f' in space `{target["space"]}`'
            lines.append(target_line)

        if impact.warnings or impact.blocking_issues:
            lines.extend([
                '',
                '## Warnings and Open Questions',
            ])
            for warning in impact.warnings:
                lines.append(f'- Warning: {warning}')
            for blocker in impact.blocking_issues:
                lines.append(f'- Blocker: {blocker}')

        lines.extend([
            '',
            '## Source References',
        ])
        for ref in self._merge_source_refs(request, source_materials):
            lines.append(f'- `{ref}`')

        evidence_refs = evidence_bundle.to_summary().get('source_refs') or []
        for ref in evidence_refs:
            if ref not in request.source_refs and ref not in request.source_paths:
                lines.append(f'- `{ref}`')

        return '\n'.join(lines).rstrip() + '\n'

    def _build_patches(
        self,
        request: DocumentationRequest,
        impact: DocumentationImpactRecord,
        content_markdown: str,
        source_refs: List[str],
    ) -> List[DocumentationPatch]:
        '''
        Build candidate patches for each affected internal target.
        '''
        patches: List[DocumentationPatch] = []
        title = request.title or self._derive_title(request)

        for target in impact.affected_targets:
            if target['target_type'] == 'repo_markdown':
                patch = DocumentationPatch(
                    target_type='repo_markdown',
                    operation=target['operation'],
                    title=title,
                    target_ref=target['target_ref'],
                    content_markdown=content_markdown,
                    source_refs=source_refs,
                    preview={
                        'target_path': target['target_ref'],
                        'line_count': content_markdown.count('\n'),
                        'excerpt': self._build_excerpt(content_markdown, max_lines=8),
                    },
                    metadata={'file_path': target['target_ref']},
                )
                patches.append(patch)
                continue

            if target['target_type'] == 'confluence_page':
                patch = DocumentationPatch(
                    target_type='confluence_page',
                    operation=target['operation'],
                    title=title if target['operation'] == 'create' else (
                        request.confluence_title or title
                    ),
                    target_ref=target['target_ref'],
                    content_markdown=content_markdown,
                    source_refs=source_refs,
                    metadata={
                        'page_id_or_title': request.confluence_page or target['target_ref'],
                        'space': request.confluence_space,
                        'parent_id': request.confluence_parent_id,
                        'version_message': request.version_message,
                    },
                )
                patch.preview = self._preview_confluence_patch(request, patch)
                patches.append(patch)

        return patches

    def _preview_confluence_patch(
        self,
        request: DocumentationRequest,
        patch: DocumentationPatch,
    ) -> Dict[str, Any]:
        '''
        Dry-run a Confluence target when possible to capture a safe preview.
        '''
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            suffix='.md',
            delete=False,
        ) as handle:
            handle.write(patch.content_markdown)
            temp_path = handle.name

        try:
            if patch.operation == 'create':
                result = create_confluence_page(
                    title=patch.title,
                    input_file=temp_path,
                    space=request.confluence_space,
                    parent_id=request.confluence_parent_id,
                    version_message=request.version_message,
                    dry_run=True,
                )
            else:
                result = update_confluence_page(
                    page_id_or_title=request.confluence_page or patch.target_ref,
                    input_file=temp_path,
                    space=request.confluence_space,
                    version_message=request.version_message,
                    dry_run=True,
                )

            if result.is_success:
                preview = dict(result.data or {})
                preview['preview_available'] = True
                return preview

            return {
                'preview_available': False,
                'error': result.error,
                'excerpt': self._build_excerpt(patch.content_markdown, max_lines=8),
            }
        except Exception as e:
            return {
                'preview_available': False,
                'error': str(e),
                'excerpt': self._build_excerpt(patch.content_markdown, max_lines=8),
            }
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def _validate_patches(
        self,
        request: DocumentationRequest,
        patches: List[DocumentationPatch],
        evidence_bundle: EvidenceBundle,
        source_refs: List[str],
    ) -> Tuple[Dict[str, Any], List[str], str]:
        '''
        Validate the generated documentation patches.
        '''
        warnings: List[str] = []
        blocking_issues: List[str] = []
        by_target = Counter()

        if not patches:
            blocking_issues.append('No documentation targets were resolved.')

        for patch in patches:
            by_target[patch.target_type] += 1
            patch_warnings: List[str] = []
            patch_blockers: List[str] = []
            section_names = self._extract_section_names(patch.content_markdown)

            if not patch.content_markdown.strip():
                patch_blockers.append('Generated patch content is empty.')

            if not patch.content_markdown.lstrip().startswith(f'# {patch.title}'):
                patch_blockers.append('Patch is missing a top-level title heading.')

            missing_sections = [
                section for section in self._required_sections_for(request.doc_type)
                if section not in section_names
            ]
            if missing_sections:
                patch_blockers.append(
                    'Patch is missing required sections: ' + ', '.join(missing_sections)
                )

            if not patch.source_refs:
                patch_blockers.append('Patch has no source references.')

            if request.validation_profile in {'strict', 'sphinx'} and not source_refs:
                patch_blockers.append('Strict validation requires source references.')

            if evidence_bundle.records and 'Evidence Highlights' not in section_names:
                patch_warnings.append(
                    'Evidence inputs were provided but no Evidence Highlights section was generated.'
                )

            broken_links = self._find_broken_links(
                patch.content_markdown,
                base_path=patch.target_ref if patch.target_type == 'repo_markdown' else None,
            )
            if broken_links:
                patch_warnings.append(
                    'Broken relative links detected: ' + ', '.join(broken_links[:5])
                )

            if patch.target_type == 'repo_markdown':
                if not patch.target_ref.endswith('.md'):
                    patch_warnings.append('Repo documentation target does not end in .md.')
                sphinx_result = self._maybe_run_sphinx_validation(request, patch)
                if sphinx_result.get('warning'):
                    patch_warnings.append(str(sphinx_result['warning']))
                if sphinx_result.get('error'):
                    patch_blockers.append(str(sphinx_result['error']))
                if sphinx_result:
                    patch.metadata['sphinx_validation'] = sphinx_result

            if patch.target_type == 'confluence_page':
                preview_error = str((patch.preview or {}).get('error') or '').strip()
                if patch.operation == 'create' and not request.confluence_space:
                    patch_blockers.append('Confluence create target is missing space.')
                if preview_error:
                    patch_warnings.append(f'Confluence preview warning: {preview_error}')

            patch.validation = {
                'warnings': patch_warnings,
                'blocking_issues': patch_blockers,
                'valid': not patch_blockers,
            }
            warnings.extend(patch_warnings)
            blocking_issues.extend(patch_blockers)

        confidence = 'high'
        if warnings:
            confidence = 'medium'
        if blocking_issues:
            confidence = 'low'

        return ({
            'valid': not blocking_issues,
            'warnings': warnings,
            'blocking_issues': blocking_issues,
            'targets_by_type': dict(by_target),
        }, warnings, confidence)

    def _format_record_summary(
        self,
        request: DocumentationRequest,
        impact: DocumentationImpactRecord,
        patches: List[DocumentationPatch],
        validation: Dict[str, Any],
        warnings: List[str],
        confidence: str,
    ) -> str:
        '''
        Format the high-level Hypatia summary used in records and workflow output.
        '''
        lines = [
            f'# Hypatia Documentation Plan: {request.title or self._derive_title(request)}',
            '',
            '## Summary',
            f'- Documentation class: `{request.doc_type}`',
            f'- Confidence: `{confidence}`',
            f'- Targets: `{len(patches)}`',
            f'- Valid: `{"yes" if validation.get("valid") else "no"}`',
        ]
        if request.project_key:
            lines.append(f'- Project: `{request.project_key}`')

        lines.extend([
            '',
            '## Impact',
        ])
        for reason in impact.reasons:
            lines.append(f'- {reason}')

        lines.extend([
            '',
            '## Proposed Patches',
        ])
        for patch in patches:
            lines.append(
                f'- `{patch.target_type}` `{patch.operation}` -> `{patch.target_ref}`'
            )
            preview_excerpt = str((patch.preview or {}).get('excerpt') or '').strip()
            if preview_excerpt:
                lines.append(f'  - Preview: {preview_excerpt.splitlines()[0]}')

        if warnings or impact.blocking_issues:
            lines.extend([
                '',
                '## Warnings',
            ])
            for warning in warnings:
                lines.append(f'- {warning}')
            for blocker in impact.blocking_issues:
                lines.append(f'- {blocker}')

        return '\n'.join(lines)

    def _merge_source_refs(
        self,
        request: DocumentationRequest,
        source_materials: List[Dict[str, Any]],
        evidence_bundle: Optional[EvidenceBundle] = None,
    ) -> List[str]:
        refs: List[str] = []
        for ref in request.source_refs:
            if ref and ref not in refs:
                refs.append(ref)
        for path in request.source_paths:
            if path and path not in refs:
                refs.append(path)
        for path in request.evidence_paths:
            if path and path not in refs:
                refs.append(path)
        for material in source_materials:
            path = str(material.get('path') or '')
            if path and path not in refs:
                refs.append(path)
        if evidence_bundle is not None:
            for ref in evidence_bundle.to_summary().get('source_refs') or []:
                if ref and ref not in refs:
                    refs.append(ref)
        return refs

    @staticmethod
    def _required_sections_for(doc_type: str) -> List[str]:
        base_sections = [
            'Purpose',
            'Metadata',
            'Authoritative Inputs',
            'Key Facts',
            'Source References',
        ]
        if doc_type in {'how_to', 'as_built'}:
            return base_sections + ['Publication Targets']
        return base_sections

    @staticmethod
    def _extract_section_names(content: str) -> List[str]:
        return [
            match.group(1).strip()
            for match in re.finditer(r'^##\s+(.+?)\s*$', content, flags=re.MULTILINE)
        ]

    def _find_broken_links(
        self,
        content: str,
        base_path: Optional[str] = None,
    ) -> List[str]:
        broken: List[str] = []
        base_dir = Path(base_path).resolve().parent if base_path else Path.cwd()

        for match in re.finditer(r'\[[^\]]+\]\(([^)]+)\)', content):
            link_target = match.group(1).strip()
            if not link_target or link_target.startswith(('#', 'http://', 'https://', 'mailto:')):
                continue
            candidate = Path(link_target)
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            if not candidate.exists():
                broken.append(link_target)

        return broken

    def _maybe_run_sphinx_validation(
        self,
        request: DocumentationRequest,
        patch: DocumentationPatch,
    ) -> Dict[str, Any]:
        should_validate = (
            request.validation_profile == 'sphinx'
            or patch.target_ref.startswith('docs/source/')
        )
        if not should_validate:
            return {}

        sphinx_build = shutil.which('sphinx-build')
        if not sphinx_build:
            return {'warning': 'Sphinx validation requested but sphinx-build is unavailable.'}

        source_dir = self._find_sphinx_source_dir(patch.target_ref)
        if source_dir is None:
            return {'warning': 'Sphinx validation requested but no conf.py was found.'}

        with tempfile.TemporaryDirectory(prefix='hypatia-sphinx-') as temp_dir:
            try:
                completed = subprocess.run(
                    [sphinx_build, '-b', 'dummy', str(source_dir), temp_dir],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except Exception as e:
                return {'error': f'Sphinx validation failed to start: {e}'}

        if completed.returncode != 0:
            stderr = (completed.stderr or completed.stdout or '').strip()
            return {
                'error': 'Sphinx validation failed.'
                + (f' {stderr[:240]}' if stderr else ''),
            }

        return {
            'validated': True,
            'builder': 'dummy',
            'source_dir': str(source_dir),
        }

    @staticmethod
    def _find_sphinx_source_dir(target_ref: str) -> Optional[Path]:
        target_path = Path(target_ref)
        candidate_dirs = [target_path.parent, *target_path.parents]
        for directory in candidate_dirs:
            if (directory / 'conf.py').exists():
                return directory

        default_source = Path('docs/source')
        if (default_source / 'conf.py').exists():
            return default_source
        return None

    def _extract_fact_lines(
        self,
        content: str,
        limit: int = 8,
    ) -> List[str]:
        '''
        Pull concise, deterministic fact-like lines from source text.
        '''
        facts: List[str] = []
        seen = set()

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('```'):
                continue
            if line.startswith('#'):
                normalized = line.lstrip('#').strip()
            elif line.startswith(('- ', '* ')):
                normalized = line[2:].strip()
            elif line.startswith('.. '):
                continue
            else:
                normalized = line

            normalized = re.sub(r'\s+', ' ', normalized).strip()
            if len(normalized) < 8:
                continue
            if normalized in seen:
                continue

            seen.add(normalized)
            facts.append(normalized)
            if len(facts) >= limit:
                break

        return facts

    def _build_excerpt(
        self,
        content: str,
        max_lines: int = 6,
    ) -> str:
        '''
        Build a short multiline excerpt for previews.
        '''
        lines = [
            line.rstrip()
            for line in content.splitlines()
            if line.strip()
        ]
        return '\n'.join(lines[:max_lines])
