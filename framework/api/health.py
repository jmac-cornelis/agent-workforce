"""Health check endpoint for load balancers and monitoring.

Every agent exposes GET /health. The response includes per-component
health checks so operators can quickly identify degraded subsystems.

Agents register health-check callables on app.state.health_checks:
    app.state.health_checks = {
        "database": check_db,
        "redis": check_redis,
    }
Each callable should return "healthy", "degraded", or "unhealthy".
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Union

from fastapi import APIRouter, Request
from pydantic import BaseModel

HealthCheckFn = Callable[[], Union[str, Awaitable[str]]]

health_router = APIRouter()

_start_time = time.time()


class HealthResponse(BaseModel):
    """Structured health check response."""

    status: str  # "healthy", "degraded", "unhealthy"
    agent_id: str
    version: str
    uptime_seconds: int
    checks: dict[str, str]  # component name -> "healthy" | "degraded" | "unhealthy"


@health_router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Health check endpoint for load balancers and monitoring.

    Iterates over registered health-check callables and aggregates their
    results. Overall status is the worst individual status:
        all healthy  -> "healthy"
        any degraded -> "degraded"
        any unhealthy -> "unhealthy"
    """
    agent_id = getattr(request.app.state, "agent_id", "unknown")
    version = request.app.version

    checks: dict[str, str] = {}
    registered_checks: dict[str, HealthCheckFn] = getattr(
        request.app.state, "health_checks", {}
    )

    for component, check_fn in registered_checks.items():
        try:
            raw = check_fn()
            if isinstance(raw, str):
                checks[component] = raw
            else:
                checks[component] = await raw
        except Exception:
            checks[component] = "unhealthy"

    if not checks:
        overall = "healthy"
    elif any(v == "unhealthy" for v in checks.values()):
        overall = "unhealthy"
    elif any(v == "degraded" for v in checks.values()):
        overall = "degraded"
    else:
        overall = "healthy"

    uptime = int(time.time() - _start_time)

    return HealthResponse(
        status=overall,
        agent_id=agent_id,
        version=version,
        uptime_seconds=uptime,
        checks=checks,
    )
