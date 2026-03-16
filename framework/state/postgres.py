"""PostgreSQL-backed state persistence for agents.

Provides the same key-value and session interface as the SQLite layer
in state/persistence.py, but uses asyncpg for async PostgreSQL access.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

import asyncpg  # type: ignore[import-untyped]

log = logging.getLogger(os.path.basename(sys.argv[0]))

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class PostgresStateBackend:
    """PostgreSQL-backed state persistence for agents.

    Mirrors the key-value and session operations of SQLitePersistence
    while adding async support and richer session metadata via JSONB.
    """

    def __init__(self, db_url: str, agent_id: str) -> None:
        self._db_url = db_url
        self._agent_id = agent_id
        self._pool: Optional[asyncpg.Pool] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(self._db_url, min_size=1, max_size=5)
        await self._ensure_schema()
        log.debug("PostgresStateBackend connected for agent=%s", self._agent_id)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
            log.debug("PostgresStateBackend closed for agent=%s", self._agent_id)

    async def _ensure_schema(self) -> None:
        """Apply the DDL from schema.sql idempotently (IF NOT EXISTS)."""
        ddl = _SCHEMA_PATH.read_text()
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(ddl)

    def _require_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("PostgresStateBackend.connect() has not been called")
        return self._pool

    # ------------------------------------------------------------------
    # Key-value state
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Optional[str]:
        pool = self._require_pool()
        row = await pool.fetchrow(
            "SELECT value FROM agent_state WHERE agent_id = $1 AND key = $2",
            self._agent_id,
            key,
        )
        return row["value"] if row else None

    async def set(self, key: str, value: str) -> None:
        pool = self._require_pool()
        await pool.execute(
            """
            INSERT INTO agent_state (agent_id, key, value, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (agent_id, key)
            DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
            """,
            self._agent_id,
            key,
            value,
        )

    async def delete(self, key: str) -> None:
        pool = self._require_pool()
        await pool.execute(
            "DELETE FROM agent_state WHERE agent_id = $1 AND key = $2",
            self._agent_id,
            key,
        )

    async def list_keys(self, prefix: str = "") -> list[str]:
        pool = self._require_pool()
        rows = await pool.fetch(
            "SELECT key FROM agent_state WHERE agent_id = $1 AND key LIKE $2 ORDER BY key",
            self._agent_id,
            f"{prefix}%",
        )
        return [r["key"] for r in rows]

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    async def create_session(
        self, session_id: str, metadata: Optional[dict[str, Any]] = None
    ) -> None:
        pool = self._require_pool()
        await pool.execute(
            """
            INSERT INTO agent_sessions (session_id, agent_id, metadata, created_at, updated_at)
            VALUES ($1, $2, $3::jsonb, NOW(), NOW())
            ON CONFLICT (session_id) DO NOTHING
            """,
            session_id,
            self._agent_id,
            json.dumps(metadata or {}),
        )

    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        pool = self._require_pool()
        row = await pool.fetchrow(
            "SELECT session_id, agent_id, metadata, data, created_at, updated_at "
            "FROM agent_sessions WHERE session_id = $1",
            session_id,
        )
        if not row:
            return None
        return {
            "session_id": row["session_id"],
            "agent_id": row["agent_id"],
            "metadata": json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
            "data": json.loads(row["data"]) if isinstance(row["data"], str) else row["data"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

    async def update_session(self, session_id: str, data: dict[str, Any]) -> None:
        pool = self._require_pool()
        await pool.execute(
            """
            UPDATE agent_sessions
            SET data = $2::jsonb, updated_at = NOW()
            WHERE session_id = $1
            """,
            session_id,
            json.dumps(data),
        )

    async def list_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        pool = self._require_pool()
        rows = await pool.fetch(
            "SELECT session_id, agent_id, metadata, data, created_at, updated_at "
            "FROM agent_sessions WHERE agent_id = $1 "
            "ORDER BY updated_at DESC LIMIT $2",
            self._agent_id,
            limit,
        )
        return [
            {
                "session_id": r["session_id"],
                "agent_id": r["agent_id"],
                "metadata": json.loads(r["metadata"]) if isinstance(r["metadata"], str) else r["metadata"],
                "data": json.loads(r["data"]) if isinstance(r["data"], str) else r["data"],
                "created_at": r["created_at"].isoformat(),
                "updated_at": r["updated_at"].isoformat(),
            }
            for r in rows
        ]
