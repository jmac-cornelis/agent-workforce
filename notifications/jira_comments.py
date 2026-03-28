##########################################################################################
#
# Module: notifications/jira_comments.py
#
# Description: Jira comment helpers for Drucker review-gated remediation.
#              Builds consistent marker-based comments and supports duplicate
#              detection for safe comment posting.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from typing import Any, Dict, List, Optional

from config.env_loader import resolve_dry_run
from notifications.base import NotificationBackend


class JiraCommentNotifier(NotificationBackend):
    MARKER = '[Drucker]'

    _LEVEL_TITLES = {
        'auto_fill': 'Suggested metadata update',
        'suggest': 'Suggested metadata update',
        'flag': 'Metadata review',
    }

    def __init__(self, jira: Any):
        self.jira = jira

    @classmethod
    def _normalize_level(cls, level: Optional[str]) -> str:
        normalized = str(level or 'flag').strip().lower()
        return normalized if normalized in cls._LEVEL_TITLES else 'flag'

    @staticmethod
    def _normalize_comment_text(comment_body: Any) -> str:
        if isinstance(comment_body, str):
            return comment_body
        if isinstance(comment_body, dict):
            return str(comment_body)
        return str(comment_body or '')

    @classmethod
    def build_hygiene_comment(
        cls,
        ticket: Dict[str, Any],
        findings: List[Any],
        suggested_updates: Optional[Dict[str, Any]] = None,
    ) -> str:
        summary = str(ticket.get('summary') or '').strip()
        lines = [
            f'{cls.MARKER} Drucker hygiene review',
            '',
            f'Ticket: {ticket.get("key", "")} - {summary}',
            'Findings:',
        ]

        recommendations: List[str] = []
        for finding in findings:
            title = str(getattr(finding, 'title', '') or '')
            description = str(getattr(finding, 'description', '') or '')
            recommendation = str(getattr(finding, 'recommendation', '') or '')
            lines.append(f'- {title}: {description}')
            if recommendation and recommendation not in recommendations:
                recommendations.append(recommendation)

        if suggested_updates:
            lines.append('')
            lines.append('Suggested metadata updates for review:')
            for field_name, value in sorted(suggested_updates.items()):
                if isinstance(value, list):
                    value_text = ', '.join(str(item) for item in value)
                else:
                    value_text = str(value)
                lines.append(f'- {field_name}: {value_text}')

        if recommendations:
            lines.append('')
            lines.append('Recommended follow-up:')
            for recommendation in recommendations:
                lines.append(f'- {recommendation}')

        return '\n'.join(lines)

    def has_existing_comment(self, ticket_key: str, field: Optional[str] = None) -> bool:
        try:
            comments = self.jira.comments(ticket_key)
        except Exception:
            return False

        field_token = str(field).strip().lower() if field else None
        for comment in comments:
            body = self._normalize_comment_text(getattr(comment, 'body', ''))
            normalized = body.lower()

            if self.MARKER.lower() not in normalized:
                continue
            if field_token and field_token not in normalized:
                continue

            return True

        return False

    def send(
        self,
        ticket_key: str,
        message: str,
        level: str = 'flag',
        context: Optional[Dict[str, Any]] = None,
        dry_run: Optional[bool] = None,
    ) -> Any:
        ctx = context or {}
        field = ctx.get('field')

        title = self._LEVEL_TITLES[self._normalize_level(level)]
        body = f'{self.MARKER} {title}\n\n{message}'

        if resolve_dry_run(dry_run):
            has_existing = self.has_existing_comment(ticket_key, field=field)
            return {
                'dry_run': True,
                'ticket_key': ticket_key,
                'level': self._normalize_level(level),
                'body': body,
                'would_skip': has_existing,
            }

        if self.has_existing_comment(ticket_key, field=field):
            return False

        try:
            self.jira.add_comment(ticket_key, body)
            return True
        except Exception:
            return False
