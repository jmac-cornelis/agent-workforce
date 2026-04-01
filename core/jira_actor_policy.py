##########################################################################################
#
# Module: core/jira_actor_policy.py
#
# Description: Resolve Jira actor identity from policy rules.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Optional

import yaml

from config.jira_identity import (
    DRAFT_ONLY,
    REQUESTER,
    SERVICE_ACCOUNT,
    get_jira_actor_email,
    has_jira_credentials,
    normalize_actor_mode,
)

log = logging.getLogger(os.path.basename(sys.argv[0]))

_POLICY_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'jira_actor_identity_policy.yaml')
)
_POLICY_CACHE: Optional[dict[str, Any]] = None


@dataclass
class ActorResolution:
    '''
    Resolved Jira actor decision and audit context.
    '''
    actor_mode: str
    policy_rule: str
    rationale: str
    requested_by: Optional[str]
    approved_by: Optional[str]
    executed_by: Optional[str]
    correlation_id: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            'actor_mode': self.actor_mode,
            'policy_rule': self.policy_rule,
            'rationale': self.rationale,
            'requested_by': self.requested_by,
            'approved_by': self.approved_by,
            'executed_by': self.executed_by,
            'correlation_id': self.correlation_id,
        }


def load_actor_policy(path: Optional[str] = None, force_reload: bool = False) -> dict[str, Any]:
    '''
    Load the Jira actor identity policy YAML.
    '''
    global _POLICY_CACHE
    target_path = path or _POLICY_PATH
    if not force_reload and _POLICY_CACHE is not None and target_path == _POLICY_PATH:
        return _POLICY_CACHE

    with open(target_path, 'r', encoding='utf-8') as handle:
        policy = yaml.safe_load(handle) or {}

    if target_path == _POLICY_PATH:
        _POLICY_CACHE = policy
    return policy


def _value_matches(expected: Any, actual: Any) -> bool:
    '''
    Match a rule value against one context value.
    '''
    if isinstance(expected, list):
        return actual in expected
    return actual == expected


def _rule_matches(rule: dict[str, Any], context: dict[str, Any]) -> bool:
    '''
    Return True when a rule matches the supplied context.
    '''
    match = rule.get('match', {}) or {}
    for key, expected in match.items():
        actual = context.get(key)
        if not _value_matches(expected, actual):
            return False
    return True


def _default_actor(policy: dict[str, Any], trigger: str) -> str:
    '''
    Resolve the default actor for one trigger type.
    '''
    defaults = policy.get('defaults', {}) or {}
    if trigger == 'polling':
        return normalize_actor_mode(defaults.get('background_mode', REQUESTER))
    return normalize_actor_mode(defaults.get('interactive_mode', DRAFT_ONLY))


def resolve_jira_actor(
    action_class: str,
    trigger: str = 'interactive',
    risk: str = 'low',
    approval_required: bool = False,
    approved: bool = False,
    agent_name: str = '',
    requested_by: Optional[str] = None,
    approved_by: Optional[str] = None,
    correlation_id: Optional[str] = None,
    policy_path: Optional[str] = None,
) -> ActorResolution:
    '''
    Resolve the Jira actor mode from the policy YAML and current context.
    '''
    policy = load_actor_policy(path=policy_path)
    context = {
        'action_class': action_class,
        'trigger': trigger,
        'risk': risk,
        'approval_required': approval_required,
        'approved': approved,
        'agent_name': agent_name,
    }

    actor_mode = _default_actor(policy, trigger)
    policy_rule = 'default_interactive_mode' if trigger != 'polling' else 'default_background_mode'
    rationale = 'Default actor mode from policy defaults.'

    for rule in policy.get('rules', []) or []:
        if _rule_matches(rule, context):
            actor_mode = normalize_actor_mode(rule.get('actor'))
            policy_rule = str(rule.get('id', policy_rule))
            rationale = str(rule.get('rationale', rationale))
            break

    if not requested_by:
        default_requester_actor = SERVICE_ACCOUNT if trigger == 'polling' else REQUESTER
        requested_by = get_jira_actor_email(default_requester_actor)
    if approved and not approved_by:
        approved_by = requested_by

    if actor_mode == REQUESTER and not has_jira_credentials(REQUESTER):
        fallback = ((policy.get('defaults', {}) or {}).get('fallback_no_requester_credentials', {}) or {})
        if risk == 'sensitive':
            actor_mode = normalize_actor_mode(fallback.get('sensitive_actions', DRAFT_ONLY))
        else:
            actor_mode = normalize_actor_mode(fallback.get('low_risk_actions', DRAFT_ONLY))
        policy_rule = f'{policy_rule}_fallback_no_requester_credentials'
        rationale = f'{rationale} Requester credentials unavailable; falling back to {actor_mode}.'

    executed_by = None if actor_mode == DRAFT_ONLY else get_jira_actor_email(actor_mode)
    return ActorResolution(
        actor_mode=actor_mode,
        policy_rule=policy_rule,
        rationale=rationale,
        requested_by=requested_by,
        approved_by=approved_by,
        executed_by=executed_by,
        correlation_id=correlation_id,
    )
