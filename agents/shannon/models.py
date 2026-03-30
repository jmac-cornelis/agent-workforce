##########################################################################################
#
# Module: agents/workforce/shannon/models.py
#
# Description: Pydantic models for the Shannon Communications agent.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentRegistryEntry(BaseModel):
    '''Registry entry mapping a Teams channel to an agent.'''
    agent_id: str = Field(..., description='Agent identifier')
    agent_name: str = Field(..., description='Human-readable agent name')
    channel_id: str = Field(..., description='Teams channel identifier')
    channel_name: str = Field(..., description='Teams channel name (e.g. #agent-josephine)')
    api_base_url: str = Field(..., description='Agent API base URL')
    approval_types: List[str] = Field(
        default_factory=list, description='Approval types this agent may request'
    )
    custom_commands: List[Dict[str, Any]] = Field(
        default_factory=list, description='Agent-specific custom commands'
    )
    enabled: bool = Field(True, description='Whether the agent is active')


class ConversationRecord(BaseModel):
    '''Record of a conversation thread in a Teams channel.'''
    conversation_id: str = Field(..., description='Unique conversation identifier')
    channel_id: str = Field(..., description='Teams channel identifier')
    agent_id: str = Field(..., description='Associated agent identifier')
    thread_id: Optional[str] = Field(None, description='Teams thread identifier')
    user_id: str = Field(..., description='User who initiated the conversation')
    command: Optional[str] = Field(None, description='Command that started the conversation')
    status: str = Field(
        'active', description='Status: active, completed, error'
    )
    created_at: Optional[datetime] = Field(None)
    updated_at: Optional[datetime] = Field(None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ApprovalRecord(BaseModel):
    '''Record of an approval request and its lifecycle.'''
    approval_id: str = Field(..., description='Unique approval identifier')
    agent_id: str = Field(..., description='Requesting agent identifier')
    approval_type: str = Field(..., description='Type of approval')
    title: str = Field(..., description='Approval request title')
    description: str = Field(..., description='What is being approved')
    evidence: Dict[str, Any] = Field(
        default_factory=dict, description='Supporting evidence'
    )
    status: str = Field(
        'pending',
        description='Status: pending, approved, rejected, expired, escalated',
    )
    requested_at: Optional[datetime] = Field(None)
    responded_at: Optional[datetime] = Field(None)
    responded_by: Optional[str] = Field(None, description='User who responded')
    timeout_hours: Optional[int] = Field(None, description='Hours before escalation')
    escalation_targets: List[str] = Field(
        default_factory=list, description='Users to escalate to'
    )
    correlation_id: Optional[str] = Field(None, description='Correlation ID for audit')


class NotificationRequest(BaseModel):
    '''Request to post a notification to a Teams channel.'''
    notification_id: str = Field(..., description='Unique notification identifier')
    agent_id: str = Field(..., description='Source agent identifier')
    channel_id: Optional[str] = Field(None, description='Target channel (resolved from agent_id)')
    message: str = Field(..., description='Notification message content')
    card_type: Optional[str] = Field(
        None, description='Adaptive Card type: activity, decision, error, stats'
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = Field(None)


class InputRequest(BaseModel):
    '''Request for structured human input via a form card.'''
    request_id: str = Field(..., description='Unique input request identifier')
    agent_id: str = Field(..., description='Requesting agent identifier')
    title: str = Field(..., description='Input request title')
    context: Optional[str] = Field(None, description='Context for the request')
    fields: List[Dict[str, Any]] = Field(
        ..., description='Field definitions for the form'
    )
    status: str = Field(
        'pending', description='Status: pending, received, expired'
    )
    response: Optional[Dict[str, Any]] = Field(None, description='User response data')
    created_at: Optional[datetime] = Field(None)
    responded_at: Optional[datetime] = Field(None)
    responded_by: Optional[str] = Field(None)
