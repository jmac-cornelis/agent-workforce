##########################################################################################
#
# Module: agents/workforce/shannon/cards.py
#
# Description: Adaptive Card templates for Teams notifications.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_CARD_SCHEMA = 'http://adaptivecards.io/schemas/adaptive-card.json'
_CARD_VERSION = '1.4'

_SEVERITY_COLORS: Dict[str, str] = {
    'critical': 'attention',
    'high': 'attention',
    'medium': 'warning',
    'low': 'good',
    'info': 'default',
}

_SEVERITY_EMOJI: Dict[str, str] = {
    'critical': '🔴',
    'high': '🟠',
    'medium': '🟡',
    'low': '🟢',
    'info': 'ℹ️',
}


def _base_card() -> Dict[str, Any]:
    return {
        '$schema': _CARD_SCHEMA,
        'type': 'AdaptiveCard',
        'version': _CARD_VERSION,
        'body': [],
    }


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')


def _header(title: str, subtitle: Optional[str] = None,
            style: str = 'default') -> Dict[str, Any]:
    column_items: List[Dict[str, Any]] = [
        {
            'type': 'TextBlock',
            'text': title,
            'weight': 'bolder',
            'size': 'medium',
            'wrap': True,
        }
    ]
    if subtitle:
        column_items.append({
            'type': 'TextBlock',
            'text': subtitle,
            'isSubtle': True,
            'spacing': 'none',
            'wrap': True,
        })

    container: Dict[str, Any] = {
        'type': 'Container',
        'items': column_items,
    }
    if style != 'default':
        container['style'] = style

    return container


def _fact_set(facts: Dict[str, str]) -> Dict[str, Any]:
    return {
        'type': 'FactSet',
        'facts': [
            {'title': k, 'value': str(v)} for k, v in facts.items()
        ],
    }


