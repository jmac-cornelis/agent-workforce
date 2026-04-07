'''
Unified notification router — dispatches to Teams DM and email.

Usage:
    router = NotificationRouter()
    await router.notify(
        agent_id='drucker',
        title='PR Reminders Sent',
        text='3 reminders sent',
        body_lines=['PR #42: stale 7 days', 'PR #55: stale 3 days'],
        target_users=['jmac-cornelis'],  # GitHub logins, or None for all
    )

Delivery channels are controlled per-user in config/identity_map.yaml:
    notify_via: [teams_dm, email]
'''

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml

log = logging.getLogger(__name__)

_CONFIG_DIR = Path(os.getenv('CONFIG_DIR', 'config'))
_IDENTITY_MAP_PATH = _CONFIG_DIR / 'identity_map.yaml'


class NotificationRouter:
    '''Multi-channel notification dispatcher.'''

    def __init__(self, identity_map_path: Optional[Path] = None):
        self._identity_map_path = identity_map_path or _IDENTITY_MAP_PATH
        self._identity_map: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Identity map
    # ------------------------------------------------------------------

    def _load_identity_map(self) -> Dict[str, Any]:
        '''Load and cache identity_map.yaml.'''
        if self._identity_map is None:
            try:
                with open(self._identity_map_path, 'r', encoding='utf-8') as f:
                    self._identity_map = yaml.safe_load(f) or {}
            except Exception as e:
                log.error('Failed to load identity map from %s: %s', self._identity_map_path, e)
                self._identity_map = {}
        return self._identity_map

    def get_user(self, github_login: str) -> Optional[Dict[str, Any]]:
        '''Look up a user by GitHub login.'''
        identity_map = self._load_identity_map()
        return identity_map.get('users', {}).get(github_login)

    def get_defaults(self) -> Dict[str, Any]:
        '''Get default notification settings.'''
        identity_map = self._load_identity_map()
        return identity_map.get('defaults', {})

    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        '''Return all users from the identity map.'''
        identity_map = self._load_identity_map()
        return identity_map.get('users', {})

    def resolve_notify_channels(self, user: Dict[str, Any]) -> List[str]:
        '''Get notification channels for a user, falling back to defaults.'''
        channels = user.get('notify_via')
        if channels:
            return list(channels)
        defaults = self.get_defaults()
        return list(defaults.get('notify_via', ['teams_dm', 'email']))

    def get_email_from(self) -> str:
        '''Get the from-address for email notifications.'''
        defaults = self.get_defaults()
        return defaults.get('email_from', os.getenv('NOTIFICATION_EMAIL_FROM', 'shannon@cornelisnetworks.com'))

    # ------------------------------------------------------------------
    # Reverse lookups
    # ------------------------------------------------------------------

    def resolve_github_login_by_email(self, email: str) -> Optional[str]:
        '''Reverse-lookup: email -> GitHub login.'''
        for login, user in self.get_all_users().items():
            if user.get('email', '').lower() == email.lower():
                return login
            if user.get('teams_email', '').lower() == email.lower():
                return login
        return None

    def resolve_github_login_by_jira_account_id(self, account_id: str) -> Optional[str]:
        '''Reverse-lookup: Jira accountId -> GitHub login.'''
        for login, user in self.get_all_users().items():
            if user.get('jira_account_id') == account_id:
                return login
        return None

    # ------------------------------------------------------------------
    # Notification dispatch
    # ------------------------------------------------------------------

    async def notify(
        self,
        agent_id: str,
        title: str,
        text: str,
        body_lines: Optional[Iterable[str]] = None,
        target_users: Optional[List[str]] = None,
        card: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        '''
        Send notification to target users via their preferred channels.

        Args:
            agent_id: Source agent (drucker, gantt, hemingway).
            title: Notification title.
            text: Notification body text.
            body_lines: Additional detail lines.
            target_users: GitHub logins to notify. None = all users.
            card: Optional pre-built Adaptive Card dict.

        Returns:
            Summary dict with per-user, per-channel results.
        '''
        if target_users is None:
            target_users = list(self.get_all_users().keys())

        results: Dict[str, Any] = {}
        for github_login in target_users:
            user = self.get_user(github_login)
            if not user:
                log.warning('User %s not found in identity map — skipping', github_login)
                results[github_login] = {'error': 'not_found'}
                continue

            channels = self.resolve_notify_channels(user)
            user_results: Dict[str, Any] = {}

            for channel in channels:
                try:
                    if channel == 'teams_dm':
                        user_results['teams_dm'] = await self._send_teams_dm(
                            user=user,
                            agent_id=agent_id,
                            title=title,
                            text=text,
                            body_lines=body_lines,
                            card=card,
                        )
                    elif channel == 'email':
                        user_results['email'] = await self._send_email(
                            user=user,
                            agent_id=agent_id,
                            title=title,
                            text=text,
                            body_lines=body_lines,
                        )
                    else:
                        log.warning('Unknown notification channel: %s', channel)
                        user_results[channel] = {'error': 'unknown_channel'}
                except Exception as e:
                    log.error(
                        'Notification to %s via %s failed: %s',
                        github_login, channel, e,
                    )
                    user_results[channel] = {'error': str(e)}

            results[github_login] = user_results

        return {'ok': True, 'agent_id': agent_id, 'title': title, 'results': results}

    # ------------------------------------------------------------------
    # Channel implementations
    # ------------------------------------------------------------------

    async def _send_teams_dm(
        self,
        user: Dict[str, Any],
        agent_id: str,
        title: str,
        text: str,
        body_lines: Optional[Iterable[str]] = None,
        card: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        '''Send a Teams 1:1 DM to the user.'''
        # Lazy import to avoid circular dependency with shannon package
        from agents.shannon.graph_client import TeamsGraphClient

        teams_email = user.get('teams_email') or user.get('email')
        if not teams_email:
            return {'error': 'no_teams_email'}

        async with TeamsGraphClient() as graph:
            # Resolve Azure AD user by email
            resolved = await graph.resolve_user_by_email(teams_email)
            if not resolved or not resolved.get('id'):
                return {'error': f'could_not_resolve_user: {teams_email}'}

            user_id = resolved['id']

            # Create or get 1:1 chat
            chat = await graph.create_one_on_one_chat(user_id)
            chat_id = chat.get('id')
            if not chat_id:
                return {'error': 'could_not_create_chat'}

            # Send pre-built Adaptive Card or fall back to HTML text
            if card:
                await graph.send_chat_adaptive_card(
                    chat_id=chat_id,
                    card=card,
                    summary=f'[{agent_id}] {title}',
                )
            else:
                # Build simple HTML message
                html_parts = [f'<b>[{agent_id.upper()}] {title}</b>', f'<p>{text}</p>']
                if body_lines:
                    html_parts.append('<ul>')
                    for line in body_lines:
                        html_parts.append(f'<li>{line}</li>')
                    html_parts.append('</ul>')
                await graph.send_chat_message(
                    chat_id=chat_id,
                    content='\n'.join(html_parts),
                    content_type='html',
                )

        log.info('Sent Teams DM to %s for [%s] %s', teams_email, agent_id, title)
        return {'ok': True, 'chat_id': chat_id, 'user_id': user_id}

    async def _send_email(
        self,
        user: Dict[str, Any],
        agent_id: str,
        title: str,
        text: str,
        body_lines: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        '''Send an email notification to the user via Graph API.'''
        # Lazy import to avoid circular dependency with shannon package
        from agents.shannon.graph_client import TeamsGraphClient

        to_email = user.get('email')
        if not to_email:
            return {'error': 'no_email'}

        from_address = self.get_email_from()
        subject = f'[{agent_id.upper()}] {title}'

        # Build HTML body with inline styles (email-safe)
        html_parts = [
            '<html><body>',
            '<div style="font-family: Segoe UI, Arial, sans-serif; max-width: 600px;">',
            f'<h2 style="color: #0078d4;">{title}</h2>',
            f'<p>{text}</p>',
        ]
        if body_lines:
            html_parts.append('<ul style="padding-left: 20px;">')
            for line in body_lines:
                html_parts.append(f'<li style="margin-bottom: 4px;">{line}</li>')
            html_parts.append('</ul>')
        html_parts.extend([
            '<hr style="border: none; border-top: 1px solid #e0e0e0; margin-top: 20px;">',
            f'<p style="color: #888; font-size: 12px;">Sent by Shannon \u2014 {agent_id} agent</p>',
            '</div>',
            '</body></html>',
        ])
        body_html = '\n'.join(html_parts)

        async with TeamsGraphClient() as graph:
            await graph.send_email(
                from_user=from_address,
                to_addresses=[to_email],
                subject=subject,
                body_html=body_html,
            )

        log.info('Sent email to %s for [%s] %s', to_email, agent_id, title)
        return {'ok': True, 'to': to_email, 'subject': subject}


# ------------------------------------------------------------------
# Convenience function (sync wrapper for use in non-async code)
# ------------------------------------------------------------------

def send_notification(
    agent_id: str,
    title: str,
    text: str,
    body_lines: Optional[Iterable[str]] = None,
    target_users: Optional[List[str]] = None,
    card: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    '''
    Synchronous convenience wrapper for NotificationRouter.notify().

    Safe to call from sync code (creates event loop if needed).
    '''
    router = NotificationRouter()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already in an async context — run in a thread to avoid blocking
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(
                asyncio.run,
                router.notify(
                    agent_id=agent_id,
                    title=title,
                    text=text,
                    body_lines=body_lines,
                    target_users=target_users,
                    card=card,
                ),
            )
            return future.result(timeout=30)
    else:
        return asyncio.run(
            router.notify(
                agent_id=agent_id,
                title=title,
                text=text,
                body_lines=body_lines,
                target_users=target_users,
                card=card,
            ),
        )
