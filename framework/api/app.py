"""Base FastAPI app factory that every agent uses.

Call create_agent_app() to get a FastAPI instance pre-configured with
standard middleware (correlation ID, request logging, metrics) and
standard routes (health check, status endpoints).

Agents extend the returned app by including their own routers:

    app = create_agent_app("triage", "Triage Agent", "Handles ticket triage")
    app.include_router(triage_router, prefix="/v1/triage", tags=["triage"])
"""

from fastapi import FastAPI

from .health import health_router
from .middleware import add_correlation_id, add_metrics, add_request_logging
from .status import status_router


def create_agent_app(
    agent_id: str,
    title: str,
    description: str,
    version: str = "0.1.0",
) -> FastAPI:
    """Create a FastAPI app for an agent with standard middleware and routes.

    Args:
        agent_id: Unique identifier for this agent (e.g. "shannon", "triage").
        title: Human-readable title shown in OpenAPI docs.
        description: Description shown in OpenAPI docs.
        version: Semantic version string for the agent API.

    Returns:
        A FastAPI instance ready for the agent to attach its own routers.
    """
    app = FastAPI(title=title, description=description, version=version)

    # Standard middleware — applied in reverse registration order, so
    # correlation_id runs first (outermost), then logging, then metrics.
    app.middleware("http")(add_metrics)
    app.middleware("http")(add_request_logging)
    app.middleware("http")(add_correlation_id)

    app.include_router(status_router, prefix="/v1/status", tags=["status"])
    app.include_router(health_router, tags=["health"])

    app.state.agent_id = agent_id

    return app
