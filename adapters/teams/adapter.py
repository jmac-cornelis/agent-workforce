"""
Microsoft Teams adapter interface and Graph API implementation skeleton.

Provides:
    TeamsAdapter      — ABC defining the Teams integration surface.
    TeamsGraphAdapter — Concrete skeleton using Microsoft Graph API.
"""

from abc import ABC, abstractmethod
from typing import Any


class TeamsAdapter(ABC):
    """Interface for Microsoft Teams integration.

    Covers channel messaging, adaptive cards, threaded replies,
    and meeting transcript retrieval.
    """

    @abstractmethod
    async def post_message(self, channel_id: str, message: str) -> str:
        ...

    @abstractmethod
    async def post_adaptive_card(self, channel_id: str, card: dict[str, Any]) -> str:
        ...

    @abstractmethod
    async def reply_to_message(
        self, channel_id: str, message_id: str, reply: str
    ) -> str:
        ...

    @abstractmethod
    async def get_transcript(self, meeting_id: str) -> str:
        ...


class TeamsGraphAdapter(TeamsAdapter):
    """Microsoft Graph API implementation.

    Authenticates via OAuth2 client-credentials flow.
    All methods are skeleton stubs.
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        team_id: str | None = None,
    ) -> None:
        self.tenant_id: str = tenant_id
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.team_id: str | None = team_id
        self._base_url: str = "https://graph.microsoft.com/v1.0"
        self._access_token: str | None = None

    async def _ensure_token(self) -> str:
        if self._access_token is None:
            raise NotImplementedError("Token acquisition not yet implemented")
        return self._access_token

    async def post_message(self, channel_id: str, message: str) -> str:
        raise NotImplementedError

    async def post_adaptive_card(self, channel_id: str, card: dict[str, Any]) -> str:
        raise NotImplementedError

    async def reply_to_message(
        self, channel_id: str, message_id: str, reply: str
    ) -> str:
        raise NotImplementedError

    async def get_transcript(self, meeting_id: str) -> str:
        raise NotImplementedError
