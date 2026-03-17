"""Standard status endpoints that every agent exposes.

These endpoints are what Shannon routes /token-status, /stats, etc. to.
Each agent registers a StatusProvider on app.state that supplies the
actual data; the endpoints here handle serialization and HTTP concerns.

Agents that don't yet have a provider get sensible placeholder responses.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel

status_router = APIRouter()


class TokenStatus(BaseModel):
    """Token usage and cost summary for an agent."""

    agent_id: str
    today_input_tokens: int
    today_output_tokens: int
    today_cost_usd: float
    cumulative_input_tokens: int
    cumulative_output_tokens: int
    cumulative_cost_usd: float
    efficiency_ratio: float  # deterministic_actions / total_actions
    seven_day_avg_cost_usd: float


class OperationalStats(BaseModel):
    """Operational statistics for monitoring dashboards."""

    agent_id: str
    uptime_seconds: int
    total_actions_today: int
    total_actions_week: int
    total_actions_month: int
    success_rate: float
    avg_latency_ms: float
    queue_depth: int
    active_jobs: int
    error_rate_trend: str  # "increasing", "stable", "decreasing"


class WorkSummary(BaseModel):
    """Daily work summary for an agent."""

    agent_id: str
    date: str
    jobs_processed: int
    key_outcomes: list[str]
    notable_decisions: list[str]
    failures: list[str]
    blocked_items: list[str]


class LoadStatus(BaseModel):
    """Current load / capacity status."""

    agent_id: str
    status: str  # "idle", "working", "busy", "overloaded"
    active_jobs: int
    queue_depth: int
    estimated_drain_minutes: float | None = None


class DecisionSummary(BaseModel):
    """High-level record of an autonomous decision."""

    decision_id: str
    timestamp: datetime
    decision_type: str
    inputs: dict[str, object]
    candidates: list[str]
    selected: str
    rationale: str


class DecisionDetail(DecisionSummary):
    """Full audit trail for a single decision."""

    rules_evaluated: list[str]
    alternatives_rejected: list[dict[str, object]]
    source_data_links: list[str]


def _agent_id(request: Request) -> str:
    return getattr(request.app.state, "agent_id", "unknown")


@status_router.get("/tokens", response_model=TokenStatus)
async def get_token_status(request: Request):
    """Get token usage summary. Delegates to app.state.status_provider if registered."""
    provider = getattr(request.app.state, "status_provider", None)
    if provider and hasattr(provider, "get_token_status"):
        return await provider.get_token_status()

    return TokenStatus(
        agent_id=_agent_id(request),
        today_input_tokens=0,
        today_output_tokens=0,
        today_cost_usd=0.0,
        cumulative_input_tokens=0,
        cumulative_output_tokens=0,
        cumulative_cost_usd=0.0,
        efficiency_ratio=0.0,
        seven_day_avg_cost_usd=0.0,
    )


@status_router.get("/stats", response_model=OperationalStats)
async def get_stats(request: Request):
    """Get operational statistics."""
    provider = getattr(request.app.state, "status_provider", None)
    if provider and hasattr(provider, "get_stats"):
        return await provider.get_stats()

    return OperationalStats(
        agent_id=_agent_id(request),
        uptime_seconds=0,
        total_actions_today=0,
        total_actions_week=0,
        total_actions_month=0,
        success_rate=0.0,
        avg_latency_ms=0.0,
        queue_depth=0,
        active_jobs=0,
        error_rate_trend="stable",
    )


@status_router.get("/work-summary", response_model=WorkSummary)
async def get_work_summary(request: Request):
    """Get today's work summary."""
    provider = getattr(request.app.state, "status_provider", None)
    if provider and hasattr(provider, "get_work_summary"):
        return await provider.get_work_summary()

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return WorkSummary(
        agent_id=_agent_id(request),
        date=today,
        jobs_processed=0,
        key_outcomes=[],
        notable_decisions=[],
        failures=[],
        blocked_items=[],
    )


@status_router.get("/load", response_model=LoadStatus)
async def get_load(request: Request):
    """Get current load status."""
    provider = getattr(request.app.state, "status_provider", None)
    if provider and hasattr(provider, "get_load"):
        return await provider.get_load()

    return LoadStatus(
        agent_id=_agent_id(request),
        status="idle",
        active_jobs=0,
        queue_depth=0,
        estimated_drain_minutes=None,
    )


@status_router.get("/decisions", response_model=list[DecisionSummary])
async def get_decisions(request: Request, limit: int = 20):
    """Get recent decisions.

    Args:
        limit: Maximum number of decisions to return (default 20).
    """
    provider = getattr(request.app.state, "status_provider", None)
    if provider and hasattr(provider, "get_decisions"):
        return await provider.get_decisions(limit=limit)

    return []


@status_router.get("/decisions/{decision_id}", response_model=DecisionDetail)
async def get_decision_detail(request: Request, decision_id: str):
    """Get detailed decision breakdown.

    Args:
        decision_id: Unique identifier of the decision to retrieve.
    """
    provider = getattr(request.app.state, "status_provider", None)
    if provider and hasattr(provider, "get_decision_detail"):
        return await provider.get_decision_detail(decision_id)

    return DecisionDetail(
        decision_id=decision_id,
        timestamp=datetime.now(UTC),
        decision_type="unknown",
        inputs={},
        candidates=[],
        selected="",
        rationale="No status provider registered",
        rules_evaluated=[],
        alternatives_rejected=[],
        source_data_links=[],
    )
