##########################################################################################
#
# Module: shannon/models.py
#
# Description: Data models for the Shannon Teams bot service.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    '''Return the current UTC timestamp in ISO-8601 format.'''
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentChannelRegistration:
    '''
    Registry entry describing how Shannon maps a Teams channel to an agent.
    '''
    agent_id: str
    display_name: str
    role: str
    description: str
    zone: str = 'service_infrastructure'
    channel_id: str = ''
    channel_name: str = ''
    team_id: str = ''
    api_base_url: str = ''
    icon_url: str = ''
    notifications_webhook_url: str = ''
    approval_types: List[str] = field(default_factory=list)
    custom_commands: List[Dict[str, Any]] = field(default_factory=list)
    timeout_seconds: int = 30

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentChannelRegistration':
        return cls(
            agent_id=str(data.get('agent_id') or '').strip(),
            display_name=str(data.get('display_name') or '').strip(),
            role=str(data.get('role') or '').strip(),
            description=str(data.get('description') or '').strip(),
            zone=str(data.get('zone') or 'service_infrastructure').strip(),
            channel_id=str(data.get('channel_id') or '').strip(),
            channel_name=str(data.get('channel_name') or '').strip(),
            team_id=str(data.get('team_id') or '').strip(),
            api_base_url=str(data.get('api_base_url') or '').strip(),
            icon_url=str(data.get('icon_url') or '').strip(),
            notifications_webhook_url=str(data.get('notifications_webhook_url') or '').strip(),
            approval_types=list(data.get('approval_types') or []),
            custom_commands=list(data.get('custom_commands') or []),
            timeout_seconds=int(data.get('timeout_seconds') or 30),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConversationReference:
    '''
    Teams conversation reference persisted by Shannon for replies and notifications.
    '''
    reference_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    captured_at: str = field(default_factory=utc_now_iso)
    agent_id: str = ''
    service_url: str = ''
    channel_id: str = ''
    channel_name: str = ''
    team_id: str = ''
    tenant_id: str = ''
    conversation_id: str = ''
    conversation_type: str = ''
    reply_to_id: str = ''
    user_id: str = ''
    user_name: str = ''
    bot_id: str = ''
    bot_name: str = ''
    raw_activity_type: str = ''

    @classmethod
    def from_activity(
        cls,
        activity: Dict[str, Any],
        agent_id: str = '',
    ) -> 'ConversationReference':
        channel_data = activity.get('channelData') or {}
        team = channel_data.get('team') or {}
        channel = channel_data.get('channel') or {}
        tenant = channel_data.get('tenant') or {}
        conversation = activity.get('conversation') or {}
        sender = activity.get('from') or {}
        recipient = activity.get('recipient') or {}

        tenant_id = str(
            tenant.get('id')
            or conversation.get('tenantId')
            or ''
        ).strip()

        return cls(
            agent_id=str(agent_id or '').strip(),
            service_url=str(activity.get('serviceUrl') or '').strip(),
            channel_id=str(channel.get('id') or '').strip(),
            channel_name=str(channel.get('name') or '').strip(),
            team_id=str(team.get('id') or '').strip(),
            tenant_id=tenant_id,
            conversation_id=str(conversation.get('id') or '').strip(),
            conversation_type=str(conversation.get('conversationType') or '').strip(),
            reply_to_id=str(activity.get('id') or activity.get('replyToId') or '').strip(),
            user_id=str(sender.get('id') or '').strip(),
            user_name=str(sender.get('name') or '').strip(),
            bot_id=str(recipient.get('id') or '').strip(),
            bot_name=str(recipient.get('name') or '').strip(),
            raw_activity_type=str(activity.get('type') or '').strip(),
        )

    def key(self) -> str:
        return self.channel_id or self.conversation_id or self.reference_id

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditRecord:
    '''
    Audit record for a Shannon event or decision.
    '''
    record_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=utc_now_iso)
    event_type: str = ''
    status: str = 'ok'
    agent_id: str = 'shannon'
    channel_id: str = ''
    conversation_id: str = ''
    team_id: str = ''
    user_id: str = ''
    user_name: str = ''
    command: str = ''
    decision: str = ''
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ShannonResponse:
    '''
    Response payload generated by Shannon before posting to Teams.
    '''
    text: str
    card: Optional[Dict[str, Any]] = None
    command: str = ''
    decision: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_message_activity(self) -> Dict[str, Any]:
        activity: Dict[str, Any] = {
            'type': 'message',
            'text': self.text,
        }
        if self.card is not None:
            activity['attachments'] = [{
                'contentType': 'application/vnd.microsoft.card.adaptive',
                'content': self.card,
            }]
        return activity

    def to_outgoing_webhook_response(self) -> Dict[str, Any]:
        '''
        Convert to the response shape expected by Teams Outgoing Webhooks.
        '''
        response = self.to_message_activity()
        if 'attachments' in response:
            for attachment in response['attachments']:
                attachment.setdefault('contentUrl', None)
                attachment.setdefault('name', None)
                attachment.setdefault('thumbnailUrl', None)
        return response


MENTION_RE = re.compile(r'<at>.*?</at>', re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r'<[^>]+>')


def normalize_command_text(text: str) -> str:
    '''
    Strip Teams mention markup and normalize the resulting command text.
    '''
    clean = MENTION_RE.sub(' ', str(text or ''))
    clean = TAG_RE.sub(' ', clean)
    clean = clean.replace('&nbsp;', ' ')
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean
