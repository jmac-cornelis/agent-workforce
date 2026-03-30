##########################################################################################
#
# Module: state/drucker_learning_store.py
#
# Description: Drucker-owned learning store for ticket-intake suggestions.
#              Tracks keyword/component patterns, reporter field habits, and
#              basic observation history for review-gated metadata suggestions.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

log = logging.getLogger(os.path.basename(sys.argv[0]))


class DruckerLearningStore:
    _STOPWORDS = {
        'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'onto', 'about',
        'are', 'was', 'were', 'have', 'has', 'had', 'will', 'would', 'could', 'should',
        'can', 'not', 'but', 'you', 'your', 'our', 'their', 'they', 'them', 'its',
        'issue', 'ticket', 'bug', 'story', 'task', 'subtask', 'sub', 'epic',
        'after', 'before', 'when', 'where', 'while', 'then', 'than', 'over', 'under',
        'new', 'old', 'set', 'gets', 'got', 'too', 'very', 'via', 'out', 'all',
        'open', 'close', 'closed', 'ready', 'todo', 'done', 'fix', 'fixed',
    }

    def __init__(
        self,
        db_path: str = 'data/drucker_learning.db',
        min_observations: int = 20,
    ):
        self.db_path = db_path
        self.min_observations = max(int(min_observations or 0), 1)
        self._lock = threading.RLock()
        self._ticket_keywords: Dict[str, list[str]] = {}

        if db_path != ':memory:':
            path = Path(db_path)
            path.parent.mkdir(parents=True, exist_ok=True)

        self.conn: Optional[sqlite3.Connection] = sqlite3.connect(
            db_path,
            check_same_thread=False,
        )
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_key TEXT NOT NULL,
                    field TEXT NOT NULL,
                    predicted_value TEXT,
                    actual_value TEXT,
                    correct INTEGER NOT NULL,
                    timestamp TEXT NOT NULL
                )
                '''
            )
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS keyword_patterns (
                    keyword TEXT NOT NULL,
                    field TEXT NOT NULL,
                    value TEXT NOT NULL,
                    hit_count INTEGER NOT NULL DEFAULT 0,
                    miss_count INTEGER NOT NULL DEFAULT 0,
                    confidence REAL NOT NULL DEFAULT 0.0,
                    PRIMARY KEY (keyword, field, value)
                )
                '''
            )
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS reporter_profiles (
                    reporter_id TEXT NOT NULL,
                    field TEXT NOT NULL,
                    value TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    total INTEGER NOT NULL DEFAULT 0,
                    compliance_rate REAL NOT NULL DEFAULT 0.0,
                    PRIMARY KEY (reporter_id, field, value)
                )
                '''
            )
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS learned_tickets (
                    ticket_key TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    learned_at TEXT NOT NULL,
                    PRIMARY KEY (ticket_key, fingerprint)
                )
                '''
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_drucker_obs_ticket_field '
                'ON observations(ticket_key, field)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_drucker_keyword_patterns '
                'ON keyword_patterns(field, keyword)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_drucker_reporter_profiles '
                'ON reporter_profiles(reporter_id, field, count DESC)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_drucker_learned_tickets_key '
                'ON learned_tickets(ticket_key)'
            )
            conn.commit()

    def _require_conn(self) -> sqlite3.Connection:
        if self.conn is None:
            raise RuntimeError('DruckerLearningStore connection is closed')
        return self.conn

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def set_min_observations(self, min_observations: int) -> None:
        self.min_observations = max(int(min_observations or 0), 1)

    @staticmethod
    def _normalize_field(field: str) -> str:
        lowered = str(field or '').strip().lower().replace('-', '_')

        if lowered in {'component', 'components'}:
            return 'components'
        if lowered in {'fix_version', 'fix_versions', 'fixversion', 'fixversions'}:
            return 'fix_versions'
        if lowered in {'priority', 'priority_name'}:
            return 'priority'

        return lowered

    def _extract_keywords(self, summary: str) -> list[str]:
        if not summary:
            return []

        tokens = re.split(r'[^a-zA-Z0-9]+', summary.lower())
        keywords: list[str] = []
        seen: set[str] = set()

        for token in tokens:
            if len(token) < 3:
                continue
            if token in self._STOPWORDS:
                continue
            if token in seen:
                continue
            seen.add(token)
            keywords.append(token)

        return keywords

    @staticmethod
    def _first_value(value: Any) -> str:
        if value is None:
            return ''

        if isinstance(value, list):
            if not value:
                return ''
            first = value[0]
            return str(first).strip() if first is not None else ''

        if isinstance(value, str):
            parts = [part.strip() for part in value.split(',')]
            return parts[0] if parts and parts[0] else ''

        return str(value).strip()

    def _update_keyword_pattern(self, keyword: str, field: str, value: str) -> None:
        normalized_keyword = keyword.strip().lower()
        normalized_field = self._normalize_field(field)
        normalized_value = (value or '').strip()

        if not normalized_keyword or not normalized_value:
            return

        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT hit_count, miss_count
                FROM keyword_patterns
                WHERE keyword = ? AND field = ? AND value = ?
                ''',
                (normalized_keyword, normalized_field, normalized_value),
            )
            row = cursor.fetchone()

            hit_count = int(row['hit_count']) if row else 0
            miss_count = int(row['miss_count']) if row else 0
            hit_count += 1
            confidence = hit_count / (hit_count + miss_count + 2)

            cursor.execute(
                '''
                INSERT INTO keyword_patterns (keyword, field, value, hit_count, miss_count, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(keyword, field, value)
                DO UPDATE SET
                    hit_count = excluded.hit_count,
                    miss_count = excluded.miss_count,
                    confidence = excluded.confidence
                ''',
                (
                    normalized_keyword,
                    normalized_field,
                    normalized_value,
                    hit_count,
                    miss_count,
                    confidence,
                ),
            )
            conn.commit()

    def _update_reporter_compliance(self, reporter_id: str, field: str, has_value: bool) -> None:
        normalized_reporter = (reporter_id or '').strip()
        normalized_field = self._normalize_field(field)

        if not normalized_reporter or not normalized_field:
            return

        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT count, total
                FROM reporter_profiles
                WHERE reporter_id = ? AND field = ? AND value = '__present__'
                ''',
                (normalized_reporter, normalized_field),
            )
            row = cursor.fetchone()

            current_count = int(row['count']) if row else 0
            current_total = int(row['total']) if row else 0

            if has_value:
                current_count += 1
            current_total += 1

            compliance_rate = current_count / current_total if current_total else 0.0

            cursor.execute(
                '''
                INSERT INTO reporter_profiles (reporter_id, field, value, count, total, compliance_rate)
                VALUES (?, ?, '__present__', ?, ?, ?)
                ON CONFLICT(reporter_id, field, value)
                DO UPDATE SET
                    count = excluded.count,
                    total = excluded.total,
                    compliance_rate = excluded.compliance_rate
                ''',
                (
                    normalized_reporter,
                    normalized_field,
                    current_count,
                    current_total,
                    compliance_rate,
                ),
            )
            conn.commit()

    def _update_reporter_value(self, reporter_id: str, field: str, value: str) -> None:
        normalized_reporter = (reporter_id or '').strip()
        normalized_field = self._normalize_field(field)
        normalized_value = (value or '').strip()

        if not normalized_reporter or not normalized_field or not normalized_value:
            return

        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT COALESCE(SUM(count), 0) AS total_count
                FROM reporter_profiles
                WHERE reporter_id = ? AND field = ? AND value != '__present__'
                ''',
                (normalized_reporter, normalized_field),
            )
            total_before = int(cursor.fetchone()['total_count'])
            total_after = total_before + 1

            cursor.execute(
                '''
                SELECT count
                FROM reporter_profiles
                WHERE reporter_id = ? AND field = ? AND value = ?
                ''',
                (normalized_reporter, normalized_field, normalized_value),
            )
            row = cursor.fetchone()
            value_count = int(row['count']) if row else 0
            new_value_count = value_count + 1

            cursor.execute(
                '''
                INSERT INTO reporter_profiles (reporter_id, field, value, count, total, compliance_rate)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(reporter_id, field, value)
                DO UPDATE SET
                    count = excluded.count,
                    total = excluded.total,
                    compliance_rate = excluded.compliance_rate
                ''',
                (
                    normalized_reporter,
                    normalized_field,
                    normalized_value,
                    new_value_count,
                    total_after,
                    new_value_count / total_after if total_after else 0.0,
                ),
            )

            cursor.execute(
                '''
                UPDATE reporter_profiles
                SET total = ?,
                    compliance_rate = CASE WHEN ? > 0 THEN CAST(count AS REAL) / ? ELSE 0.0 END
                WHERE reporter_id = ? AND field = ? AND value != '__present__'
                ''',
                (
                    total_after,
                    total_after,
                    total_after,
                    normalized_reporter,
                    normalized_field,
                ),
            )
            conn.commit()

    def _predict_from_reporter(self, field: str, ticket_dict: Dict[str, Any]) -> Tuple[str, float]:
        reporter_id = (
            str(ticket_dict.get('reporter_id') or '').strip()
            or str(ticket_dict.get('reporter') or '').strip()
            or str(ticket_dict.get('reporter_display') or '').strip()
        )
        if not reporter_id:
            return '', 0.0

        normalized_field = self._normalize_field(field)

        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT value, count, total
                FROM reporter_profiles
                WHERE reporter_id = ?
                  AND field = ?
                  AND value != '__present__'
                ORDER BY count DESC, value ASC
                LIMIT 1
                ''',
                (reporter_id, normalized_field),
            )
            row = cursor.fetchone()

        if not row:
            return '', 0.0

        count = int(row['count'])
        total = int(row['total'])
        if count < self.min_observations or total < self.min_observations:
            return '', 0.0

        confidence = count / (total + 2)
        return str(row['value']), confidence

    def predict_component(self, ticket_dict: Dict[str, Any]) -> Tuple[str, float]:
        summary = str(ticket_dict.get('summary') or '')
        keywords = self._extract_keywords(summary)

        weighted_sum: Dict[str, float] = {}
        total_weight: Dict[str, float] = {}

        if keywords:
            placeholders = ','.join(['?'] * len(keywords))
            params = ['components', *keywords]
            conn = self._require_conn()
            with self._lock:
                cursor = conn.cursor()
                cursor.execute(
                    (
                        'SELECT keyword, value, hit_count, miss_count, confidence '
                        'FROM keyword_patterns '
                        f'WHERE field = ? AND keyword IN ({placeholders})'
                    ),
                    params,
                )
                rows = cursor.fetchall()

            for row in rows:
                hit_count = int(row['hit_count'])
                miss_count = int(row['miss_count'])
                if hit_count < self.min_observations:
                    continue
                value = str(row['value'])
                confidence = float(row['confidence'])
                weight = float(hit_count + miss_count + 1)
                weighted_sum[value] = weighted_sum.get(value, 0.0) + confidence * weight
                total_weight[value] = total_weight.get(value, 0.0) + weight

        best_value = ''
        best_confidence = 0.0
        for value, value_weight_sum in weighted_sum.items():
            score = value_weight_sum / total_weight[value] if total_weight[value] else 0.0
            if score > best_confidence:
                best_confidence = score
                best_value = value

        reporter_value, reporter_confidence = self._predict_from_reporter(
            'components',
            ticket_dict,
        )
        if reporter_confidence > best_confidence:
            return reporter_value, reporter_confidence

        return best_value, best_confidence

    def get_field_prediction(self, field: str, ticket_dict: Dict[str, Any]) -> Tuple[str, float]:
        normalized_field = self._normalize_field(field)

        if normalized_field == 'components':
            return self.predict_component(ticket_dict)
        if normalized_field == 'fix_versions':
            return self._predict_from_reporter('fix_versions', ticket_dict)
        if normalized_field == 'priority':
            return self._predict_from_reporter('priority', ticket_dict)

        return '', 0.0

    def record_observation(
        self,
        ticket_key: str,
        field: str,
        predicted: str,
        actual: str,
        correct: bool,
    ) -> None:
        normalized_field = self._normalize_field(field)
        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO observations
                (ticket_key, field, predicted_value, actual_value, correct, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (
                    ticket_key,
                    normalized_field,
                    predicted or '',
                    actual or '',
                    1 if correct else 0,
                    self._utc_now_iso(),
                ),
            )
            conn.commit()

    @staticmethod
    def _ticket_fingerprint(ticket_dict: Dict[str, Any]) -> str:
        payload = {
            'summary': str(ticket_dict.get('summary') or '').strip(),
            'reporter_id': (
                str(ticket_dict.get('reporter_id') or '').strip()
                or str(ticket_dict.get('reporter') or '').strip()
                or str(ticket_dict.get('reporter_display') or '').strip()
            ),
            'components': [
                str(item).strip()
                for item in (ticket_dict.get('components') or [])
                if str(item).strip()
            ],
            'fix_versions': [
                str(item).strip()
                for item in (ticket_dict.get('fix_versions') or [])
                if str(item).strip()
            ],
            'priority': str(ticket_dict.get('priority') or '').strip(),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(encoded.encode('utf-8')).hexdigest()

    def _is_ticket_fingerprint_recorded(
        self,
        ticket_key: str,
        fingerprint: str,
    ) -> bool:
        if not ticket_key or not fingerprint:
            return False

        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT 1
                FROM learned_tickets
                WHERE ticket_key = ? AND fingerprint = ?
                LIMIT 1
                ''',
                (ticket_key, fingerprint),
            )
            return cursor.fetchone() is not None

    def _record_ticket_fingerprint(
        self,
        ticket_key: str,
        fingerprint: str,
    ) -> None:
        if not ticket_key or not fingerprint:
            return

        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT OR IGNORE INTO learned_tickets (ticket_key, fingerprint, learned_at)
                VALUES (?, ?, ?)
                ''',
                (ticket_key, fingerprint, self._utc_now_iso()),
            )
            conn.commit()

    def record_ticket(self, ticket_dict: Dict[str, Any]) -> None:
        ticket_key = str(ticket_dict.get('key') or '').strip()
        summary = str(ticket_dict.get('summary') or '')
        keywords = self._extract_keywords(summary)
        fingerprint = self._ticket_fingerprint(ticket_dict)

        if ticket_key and self._is_ticket_fingerprint_recorded(ticket_key, fingerprint):
            return

        if ticket_key:
            self._ticket_keywords[ticket_key] = keywords

        component = self._first_value(
            ticket_dict.get('components') or ticket_dict.get('component')
        )
        fix_version = self._first_value(
            ticket_dict.get('fix_versions') or ticket_dict.get('fix_version')
        )
        priority = self._first_value(ticket_dict.get('priority'))
        reporter_id = (
            str(ticket_dict.get('reporter_id') or '').strip()
            or str(ticket_dict.get('reporter') or '').strip()
            or str(ticket_dict.get('reporter_display') or '').strip()
        )

        if component:
            for keyword in keywords:
                self._update_keyword_pattern(keyword, 'components', component)

        if reporter_id:
            self._update_reporter_compliance(reporter_id, 'components', bool(component))
            self._update_reporter_compliance(reporter_id, 'fix_versions', bool(fix_version))
            self._update_reporter_compliance(reporter_id, 'priority', bool(priority))

            if component:
                self._update_reporter_value(reporter_id, 'components', component)
            if fix_version:
                self._update_reporter_value(reporter_id, 'fix_versions', fix_version)
            if priority:
                self._update_reporter_value(reporter_id, 'priority', priority)

        if ticket_key:
            self._record_ticket_fingerprint(ticket_key, fingerprint)

    def get_stats(self) -> Dict[str, Any]:
        table_names = [
            'observations',
            'keyword_patterns',
            'reporter_profiles',
            'learned_tickets',
        ]
        stats: Dict[str, Any] = {
            'tables': {},
            'observations': {
                'total': 0,
                'correct': 0,
                'accuracy': 0.0,
            },
        }

        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            for name in table_names:
                cursor.execute(f'SELECT COUNT(*) AS count FROM {name}')
                stats['tables'][name] = int(cursor.fetchone()['count'])

            cursor.execute('SELECT COUNT(*) AS count FROM observations')
            total_observations = int(cursor.fetchone()['count'])

            cursor.execute('SELECT COUNT(*) AS count FROM observations WHERE correct = 1')
            correct_observations = int(cursor.fetchone()['count'])

        stats['observations']['total'] = total_observations
        stats['observations']['correct'] = correct_observations
        stats['observations']['accuracy'] = (
            correct_observations / total_observations if total_observations else 0.0
        )
        return stats

    def reset(self) -> None:
        conn = self._require_conn()
        with self._lock:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM observations')
            cursor.execute('DELETE FROM keyword_patterns')
            cursor.execute('DELETE FROM reporter_profiles')
            cursor.execute('DELETE FROM learned_tickets')
            conn.commit()
        self._ticket_keywords = {}

    def close(self) -> None:
        with self._lock:
            if self.conn is not None:
                self.conn.close()
                self.conn = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
