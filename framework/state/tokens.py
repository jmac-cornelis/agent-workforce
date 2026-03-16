"""LLM token usage tracking per agent.

Records every LLM call (input/output tokens, cost, latency) and every
deterministic action so the /token-status endpoint can report efficiency
ratios, daily summaries, and rolling averages.
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import asyncpg  # type: ignore[import-untyped]

log = logging.getLogger(os.path.basename(sys.argv[0]))


class TokenTracker:
    """Tracks LLM token usage per agent in PostgreSQL.

    Each record represents either an LLM call (with token counts, model,
    latency, cost) or a deterministic action (is_deterministic=True,
    zero tokens/cost).  Aggregation queries power the /token-status API.
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
            raise RuntimeError("TokenTracker.connect() has not been called")
        return self._pool

    async def record_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        latency_ms: float,
        cost_usd: float,
        operation: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        pool = self._require_pool()
        corr = uuid.UUID(correlation_id) if correlation_id else None
        await pool.execute(
            """
            INSERT INTO token_usage
                (agent_id, operation, input_tokens, output_tokens,
                 model, latency_ms, cost_usd, is_deterministic, correlation_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, FALSE, $8)
            """,
            self._agent_id,
            operation,
            input_tokens,
            output_tokens,
            model,
            latency_ms,
            cost_usd,
            corr,
        )

    async def record_deterministic_action(
        self,
        operation: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        pool = self._require_pool()
        corr = uuid.UUID(correlation_id) if correlation_id else None
        await pool.execute(
            """
            INSERT INTO token_usage
                (agent_id, operation, input_tokens, output_tokens,
                 cost_usd, is_deterministic, correlation_id)
            VALUES ($1, $2, 0, 0, 0, TRUE, $3)
            """,
            self._agent_id,
            operation,
            corr,
        )

    async def get_today_summary(self) -> dict[str, Any]:
        """Aggregate today's usage: tokens, cost, LLM vs deterministic counts."""
        pool = self._require_pool()
        today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
        row = await pool.fetchrow(
            """
            SELECT
                COALESCE(SUM(input_tokens), 0)                          AS input_tokens,
                COALESCE(SUM(output_tokens), 0)                         AS output_tokens,
                COALESCE(SUM(cost_usd), 0)                              AS cost_usd,
                COUNT(*) FILTER (WHERE is_deterministic = TRUE)         AS deterministic_count,
                COUNT(*) FILTER (WHERE is_deterministic = FALSE)        AS llm_count
            FROM token_usage
            WHERE agent_id = $1 AND created_at >= $2
            """,
            self._agent_id,
            today_start,
        )
        assert row is not None
        total = row["deterministic_count"] + row["llm_count"]
        efficiency = (
            round(row["deterministic_count"] / total, 4) if total > 0 else 0.0
        )
        return {
            "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
            "cost_usd": round(float(row["cost_usd"]), 6),
            "deterministic_count": row["deterministic_count"],
            "llm_count": row["llm_count"],
            "efficiency_ratio": efficiency,
        }

    async def get_cumulative(self) -> dict[str, Any]:
        pool = self._require_pool()
        row = await pool.fetchrow(
            """
            SELECT
                COALESCE(SUM(input_tokens), 0)                          AS input_tokens,
                COALESCE(SUM(output_tokens), 0)                         AS output_tokens,
                COALESCE(SUM(cost_usd), 0)                              AS cost_usd,
                COUNT(*) FILTER (WHERE is_deterministic = TRUE)         AS deterministic_count,
                COUNT(*) FILTER (WHERE is_deterministic = FALSE)        AS llm_count,
                MIN(created_at)                                         AS first_recorded,
                MAX(created_at)                                         AS last_recorded
            FROM token_usage
            WHERE agent_id = $1
            """,
            self._agent_id,
        )
        assert row is not None
        total = row["deterministic_count"] + row["llm_count"]
        efficiency = (
            round(row["deterministic_count"] / total, 4) if total > 0 else 0.0
        )
        return {
            "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
            "cost_usd": round(float(row["cost_usd"]), 6),
            "deterministic_count": row["deterministic_count"],
            "llm_count": row["llm_count"],
            "efficiency_ratio": efficiency,
            "first_recorded": row["first_recorded"].isoformat() if row["first_recorded"] else None,
            "last_recorded": row["last_recorded"].isoformat() if row["last_recorded"] else None,
        }

    async def get_seven_day_average(self) -> dict[str, Any]:
        """Rolling 7-day daily average for tokens, cost, and action counts."""
        pool = self._require_pool()
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)
        row = await pool.fetchrow(
            """
            WITH daily AS (
                SELECT
                    DATE(created_at AT TIME ZONE 'UTC') AS day,
                    SUM(input_tokens)                   AS input_tokens,
                    SUM(output_tokens)                  AS output_tokens,
                    SUM(cost_usd)                       AS cost_usd,
                    COUNT(*) FILTER (WHERE is_deterministic = TRUE)  AS deterministic_count,
                    COUNT(*) FILTER (WHERE is_deterministic = FALSE) AS llm_count
                FROM token_usage
                WHERE agent_id = $1 AND created_at >= $2
                GROUP BY day
            )
            SELECT
                COALESCE(AVG(input_tokens), 0)          AS avg_input_tokens,
                COALESCE(AVG(output_tokens), 0)         AS avg_output_tokens,
                COALESCE(AVG(cost_usd), 0)              AS avg_cost_usd,
                COALESCE(AVG(deterministic_count), 0)   AS avg_deterministic,
                COALESCE(AVG(llm_count), 0)             AS avg_llm,
                COUNT(*)                                AS days_with_activity
            FROM daily
            """,
            self._agent_id,
            cutoff,
        )
        assert row is not None
        avg_det = float(row["avg_deterministic"])
        avg_llm = float(row["avg_llm"])
        avg_total = avg_det + avg_llm
        efficiency = round(avg_det / avg_total, 4) if avg_total > 0 else 0.0
        return {
            "avg_input_tokens_per_day": round(float(row["avg_input_tokens"]), 2),
            "avg_output_tokens_per_day": round(float(row["avg_output_tokens"]), 2),
            "avg_cost_usd_per_day": round(float(row["avg_cost_usd"]), 6),
            "avg_deterministic_per_day": round(avg_det, 2),
            "avg_llm_per_day": round(avg_llm, 2),
            "avg_efficiency_ratio": efficiency,
            "days_with_activity": row["days_with_activity"],
        }