def activity_card(
    agent_id: str,
    action: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Activity notification — an agent performed an action.

    Required for audit trail of agent operations in Teams channels.
    """
    card = _base_card()

    card['body'].append(_header(
        f'🤖 {agent_id}',
        subtitle=f'Activity — {_timestamp()}',
    ))

    card['body'].append({
        'type': 'TextBlock',
        'text': action,
        'wrap': True,
        'spacing': 'medium',
    })

    if details:
        if isinstance(details, str):
            card['body'].append({
                'type': 'TextBlock',
                'text': details,
                'wrap': True,
                'spacing': 'medium',
            })
        else:
            card['body'].append({
                'type': 'Container',
                'separator': True,
                'spacing': 'medium',
                'items': [_fact_set(
                    {k: str(v) for k, v in details.items()}
                )],
            })

    return card


def decision_card(
    agent_id: str,
    decision_type: str,
    inputs: Optional[Dict[str, Any]] = None,
    candidates: Optional[List[Dict[str, Any]]] = None,
    selected: Optional[str] = None,
    rationale: Optional[str] = None,
    decision_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Decision notification — an agent made a decision with rationale.

    Necessary for transparency: shows inputs, candidates, selection, and reasoning.
    """
    card = _base_card()

    title = f'📋 Decision: {decision_type}'
    card['body'].append(_header(title, subtitle=f'{agent_id} — {_timestamp()}'))

    if decision_id:
        card['body'].append({
            'type': 'TextBlock',
            'text': f'Decision ID: `{decision_id}`',
            'isSubtle': True,
            'size': 'small',
        })

    if inputs:
        card['body'].append({
            'type': 'Container',
            'separator': True,
            'spacing': 'medium',
            'items': [
                {'type': 'TextBlock', 'text': '**Inputs**', 'wrap': True},
                _fact_set({k: str(v) for k, v in inputs.items()}),
            ],
        })

    if candidates:
        candidate_items: List[Dict[str, Any]] = [
            {'type': 'TextBlock', 'text': '**Candidates**', 'wrap': True},
        ]
        for i, c in enumerate(candidates, 1):
            label = c.get('name', c.get('id', f'Option {i}'))
            score = c.get('score', '')
            reason = c.get('reason', '')
            line = f'{i}. **{label}**'
            if score:
                line += f' (score: {score})'
            if reason:
                line += f' — {reason}'
            candidate_items.append({
                'type': 'TextBlock',
                'text': line,
                'wrap': True,
                'spacing': 'small',
            })
        card['body'].append({
            'type': 'Container',
            'separator': True,
            'spacing': 'medium',
            'items': candidate_items,
        })

    if selected:
        card['body'].append({
            'type': 'Container',
            'style': 'emphasis',
            'spacing': 'medium',
            'items': [{
                'type': 'TextBlock',
                'text': f'✅ **Selected:** {selected}',
                'wrap': True,
                'weight': 'bolder',
            }],
        })

    if rationale:
        card['body'].append({
            'type': 'Container',
            'separator': True,
            'spacing': 'medium',
            'items': [
                {'type': 'TextBlock', 'text': '**Rationale**', 'wrap': True},
                {'type': 'TextBlock', 'text': rationale, 'wrap': True},
            ],
        })

    return card


def alert_card(
    agent_id: str,
    severity: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    suggested_actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Error/alert notification with severity color coding.

    Severity-to-style mapping is critical for visual triage in Teams.
    """
    card = _base_card()
    severity_lower = severity.lower()
    emoji = _SEVERITY_EMOJI.get(severity_lower, '⚠️')
    style = _SEVERITY_COLORS.get(severity_lower, 'default')

    card['body'].append(_header(
        f'{emoji} Alert: {severity.upper()}',
        subtitle=f'{agent_id} — {_timestamp()}',
        style=style,
    ))

    card['body'].append({
        'type': 'TextBlock',
        'text': message,
        'wrap': True,
        'spacing': 'medium',
        'weight': 'bolder' if severity_lower in ('critical', 'high') else 'default',
    })

    if details:
        if isinstance(details, str):
            card['body'].append({
                'type': 'TextBlock',
                'text': details,
                'wrap': True,
                'spacing': 'medium',
            })
        else:
            card['body'].append({
                'type': 'Container',
                'separator': True,
                'spacing': 'medium',
                'items': [_fact_set({k: str(v) for k, v in details.items()})],
            })

    if suggested_actions:
        action_items: List[Dict[str, Any]] = [
            {'type': 'TextBlock', 'text': '**Suggested Actions**', 'wrap': True},
        ]
        for i, action in enumerate(suggested_actions, 1):
            action_items.append({
                'type': 'TextBlock',
                'text': f'{i}. {action}',
                'wrap': True,
                'spacing': 'small',
            })
        card['body'].append({
            'type': 'Container',
            'separator': True,
            'spacing': 'medium',
            'items': action_items,
        })

    return card


def stats_card(
    agent_id: str,
    stats: Dict[str, Any],
) -> Dict[str, Any]:
    """Operational statistics table for an agent."""
    card = _base_card()

    card['body'].append(_header(
        f'📊 Stats: {agent_id}',
        subtitle=_timestamp(),
    ))

    card['body'].append(_fact_set({k: str(v) for k, v in stats.items()}))

    return card


def token_status_card(
    agent_id: str,
    token_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Token usage summary — tracks LLM token consumption.

    Necessary for cost monitoring and budget alerting.
    """
    card = _base_card()

    card['body'].append(_header(
        f'🔑 Token Usage: {agent_id}',
        subtitle=_timestamp(),
    ))

    prompt_tokens = token_data.get('prompt_tokens', 0)
    completion_tokens = token_data.get('completion_tokens', 0)
    total_tokens = token_data.get('total_tokens', prompt_tokens + completion_tokens)
    budget = token_data.get('budget', 'N/A')
    remaining = token_data.get('remaining', 'N/A')
    model = token_data.get('model', 'unknown')

    card['body'].append(_fact_set({
        'Model': model,
        'Prompt Tokens': f'{prompt_tokens:,}',
        'Completion Tokens': f'{completion_tokens:,}',
        'Total Tokens': f'{total_tokens:,}',
        'Budget': str(budget),
        'Remaining': str(remaining),
    }))

    usage_pct = token_data.get('usage_percent')
    if usage_pct is not None:
        color = 'good' if usage_pct < 70 else ('warning' if usage_pct < 90 else 'attention')
        card['body'].append({
            'type': 'Container',
            'style': color,
            'spacing': 'medium',
            'items': [{
                'type': 'TextBlock',
                'text': f'Usage: {usage_pct:.1f}%',
                'weight': 'bolder',
            }],
        })

    return card


def work_summary_card(
    agent_id: str,
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    """Daily work summary for an agent."""
    card = _base_card()

    period = summary.get('period', 'Today')
    card['body'].append(_header(
        f'📝 Work Summary: {agent_id}',
        subtitle=f'{period} — {_timestamp()}',
    ))

    overview_facts: Dict[str, str] = {}
    for key in ('tasks_completed', 'tasks_in_progress', 'tasks_failed',
                'decisions_made', 'approvals_requested', 'messages_sent'):
        if key in summary:
            label = key.replace('_', ' ').title()
            overview_facts[label] = str(summary[key])

    if overview_facts:
        card['body'].append(_fact_set(overview_facts))

    highlights = summary.get('highlights', [])
    if highlights:
        highlight_items: List[Dict[str, Any]] = [
            {'type': 'TextBlock', 'text': '**Highlights**', 'wrap': True,
             'spacing': 'medium'},
        ]
        for h in highlights:
            highlight_items.append({
                'type': 'TextBlock',
                'text': f'• {h}',
                'wrap': True,
                'spacing': 'small',
            })
        card['body'].append({
            'type': 'Container',
            'separator': True,
            'items': highlight_items,
        })

    issues = summary.get('issues', [])
    if issues:
        issue_items: List[Dict[str, Any]] = [
            {'type': 'TextBlock', 'text': '**Issues**', 'wrap': True,
             'spacing': 'medium', 'color': 'attention'},
        ]
        for issue in issues:
            issue_items.append({
                'type': 'TextBlock',
                'text': f'⚠️ {issue}',
                'wrap': True,
                'spacing': 'small',
            })
        card['body'].append({
            'type': 'Container',
            'separator': True,
            'items': issue_items,
        })

    return card


def approval_card(
    agent_id: str,
    approval_type: str,
    context: Optional[Dict[str, Any]] = None,
    approval_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Approval request card (display-only for Phase 1).

    Phase 1: read-only display. Phase 2 will add Action.Submit buttons
    once the bot framework webhook is wired up.
    """
    card = _base_card()

    card['body'].append(_header(
        f'🔐 Approval Required: {approval_type}',
        subtitle=f'{agent_id} — {_timestamp()}',
        style='warning',
    ))

    if approval_id:
        card['body'].append({
            'type': 'TextBlock',
            'text': f'Approval ID: `{approval_id}`',
            'isSubtle': True,
            'size': 'small',
        })

    if context:
        title = context.get('title', '')
        description = context.get('description', '')
        evidence = context.get('evidence', {})

        if title:
            card['body'].append({
                'type': 'TextBlock',
                'text': f'**{title}**',
                'wrap': True,
                'spacing': 'medium',
            })

        if description:
            card['body'].append({
                'type': 'TextBlock',
                'text': description,
                'wrap': True,
            })

        if evidence:
            card['body'].append({
                'type': 'Container',
                'separator': True,
                'spacing': 'medium',
                'items': [
                    {'type': 'TextBlock', 'text': '**Evidence**', 'wrap': True},
                    _fact_set({k: str(v) for k, v in evidence.items()}),
                ],
            })

    card['body'].append({
        'type': 'Container',
        'separator': True,
        'spacing': 'medium',
        'style': 'emphasis',
        'items': [{
            'type': 'TextBlock',
            'text': '⏳ Awaiting human approval. '
                    'Reply in this thread with **approve** or **reject**.',
            'wrap': True,
            'isSubtle': True,
        }],
    })

    return card
