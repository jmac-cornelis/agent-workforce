"""Subscribes to events from the PostgreSQL event store."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Awaitable, Callable, Optional

import asyncpg

from .dead_letter import DeadLetterQueue
from .envelope import EventEnvelope

logger = logging.getLogger(__name__)

EventHandler = Callable[[EventEnvelope], Awaitable[None]]

# Failed events are retried up to this many times before moving to the DLQ.
MAX_RETRIES = 3

# Polling interval in seconds — catches any pg_notify misses.
POLL_INTERVAL_SECONDS = 7


class EventConsumer:
    """Subscribes to events from the PostgreSQL event store.

    Dual delivery: real-time via pg_notify LISTEN, plus a periodic polling
    fallback that catches missed notifications. Processing is idempotent —
    events already consumed (by event_id) are skipped.

    Usage::

        consumer = EventConsumer("ada", db_url)
        consumer.subscribe("build.completed", handle_build)
        await consumer.start()
        # ... runs until stop() is called
        await consumer.stop()
    """

    def __init__(self, consumer_id: str, db_url: str) -> None:
        self._consumer_id = consumer_id
        self._db_url = db_url
        self._handlers: dict[str, list[EventHandler]] = {}
        self._pool: Optional[asyncpg.Pool] = None
        self._listen_conn: Optional[asyncpg.Connection] = None
        self._running = False
        self._poll_task: Optional[asyncio.Task[None]] = None
        self._processed_ids: set[str] = set()
        self._dlq: Optional[DeadLetterQueue] = None

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def start(self) -> None:
        self._pool = await asyncpg.create_pool(self._db_url, min_size=2, max_size=10)
        self._dlq = DeadLetterQueue(pool=self._pool)
        self._running = True

        await self._ensure_consumer_offset()

        listen_conn = await asyncpg.connect(self._db_url)
        self._listen_conn = listen_conn
        for event_type in self._handlers:
            await listen_conn.add_listener(event_type, self._on_notification)

        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info(
            "EventConsumer %s started, listening on %s",
            self._consumer_id,
            list(self._handlers.keys()),
        )

    async def stop(self) -> None:
        self._running = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        if self._listen_conn:
            for event_type in self._handlers:
                await self._listen_conn.remove_listener(event_type, self._on_notification)
            await self._listen_conn.close()
            self._listen_conn = None

        if self._pool:
            await self._pool.close()
            self._pool = None

        logger.info("EventConsumer %s stopped", self._consumer_id)

    # ------------------------------------------------------------------
    # pg_notify callback
    # ------------------------------------------------------------------

    def _on_notification(
        self,
        connection: asyncpg.Connection,
        pid: int,
        channel: str,
        payload: str,
    ) -> None:
        """Callback from pg_notify — schedules async event fetch + processing."""
        asyncio.ensure_future(self._fetch_and_process_by_event_id(payload))

    async def _fetch_and_process_by_event_id(self, event_id: str) -> None:
        pool = self._ensure_connected()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM events WHERE event_id = $1", event_id
            )
        if row:
            envelope = self._row_to_envelope(row)
            await self._process_event(envelope)

    # ------------------------------------------------------------------
    # Polling fallback
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._poll_new_events()
            except Exception:
                logger.exception("Poll loop error in consumer %s", self._consumer_id)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def _poll_new_events(self) -> None:
        pool = self._ensure_connected()
        subscribed_types = list(self._handlers.keys())
        if not subscribed_types:
            return

        async with pool.acquire() as conn:
            last_offset = await self._get_consumer_offset(conn)
            rows = await conn.fetch(
                """
                SELECT * FROM events
                WHERE id > $1 AND event_type = ANY($2::text[])
                ORDER BY id ASC
                LIMIT 100
                """,
                last_offset,
                subscribed_types,
            )

        for row in rows:
            envelope = self._row_to_envelope(row)
            await self._process_event(envelope, sequence_id=row["id"])

    # ------------------------------------------------------------------
    # Event processing (idempotent)
    # ------------------------------------------------------------------

    async def _process_event(
        self, envelope: EventEnvelope, sequence_id: Optional[int] = None
    ) -> None:
        if envelope.event_id in self._processed_ids:
            return

        handlers = self._handlers.get(envelope.event_type, [])
        if not handlers:
            return

        for handler in handlers:
            try:
                await handler(envelope)
            except Exception as exc:
                logger.error(
                    "Handler failed for event %s (type=%s): %s",
                    envelope.event_id,
                    envelope.event_type,
                    exc,
                )
                await self._handle_failure(envelope, str(exc))
                return

        self._processed_ids.add(envelope.event_id)

        if sequence_id is not None:
            await self._update_consumer_offset(sequence_id)

        logger.debug(
            "Processed event %s (type=%s) for consumer %s",
            envelope.event_id,
            envelope.event_type,
            self._consumer_id,
        )

    async def _handle_failure(self, envelope: EventEnvelope, error: str) -> None:
        """Increment retry count; move to DLQ after MAX_RETRIES."""
        pool = self._ensure_connected()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT retry_count FROM dead_letter_events
                WHERE event_id = $1 AND consumer_id = $2
                """,
                envelope.event_id,
                self._consumer_id,
            )

            if row and row["retry_count"] >= MAX_RETRIES:
                logger.warning(
                    "Event %s exceeded max retries (%d) for consumer %s — in DLQ",
                    envelope.event_id,
                    MAX_RETRIES,
                    self._consumer_id,
                )
                return

        if self._dlq:
            await self._dlq.add(envelope, error, self._consumer_id)

    # ------------------------------------------------------------------
    # Consumer offset management
    # ------------------------------------------------------------------

    async def _ensure_consumer_offset(self) -> None:
        pool = self._ensure_connected()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO consumer_offsets (consumer_id, last_event_id)
                VALUES ($1, 0)
                ON CONFLICT (consumer_id) DO NOTHING
                """,
                self._consumer_id,
            )

    async def _get_consumer_offset(self, conn: asyncpg.Connection) -> int:
        row = await conn.fetchrow(
            "SELECT last_event_id FROM consumer_offsets WHERE consumer_id = $1",
            self._consumer_id,
        )
        return row["last_event_id"] if row else 0

    async def _update_consumer_offset(self, sequence_id: int) -> None:
        pool = self._ensure_connected()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE consumer_offsets
                SET last_event_id = $1, updated_at = NOW()
                WHERE consumer_id = $2
                """,
                sequence_id,
                self._consumer_id,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ensure_connected(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("EventConsumer is not connected. Call start() first.")
        return self._pool

    @staticmethod
    def _row_to_envelope(row: asyncpg.Record) -> EventEnvelope:
        payload = row["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return EventEnvelope(
            event_id=str(row["event_id"]),
            event_type=row["event_type"],
            producer=row["producer"],
            occurred_at=row["occurred_at"],
            correlation_id=str(row["correlation_id"]),
            subject_id=row["subject_id"],
            payload=payload,
            schema_version=row["schema_version"],
            idempotency_key=row.get("idempotency_key"),
        )

    async def __aenter__(self) -> EventConsumer:
        await self.start()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.stop()
