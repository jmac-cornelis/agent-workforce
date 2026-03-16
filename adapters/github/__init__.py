"""GitHub adapter — PR events, status checks, review comments, webhooks."""

from .adapter import PREvent, GitHubAdapter, GitHubRESTAdapter

__all__ = ["PREvent", "GitHubAdapter", "GitHubRESTAdapter"]
