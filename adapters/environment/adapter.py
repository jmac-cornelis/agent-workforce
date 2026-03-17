"""
Test environment adapter interface and ATF resource file implementation skeleton.

Provides:
    EnvironmentAdapter  — ABC defining the environment management surface.
    ATFResourceAdapter  — Concrete skeleton that parses ATF resource files.
"""

from abc import ABC, abstractmethod
from typing import Any


class EnvironmentAdapter(ABC):
    """Interface for test environment management.

    Exposes HIL rack availability, hardware identity, capability matrices,
    and health status. Backed by ATF resource files or a scheduling service.
    """

    @abstractmethod
    async def list_environments(
        self, capability_filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_environment(self, env_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def check_health(self, env_id: str) -> dict[str, Any]:
        ...


class ATFResourceAdapter(EnvironmentAdapter):
    """Parses ATF resource files for the environment catalog.

    Resource files describe HIL racks, mock topologies, and hardware
    capability matrices used by the test infrastructure.
    """

    def __init__(self, resource_dir: str) -> None:
        self.resource_dir: str = resource_dir

    async def list_environments(
        self, capability_filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def get_environment(self, env_id: str) -> dict[str, Any]:
        raise NotImplementedError

    async def check_health(self, env_id: str) -> dict[str, Any]:
        raise NotImplementedError
