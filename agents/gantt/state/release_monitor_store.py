##########################################################################################
#
# Module: state/gantt_release_monitor_store.py
#
# Description: Persistence helpers for Gantt release-monitor reports.
#              Stores durable JSON + Markdown artifacts and optionally copies
#              the generated xlsx output file alongside the stored report.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.gantt.models import ReleaseMonitorReport

log = logging.getLogger(os.path.basename(sys.argv[0]))


class GanttReleaseMonitorStore:
    '''
    JSON + Markdown persistence for Gantt release-monitor reports.

    Reports are stored at:
        data/gantt_release_monitors/<PROJECT>/<REPORT_ID>/report.json
        data/gantt_release_monitors/<PROJECT>/<REPORT_ID>/summary.md
        data/gantt_release_monitors/<PROJECT>/<REPORT_ID>/<name>.xlsx  (optional)
    '''

    def __init__(self, storage_dir: Optional[str] = None):
        env_dir = os.getenv('GANTT_RELEASE_MONITOR_DIR')
        resolved_dir = storage_dir or env_dir or 'data/gantt_release_monitors'
        self.storage_dir = Path(resolved_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        log.debug(f'GanttReleaseMonitorStore initialized: {self.storage_dir}')

    def save_report(
        self,
        report: ReleaseMonitorReport | Dict[str, Any],
        summary_markdown: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Persist a release-monitor report and return a summary record.
        '''
        if isinstance(report, ReleaseMonitorReport):
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

        output_file = str(report_data.get('output_file') or '').strip()
        copied_output = ''
        if output_file:
            source_path = Path(output_file)
            if source_path.exists() and source_path.is_file():
                dest_path = report_dir / source_path.name
                shutil.copy2(str(source_path), str(dest_path))
                copied_output = str(dest_path)

        summary = self._build_summary(report_data, json_path, markdown_path)
        if copied_output:
            summary['output_copy_path'] = copied_output
        log.info(f'Saved Gantt release monitor report {report_id} to {report_dir}')
        return summary

    def get_report(
        self,
        report_id: str,
        project_key: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        '''
        Load a stored release-monitor report by ID.
        '''
        json_path = self._find_report_json(report_id, project_key=project_key)
        if json_path is None:
            return None

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
        except Exception as e:
            log.error(f'Failed to load Gantt release monitor report {report_id}: {e}')
            return None

        markdown_path = json_path.parent / 'summary.md'
        summary_markdown = ''
        if markdown_path.exists():
            try:
                summary_markdown = markdown_path.read_text(encoding='utf-8')
            except Exception as e:
                log.warning(
                    f'Failed to read Gantt release monitor markdown {markdown_path}: {e}'
                )

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
        List stored release-monitor reports, optionally filtered by project.
        '''
        summaries: List[Dict[str, Any]] = []
        json_paths = self._iter_report_json_paths(project_key=project_key)

        for json_path in json_paths:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
            except Exception as e:
                log.warning(f'Skipping unreadable release monitor file {json_path}: {e}')
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

    def get_latest_compatible_report(
        self,
        project_key: str,
        releases: List[str],
        scope_label: Optional[str] = None,
        *,
        exclude_report_id: Optional[str] = None,
        limit: int = 50,
    ) -> Optional[Dict[str, Any]]:
        '''
        Return the most recent stored report for the same project/release scope.
        '''
        target_releases = sorted(str(item).strip() for item in releases if str(item).strip())
        target_scope = str(scope_label or '').strip()
        excluded = str(exclude_report_id or '').strip()

        for summary in self.list_reports(project_key=project_key, limit=limit):
            report_id = str(summary.get('report_id') or '').strip()
            if excluded and report_id == excluded:
                continue

            record = self.get_report(report_id, project_key=project_key)
            if not record:
                continue

            report = record.get('report') or {}
            report_releases = sorted(
                str(item).strip()
                for item in (report.get('releases_monitored') or [])
                if str(item).strip()
            )
            report_scope = str(report.get('scope_label') or '').strip()

            if report_releases != target_releases:
                continue
            if report_scope != target_scope:
                continue

            return record

        return None

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
                'Multiple stored Gantt release monitor reports matched ID '
                f'{report_id}; using {matches[0]}'
            )

        return matches[0]

    @staticmethod
    def _build_summary(
        report_data: Dict[str, Any],
        json_path: Path,
        markdown_path: Path,
    ) -> Dict[str, Any]:
        return {
            'report_id': str(report_data.get('report_id') or ''),
            'project_key': str(report_data.get('project_key') or '').upper(),
            'created_at': str(report_data.get('created_at') or ''),
            'scope_label': str(report_data.get('scope_label') or ''),
            'release_count': len(report_data.get('releases_monitored') or []),
            'total_bugs': int(report_data.get('total_bugs') or 0),
            'total_p0': int(report_data.get('total_p0') or 0),
            'total_p1': int(report_data.get('total_p1') or 0),
            'output_file': str(report_data.get('output_file') or ''),
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
