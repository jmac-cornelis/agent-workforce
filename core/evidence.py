##########################################################################################
#
# Module: core/evidence.py
#
# Description: Shared evidence contracts and file-backed loading helpers.
#              Provides a lightweight, durable way for agents to consume build,
#              test, release, traceability, meeting, and generic evidence inputs.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import json
import logging
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


EVIDENCE_TYPE_ALIASES = {
    'build': 'build',
    'builds': 'build',
    'ci': 'build',
    'test': 'test',
    'tests': 'test',
    'qa': 'test',
    'release': 'release',
    'releases': 'release',
    'version': 'release',
    'traceability': 'traceability',
    'trace': 'traceability',
    'meeting': 'meeting',
    'meetings': 'meeting',
    'transcript': 'meeting',
    'doc': 'documentation',
    'documentation': 'documentation',
    'generic': 'generic',
}


def normalize_evidence_type(value: Optional[str]) -> str:
    '''
    Normalize evidence type names to a small canonical set.
    '''
    raw = str(value or 'generic').strip().casefold()
    if raw in EVIDENCE_TYPE_ALIASES:
        return EVIDENCE_TYPE_ALIASES[raw]
    for alias, normalized in EVIDENCE_TYPE_ALIASES.items():
        if alias and alias in raw:
            return normalized
    return raw or 'generic'


@dataclass
class EvidenceRecord:
    '''
    A single evidence record loaded from a file-backed source.
    '''
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    evidence_type: str = 'generic'
    title: str = ''
    summary: str = ''
    source_ref: str = ''
    facts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: str = 'medium'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'evidence_id': self.evidence_id,
            'evidence_type': self.evidence_type,
            'title': self.title,
            'summary': self.summary,
            'source_ref': self.source_ref,
            'facts': self.facts,
            'metadata': self.metadata,
            'confidence': self.confidence,
        }


