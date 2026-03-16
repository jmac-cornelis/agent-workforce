"""Standard middleware for all agent APIs.

Provides correlation ID tracking, structured request logging, and metrics
collection. Every agent app created via create_agent_app() gets these
middleware automatically.
"""

import uuid
import time
import logging
from typing import Any, Callable, Coroutine
from fastapi import Request
from starlette.responses import Response

RequestResponseEndpoint = Callable[[Request], Coroutine[Any, Any, Response]]

logger = logging.getLogger("agent.api")


async def add_correlation_id(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    """Add correlation_id to every request.

    Uses the existing X-Correlation-ID header if provided by the caller
    (e.g., Shannon forwarding a request), otherwise generates a new UUID.
    The correlation ID is stored on request.state for downstream use and
    echoed back in the response header.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


async def add_request_logging(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    """Log every request with agent_id, method, path, and duration.

    Emits structured log entries suitable for aggregation by a central
    logging service. Duration is measured wall-clock in milliseconds.
    """
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000

    agent_id = getattr(request.app.state, "agent_id", "unknown")

    logger.info(
        "request",
        extra={
            "agent_id": agent_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "correlation_id": getattr(request.state, "correlation_id", None),
        },
    )
    return response


async def add_metrics(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    """Placeholder for Prometheus-compatible request metrics."""
    # TODO: Integrate with prometheus_client
    response = await call_next(request)
    return response
