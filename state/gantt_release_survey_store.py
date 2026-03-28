##########################################################################################
#
# Module: state/gantt_release_survey_store.py
#
# Description: Persistence helpers for Gantt release-survey reports.
#              Stores durable JSON + Markdown artifacts and optionally copies
#              the generated xlsx output file alongside the stored survey.
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

from agents.gantt_models import ReleaseSurveyReport

log = logging.getLogger(os.path.basename(sys.argv[0]))


class GanttReleaseSurveyStore:
    '''
    JSON + Markdown persistence for Gantt release-survey reports.

    Surveys are stored at:
        data/gantt_release_surveys/<PROJECT>/<SURVEY_ID>/survey.json
        data/gantt_release_surveys/<PROJECT>/<SURVEY_ID>/summary.md
        data/gantt_release_surveys/<PROJECT>/<SURVEY_ID>/<name>.xlsx  (optional)
    '''

    def __init__(self, storage_dir: Optional[str] = None):
        env_dir = os.getenv('GANTT_RELEASE_SURVEY_DIR')
        resolved_dir = storage_dir or env_dir or 'data/gantt_release_surveys'
        self.storage_dir = Path(resolved_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        log.debug(f'GanttReleaseSurveyStore initialized: {self.storage_dir}')

    def save_survey(
        self,
        survey: ReleaseSurveyReport | Dict[str, Any],
        summary_markdown: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Persist a release-survey report and return a summary record.
        '''
        if isinstance(survey, ReleaseSurveyReport):
            survey_data = survey.to_dict()
            if summary_markdown is None:
                summary_markdown = survey.summary_markdown
        else:
            survey_data = dict(survey)

        survey_id = str(survey_data.get('survey_id') or '').strip()
        if not survey_id:
            raise ValueError('Survey is missing survey_id')

        project_key = str(survey_data.get('project_key') or '').strip().upper()
        if not project_key:
            raise ValueError('Survey is missing project_key')

        survey_dir = self.storage_dir / project_key / survey_id
        survey_dir.mkdir(parents=True, exist_ok=True)

        json_path = survey_dir / 'survey.json'
        markdown_path = survey_dir / 'summary.md'

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(survey_data, f, indent=2, default=str)

        markdown_text = summary_markdown
        if markdown_text is None:
            markdown_text = str(survey_data.get('summary_markdown') or '')

        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        output_file = str(survey_data.get('output_file') or '').strip()
        copied_output = ''
        if output_file:
            source_path = Path(output_file)
            if source_path.exists() and source_path.is_file():
                dest_path = survey_dir / source_path.name
                shutil.copy2(str(source_path), str(dest_path))
                copied_output = str(dest_path)

        summary = self._build_summary(survey_data, json_path, markdown_path)
        if copied_output:
            summary['output_copy_path'] = copied_output
        log.info(f'Saved Gantt release survey {survey_id} to {survey_dir}')
        return summary

    def get_survey(
        self,
        survey_id: str,
        project_key: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        '''
        Load a stored release-survey report by ID.
        '''
        json_path = self._find_survey_json(survey_id, project_key=project_key)
        if json_path is None:
            return None

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                survey_data = json.load(f)
        except Exception as e:
            log.error(f'Failed to load Gantt release survey {survey_id}: {e}')
            return None

        markdown_path = json_path.parent / 'summary.md'
        summary_markdown = ''
        if markdown_path.exists():
            try:
                summary_markdown = markdown_path.read_text(encoding='utf-8')
            except Exception as e:
                log.warning(
                    f'Failed to read Gantt release survey markdown {markdown_path}: {e}'
                )

        return {
            'survey': survey_data,
            'summary_markdown': summary_markdown,
            'summary': self._build_summary(survey_data, json_path, markdown_path),
        }

    def list_surveys(
        self,
        project_key: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        '''
        List stored release-survey reports, optionally filtered by project.
        '''
        summaries: List[Dict[str, Any]] = []
        json_paths = self._iter_survey_json_paths(project_key=project_key)

        for json_path in json_paths:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    survey_data = json.load(f)
            except Exception as e:
                log.warning(f'Skipping unreadable release survey file {json_path}: {e}')
                continue

            summaries.append(
                self._build_summary(
                    survey_data,
                    json_path,
                    json_path.parent / 'summary.md',
                )
            )

        summaries.sort(
            key=lambda item: (
                self._sort_timestamp(item.get('created_at')),
                str(item.get('survey_id') or ''),
            ),
            reverse=True,
        )

        if limit is not None and limit >= 0:
            summaries = summaries[:limit]

        return summaries

    def _iter_survey_json_paths(self, project_key: Optional[str] = None) -> List[Path]:
        if project_key:
            project_dir = self.storage_dir / str(project_key).upper()
            if not project_dir.exists():
                return []
            return sorted(project_dir.glob('*/survey.json'))

        return sorted(self.storage_dir.glob('*/*/survey.json'))

    def _find_survey_json(
        self,
        survey_id: str,
        project_key: Optional[str] = None,
    ) -> Optional[Path]:
        survey_id = str(survey_id).strip()
        if not survey_id:
            return None

        if project_key:
            candidate = (
                self.storage_dir / str(project_key).upper() / survey_id / 'survey.json'
            )
            return candidate if candidate.exists() else None

        matches = list(self.storage_dir.glob(f'*/{survey_id}/survey.json'))
        if not matches:
            return None

        if len(matches) > 1:
            log.warning(
                'Multiple stored Gantt release surveys matched ID '
                f'{survey_id}; using {matches[0]}'
            )

        return matches[0]

    @staticmethod
    def _build_summary(
        survey_data: Dict[str, Any],
        json_path: Path,
        markdown_path: Path,
    ) -> Dict[str, Any]:
        return {
            'survey_id': str(survey_data.get('survey_id') or ''),
            'project_key': str(survey_data.get('project_key') or '').upper(),
            'created_at': str(survey_data.get('created_at') or ''),
            'scope_label': str(survey_data.get('scope_label') or ''),
            'survey_mode': str(survey_data.get('survey_mode') or 'feature_dev'),
            'release_count': len(survey_data.get('releases_surveyed') or []),
            'total_tickets': int(survey_data.get('total_tickets') or 0),
            'done_count': int(survey_data.get('done_count') or 0),
            'in_progress_count': int(survey_data.get('in_progress_count') or 0),
            'remaining_count': int(survey_data.get('remaining_count') or 0),
            'blocked_count': int(survey_data.get('blocked_count') or 0),
            'stale_count': int(survey_data.get('stale_count') or 0),
            'unassigned_count': int(survey_data.get('unassigned_count') or 0),
            'completion_pct': float(survey_data.get('completion_pct') or 0.0),
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
