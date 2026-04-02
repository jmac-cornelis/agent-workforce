##########################################################################################
#
# Module: agents/drucker_models.py
#
# Description: Data models for the Drucker Jira Coordinator agent.
#              Defines hygiene findings, proposed Jira actions, and durable
#              project hygiene reports.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


@dataclass
class DruckerRequest:
    '''
    Input request for generating a Drucker hygiene report.
    '''
    project_key: str = ''
    ticket_key: Optional[str] = None
    limit: int = 200
    include_done: bool = False
    stale_days: int = 30
    jql: Optional[str] = None
    since: Optional[str] = None
    recent_only: bool = False
    label_prefix: str = 'drucker'
    requested_by: Optional[str] = None
    approved_by: Optional[str] = None
    correlation_id: Optional[str] = None
    trigger: str = 'interactive'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_key': self.project_key,
            'ticket_key': self.ticket_key,
            'limit': self.limit,
            'include_done': self.include_done,
            'stale_days': self.stale_days,
            'jql': self.jql,
            'since': self.since,
            'recent_only': self.recent_only,
            'label_prefix': self.label_prefix,
            'requested_by': self.requested_by,
            'approved_by': self.approved_by,
            'correlation_id': self.correlation_id,
            'trigger': self.trigger,
        }


@dataclass
class DruckerFinding:
    '''
    A single Jira hygiene finding for a ticket.
    '''
    finding_id: str
    ticket_key: str
    category: str
    severity: str
    title: str
    description: str
    evidence: List[str] = field(default_factory=list)
    recommendation: str = ''
    action_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'finding_id': self.finding_id,
            'ticket_key': self.ticket_key,
            'category': self.category,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'evidence': self.evidence,
            'recommendation': self.recommendation,
            'action_ids': self.action_ids,
        }


@dataclass
class DruckerAction:
    '''
    A proposed Jira write-back action derived from hygiene findings.
    '''
    action_id: str
    ticket_key: str
    action_type: str
    title: str
    description: str = ''
    finding_ids: List[str] = field(default_factory=list)
    confidence: str = 'medium'
    comment: str = ''
    update_fields: Dict[str, Any] = field(default_factory=dict)
    transition_to: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'ticket_key': self.ticket_key,
            'action_type': self.action_type,
            'title': self.title,
            'description': self.description,
            'finding_ids': self.finding_ids,
            'confidence': self.confidence,
            'comment': self.comment,
            'update_fields': self.update_fields,
            'transition_to': self.transition_to,
        }


@dataclass
class DruckerHygieneReport:
    '''
    Durable Jira hygiene report produced by the Drucker coordinator.
    '''
    project_key: str = ''
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    request: Dict[str, Any] = field(default_factory=dict)
    project_info: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    findings: List[DruckerFinding] = field(default_factory=list)
    proposed_actions: List[DruckerAction] = field(default_factory=list)
    tickets: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    summary_markdown: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'project_key': self.project_key,
            'created_at': self.created_at,
            'request': self.request,
            'project_info': self.project_info,
            'summary': self.summary,
            'findings': [finding.to_dict() for finding in self.findings],
            'proposed_actions': [action.to_dict() for action in self.proposed_actions],
            'tickets': self.tickets,
            'errors': self.errors,
            'summary_markdown': self.summary_markdown,
        }
