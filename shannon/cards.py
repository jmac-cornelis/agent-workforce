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
    monitor_scope = summary.get('monitor_scope', '')

    # Build title and subtitle
    if monitor_scope == 'ticket':
        title = f'Drucker Issue Check — {project_key}'
    elif monitor_scope == 'recent_ticket_intake':
        title = f'Drucker Ticket Intake — {project_key}'
    else:
        title = f'Drucker Hygiene Report — {project_key}'
    subtitle = f'{created_at} | Report ID: {report_id}'

    # Build fact set from summary
    by_severity = summary.get('by_severity', {})
    facts = {
        'Total Findings': summary.get(
            'finding_count',
            summary.get('total_findings', 0),
        ),
        'Critical': by_severity.get('critical', 0),
        'High': by_severity.get('high', 0),
        'Medium': by_severity.get('medium', 0),
        'Low': by_severity.get('low', 0),
        'Proposed Actions': summary.get('action_count', len(proposed_actions)),
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


def build_gantt_snapshot_card(payload: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Gantt planning snapshot response.
    '''
    snapshot = payload.get('snapshot', payload)
    overview = snapshot.get('backlog_overview', {})
    milestones = snapshot.get('milestones', [])
    dependency_graph = snapshot.get('dependency_graph', {})
    risks = snapshot.get('risks', [])

    facts = {
        'Project': snapshot.get('project_key', ''),
        'Issues': overview.get('total_issues', 0),
        'Blocked': overview.get('blocked_issues', 0),
        'Stale': overview.get('stale_issues', 0),
        'Milestones': len(milestones),
        'Dependencies': dependency_graph.get('edge_count', 0),
        'Risks': len(risks),
    }

    body_lines: list[str] = []
    for milestone in milestones[:5]:
        body_lines.append(
            f'• {milestone.get("name", "")}: '
            f'{milestone.get("open_issues", 0)} open / '
            f'{milestone.get("blocked_issues", 0)} blocked'
        )

    if len(milestones) > 5:
        body_lines.append(f'...and {len(milestones) - 5} more milestones')

    if not body_lines:
        body_lines.append('No milestone proposals were generated.')

    return build_fact_card(
        title=f'Gantt Planning Snapshot — {snapshot.get("project_key", "")}',
        subtitle=str(snapshot.get('created_at', '') or '').strip() or None,
        facts=facts,
        body_lines=body_lines,
    )


def build_gantt_release_monitor_card(payload: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Gantt release-monitor response.
    '''
    report = payload.get('report', payload)
    releases = report.get('releases_monitored', [])
    facts = {
        'Project': report.get('project_key', ''),
        'Releases': len(releases),
        'Total Bugs': report.get('total_bugs', 0),
        'P0': report.get('total_p0', 0),
        'P1': report.get('total_p1', 0),
    }

    body_lines: list[str] = []
    for summary in (report.get('bug_summaries') or [])[:5]:
        body_lines.append(
            f'• {summary.get("release", "")}: '
            f'{summary.get("total_bugs", 0)} bugs, '
            f'P0={summary.get("by_priority", {}).get("P0", 0)}, '
            f'P1={summary.get("by_priority", {}).get("P1", 0)}'
        )

    readiness = report.get('readiness') or {}
    if readiness:
        body_lines.append(
            'Readiness: '
            f'{readiness.get("total_open", 0)} open, '
            f'{readiness.get("p0_open", 0)} P0, '
            f'{readiness.get("p1_open", 0)} P1'
        )

    if not body_lines:
        body_lines.append('No release-monitor details were returned.')

    return build_fact_card(
        title=f'Gantt Release Monitor — {report.get("project_key", "")}',
        subtitle=str(report.get('created_at', '') or '').strip() or None,
        facts=facts,
        body_lines=body_lines,
    )


def build_bug_activity_card(data: Dict[str, Any]) -> Dict[str, Any]:
    project = data.get('project', '')
    target_date = data.get('date', '')
    summary = data.get('summary', {})
    opened = data.get('opened', [])
    status_changed = data.get('status_changed', [])
    commented = data.get('commented', [])

    facts = {
        'Date': target_date,
        'Bugs Opened': summary.get('bugs_opened', 0),
        'Status Transitions': summary.get('status_transitions', 0),
        'Bugs With Comments': summary.get('bugs_with_comments', 0),
        'Total Active Bugs': summary.get('total_active_bugs', 0),
    }

    body_lines: list[str] = []

    if opened:
        body_lines.append('**Opened Today:**')
        for bug in opened[:5]:
            key = bug.get('key', '')
            title = bug.get('summary', '')
            pri = bug.get('priority', '')
            body_lines.append(f'• {key} [{pri}] {title}')
        if len(opened) > 5:
            body_lines.append(f'  ...and {len(opened) - 5} more')

    if status_changed:
        body_lines.append('**Status Changes:**')
        for sc in status_changed[:5]:
            body_lines.append(
                f'• {sc.get("key", "")} {sc.get("from_status", "")} → '
                f'{sc.get("to_status", "")} ({sc.get("changed_by", "")})'
            )
        if len(status_changed) > 5:
            body_lines.append(f'  ...and {len(status_changed) - 5} more')

    if commented:
        body_lines.append('**Comments:**')
        for c in commented[:5]:
            body_lines.append(
                f'• {c.get("key", "")} — {c.get("comment_count", 0)} comment(s) '
                f'(latest: {c.get("latest_author", "")})'
            )
        if len(commented) > 5:
            body_lines.append(f'  ...and {len(commented) - 5} more')

    if not body_lines:
        body_lines.append('No bug activity recorded today.')

    return build_fact_card(
        title=f'Bug Activity — {project}',
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
