##########################################################################################
#
# Module: state/drucker_report_store.py
#
# Description: Persistence helpers for Drucker hygiene reports.
#              Stores durable JSON + Markdown artifacts for Jira hygiene analysis.
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

from agents.drucker.models import DruckerHygieneReport

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class DruckerReportStore:
    '''
    JSON + Markdown persistence for Drucker hygiene reports.

    Reports are stored at:
        data/drucker_reports/<PROJECT>/<REPORT_ID>/report.json
        data/drucker_reports/<PROJECT>/<REPORT_ID>/summary.md
    '''

    def __init__(self, storage_dir: Optional[str] = None):
        env_dir = os.getenv('DRUCKER_REPORT_DIR')
        resolved_dir = storage_dir or env_dir or 'data/drucker_reports'
        self.storage_dir = Path(resolved_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        log.debug(f'DruckerReportStore initialized: {self.storage_dir}')

    def save_report(
        self,
        report: DruckerHygieneReport | Dict[str, Any],
        summary_markdown: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Persist a report and return a summary record.
        '''
        if isinstance(report, DruckerHygieneReport):
            report_data = report.to_dict()
            if summary_markdown is None:
                summary_markdown = report.summary_markdown
        else:
            report_data = dict(report)

        report_id = str(report_data.get('report_id') or '').strip()
        if not report_id:
            raise ValueError('Report is missing report_id')

        project_key = str(report_data.get('project_key') or '').strip().upper()
        if not project_key:
            raise ValueError('Report is missing project_key')

        report_dir = self.storage_dir / project_key / report_id
        report_dir.mkdir(parents=True, exist_ok=True)

        json_path = report_dir / 'report.json'
        markdown_path = report_dir / 'summary.md'

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)

        markdown_text = summary_markdown
        if markdown_text is None:
            markdown_text = str(report_data.get('summary_markdown') or '')

        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        summary = self._build_summary(report_data, json_path, markdown_path)
        log.info(f'Saved Drucker report {report_id} to {report_dir}')
        return summary

    def get_report(
        self,
        report_id: str,
        project_key: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        '''
        Load a stored report by ID.
        '''
        json_path = self._find_report_json(report_id, project_key=project_key)
        if json_path is None:
            return None

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
        except Exception as e:
            log.error(f'Failed to load Drucker report {report_id}: {e}')
            return None

        markdown_path = json_path.parent / 'summary.md'
        summary_markdown = ''
        if markdown_path.exists():
            try:
                summary_markdown = markdown_path.read_text(encoding='utf-8')
            except Exception as e:
                log.warning(f'Failed to read Drucker summary markdown {markdown_path}: {e}')

        return {
            'report': report_data,
            'summary_markdown': summary_markdown,
            'summary': self._build_summary(report_data, json_path, markdown_path),
        }

    def list_reports(
        self,
        project_key: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        '''
        List stored reports, optionally filtered by project.
        '''
        summaries: List[Dict[str, Any]] = []
        json_paths = self._iter_report_json_paths(project_key=project_key)

        for json_path in json_paths:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
            except Exception as e:
                log.warning(f'Skipping unreadable report file {json_path}: {e}')
                continue

            summaries.append(
                self._build_summary(
                    report_data,
                    json_path,
                    json_path.parent / 'summary.md',
                )
            )

        summaries.sort(
            key=lambda item: (
                self._sort_timestamp(item.get('created_at')),
                str(item.get('report_id') or ''),
            ),
            reverse=True,
        )

        if limit is not None and limit >= 0:
            summaries = summaries[:limit]

        return summaries

    def _iter_report_json_paths(self, project_key: Optional[str] = None) -> List[Path]:
        if project_key:
            project_dir = self.storage_dir / str(project_key).upper()
            if not project_dir.exists():
                return []
            return sorted(project_dir.glob('*/report.json'))

        return sorted(self.storage_dir.glob('*/*/report.json'))

    def _find_report_json(
        self,
        report_id: str,
        project_key: Optional[str] = None,
    ) -> Optional[Path]:
        report_id = str(report_id).strip()
        if not report_id:
            return None

        if project_key:
            candidate = (
                self.storage_dir / str(project_key).upper() / report_id / 'report.json'
            )
            return candidate if candidate.exists() else None

        matches = list(self.storage_dir.glob(f'*/{report_id}/report.json'))
        if not matches:
            return None

        if len(matches) > 1:
            log.warning(
                f'Multiple stored Drucker reports matched ID {report_id}; using {matches[0]}'
            )

        return matches[0]

    @staticmethod
    def _build_summary(
        report_data: Dict[str, Any],
        json_path: Path,
        markdown_path: Path,
    ) -> Dict[str, Any]:
        summary = report_data.get('summary') or {}

        return {
            'report_id': str(report_data.get('report_id') or ''),
            'project_key': str(report_data.get('project_key') or '').upper(),
            'created_at': str(report_data.get('created_at') or ''),
            'total_tickets': int(summary.get('total_tickets') or 0),
            'finding_count': int(summary.get('finding_count') or 0),
            'action_count': int(summary.get('action_count') or 0),
            'tickets_with_findings': int(summary.get('tickets_with_findings') or 0),
            'high_severity_count': int(summary.get('by_severity', {}).get('high') or 0),
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
