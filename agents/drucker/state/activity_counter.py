##########################################################################################
#
# Module: state/activity_counter.py
#
# Description: SQLite-backed persistent counter for all Drucker API request activity.
#              Tracks request counts, error counts, and first/last timestamps by
#              endpoint category (hygiene, jira, github, nl, pr-reminders).
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class ActivityCounter:

    def __init__(self, db_path: str = 'data/drucker_activity.db'):
        self.db_path = db_path
        self._lock = threading.RLock()

        if db_path != ':memory:':
            path = Path(db_path)
            path.parent.mkdir(parents=True, exist_ok=True)

        self.conn: Optional[sqlite3.Connection] = sqlite3.connect(
            db_path,
            check_same_thread=False,
        )
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _require_conn(self) -> sqlite3.Connection:
        if self.conn is None:
            raise RuntimeError('ActivityCounter connection is closed')
        return self.conn

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _init_db(self) -> None:
        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS activity (
                    category TEXT PRIMARY KEY,
                    request_count INTEGER NOT NULL DEFAULT 0,
                    error_count INTEGER NOT NULL DEFAULT 0,
                    first_request_at TEXT,
                    last_request_at TEXT
                )
                '''
            )
            conn.commit()

    def record(self, category: str, is_error: bool = False) -> None:
        conn = self._require_conn()
        now = self._utc_now_iso()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO activity (category, request_count, error_count, first_request_at, last_request_at)
                VALUES (?, 1, ?, ?, ?)
                ON CONFLICT(category) DO UPDATE SET
                    request_count = request_count + 1,
                    error_count = error_count + ?,
                    last_request_at = ?
                ''',
                (category, int(is_error), now, now, int(is_error), now),
            )
            conn.commit()

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM activity ORDER BY category')
            rows = cursor.fetchall()
        return {
            row['category']: {
                'request_count': row['request_count'],
                'error_count': row['error_count'],
                'first_request_at': row['first_request_at'] or '',
                'last_request_at': row['last_request_at'] or '',
            }
            for row in rows
        }

    def get_totals(self) -> Dict[str, Any]:
        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COALESCE(SUM(request_count), 0) AS total_requests, '
                'COALESCE(SUM(error_count), 0) AS total_errors, '
                'MIN(first_request_at) AS first_request_at, '
                'MAX(last_request_at) AS last_request_at '
                'FROM activity'
            )
            row = cursor.fetchone()
        return {
            'total_requests': row['total_requests'],
            'total_errors': row['total_errors'],
            'first_request_at': row['first_request_at'] or '',
            'last_request_at': row['last_request_at'] or '',
        }

    def close(self) -> None:
        with self._lock:
            if self.conn:
                self.conn.close()
                self.conn = None
