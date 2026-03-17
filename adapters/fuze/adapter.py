"""
Fuze build/test system adapter interface and CLI implementation skeleton.

Provides:
    FuzeAdapter    — ABC defining the Fuze integration surface.
    FuzeCLIAdapter — Concrete skeleton wrapping the Fuze CLI.
"""

from abc import ABC, abstractmethod
from typing import Any


class FuzeAdapter(ABC):
    """Interface for the Fuze build/test system.

    Fuze is the source of build configuration truth and internal build identity.
    This adapter covers build submission, status polling, artifact retrieval,
    release version lookup, and test execution.
    """

    @abstractmethod
    async def submit_build(self, config: dict[str, Any]) -> str:
        ...

    @abstractmethod
    async def get_build_status(self, build_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_build_artifacts(self, build_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_release_version(self, build_id: str) -> str | None:
        ...

    @abstractmethod
    async def run_test_dry_run(self, config: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def execute_test(self, config: dict[str, Any]) -> dict[str, Any]:
        ...


class FuzeCLIAdapter(FuzeAdapter):
    """Wraps the Fuze CLI as a library.

    Invokes Fuze CLI commands via subprocess and parses structured output.
    """

    def __init__(
        self,
        fuze_bin: str = "fuze",
        config_dir: str | None = None,
    ) -> None:
        self.fuze_bin: str = fuze_bin
        self.config_dir: str | None = config_dir

    async def submit_build(self, config: dict[str, Any]) -> str:
        raise NotImplementedError

    async def get_build_status(self, build_id: str) -> dict[str, Any]:
        raise NotImplementedError

    async def get_build_artifacts(self, build_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def get_release_version(self, build_id: str) -> str | None:
        raise NotImplementedError

    async def run_test_dry_run(self, config: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def execute_test(self, config: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
