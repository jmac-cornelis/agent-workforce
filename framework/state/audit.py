"""Decision and action audit logging to PostgreSQL.

Every agent action, decision, and rejection is recorded with full
provenance (correlation_id, decision tree, rationale) for the
/audit-trail and /decisions API endpoints.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

import asyncpg  # type: ignore[import-untyped]

log = logging.getLogger(os.path.basename(sys.argv[0]))


class AuditLogger:
    """Logs all agent actions and decisions to PostgreSQL.

    Requires that the schema from ``schema.sql`` has already been applied
    (PostgresStateBackend.connect() handles this automatically).
    """

    def __init__(self, db_url: str, agent_id: str) -> None:
        self._db_url = db_url
        self._agent_id = agent_id
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(self._db_url, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    def _require_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("AuditLogger.connect() has not been called")
        return self._pool

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    async def log_action(
        self,
        action: str,
        details: dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> str:
        pool = self._require_pool()
        action_id = str(uuid.uuid4())
        corr = uuid.UUID(correlation_id) if correlation_id else None
        await pool.execute(
            """
            INSERT INTO audit_actions (action_id, agent_id, action, details, correlation_id)
            VALUES ($1, $2, $3, $4::jsonb, $5)
            """,
            uuid.UUID(action_id),
            self._agent_id,
            action,
            json.dumps(details),
            corr,
        )
        return action_id

    async def get_actions_today(self) -> list[dict[str, Any]]:
        pool = self._require_pool()
        today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
        rows = await pool.fetch(
            """
            SELECT action_id, agent_id, action, details, correlation_id, created_at
            FROM audit_actions
            WHERE agent_id = $1 AND created_at >= $2
            ORDER BY created_at DESC
            """,
            self._agent_id,
            today_start,
        )
        return [_action_row_to_dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------------

    async def log_decision(
        self,
        decision_type: str,
        inputs: dict[str, Any],
        candidates: list[Any],
        selected: str,
        rationale: str,
        correlation_id: Optional[str] = None,
        rules_evaluated: Optional[list[Any]] = None,
        alternatives_rejected: Optional[list[Any]] = None,
        source_data_links: Optional[list[str]] = None,
    ) -> str:
        pool = self._require_pool()
        decision_id = str(uuid.uuid4())
        corr = uuid.UUID(correlation_id) if correlation_id else None
        await pool.execute(
            """
            INSERT INTO audit_decisions
                (decision_id, agent_id, decision_type, inputs, candidates,
                 selected, rationale, rules_evaluated, alternatives_rejected,
                 source_data_links, correlation_id)
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8::jsonb, $9::jsonb, $10::jsonb, $11)
            """,
            uuid.UUID(decision_id),
            self._agent_id,
            decision_type,
            json.dumps(inputs),
            json.dumps(candidates),
            selected,
            rationale,
            json.dumps(rules_evaluated or []),
            json.dumps(alternatives_rejected or []),
            json.dumps(source_data_links or []),
            corr,
        )
        return decision_id

    async def get_decisions(
        self, limit: int = 20, decision_type: Optional[str] = None
    ) -> list[dict[str, Any]]:
        pool = self._require_pool()
        if decision_type:
            rows = await pool.fetch(
                """
                SELECT decision_id, agent_id, decision_type, inputs, candidates,
                       selected, rationale, rules_evaluated, alternatives_rejected,
                       source_data_links, correlation_id, created_at
                FROM audit_decisions
                WHERE agent_id = $1 AND decision_type = $2
                ORDER BY created_at DESC LIMIT $3
                """,
                self._agent_id,
                decision_type,
                limit,
            )
        else:
            rows = await pool.fetch(
                """
                SELECT decision_id, agent_id, decision_type, inputs, candidates,
                       selected, rationale, rules_evaluated, alternatives_rejected,
                       source_data_links, correlation_id, created_at
                FROM audit_decisions
                WHERE agent_id = $1
                ORDER BY created_at DESC LIMIT $2
                """,
                self._agent_id,
                limit,
            )
        return [_decision_row_to_dict(r) for r in rows]

    async def get_decision(self, decision_id: str) -> Optional[dict[str, Any]]:
        pool = self._require_pool()
        row = await pool.fetchrow(
            """
            SELECT decision_id, agent_id, decision_type, inputs, candidates,
                   selected, rationale, rules_evaluated, alternatives_rejected,
                   source_data_links, correlation_id, created_at
            FROM audit_decisions
            WHERE decision_id = $1
            """,
            uuid.UUID(decision_id),
        )
        if not row:
            return None
        return _decision_row_to_dict(row)

    # ------------------------------------------------------------------
    # Rejections
    # ------------------------------------------------------------------

    async def log_rejection(
        self,
        action: str,
        blocked_by: str,
        alternative: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        pool = self._require_pool()
        rejection_id = str(uuid.uuid4())
        corr = uuid.UUID(correlation_id) if correlation_id else None
        await pool.execute(
            """
            INSERT INTO audit_rejections
                (rejection_id, agent_id, action, blocked_by, alternative, correlation_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            uuid.UUID(rejection_id),
            self._agent_id,
            action,
            blocked_by,
            alternative,
            corr,
        )
        return rejection_id


# ------------------------------------------------------------------
# Row → dict helpers
# ------------------------------------------------------------------

def _jsonb_field(row: asyncpg.Record, field: str) -> Any:
    val = row[field]
    if isinstance(val, str):
        return json.loads(val)
    return val


def _action_row_to_dict(row: asyncpg.Record) -> dict[str, Any]:
    return {
        "action_id": str(row["action_id"]),
        "agent_id": row["agent_id"],
        "action": row["action"],
        "details": _jsonb_field(row, "details"),
        "correlation_id": str(row["correlation_id"]) if row["correlation_id"] else None,
        "created_at": row["created_at"].isoformat(),
    }


def _decision_row_to_dict(row: asyncpg.Record) -> dict[str, Any]:
    return {
        "decision_id": str(row["decision_id"]),
        "agent_id": row["agent_id"],
        "decision_type": row["decision_type"],
        "inputs": _jsonb_field(row, "inputs"),
        "candidates": _jsonb_field(row, "candidates"),
        "selected": row["selected"],
        "rationale": row["rationale"],
        "rules_evaluated": _jsonb_field(row, "rules_evaluated"),
        "alternatives_rejected": _jsonb_field(row, "alternatives_rejected"),
        "source_data_links": _jsonb_field(row, "source_data_links"),
        "correlation_id": str(row["correlation_id"]) if row["correlation_id"] else None,
        "created_at": row["created_at"].isoformat(),
    }
