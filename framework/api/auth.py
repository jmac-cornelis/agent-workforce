"""Service principal authentication for agent APIs.

Provides API-key-based authentication via the X-Agent-API-Key header.
Each key maps to a ServicePrincipal with an agent_id and a set of
scopes that control access to protected endpoints.

Usage in an agent router:
    from framework.api.auth import verify_api_key, require_scope, ServicePrincipal

    @router.post("/do-thing")
    async def do_thing(principal: ServicePrincipal = Depends(verify_api_key)):
        ...

    @router.post("/admin-thing")
    async def admin_thing(principal: ServicePrincipal = Depends(require_scope("admin"))):
        ...
"""

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from typing import Optional

# Header name used across all agent APIs for authentication
api_key_header = APIKeyHeader(name="X-Agent-API-Key", auto_error=False)


class ServicePrincipal:
    """Represents an authenticated service caller.

    Attributes:
        agent_id: Identifier of the calling agent or service.
        scopes: List of permission scopes granted to this principal.
    """

    def __init__(self, agent_id: str, scopes: list[str]):
        self.agent_id = agent_id
        self.scopes = scopes

    def __repr__(self) -> str:
        return f"ServicePrincipal(agent_id={self.agent_id!r}, scopes={self.scopes!r})"


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> ServicePrincipal:
    """Verify the API key and return the service principal.

    Currently accepts any non-empty key and derives the agent_id from
    the key prefix (everything before the first dot). This will be
    replaced with a database/config lookup once the auth infrastructure
    is in place.

    Raises:
        HTTPException 401: If the API key is missing or empty.
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    # TODO: Look up key in database/config to resolve principal and scopes.
    # Placeholder: derive agent_id from key prefix, grant wildcard scope.
    agent_id = api_key.split(".")[0] if "." in api_key else "unknown"
    scopes = ["*"]  # Placeholder — real implementation restricts scopes

    return ServicePrincipal(agent_id=agent_id, scopes=scopes)


def require_scope(scope: str):
    """Dependency factory that requires a specific scope on the principal.

    Usage:
        @router.get("/protected")
        async def protected(principal = Depends(require_scope("admin"))):
            ...

    Args:
        scope: The scope string that must be present on the principal.

    Returns:
        An async dependency that resolves to a ServicePrincipal or raises 403.
    """

    async def check(
        principal: ServicePrincipal = Depends(verify_api_key),
    ) -> ServicePrincipal:
        # Wildcard scope grants everything
        if "*" in principal.scopes:
            return principal
        if scope not in principal.scopes:
            raise HTTPException(
                status_code=403, detail=f"Missing required scope: {scope}"
            )
        return principal

    return check