@dataclass
class EvidenceBundle:
    '''
    A collection of evidence records plus load-time warnings.
    '''
    records: List[EvidenceRecord] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'records': [record.to_dict() for record in self.records],
            'warnings': self.warnings,
            'summary': self.to_summary(),
        }

    def to_summary(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        source_refs: List[str] = []

        for record in self.records:
            by_type[record.evidence_type] = by_type.get(record.evidence_type, 0) + 1
            if record.source_ref and record.source_ref not in source_refs:
                source_refs.append(record.source_ref)

        return {
            'record_count': len(self.records),
            'by_type': by_type,
            'source_refs': source_refs,
            'warnings': list(self.warnings),
        }

    def has_type(self, evidence_type: str) -> bool:
        normalized = normalize_evidence_type(evidence_type)
        return any(record.evidence_type == normalized for record in self.records)


class FileEvidenceProvider:
    '''
    Load evidence records from JSON, YAML, Markdown, or text files.
    '''

    def load_bundle(self, paths: List[str]) -> EvidenceBundle:
        bundle = EvidenceBundle()

        for raw_path in paths:
            path = Path(raw_path)
            if not path.exists():
                bundle.warnings.append(f'Evidence file not found: {raw_path}')
                continue
            if not path.is_file():
                bundle.warnings.append(f'Evidence path is not a file: {raw_path}')
                continue

            try:
                records = self.load_path(path)
            except Exception as e:
                log.warning(f'Failed to load evidence file {path}: {e}')
                bundle.warnings.append(f'Failed to load evidence file {path}: {e}')
                continue

            bundle.records.extend(records)

        return bundle

    def load_path(self, path: Path) -> List[EvidenceRecord]:
        suffix = path.suffix.lower()
        if suffix == '.json':
            return self._load_json(path)
        if suffix in {'.yaml', '.yml'}:
            return self._load_yaml(path)
        return self._load_text(path)

    def _load_json(self, path: Path) -> List[EvidenceRecord]:
        with open(path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        return self._records_from_payload(payload, source_ref=str(path))

    def _load_yaml(self, path: Path) -> List[EvidenceRecord]:
        with open(path, 'r', encoding='utf-8') as f:
            payload = yaml.safe_load(f)
        return self._records_from_payload(payload, source_ref=str(path))

    def _load_text(self, path: Path) -> List[EvidenceRecord]:
        text = path.read_text(encoding='utf-8')
        title = self._derive_title(text, path.name)
        facts = self._extract_fact_lines(text, limit=8)
        summary = self._derive_summary(text)
        evidence_type = normalize_evidence_type(path.stem)
        return [EvidenceRecord(
            evidence_type=evidence_type,
            title=title,
            summary=summary,
            source_ref=str(path),
            facts=facts,
            metadata={'path': str(path)},
            confidence='medium',
        )]

    def _records_from_payload(
        self,
        payload: Any,
        source_ref: str,
    ) -> List[EvidenceRecord]:
        if isinstance(payload, list):
            records = []
            for item in payload:
                if isinstance(item, dict):
                    records.append(self._record_from_mapping(item, source_ref=source_ref))
            return records

        if isinstance(payload, dict):
            return [self._record_from_mapping(payload, source_ref=source_ref)]

        return [EvidenceRecord(
            evidence_type='generic',
            title=Path(source_ref).stem,
            summary=str(payload),
            source_ref=source_ref,
            facts=[str(payload)],
            metadata={'path': source_ref},
            confidence='low',
        )]

    def _record_from_mapping(
        self,
        payload: Dict[str, Any],
        source_ref: str,
    ) -> EvidenceRecord:
        evidence_type = normalize_evidence_type(
            payload.get('evidence_type') or payload.get('type')
        )
        title = str(
            payload.get('title')
            or payload.get('name')
            or Path(source_ref).stem.replace('-', ' ').title()
        )
        summary = str(
            payload.get('summary')
            or payload.get('description')
            or payload.get('status')
            or ''
        )
        raw_facts = payload.get('facts')
        facts: List[str]
        if isinstance(raw_facts, list):
            facts = [str(item) for item in raw_facts if str(item).strip()]
        elif isinstance(raw_facts, str):
            facts = [raw_facts]
        else:
            facts = []

        if not facts:
            facts = self._extract_mapping_facts(payload)

        metadata = dict(payload.get('metadata') or {})
        if 'source_ref' in payload:
            source_ref = str(payload['source_ref'])

        return EvidenceRecord(
            evidence_type=evidence_type,
            title=title,
            summary=summary,
            source_ref=source_ref,
            facts=facts,
            metadata=metadata,
            confidence=str(payload.get('confidence') or 'medium'),
        )

    @staticmethod
    def _derive_title(text: str, fallback: str) -> str:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith('#'):
                return stripped.lstrip('#').strip()
            if stripped:
                return stripped[:80]
        return fallback

    @staticmethod
    def _derive_summary(text: str) -> str:
        paragraphs = [
            re.sub(r'\s+', ' ', block.strip())
            for block in text.split('\n\n')
            if block.strip()
        ]
        return paragraphs[0][:240] if paragraphs else ''

    @staticmethod
    def _extract_fact_lines(text: str, limit: int = 8) -> List[str]:
        facts: List[str] = []
        seen = set()
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith('```'):
                continue
            if line.startswith('#'):
                normalized = line.lstrip('#').strip()
            elif line.startswith(('- ', '* ')):
                normalized = line[2:].strip()
            else:
                normalized = line
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            if len(normalized) < 6 or normalized in seen:
                continue
            facts.append(normalized)
            seen.add(normalized)
            if len(facts) >= limit:
                break
        return facts

    @staticmethod
    def _extract_mapping_facts(payload: Dict[str, Any]) -> List[str]:
        facts: List[str] = []
        for key, value in payload.items():
            if key in {'metadata', 'facts'}:
                continue
            if isinstance(value, (dict, list)):
                continue
            rendered = str(value).strip()
            if not rendered:
                continue
            facts.append(f'{key}: {rendered}')
            if len(facts) >= 8:
                break
        return facts


def load_evidence_bundle(paths: Optional[List[str]] = None) -> EvidenceBundle:
    '''
    Convenience loader for file-backed evidence bundles.
    '''
    provider = FileEvidenceProvider()
    return provider.load_bundle(list(paths or []))
