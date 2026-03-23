##########################################################################################
#
# Module: state/roadmap_snapshot_store.py
#
# Description: Persistence helpers for roadmap planning snapshots.
#              Stores durable JSON + Markdown snapshot artifacts and supports
#              retrieval/listing for later review.  Optionally copies the
#              generated xlsx output file alongside the snapshot.
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

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class RoadmapSnapshotStore:
    '''
    JSON + Markdown persistence for roadmap planning snapshots.

    Snapshots are stored at:
        data/roadmap_snapshots/<PROJECT>/<SNAPSHOT_ID>/snapshot.json
        data/roadmap_snapshots/<PROJECT>/<SNAPSHOT_ID>/summary.md
        data/roadmap_snapshots/<PROJECT>/<SNAPSHOT_ID>/<name>.xlsx  (optional)
    '''

    def __init__(self, storage_dir: Optional[str] = None):
        # Resolve storage directory: explicit arg > env var > default
        env_dir = os.getenv('ROADMAP_SNAPSHOT_DIR')
        resolved_dir = storage_dir or env_dir or 'data/roadmap_snapshots'
        self.storage_dir = Path(resolved_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        log.debug(f'RoadmapSnapshotStore initialized: {self.storage_dir}')

    # ----------------------------------------------------------------------- save
    def save_snapshot(
        self,
        snapshot: Dict[str, Any],
        summary_markdown: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Persist a snapshot dict and return a summary record for indexing/reporting.

        If the snapshot dict contains an ``xlsx_path`` key pointing to an existing
        file, that file is copied into the snapshot directory.
        '''
        snapshot_data = dict(snapshot)

        # -- validate required fields ----------------------------------------
        snapshot_id = str(snapshot_data.get('snapshot_id') or '').strip()
        if not snapshot_id:
            raise ValueError('Snapshot is missing snapshot_id')

        project_key = str(snapshot_data.get('project_key') or '').strip().upper()
        if not project_key:
            raise ValueError('Snapshot is missing project_key')

        # -- create snapshot directory ----------------------------------------
        snapshot_dir = self.storage_dir / project_key / snapshot_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # -- write JSON -------------------------------------------------------
        json_path = snapshot_dir / 'snapshot.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, default=str)

        # -- write Markdown summary -------------------------------------------
        markdown_path = snapshot_dir / 'summary.md'
        markdown_text = summary_markdown
        if markdown_text is None:
            markdown_text = str(snapshot_data.get('summary_markdown') or '')

        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        # -- copy xlsx output if it exists ------------------------------------
        xlsx_source = snapshot_data.get('xlsx_path')
        if xlsx_source:
            xlsx_source_path = Path(xlsx_source)
            if xlsx_source_path.exists() and xlsx_source_path.is_file():
                xlsx_dest = snapshot_dir / xlsx_source_path.name
                shutil.copy2(str(xlsx_source_path), str(xlsx_dest))
                log.debug(f'Copied xlsx artifact to {xlsx_dest}')

        summary = self._build_summary(snapshot_data, json_path, markdown_path)
        log.info(f'Saved roadmap snapshot {snapshot_id} to {snapshot_dir}')
        return summary

    # ----------------------------------------------------------------------- get
    def get_snapshot(
        self,
        project_key: str,
        snapshot_id: str,
    ) -> Optional[Dict[str, Any]]:
        '''
        Load a stored snapshot by project key and snapshot ID.
        Returns None if the snapshot does not exist or cannot be read.
        '''
        json_path = self._find_snapshot_json(snapshot_id, project_key=project_key)
        if json_path is None:
            return None

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)
        except Exception as e:
            log.error(f'Failed to load roadmap snapshot {snapshot_id}: {e}')
            return None

        # Read companion markdown if present
        markdown_path = json_path.parent / 'summary.md'
        summary_markdown = ''
        if markdown_path.exists():
            try:
                summary_markdown = markdown_path.read_text(encoding='utf-8')
            except Exception as e:
                log.warning(f'Failed to read roadmap summary markdown {markdown_path}: {e}')

        return {
            'snapshot': snapshot_data,
            'summary_markdown': summary_markdown,
            'summary': self._build_summary(snapshot_data, json_path, markdown_path),
        }

    # ----------------------------------------------------------------------- list
    def list_snapshots(
        self,
        project_key: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        '''
        List stored snapshots, optionally filtered by project.
        Returns summaries sorted newest-first.
        '''
        summaries: List[Dict[str, Any]] = []
        json_paths = self._iter_snapshot_json_paths(project_key=project_key)

        for json_path in json_paths:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    snapshot_data = json.load(f)
            except Exception as e:
                log.warning(f'Skipping unreadable snapshot file {json_path}: {e}')
                continue

            summaries.append(
                self._build_summary(
                    snapshot_data,
                    json_path,
                    json_path.parent / 'summary.md',
                )
            )

        # Sort newest-first by created_at, then by snapshot_id for stability
        summaries.sort(
            key=lambda item: (
                self._sort_timestamp(item.get('created_at')),
                str(item.get('snapshot_id') or ''),
            ),
            reverse=True,
        )

        if limit is not None and limit >= 0:
            summaries = summaries[:limit]

        return summaries

    # ----------------------------------------------------------------------- latest
    def get_latest_snapshot(
        self,
        project_key: str,
    ) -> Optional[Dict[str, Any]]:
        '''
        Convenience: return the most recent snapshot for a project, or None.
        '''
        snapshots = self.list_snapshots(project_key=project_key, limit=1)
        if not snapshots:
            return None

        # list_snapshots returns summaries; load the full snapshot
        latest = snapshots[0]
        return self.get_snapshot(
            project_key=latest['project_key'],
            snapshot_id=latest['snapshot_id'],
        )

    # ======================================================================= private

    def _iter_snapshot_json_paths(self, project_key: Optional[str] = None) -> List[Path]:
        '''Glob for all snapshot.json files under the storage tree.'''
        if project_key:
            project_dir = self.storage_dir / str(project_key).upper()
            if not project_dir.exists():
                return []
            return sorted(project_dir.glob('*/snapshot.json'))

        return sorted(self.storage_dir.glob('*/*/snapshot.json'))

    def _find_snapshot_json(
        self,
        snapshot_id: str,
        project_key: Optional[str] = None,
    ) -> Optional[Path]:
        '''Locate the snapshot.json for a given ID, optionally scoped to a project.'''
        snapshot_id = str(snapshot_id).strip()
        if not snapshot_id:
            return None

        if project_key:
            candidate = (
                self.storage_dir / str(project_key).upper() / snapshot_id / 'snapshot.json'
            )
            return candidate if candidate.exists() else None

        # Fallback: search across all projects
        matches = list(self.storage_dir.glob(f'*/{snapshot_id}/snapshot.json'))
        if not matches:
            return None

        if len(matches) > 1:
            log.warning(
                f'Multiple stored roadmap snapshots matched ID {snapshot_id}; using {matches[0]}'
            )

        return matches[0]

    @staticmethod
    def _build_summary(
        snapshot_data: Dict[str, Any],
        json_path: Path,
        markdown_path: Path,
    ) -> Dict[str, Any]:
        '''Build a lightweight summary dict from snapshot data and paths.'''
        return {
            'snapshot_id': str(snapshot_data.get('snapshot_id') or ''),
            'project_key': str(snapshot_data.get('project_key') or '').upper(),
            'created_at': str(snapshot_data.get('created_at') or ''),
            'storage_dir': str(json_path.parent),
            'json_path': str(json_path),
            'markdown_path': str(markdown_path),
        }

    @staticmethod
    def _sort_timestamp(value: Any) -> datetime:
        '''Parse an ISO timestamp for sorting; returns datetime.min on failure.'''
        raw = str(value or '').strip()
        if not raw:
            return datetime.min

        try:
            if raw.endswith('Z'):
                raw = raw[:-1] + '+00:00'
            return datetime.fromisoformat(raw)
        except ValueError:
            return datetime.min
