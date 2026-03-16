"""Dead letter queue for events that failed processing."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg

from .envelope import EventEnvelope

logger = logging.getLogger(__name__)


class DeadLetterQueue:
    """Manages events that failed processing after exhausting retries.

    Can be constructed with either a db_url (creates its own pool) or
    an existing asyncpg.Pool (shared with EventConsumer).
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        pool: Optional[asyncpg.Pool] = None,
    ) -> None:
        if db_url is None and pool is None:
            raise ValueError("Provide either db_url or pool")
        self._db_url = db_url
        self._pool: Optional[asyncpg.Pool] = pool
        self._owns_pool = pool is None

    async def connect(self) -> None:
        if self._pool is None and self._db_url:
            self._pool = await asyncpg.create_pool(self._db_url, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._owns_pool and self._pool:
            await self._pool.close()
            self._pool = None

    def _ensure_connected(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("DeadLetterQueue is not connected. Call connect() first.")
        return self._pool

    async def add(
        self, envelope: EventEnvelope, error: str, consumer_id: str
    ) -> None:
        pool = self._ensure_connected()
        async with pool.acquire() as conn:
            # UPSERT: increment retry_count if already in DLQ, otherwise insert.
            await conn.execute(
                """
                INSERT INTO dead_letter_events (event_id, consumer_id, error_message, retry_count, last_retry_at)
                VALUES ($1, $2, $3, 1, $4)
                ON CONFLICT (event_id, consumer_id)
                DO UPDATE SET
                    error_message = EXCLUDED.error_message,
                    retry_count = dead_letter_events.retry_count + 1,
                    last_retry_at = EXCLUDED.last_retry_at
                """,
                envelope.event_id,
                consumer_id,
                error,
                datetime.now(timezone.utc),
            )
        logger.warning(
            "DLQ: event %s from consumer %s — %s",
            envelope.event_id,
            consumer_id,
            error,
        )

    async def list_events(self, limit: int = 50) -> list[dict[str, Any]]:
        pool = self._ensure_connected()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT dle.id, dle.event_id, dle.consumer_id,
                       dle.error_message, dle.retry_count,
                       dle.created_at, dle.last_retry_at,
                       e.event_type, e.producer, e.payload
                FROM dead_letter_events dle
                JOIN events e ON e.event_id = dle.event_id
                ORDER BY dle.created_at DESC
                LIMIT $1
                """,
                limit,
            )
        return [dict(row) for row in rows]

    async def retry(self, event_id: str) -> None:
        """Re-insert the event into the events table for reprocessing.

        The database trigger will fire pg_notify, causing consumers to
        pick it up again. The DLQ record is deleted on successful re-queue.
        """
        pool = self._ensure_connected()
        async with pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    SELECT e.* FROM events e
                    JOIN dead_letter_events dle ON dle.event_id = e.event_id
                    WHERE dle.event_id = $1
                    """,
                    event_id,
                )
                if row is None:
                    raise ValueError(f"Event {event_id} not found in DLQ")

                # Re-insert as a new row so the trigger fires again.
                await conn.execute(
                    """
                    INSERT INTO events (
                        event_id, event_type, producer, occurred_at,
                        correlation_id, subject_id, payload,
                        schema_version, idempotency_key
                    )
                    SELECT event_id, event_type, producer, occurred_at,
                           correlation_id, subject_id, payload,
                           schema_version, idempotency_key
                    FROM events WHERE event_id = $1
                    ON CONFLICT (event_id) DO UPDATE SET
                        created_at = NOW()
                    """,
                    event_id,
                )

                await conn.execute(
                    "DELETE FROM dead_letter_events WHERE event_id = $1", event_id
                )

        logger.info("DLQ: retried event %s", event_id)

    async def discard(self, event_id: str) -> None:
        pool = self._ensure_connected()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM dead_letter_events WHERE event_id = $1", event_id
            )
        if result == "DELETE 0":
            raise ValueError(f"Event {event_id} not found in DLQ")
        logger.info("DLQ: discarded event %s", event_id)

    async def depth(self) -> int:
        pool = self._ensure_connected()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT COUNT(*) AS cnt FROM dead_letter_events")
        return row["cnt"] if row else 0

    async def __aenter__(self) -> DeadLetterQueue:
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
