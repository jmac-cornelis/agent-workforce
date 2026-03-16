"""Publishes events to the PostgreSQL event store via asyncpg."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import asyncpg

from .envelope import EventEnvelope

logger = logging.getLogger(__name__)


class EventProducer:
    """Publishes events to the PostgreSQL event store.

    Usage::

        producer = EventProducer("josephine", db_url)
        await producer.connect()
        envelope = await producer.emit("build.completed", {"build_id": "123"})
        await producer.close()
    """

    def __init__(self, agent_id: str, db_url: str) -> None:
        self._agent_id = agent_id
        self._db_url = db_url
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(self._db_url, min_size=2, max_size=10)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    def _ensure_connected(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("EventProducer is not connected. Call connect() first.")
        return self._pool

    async def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        subject_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> EventEnvelope:
        """Create and publish an event. Returns the persisted envelope."""
        kwargs: dict[str, Any] = {
            "event_type": event_type,
            "producer": self._agent_id,
            "payload": payload,
            "subject_id": subject_id,
            "idempotency_key": idempotency_key,
        }
        if correlation_id is not None:
            kwargs["correlation_id"] = correlation_id
        envelope = EventEnvelope(**kwargs)
        await self.emit_envelope(envelope)
        return envelope

    async def emit_envelope(self, envelope: EventEnvelope) -> None:
        """Persist a pre-built envelope and fire pg_notify.

        The pg_notify trigger fires automatically via the database trigger
        defined in schema.sql, so we only need the INSERT here.
        """
        pool = self._ensure_connected()

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO events (
                    event_id, event_type, producer, occurred_at,
                    correlation_id, subject_id, payload,
                    schema_version, idempotency_key
                ) VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9)
                """,
                envelope.event_id,
                envelope.event_type,
                envelope.producer,
                envelope.occurred_at,
                envelope.correlation_id,
                envelope.subject_id,
                json.dumps(envelope.payload),
                envelope.schema_version,
                envelope.idempotency_key,
            )

        logger.info(
            "Event emitted: type=%s id=%s producer=%s subject=%s",
            envelope.event_type,
            envelope.event_id,
            envelope.producer,
            envelope.subject_id,
        )

    async def __aenter__(self) -> EventProducer:
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
