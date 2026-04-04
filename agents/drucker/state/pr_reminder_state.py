##########################################################################################
#
# Module: state/pr_reminder_state.py
#
# Description: SQLite state store for PR reminder tracking. Manages reminder
#              scheduling, snooze state, and action history for pull requests
#              that need reviewer attention.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class PRReminderState:
    '''SQLite-backed state store for PR reminder lifecycle tracking.'''

    def __init__(self, db_path: str = 'data/drucker_pr_reminder_state.db'):
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_conn(self) -> sqlite3.Connection:
        if self.conn is None:
            raise RuntimeError('PRReminderState connection is closed')
        return self.conn

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        '''Convert a sqlite3.Row to a plain dict.'''
        return dict(row)

    # ------------------------------------------------------------------
    # Schema initialisation
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()

            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS pr_reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo TEXT NOT NULL,
                    pr_number INTEGER NOT NULL,
                    pr_title TEXT NOT NULL DEFAULT '',
                    pr_url TEXT NOT NULL DEFAULT '',
                    author_github TEXT NOT NULL DEFAULT '',
                    reviewers_github TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    first_reminded_at TEXT,
                    last_reminded_at TEXT,
                    next_reminder_at TEXT,
                    reminder_count INTEGER NOT NULL DEFAULT 0,
                    snoozed_until TEXT,
                    snoozed_by TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'active',
                    UNIQUE(repo, pr_number)
                )
                '''
            )

            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS reminder_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo TEXT NOT NULL,
                    pr_number INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    target_user TEXT NOT NULL DEFAULT '',
                    details_json TEXT,
                    timestamp TEXT NOT NULL
                )
                '''
            )

            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_pr_reminders_repo_status '
                'ON pr_reminders(repo, status)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_pr_reminders_next '
                'ON pr_reminders(next_reminder_at) '
                'WHERE status = \'active\''
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_reminder_history_pr '
                'ON reminder_history(repo, pr_number, timestamp DESC)'
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upsert_pr(
        self,
        repo: str,
        pr_number: int,
        pr_title: str,
        pr_url: str,
        author_github: str,
        reviewers_github: str,
        created_at: str,
    ) -> Dict[str, Any]:
        '''Insert or update a PR tracking record. Returns the row dict.'''
        conn = self._require_conn()

        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO pr_reminders
                    (repo, pr_number, pr_title, pr_url, author_github,
                     reviewers_github, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(repo, pr_number)
                DO UPDATE SET
                    pr_title = excluded.pr_title,
                    pr_url = excluded.pr_url,
                    author_github = excluded.author_github,
                    reviewers_github = excluded.reviewers_github,
                    created_at = excluded.created_at
                ''',
                (repo, pr_number, pr_title, pr_url, author_github,
                 reviewers_github, created_at),
            )
            conn.commit()

            cursor.execute(
                'SELECT * FROM pr_reminders WHERE repo = ? AND pr_number = ?',
                (repo, pr_number),
            )
            row = cursor.fetchone()

        return self._row_to_dict(row)

    def get_pr(self, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        '''Get a single PR reminder record. Returns dict or None.'''
        conn = self._require_conn()

        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM pr_reminders WHERE repo = ? AND pr_number = ?',
                (repo, pr_number),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_dict(row)

    def get_due_reminders(
        self, as_of: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        '''Return all active PRs where next_reminder_at <= as_of and not snoozed.

        Defaults as_of to now if not provided.
        '''
        now = as_of or self._utc_now_iso()
        conn = self._require_conn()

        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT * FROM pr_reminders
                WHERE status = 'active'
                  AND next_reminder_at IS NOT NULL
                  AND next_reminder_at <= ?
                  AND (snoozed_until IS NULL OR snoozed_until <= ?)
                ORDER BY next_reminder_at ASC
                ''',
                (now, now),
            )
            rows = cursor.fetchall()

        return [self._row_to_dict(r) for r in rows]

    def record_reminder(
        self,
        repo: str,
        pr_number: int,
        target_user: str,
    ) -> None:
        '''Increment reminder_count, update timestamps, log to history.'''
        now = self._utc_now_iso()
        conn = self._require_conn()

        with self._lock:
            cursor = conn.cursor()

            cursor.execute(
                '''
                UPDATE pr_reminders
                SET reminder_count = reminder_count + 1,
                    last_reminded_at = ?,
                    first_reminded_at = COALESCE(first_reminded_at, ?)
                WHERE repo = ? AND pr_number = ?
                ''',
                (now, now, repo, pr_number),
            )

            cursor.execute(
                '''
                INSERT INTO reminder_history
                    (repo, pr_number, action, target_user, timestamp)
                VALUES (?, ?, 'reminded', ?, ?)
                ''',
                (repo, pr_number, target_user, now),
            )
            conn.commit()

    def snooze_pr(
        self,
        repo: str,
        pr_number: int,
        snooze_until: str,
        snoozed_by: str,
    ) -> None:
        '''Set snoozed_until, snoozed_by, status=snoozed. Log to history.'''
        now = self._utc_now_iso()
        conn = self._require_conn()

        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                UPDATE pr_reminders
                SET snoozed_until = ?,
                    snoozed_by = ?,
                    status = 'snoozed'
                WHERE repo = ? AND pr_number = ?
                ''',
                (snooze_until, snoozed_by, repo, pr_number),
            )
            cursor.execute(
                '''
                INSERT INTO reminder_history
                    (repo, pr_number, action, target_user, details_json, timestamp)
                VALUES (?, ?, 'snoozed', ?, ?, ?)
                ''',
                (
                    repo,
                    pr_number,
                    snoozed_by,
                    json.dumps({'snooze_until': snooze_until}, sort_keys=True),
                    now,
                ),
            )
            conn.commit()

    def unsnooze_expired(
        self, as_of: Optional[str] = None,
    ) -> int:
        '''Reactivate snoozed PRs whose snooze window has elapsed.

        Returns the count of unsnoozes performed.
        '''
        now = as_of or self._utc_now_iso()
        conn = self._require_conn()

        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                UPDATE pr_reminders
                SET status = 'active',
                    snoozed_until = NULL
                WHERE status = 'snoozed'
                  AND snoozed_until IS NOT NULL
                  AND snoozed_until <= ?
                ''',
                (now,),
            )
            count = cursor.rowcount
            conn.commit()

        return count

    def mark_closed(
        self,
        repo: str,
        pr_number: int,
        action: str = 'closed',
    ) -> None:
        '''Set status to closed or merged. Log to history.'''
        now = self._utc_now_iso()
        conn = self._require_conn()

        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                UPDATE pr_reminders
                SET status = ?
                WHERE repo = ? AND pr_number = ?
                ''',
                (action, repo, pr_number),
            )
            cursor.execute(
                '''
                INSERT INTO reminder_history
                    (repo, pr_number, action, timestamp)
                VALUES (?, ?, ?, ?)
                ''',
                (repo, pr_number, action, now),
            )
            conn.commit()

    def schedule_next_reminder(
        self,
        repo: str,
        pr_number: int,
        next_at: str,
    ) -> None:
        '''Update next_reminder_at for a PR.'''
        conn = self._require_conn()

        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                UPDATE pr_reminders
                SET next_reminder_at = ?
                WHERE repo = ? AND pr_number = ?
                ''',
                (next_at, repo, pr_number),
            )
            conn.commit()

    def get_history(
        self,
        repo: Optional[str] = None,
        pr_number: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        '''Query reminder_history with optional filters. Returns list of dicts.'''
        conn = self._require_conn()

        query = (
            'SELECT id, repo, pr_number, action, target_user, '
            'details_json, timestamp '
            'FROM reminder_history WHERE 1=1'
        )
        params: list[Any] = []

        if repo:
            query += ' AND repo = ?'
            params.append(repo)

        if pr_number is not None:
            query += ' AND pr_number = ?'
            params.append(pr_number)

        query += ' ORDER BY timestamp DESC, id DESC LIMIT ?'
        params.append(limit)

        with self._lock:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        results: List[Dict[str, Any]] = []
        for row in rows:
            payload = row['details_json']
            parsed = json.loads(payload) if payload else {}
            results.append({
                'id': int(row['id']),
                'repo': str(row['repo']),
                'pr_number': int(row['pr_number']),
                'action': str(row['action']),
                'target_user': str(row['target_user']),
                'details': parsed,
                'timestamp': str(row['timestamp']),
            })

        return results

    def list_active(
        self,
        repo: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        '''List all active (non-closed, non-merged) PRs. Returns list of dicts.'''
        conn = self._require_conn()

        query = (
            'SELECT * FROM pr_reminders '
            'WHERE status NOT IN (\'closed\', \'merged\')'
        )
        params: list[Any] = []

        if repo:
            query += ' AND repo = ?'
            params.append(repo)

        query += ' ORDER BY next_reminder_at ASC NULLS LAST LIMIT ?'
        params.append(limit)

        with self._lock:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_dict(r) for r in rows]

    def reset(self) -> None:
        '''Delete all data from both tables.'''
        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM pr_reminders')
            cursor.execute('DELETE FROM reminder_history')
            conn.commit()

    def close(self) -> None:
        '''Close the SQLite connection.'''
        if self.conn is None:
            return
        with self._lock:
            self.conn.close()
            self.conn = None
