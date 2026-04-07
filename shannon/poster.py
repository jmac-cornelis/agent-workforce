##########################################################################################
#
# Module: shannon/poster.py
#
# Description: Posting adapters for sending Shannon replies to Teams.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, List, Optional

import requests

from config.env_loader import resolve_dry_run
from shannon.models import ConversationReference

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class BasePoster:
    '''
    Abstract posting interface for Shannon replies and notifications.
    '''

    def reply_to_activity(
        self,
        reference: ConversationReference,
        activity_id: str,
        activity: Dict[str, Any],
        dry_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def send_to_conversation(
        self,
        reference: ConversationReference,
        activity: Dict[str, Any],
        dry_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class MemoryPoster(BasePoster):
    '''
    In-memory poster used for local development and test verification.
    '''

    def __init__(self):
        self.sent: List[Dict[str, Any]] = []

    def reply_to_activity(
        self,
        reference: ConversationReference,
        activity_id: str,
        activity: Dict[str, Any],
        dry_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        if resolve_dry_run(dry_run):
            return {
                'ok': True,
                'dry_run': True,
                'mode': 'memory',
                'kind': 'reply',
                'activity_id': activity_id,
                'conversation_id': reference.conversation_id,
                'activity': activity,
            }
        record = {
            'mode': 'memory',
            'kind': 'reply',
            'activity_id': activity_id,
            'conversation_id': reference.conversation_id,
            'channel_id': reference.channel_id,
            'activity': activity,
        }
        self.sent.append(record)
        return {'ok': True, 'id': f'memory-reply-{len(self.sent)}', 'mode': 'memory'}

    def send_to_conversation(
        self,
        reference: ConversationReference,
        activity: Dict[str, Any],
        dry_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        if resolve_dry_run(dry_run):
            return {
                'ok': True,
                'dry_run': True,
                'mode': 'memory',
                'kind': 'conversation',
                'conversation_id': reference.conversation_id,
                'activity': activity,
            }
        record = {
            'mode': 'memory',
            'kind': 'conversation',
            'conversation_id': reference.conversation_id,
            'channel_id': reference.channel_id,
            'activity': activity,
        }
        self.sent.append(record)
        return {'ok': True, 'id': f'memory-message-{len(self.sent)}', 'mode': 'memory'}


class WorkflowsPoster(BasePoster):
    '''
    Post Adaptive Cards to a Teams channel via a Workflows incoming webhook.

    Workflows webhook payload format::

        {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": null,
                "content": { <adaptive card JSON> }
            }]
        }
    '''

    def __init__(
        self,
        webhook_url: str,
        session: Optional[requests.Session] = None,
    ):
        self.webhook_url = str(webhook_url or '').strip()
        self.session = session or requests.Session()

        if not self.webhook_url:
            raise ValueError('WorkflowsPoster requires a webhook_url')

    @staticmethod
    def _extract_card(activity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for attachment in activity.get('attachments') or []:
            if attachment.get('contentType') == 'application/vnd.microsoft.card.adaptive':
                return attachment.get('content')
        return None

    def _build_payload(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        card = self._extract_card(activity)
        if card is None:
            text = str(activity.get('text') or 'Shannon notification')
            card = {
                '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
                'type': 'AdaptiveCard',
                'version': '1.4',
                'body': [{'type': 'TextBlock', 'text': text, 'wrap': True}],
            }

        return {
            'type': 'message',
            'attachments': [{
                'contentType': 'application/vnd.microsoft.card.adaptive',
                'contentUrl': None,
                'content': card,
            }],
        }

    def _post(self, activity: Dict[str, Any], dry_run: Optional[bool] = None) -> Dict[str, Any]:
        payload = self._build_payload(activity)
        if resolve_dry_run(dry_run):
            return {
                'ok': True,
                'dry_run': True,
                'mode': 'workflows',
                'webhook_url': self.webhook_url,
                'payload': payload,
            }
        response = self.session.post(
            self.webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30,
        )
        response.raise_for_status()
        return {'ok': True, 'mode': 'workflows', 'status_code': response.status_code}

    def reply_to_activity(
        self,
        reference: ConversationReference,
        activity_id: str,
        activity: Dict[str, Any],
        dry_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        log.debug(
            'WorkflowsPoster: reply_to_activity posted as new message '
            '(threading not supported on Workflows webhooks)'
        )
        result = self._post(activity, dry_run=dry_run)
        result['threading'] = False
        return result

    def send_to_conversation(
        self,
        reference: ConversationReference,
        activity: Dict[str, Any],
        dry_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        return self._post(activity, dry_run=dry_run)


class BotFrameworkPoster(BasePoster):
    '''
    Send replies to Teams through the Bot Framework connector REST API.
    '''

    TOKEN_URL = 'https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token'
    TOKEN_SCOPE = 'https://api.botframework.com/.default'

    def __init__(
        self,
        app_id: str,
        app_password: str,
        session: Optional[requests.Session] = None,
    ):
        self.app_id = str(app_id or '').strip()
        self.app_password = str(app_password or '').strip()
        self.session = session or requests.Session()
        self._access_token: Optional[str] = None

        if not self.app_id or not self.app_password:
            raise ValueError('BotFrameworkPoster requires app_id and app_password')

    def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token

        response = self.session.post(
            self.TOKEN_URL,
            data={
                'grant_type': 'client_credentials',
                'client_id': self.app_id,
                'client_secret': self.app_password,
                'scope': self.TOKEN_SCOPE,
            },
            timeout=30,
        )
        response.raise_for_status()
        token_payload = response.json()
        self._access_token = str(token_payload.get('access_token') or '').strip()
        if not self._access_token:
            raise RuntimeError('Bot Framework token response did not include access_token')
        return self._access_token

    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Content-Type': 'application/json',
        }

    @staticmethod
    def _base_service_url(reference: ConversationReference) -> str:
        return str(reference.service_url or '').rstrip('/')

    def reply_to_activity(
        self,
        reference: ConversationReference,
        activity_id: str,
        activity: Dict[str, Any],
        dry_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        if not reference.conversation_id or not activity_id:
            raise ValueError('reply_to_activity requires conversation_id and activity_id')

        url = (
            f'{self._base_service_url(reference)}/v3/conversations/'
            f'{reference.conversation_id}/activities/{activity_id}'
        )
        if resolve_dry_run(dry_run):
            return {
                'ok': True,
                'dry_run': True,
                'mode': 'botframework',
                'url': url,
                'activity': activity,
            }
        response = self.session.post(url, json=activity, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return {'ok': True, 'mode': 'botframework', **response.json()}

    def send_to_conversation(
        self,
        reference: ConversationReference,
        activity: Dict[str, Any],
        dry_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        if not reference.conversation_id:
            raise ValueError('send_to_conversation requires conversation_id')

        url = (
            f'{self._base_service_url(reference)}/v3/conversations/'
            f'{reference.conversation_id}/activities'
        )
        if resolve_dry_run(dry_run):
            return {
                'ok': True,
                'dry_run': True,
                'mode': 'botframework',
                'url': url,
                'activity': activity,
            }
        response = self.session.post(url, json=activity, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return {'ok': True, 'mode': 'botframework', **response.json()}


def build_poster_from_env() -> BasePoster:
    '''
    Build the configured Shannon poster implementation.

    Modes:
        memory       — in-memory (local dev / tests)
        workflows    — zero-cost Workflows incoming webhook
        botframework — Azure Bot Framework (requires app registration)
    '''
    mode = str(os.getenv('SHANNON_TEAMS_POST_MODE', 'memory') or 'memory').strip().lower()
    if mode == 'workflows':
        webhook_url = os.getenv('SHANNON_TEAMS_WORKFLOWS_WEBHOOK_URL', '')
        return WorkflowsPoster(webhook_url=webhook_url or '')
    if mode == 'botframework':
        app_id = os.getenv('SHANNON_TEAMS_APP_ID')
        app_password = os.getenv('SHANNON_TEAMS_APP_PASSWORD')
        return BotFrameworkPoster(app_id=app_id or '', app_password=app_password or '')
    return MemoryPoster()
