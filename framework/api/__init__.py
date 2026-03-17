"""Shared FastAPI framework for Jira agent APIs.

Provides the base app factory, authentication, standard status/health
endpoints, and middleware that every agent uses.
"""

from .app import create_agent_app
from .auth import ServicePrincipal, api_key_header, require_scope, verify_api_key
from .health import HealthResponse, health_router
from .middleware import add_correlation_id, add_metrics, add_request_logging
from .status import (
    DecisionDetail,
    DecisionSummary,
    LoadStatus,
    OperationalStats,
    TokenStatus,
    WorkSummary,
    status_router,
)

__all__ = [
    "create_agent_app",
    "ServicePrincipal",
    "api_key_header",
    "verify_api_key",
    "require_scope",
    "health_router",
    "HealthResponse",
    "status_router",
    "TokenStatus",
    "OperationalStats",
    "WorkSummary",
    "LoadStatus",
    "DecisionSummary",
    "DecisionDetail",
    "add_correlation_id",
    "add_request_logging",
    "add_metrics",
]
