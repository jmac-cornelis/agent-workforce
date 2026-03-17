"""GitHub webhook receiver — verifies HMAC-SHA256 signatures, parses events, publishes to event bus."""

import hashlib
import hmac
import logging
from typing import Any

from fastapi import APIRouter, Request, HTTPException, Header

from .adapter import PREvent

logger = logging.getLogger(__name__)

webhook_router = APIRouter(tags=["github-webhook"])

_webhook_secret: str | None = None


def configure_webhook_secret(secret: str) -> None:
    global _webhook_secret  # noqa: PLW0603
    _webhook_secret = secret


def _verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """HMAC-SHA256 verification — security-critical, must match GitHub's signing scheme."""
    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@webhook_router.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
) -> dict[str, Any]:
    body = await request.body()

    if _webhook_secret:
        if not x_hub_signature_256:
            raise HTTPException(status_code=401, detail="Missing signature header")
        if not _verify_signature(body, x_hub_signature_256, _webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload: dict[str, Any] = await request.json()

    if x_github_event == "pull_request":
        pr: dict[str, Any] = payload.get("pull_request", {})
        event = PREvent(
            pr_number=payload.get("number", 0),
            repo=payload.get("repository", {}).get("full_name", ""),
            branch=pr.get("head", {}).get("ref", ""),
            author=pr.get("user", {}).get("login", ""),
            title=pr.get("title", ""),
            action=payload.get("action", ""),
            commit_sha=pr.get("head", {}).get("sha", ""),
            diff_url=pr.get("diff_url"),
        )
        logger.info("Received PR event: %s #%d (%s)", event.repo, event.pr_number, event.action)

        # TODO: await event_bus.publish("github.pull_request", event.model_dump())

        return {"status": "accepted", "event_type": "pull_request", "pr_number": event.pr_number}

    logger.debug("Ignoring GitHub event type: %s", x_github_event)
    return {"status": "ignored", "event_type": x_github_event}
