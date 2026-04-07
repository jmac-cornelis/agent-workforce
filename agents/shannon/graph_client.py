##########################################################################################
#
# Module: agents/workforce/shannon/graph_client.py
#
# Description: Microsoft Graph API client for Teams messaging.
#              Uses OAuth2 client credentials flow with Azure AD app registration.
#              All HTTP calls are async via aiohttp.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import aiohttp

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))

# Microsoft identity platform endpoints
_TOKEN_URL_TEMPLATE = 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
_GRAPH_BASE = 'https://graph.microsoft.com/v1.0'

# Default scope for client credentials flow (application permissions)
_DEFAULT_SCOPE = 'https://graph.microsoft.com/.default'

# Rate-limit retry defaults
_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 2.0  # seconds — exponential backoff base


@dataclass
class GraphToken:
    '''Cached OAuth2 access token with expiry tracking.'''
    access_token: str
    expires_at: float  # epoch seconds
    token_type: str = 'Bearer'

    @property
    def is_expired(self) -> bool:
        '''Check if token is expired (with 5-minute buffer).'''
        return time.time() >= (self.expires_at - 300)


@dataclass
class GraphMessage:
    '''Parsed Teams channel message.'''
    id: str
    body_content: str
    body_content_type: str
    from_user: Optional[str] = None
    created_datetime: Optional[str] = None
    web_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class GraphAPIError(Exception):
    '''Exception raised for Microsoft Graph API errors.'''

    def __init__(self, status: int, error_code: str, message: str,
                 request_id: Optional[str] = None):
        self.status = status
        self.error_code = error_code
        self.request_id = request_id
        super().__init__(f'Graph API {status} [{error_code}]: {message}')


