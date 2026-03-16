"""
GitHub adapter interface and REST implementation skeleton.

Provides:
    PREvent           — Pydantic model for pull request webhook payloads.
    GitHubAdapter     — ABC defining the GitHub integration surface.
    GitHubRESTAdapter — Concrete skeleton that calls the GitHub REST API.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class PREvent(BaseModel):
    """Normalized pull-request event received from a GitHub webhook."""

    pr_number: int = Field(..., description="Pull request number")
    repo: str = Field(..., description="Full repo name, e.g. 'org/repo'")
    branch: str = Field(..., description="Head branch of the PR")
    author: str = Field(..., description="GitHub login of the PR author")
    title: str = Field(..., description="PR title")
    action: str = Field(
        ...,
        description="Webhook action: opened, synchronize, closed, merged",
    )
    commit_sha: str = Field(..., description="HEAD commit SHA of the PR branch")
    diff_url: str | None = Field(
        None, description="URL to fetch the raw diff"
    )


class GitHubAdapter(ABC):
    """Interface for GitHub integration.

    All methods are async to support non-blocking I/O in the FastAPI
    service layer.
    """

    @abstractmethod
    async def get_pr_diff(self, repo: str, pr_number: int) -> str:
        ...

    @abstractmethod
    async def post_status_check(
        self,
        repo: str,
        sha: str,
        state: str,
        context: str,
        description: str,
        target_url: str | None = None,
    ) -> None:
        ...

    @abstractmethod
    async def post_pr_comment(
        self, repo: str, pr_number: int, body: str
    ) -> None:
        ...

    @abstractmethod
    async def post_inline_comment(
        self,
        repo: str,
        pr_number: int,
        path: str,
        line: int,
        body: str,
    ) -> None:
        ...


class GitHubRESTAdapter(GitHubAdapter):
    """GitHub REST API implementation.

    Uses a personal-access or GitHub-App token for authentication.
    All methods are skeleton stubs.
    """

    def __init__(
        self,
        token: str,
        base_url: str = "https://api.github.com",
    ) -> None:
        self.token: str = token
        self.base_url: str = base_url.rstrip("/")
        self._headers: dict[str, str] = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_pr_diff(self, repo: str, pr_number: int) -> str:
        raise NotImplementedError

    async def post_status_check(
        self,
        repo: str,
        sha: str,
        state: str,
        context: str,
        description: str,
        target_url: str | None = None,
    ) -> None:
        raise NotImplementedError

    async def post_pr_comment(
        self, repo: str, pr_number: int, body: str
    ) -> None:
        raise NotImplementedError

    async def post_inline_comment(
        self,
        repo: str,
        pr_number: int,
        path: str,
        line: int,
        body: str,
    ) -> None:
        raise NotImplementedError
