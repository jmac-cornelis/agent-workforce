##########################################################################################
#
# Module: shannon/cards.py
#
# Description: Adaptive Card builders for Shannon Teams responses.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


def _fact_entries(facts: Dict[str, Any]) -> list[dict[str, str]]:
    return [
        {'title': str(key), 'value': str(value)}
        for key, value in facts.items()
        if value is not None and str(value) != ''
    ]


def build_fact_card(
    title: str,
    subtitle: Optional[str] = None,
    facts: Optional[Dict[str, Any]] = None,
    body_lines: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    '''
    Build a simple Adaptive Card with a title, optional fact set, and body text.
    '''
    body: list[dict[str, Any]] = [
        {
            'type': 'TextBlock',
            'size': 'Large',
            'weight': 'Bolder',
            'text': title,
            'wrap': True,
        }
    ]

    if subtitle:
        body.append({
            'type': 'TextBlock',
            'text': subtitle,
            'wrap': True,
            'spacing': 'Small',
            'isSubtle': True,
        })

    fact_items = _fact_entries(facts or {})
    if fact_items:
        body.append({
            'type': 'FactSet',
            'facts': fact_items,
        })

    for line in body_lines or []:
        if str(line).strip():
            body.append({
                'type': 'TextBlock',
                'text': str(line),
                'wrap': True,
            })

    return {
        '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
        'type': 'AdaptiveCard',
        'version': '1.5',
        'body': body,
    }


def build_drucker_hygiene_card(report_data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Drucker hygiene report.
    '''
    project_key = report_data.get('project_key', 'Unknown')
    report_id = report_data.get('report_id', '')
    created_at = report_data.get('created_at', '')
    summary = report_data.get('summary', {})
    findings = report_data.get('findings', [])
    proposed_actions = report_data.get('proposed_actions', [])

    # Build title and subtitle
    title = f'Drucker Hygiene Report — {project_key}'
    subtitle = f'{created_at} | Report ID: {report_id}'

    # Build fact set from summary
    by_severity = summary.get('by_severity', {})
    facts = {
        'Total Findings': summary.get('total_findings', 0),
        'Critical': by_severity.get('critical', 0),
        'High': by_severity.get('high', 0),
        'Medium': by_severity.get('medium', 0),
        'Low': by_severity.get('low', 0),
        'Proposed Actions': len(proposed_actions),
    }

    # Build body lines for top 5 findings
    body_lines = []
    top_findings = findings[:5]
    for finding in top_findings:
        severity = finding.get('severity', 'unknown')
        ticket_key = finding.get('ticket_key', '')
        description = finding.get('description', '')
        body_lines.append(f'**[{severity.upper()}] {ticket_key}**: {description}')

    # Add "...and N more" if there are more than 5 findings
    if len(findings) > 5:
        remaining = len(findings) - 5
        body_lines.append(f'...and {remaining} more findings')

    return build_fact_card(
        title=title,
        subtitle=subtitle,
        facts=facts,
        body_lines=body_lines,
    )


def build_drucker_summary_card(summary: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build a simple Adaptive Card for Drucker /stats response.
    '''
    title = 'Drucker Stats'
    facts = {
        'Total Reports': summary.get('total_reports', 0),
        'Projects Analyzed': summary.get('projects_analyzed', 0),
        'Total Findings': summary.get('total_findings', 0),
        'Proposed Actions': summary.get('proposed_actions', 0),
    }
    return build_fact_card(title=title, facts=facts)