class TeamsGraphClient:
    '''
    Async Microsoft Graph API client for Teams channel messaging.

    Uses OAuth2 client credentials flow (app-only) to authenticate.
    Credentials are loaded from environment variables:
        - SHANNON_APP_ID: Azure AD Application (client) ID
        - SHANNON_APP_SECRET: Azure AD Client Secret
        - SHANNON_TENANT_ID: Azure AD Directory (tenant) ID

    All HTTP calls use aiohttp with proper token caching, error handling,
    and rate-limit retry with exponential backoff.
    '''

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        max_retries: int = _MAX_RETRIES,
    ):
        '''
        Initialize the Graph client.

        Input:
            app_id: Azure AD Application (client) ID. Falls back to SHANNON_APP_ID env.
            app_secret: Azure AD Client Secret. Falls back to SHANNON_APP_SECRET env.
            tenant_id: Azure AD Tenant ID. Falls back to SHANNON_TENANT_ID env.
            max_retries: Maximum retry attempts for rate-limited requests.
        '''
        self._app_id = app_id or os.getenv('SHANNON_APP_ID', '')
        self._app_secret = app_secret or os.getenv('SHANNON_APP_SECRET', '')
        self._tenant_id = tenant_id or os.getenv('SHANNON_TENANT_ID', '')
        self._max_retries = max_retries

        # Cached token — refreshed automatically when expired
        self._token: Optional[GraphToken] = None

        # Shared aiohttp session — created lazily, closed explicitly
        self._session: Optional[aiohttp.ClientSession] = None

        if not all([self._app_id, self._app_secret, self._tenant_id]):
            log.warning(
                'TeamsGraphClient: missing one or more credentials '
                '(SHANNON_APP_ID, SHANNON_APP_SECRET, SHANNON_TENANT_ID). '
                'API calls will fail until credentials are configured.'
            )

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def _get_session(self) -> aiohttp.ClientSession:
        '''Get or create the shared aiohttp session.'''
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self._session

    async def close(self) -> None:
        '''Close the aiohttp session. Call when done with the client.'''
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        log.debug('TeamsGraphClient session closed')

    # ------------------------------------------------------------------
    # OAuth2 token management
    # ------------------------------------------------------------------

    async def _get_token(self) -> str:
        '''
        Obtain an OAuth2 access token via client credentials flow.

        Caches the token and only refreshes when expired (with 5-min buffer).

        Output:
            Bearer access token string.

        Raises:
            GraphAPIError: If token acquisition fails.
        '''
        # Return cached token if still valid
        if self._token and not self._token.is_expired:
            return self._token.access_token

        token_url = _TOKEN_URL_TEMPLATE.format(tenant_id=self._tenant_id)
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self._app_id,
            'client_secret': self._app_secret,
            'scope': _DEFAULT_SCOPE,
        }

        session = await self._get_session()
        log.debug('Requesting new OAuth2 token from Azure AD')

        async with session.post(
            token_url,
            data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        ) as resp:
            body = await resp.json()

            if resp.status != 200:
                error_code = body.get('error', 'unknown')
                error_desc = body.get('error_description', 'Token request failed')
                log.error(f'Token acquisition failed: {error_code} — {error_desc}')
                raise GraphAPIError(
                    status=resp.status,
                    error_code=error_code,
                    message=error_desc,
                )

            # Cache the token with computed expiry
            expires_in = int(body.get('expires_in', 3600))
            self._token = GraphToken(
                access_token=body['access_token'],
                expires_at=time.time() + expires_in,
                token_type=body.get('token_type', 'Bearer'),
            )
            log.info(f'OAuth2 token acquired, expires in {expires_in}s')
            return self._token.access_token

    # ------------------------------------------------------------------
    # HTTP helpers with retry
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        url: str,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        '''
        Make an authenticated Graph API request with retry on rate-limit.

        Input:
            method: HTTP method (GET, POST, PATCH, DELETE).
            url: Full URL or path relative to Graph base.
            json_body: Optional JSON request body.
            params: Optional query parameters.

        Output:
            Parsed JSON response body.

        Raises:
            GraphAPIError: On non-retryable errors or exhausted retries.
        '''
        # Ensure full URL
        if not url.startswith('https://'):
            url = f'{_GRAPH_BASE}{url}'

        session = await self._get_session()

        for attempt in range(self._max_retries + 1):
            token = await self._get_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            }

            log.debug(f'Graph API {method} {url} (attempt {attempt + 1})')

            async with session.request(
                method, url, json=json_body, params=params, headers=headers
            ) as resp:
                # 204 No Content — success with no body
                if resp.status == 204:
                    return {}

                body_text = await resp.text()
                try:
                    body = json.loads(body_text) if body_text else {}
                except json.JSONDecodeError:
                    body = {'raw': body_text}

                # Success
                if 200 <= resp.status < 300:
                    return body

                # Rate-limited — retry with backoff
                if resp.status == 429:
                    retry_after = int(
                        resp.headers.get('Retry-After', _RETRY_BACKOFF_BASE ** (attempt + 1))
                    )
                    log.warning(
                        f'Rate-limited (429). Retrying in {retry_after}s '
                        f'(attempt {attempt + 1}/{self._max_retries})'
                    )
                    await asyncio.sleep(retry_after)
                    continue

                # Transient server errors — retry
                if resp.status >= 500 and attempt < self._max_retries:
                    wait = _RETRY_BACKOFF_BASE ** (attempt + 1)
                    log.warning(
                        f'Server error {resp.status}. Retrying in {wait}s '
                        f'(attempt {attempt + 1}/{self._max_retries})'
                    )
                    await asyncio.sleep(wait)
                    continue

                # Non-retryable error
                raw_error = body.get('error', {})
                if isinstance(raw_error, dict):
                    err_code: str = str(raw_error.get('code', 'unknown'))
                    err_msg: str = str(raw_error.get('message', body_text[:500]))
                else:
                    err_code = str(raw_error)
                    err_msg = body_text[:500]
                raise GraphAPIError(
                    status=resp.status,
                    error_code=err_code,
                    message=err_msg,
                    request_id=resp.headers.get('request-id'),
                )

        # Exhausted retries (should not reach here, but safety net)
        raise GraphAPIError(
            status=429,
            error_code='retry_exhausted',
            message=f'Exhausted {self._max_retries} retries',
        )

    # ------------------------------------------------------------------
    # Teams / Groups discovery
    # ------------------------------------------------------------------

    async def list_teams(self) -> List[Dict[str, Any]]:
        '''
        List all Teams-enabled groups the app has access to.

        Uses the /groups endpoint filtered to resourceProvisioningOptions
        containing "Team".

        Output:
            List of team dicts with id, displayName, description.
        '''
        # Filter for groups that are Teams-enabled
        params = {
            '$filter': "resourceProvisioningOptions/Any(x:x eq 'Team')",
            '$select': 'id,displayName,description',
            '$top': '100',
        }
        result = await self._request('GET', '/groups', params=params)
        teams = result.get('value', [])
        log.info(f'Found {len(teams)} Teams-enabled groups')
        return teams

    async def list_channels(self, team_id: str) -> List[Dict[str, Any]]:
        '''
        List all channels in a team.

        Input:
            team_id: The team (group) ID.

        Output:
            List of channel dicts with id, displayName, description.
        '''
        result = await self._request(
            'GET',
            f'/teams/{team_id}/channels',
            params={'$select': 'id,displayName,description,membershipType'},
        )
        channels = result.get('value', [])
        log.info(f'Team {team_id}: found {len(channels)} channels')
        return channels

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    async def send_message(
        self,
        team_id: str,
        channel_id: str,
        content: str,
        content_type: str = 'html',
    ) -> Dict[str, Any]:
        '''
        Send a message to a Teams channel.

        Input:
            team_id: The team (group) ID.
            channel_id: The channel ID.
            content: Message content (HTML or text).
            content_type: Content type — 'html' (default) or 'text'.

        Output:
            Created message dict from Graph API.
        '''
        payload = {
            'body': {
                'contentType': content_type,
                'content': content,
            }
        }
        result = await self._request(
            'POST',
            f'/teams/{team_id}/channels/{channel_id}/messages',
            json_body=payload,
        )
        msg_id = result.get('id', 'unknown')
        log.info(f'Sent message {msg_id} to channel {channel_id}')
        return result

    async def send_adaptive_card(
        self,
        team_id: str,
        channel_id: str,
        card: Dict[str, Any],
        summary: str = 'Adaptive Card',
    ) -> Dict[str, Any]:
        '''
        Send an Adaptive Card to a Teams channel.

        Input:
            team_id: The team (group) ID.
            channel_id: The channel ID.
            card: Adaptive Card JSON payload (the card body).
            summary: Fallback summary text for notifications.

        Output:
            Created message dict from Graph API.
        '''
        # Ensure the card has the required schema and type
        if '$schema' not in card:
            card['$schema'] = 'http://adaptivecards.io/schemas/adaptive-card.json'
        if 'type' not in card:
            card['type'] = 'AdaptiveCard'
        if 'version' not in card:
            card['version'] = '1.4'

        payload = {
            'body': {
                'contentType': 'html',
                'content': f'<attachment id="card"></attachment>',
            },
            'attachments': [
                {
                    'id': 'card',
                    'contentType': 'application/vnd.microsoft.card.adaptive',
                    'contentUrl': None,
                    'content': json.dumps(card),
                    'name': None,
                    'thumbnailUrl': None,
                }
            ],
        }
        result = await self._request(
            'POST',
            f'/teams/{team_id}/channels/{channel_id}/messages',
            json_body=payload,
        )
        msg_id = result.get('id', 'unknown')
        log.info(f'Sent Adaptive Card {msg_id} to channel {channel_id}')
        return result

    async def reply_to_message(
        self,
        team_id: str,
        channel_id: str,
        message_id: str,
        content: str,
        content_type: str = 'html',
    ) -> Dict[str, Any]:
        '''
        Reply to an existing message in a Teams channel (threaded reply).

        Input:
            team_id: The team (group) ID.
            channel_id: The channel ID.
            message_id: The parent message ID to reply to.
            content: Reply content.
            content_type: Content type — 'html' or 'text'.

        Output:
            Created reply message dict from Graph API.
        '''
        payload = {
            'body': {
                'contentType': content_type,
                'content': content,
            }
        }
        result = await self._request(
            'POST',
            f'/teams/{team_id}/channels/{channel_id}/messages/{message_id}/replies',
            json_body=payload,
        )
        reply_id = result.get('id', 'unknown')
        log.info(f'Sent reply {reply_id} to message {message_id}')
        return result

    async def get_messages(
        self,
        team_id: str,
        channel_id: str,
        limit: int = 20,
    ) -> List[GraphMessage]:
        '''
        Get recent messages from a Teams channel.

        Input:
            team_id: The team (group) ID.
            channel_id: The channel ID.
            limit: Maximum number of messages to retrieve (default 20, max 50).

        Output:
            List of GraphMessage objects.
        '''
        capped_limit = min(limit, 50)
        result = await self._request(
            'GET',
            f'/teams/{team_id}/channels/{channel_id}/messages',
            params={'$top': str(capped_limit)},
        )

        messages = []
        for msg in result.get('value', []):
            body = msg.get('body', {})
            from_info = msg.get('from', {})
            user_info = from_info.get('user', {}) if from_info else {}

            messages.append(GraphMessage(
                id=msg.get('id', ''),
                body_content=body.get('content', ''),
                body_content_type=body.get('contentType', 'text'),
                from_user=user_info.get('displayName'),
                created_datetime=msg.get('createdDateTime'),
                web_url=msg.get('webUrl'),
                metadata={
                    'importance': msg.get('importance'),
                    'message_type': msg.get('messageType'),
                },
            ))

        log.info(f'Retrieved {len(messages)} messages from channel {channel_id}')
        return messages

    # ------------------------------------------------------------------
    # 1:1 Chat / DM messaging
    # ------------------------------------------------------------------

    async def resolve_user_by_email(self, email: str) -> Dict[str, Any]:
        '''
        Resolve a Teams user ID from their email address.

        Input:
            email: User email address (mail or userPrincipalName).

        Output:
            Dict with 'id', 'displayName', 'mail', 'userPrincipalName'.

        Raises:
            GraphAPIError: If user not found (404) or query fails.
        '''
        params = {
            '$filter': f"mail eq '{email}' or userPrincipalName eq '{email}'",
            '$select': 'id,displayName,mail,userPrincipalName',
        }
        result = await self._request('GET', '/users', params=params)
        users = result.get('value', [])

        if not users:
            log.warning(f'No user found for email: {email}')
            raise GraphAPIError(
                status=404,
                error_code='user_not_found',
                message=f'No user found matching email: {email}',
            )

        user = users[0]
        log.info(f'Resolved user {user.get("displayName")} ({user.get("id")}) from {email}')
        return user

    async def create_one_on_one_chat(self, user_id: str) -> Dict[str, Any]:
        '''
        Create (or get existing) 1:1 chat between the bot app and a user.

        Graph API returns the existing chat if one already exists (idempotent).

        Input:
            user_id: Azure AD user ID of the target user.

        Output:
            Dict with chat 'id' and metadata.

        Raises:
            GraphAPIError: If chat creation fails.
        '''
        payload = {
            'chatType': 'oneOnOne',
            'members': [
                {
                    '@odata.type': '#microsoft.graph.aadUserConversationMember',
                    'roles': ['owner'],
                    'user@odata.bind': f"https://graph.microsoft.com/v1.0/users('{self._app_id}')",
                },
                {
                    '@odata.type': '#microsoft.graph.aadUserConversationMember',
                    'roles': ['owner'],
                    'user@odata.bind': f"https://graph.microsoft.com/v1.0/users('{user_id}')",
                },
            ],
        }
        result = await self._request('POST', '/chats', json_body=payload)
        chat_id = result.get('id', 'unknown')
        log.info(f'Created/resolved 1:1 chat {chat_id} with user {user_id}')
        return result

    async def send_chat_message(
        self,
        chat_id: str,
        content: str,
        content_type: str = 'html',
    ) -> Dict[str, Any]:
        '''
        Send a text/html message to a 1:1 chat.

        Input:
            chat_id: The chat ID.
            content: Message content (HTML or text).
            content_type: Content type — 'html' (default) or 'text'.

        Output:
            Created message dict from Graph API.

        Raises:
            GraphAPIError: If sending fails.
        '''
        payload = {
            'body': {
                'contentType': content_type,
                'content': content,
            }
        }
        result = await self._request(
            'POST',
            f'/chats/{chat_id}/messages',
            json_body=payload,
        )
        msg_id = result.get('id', 'unknown')
        log.info(f'Sent chat message {msg_id} to chat {chat_id}')
        return result

    async def send_chat_adaptive_card(
        self,
        chat_id: str,
        card: Dict[str, Any],
        summary: str = 'Adaptive Card',
    ) -> Dict[str, Any]:
        '''
        Send an Adaptive Card to a 1:1 chat.

        Input:
            chat_id: The chat ID.
            card: Adaptive Card JSON payload (the card body).
            summary: Fallback summary text for notifications.

        Output:
            Created message dict from Graph API.

        Raises:
            GraphAPIError: If sending fails.
        '''
        # Ensure the card has the required schema and type
        if '$schema' not in card:
            card['$schema'] = 'http://adaptivecards.io/schemas/adaptive-card.json'
        if 'type' not in card:
            card['type'] = 'AdaptiveCard'
        if 'version' not in card:
            card['version'] = '1.4'

        payload = {
            'body': {
                'contentType': 'html',
                'content': f'<attachment id="card"></attachment>',
            },
            'attachments': [
                {
                    'id': 'card',
                    'contentType': 'application/vnd.microsoft.card.adaptive',
                    'contentUrl': None,
                    'content': json.dumps(card),
                    'name': None,
                    'thumbnailUrl': None,
                }
            ],
        }
        result = await self._request(
            'POST',
            f'/chats/{chat_id}/messages',
            json_body=payload,
        )
        msg_id = result.get('id', 'unknown')
        log.info(f'Sent Adaptive Card {msg_id} to chat {chat_id}')
        return result


    # ------------------------------------------------------------------
    # Email via Microsoft Graph
    # ------------------------------------------------------------------

    async def send_email(
        self,
        from_user: str,
        to_addresses: list[str],
        subject: str,
        body_html: str,
        cc_addresses: list[str] | None = None,
        save_to_sent: bool = True,
    ) -> dict[str, Any]:
        '''
        Send an email via Microsoft Graph API.

        Requires Mail.Send application permission in Azure AD.

        Args:
            from_user: UPN or user-id of the sending mailbox
                       (e.g. "shannon@cornelisnetworks.com").
            to_addresses: List of recipient email addresses.
            subject: Email subject line.
            body_html: HTML email body.
            cc_addresses: Optional CC recipients.
            save_to_sent: Whether to save in the Sent Items folder.

        Returns:
            Empty dict on success (Graph returns 202 Accepted).
        '''
        to_recipients = [
            {'emailAddress': {'address': addr}}
            for addr in to_addresses
        ]
        cc_recipients = [
            {'emailAddress': {'address': addr}}
            for addr in (cc_addresses or [])
        ]

        payload: dict[str, Any] = {
            'message': {
                'subject': subject,
                'body': {
                    'contentType': 'HTML',
                    'content': body_html,
                },
                'toRecipients': to_recipients,
            },
            'saveToSentItems': save_to_sent,
        }
        if cc_recipients:
            payload['message']['ccRecipients'] = cc_recipients

        result = await self._request(
            'POST',
            f'/users/{from_user}/sendMail',
            json_body=payload,
        )
        log.info(
            'Sent email from %s to %s: %s',
            from_user,
            ', '.join(to_addresses),
            subject,
        )
        return result

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> 'TeamsGraphClient':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
