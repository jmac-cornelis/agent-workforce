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

import re
from typing import Any, Dict, Iterable, Optional

from agents.rename_registry import agent_display_name


_JIRA_BASE = 'https://cornelisnetworks.atlassian.net/browse'
_TICKET_RE = re.compile(r'(?<!\[)(?<!/)\b([A-Z][A-Z0-9]+-\d+)\b')


def _linkify_tickets(text: str) -> str:
    return _TICKET_RE.sub(
        lambda m: f'[{m.group(1)}]({_JIRA_BASE}/{m.group(1)})',
        text,
    )


def _fact_entries(facts: Dict[str, Any]) -> list[dict[str, str]]:
    return [
        {'title': str(key), 'value': _linkify_tickets(str(value))}
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
                'text': _linkify_tickets(str(line)),
                'wrap': True,
            })

    return {
        '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
        'type': 'AdaptiveCard',
        'version': '1.4',
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


def build_gantt_release_survey_card(payload: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Gantt release-survey response.
    '''
    survey = payload.get('survey', payload)
    releases = survey.get('releases_surveyed', [])
    facts = {
        'Project': survey.get('project_key', ''),
        'Mode': str(survey.get('survey_mode', 'feature_dev')).replace('_', ' ').title(),
        'Releases': len(releases),
        'Total': survey.get('total_tickets', 0),
        'Done': survey.get('done_count', 0),
        'In Progress': survey.get('in_progress_count', 0),
        'Remaining': survey.get('remaining_count', 0),
        'Blocked': survey.get('blocked_count', 0),
    }

    body_lines: list[str] = []
    for summary in (survey.get('release_summaries') or [])[:5]:
        body_lines.append(
            f'• {summary.get("release", "")}: '
            f'{summary.get("done_count", 0)} done, '
            f'{summary.get("in_progress_count", 0)} in progress, '
            f'{summary.get("remaining_count", 0)} remaining, '
            f'{summary.get("blocked_count", 0)} blocked'
        )

    if not body_lines:
        body_lines.append('No release-survey details were returned.')

    return build_fact_card(
        title=f'Gantt Release Survey — {survey.get("project_key", "")}',
        subtitle=str(survey.get('created_at', '') or '').strip() or None,
        facts=facts,
        body_lines=body_lines,
    )


def build_gantt_nl_query_card(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not data or not data.get('ok'):
        error = data.get('error', 'Query failed') if data else 'No data'
        return build_fact_card(
            title='Query Failed',
            subtitle=str(error),
        )

    query = data.get('query', '')
    tool_used = data.get('tool_used', 'unknown')
    tool_args = data.get('tool_args', {})
    summary = data.get('summary', '')
    result = data.get('result') or {}

    facts = {'Query': query, 'Tool': tool_used}

    if tool_args.get('jql'):
        facts['JQL'] = tool_args['jql']
    if tool_args.get('releases'):
        facts['Releases'] = ', '.join(tool_args['releases'])
    if tool_args.get('project_key'):
        facts['Project'] = tool_args['project_key']

    total = result.get('total') or result.get('grand_total') or result.get('count') or result.get('total_open')
    if total is not None:
        facts['Total'] = str(total)

    body_lines = []
    if summary:
        body_lines.append(summary)

    tickets = result.get('tickets', [])
    if tickets:
        body_lines.append('**Tickets:**')
        for ticket in tickets[:15]:
            key = ticket.get('key', '')
            status = ticket.get('status', '')
            ticket_summary = ticket.get('summary', '')
            assignee = ticket.get('assignee') or 'Unassigned'
            body_lines.append(f'• {key} [{status}] {ticket_summary} ({assignee})')
        if len(tickets) > 15:
            body_lines.append(f'...and {len(tickets) - 15} more')

    return build_fact_card(
        title='Gantt Query Result',
        subtitle=f'Tool: {tool_used}',
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


def build_pr_hygiene_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a GitHub PR hygiene scan result.
    '''
    repo = data.get('repo', 'Unknown')
    stale_prs = data.get('stale_prs', [])
    missing_reviews = data.get('missing_reviews', [])
    total_open = data.get('total_open_prs', 0)
    total_findings = data.get('total_findings', 0)

    facts = {
        'Repository': repo,
        'Open PRs': total_open,
        'Total Findings': total_findings,
        'Stale PRs': len(stale_prs),
        'Missing Reviews': len(missing_reviews),
    }

    body_lines: list[str] = []

    if stale_prs:
        body_lines.append('**Stale PRs:**')
        for item in stale_prs[:5]:
            pr = item.get('pr', {})
            days = item.get('days_stale', 0)
            severity = item.get('severity', 'medium')
            body_lines.append(
                f'• [{severity.upper()}] #{pr.get("number", "")} '
                f'{pr.get("title", "")} — {days}d stale '
                f'({pr.get("author", "")})'
            )
        if len(stale_prs) > 5:
            body_lines.append(f'  ...and {len(stale_prs) - 5} more')

    if missing_reviews:
        body_lines.append('**Missing Reviews:**')
        for item in missing_reviews[:5]:
            pr = item.get('pr', {})
            reason = item.get('reason', '')
            label = 'no reviewers' if reason == 'no_reviewers' else 'pending reviews'
            body_lines.append(
                f'• #{pr.get("number", "")} '
                f'{pr.get("title", "")} — {label} '
                f'({pr.get("author", "")})'
            )
        if len(missing_reviews) > 5:
            body_lines.append(f'  ...and {len(missing_reviews) - 5} more')

    if not body_lines:
        body_lines.append('No hygiene issues found.')

    return build_fact_card(
        title=f'PR Hygiene — {repo}',
        subtitle=data.get('scan_time', ''),
        facts=facts,
        body_lines=body_lines,
    )


def build_pr_stale_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a stale PR scan result.
    '''
    repo = data.get('repo', 'Unknown')
    stale_prs = data.get('stale_prs', [])
    stale_days = data.get('stale_days', 5)

    facts = {
        'Repository': repo,
        'Threshold': f'{stale_days} days',
        'Stale PRs': len(stale_prs),
    }

    body_lines: list[str] = []
    for item in stale_prs[:8]:
        pr = item.get('pr', {})
        days = item.get('days_stale', 0)
        severity = item.get('severity', 'medium')
        body_lines.append(
            f'• [{severity.upper()}] #{pr.get("number", "")} '
            f'{pr.get("title", "")} — {days}d stale '
            f'({pr.get("author", "")})'
        )
    if len(stale_prs) > 8:
        body_lines.append(f'  ...and {len(stale_prs) - 8} more')

    if not body_lines:
        body_lines.append('No stale PRs found.')

    return build_fact_card(
        title=f'Stale PRs — {repo}',
        facts=facts,
        body_lines=body_lines,
    )


def build_pr_reviews_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a missing reviews scan result.
    '''
    repo = data.get('repo', 'Unknown')
    findings = data.get('missing_reviews', [])

    no_reviewers = [f for f in findings if f.get('reason') == 'no_reviewers']
    pending = [f for f in findings if f.get('reason') == 'pending_reviews']

    facts = {
        'Repository': repo,
        'Total Findings': len(findings),
        'No Reviewers': len(no_reviewers),
        'Pending Reviews': len(pending),
    }

    body_lines: list[str] = []
    for item in findings[:8]:
        pr = item.get('pr', {})
        reason = item.get('reason', '')
        label = 'no reviewers' if reason == 'no_reviewers' else 'pending reviews'
        body_lines.append(
            f'• #{pr.get("number", "")} '
            f'{pr.get("title", "")} — {label} '
            f'({pr.get("author", "")})'
        )
    if len(findings) > 8:
        body_lines.append(f'  ...and {len(findings) - 8} more')

    if not body_lines:
        body_lines.append('All PRs have active reviews.')

    return build_fact_card(
        title=f'Missing Reviews — {repo}',
        facts=facts,
        body_lines=body_lines,
    )


def build_pr_list_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a PR listing result.
    '''
    repo = data.get('repo', 'Unknown')
    prs = data.get('prs', [])
    state = data.get('state', 'open')

    facts = {
        'Repository': repo,
        'State': state,
        'Count': len(prs),
    }

    body_lines: list[str] = []
    for pr in prs[:10]:
        draft = ' [DRAFT]' if pr.get('draft', False) else ''
        reviews = pr.get('review_count', 0)
        approved = ' ✓' if pr.get('approved', False) else ''
        body_lines.append(
            f'• #{pr.get("number", "")} '
            f'{pr.get("title", "")}{draft} '
            f'({pr.get("author", "")}) '
            f'[{reviews} review(s){approved}]'
        )
    if len(prs) > 10:
        body_lines.append(f'  ...and {len(prs) - 10} more')

    if not body_lines:
        body_lines.append(f'No {state} PRs found.')

    return build_fact_card(
        title=f'Pull Requests — {repo}',
        facts=facts,
        body_lines=body_lines,
    )


def build_todays_prs_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for today's PRs result.
    '''
    repo = data.get('repo', 'Unknown')
    prs = data.get('prs', [])
    state = data.get('state', 'all')
    target_date = data.get('target_date', 'today')

    # Group by state for the summary
    opened = [p for p in prs if p.get('state') == 'open']
    merged = [p for p in prs if p.get('merged_at')]
    closed = [p for p in prs if p.get('state') == 'closed' and not p.get('merged_at')]

    facts = {
        'Repository': repo,
        'Filter': state,
        'Date': str(target_date),
        'Total': len(prs),
    }
    if state == 'all':
        facts['Opened'] = len(opened)
        facts['Merged'] = len(merged)
        facts['Closed'] = len(closed)

    body_lines: list[str] = []
    for pr in prs[:12]:
        draft = ' [DRAFT]' if pr.get('draft', False) else ''
        merged_tag = ' ✓merged' if pr.get('merged_at') else ''
        closed_tag = ' ✗closed' if pr.get('state') == 'closed' and not pr.get('merged_at') else ''
        body_lines.append(
            f'• #{pr.get("number", "")} '
            f'{pr.get("title", "")}{draft}{merged_tag}{closed_tag} '
            f'({pr.get("author", "")})'
        )
    if len(prs) > 12:
        body_lines.append(f'  ...and {len(prs) - 12} more')

    if not body_lines:
        body_lines.append(f'No PRs found for {state} on {target_date}.')

    return build_fact_card(
        title=f"Today's PRs — {repo}",
        facts=facts,
        body_lines=body_lines,
    )


def build_bug_updates_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a bug ticket updates polling result.
    '''
    project = data.get('project_key', data.get('project', ''))
    activity = data.get('activity', data)
    summary = activity.get('summary', {})
    opened = activity.get('opened', [])
    status_changed = activity.get('status_changed', [])

    facts = {
        'Project': project,
        'Bugs Opened': summary.get('bugs_opened', 0),
        'Status Transitions': summary.get('status_transitions', 0),
        'Bugs With Comments': summary.get('bugs_with_comments', 0),
    }

    body_lines: list[str] = []
    if opened:
        body_lines.append('**New Bugs:**')
        for bug in opened[:5]:
            key = bug.get('key', '')
            pri = bug.get('priority', '')
            title = bug.get('summary', '')
            body_lines.append(f'• {key} [{pri}] {title}')
        if len(opened) > 5:
            body_lines.append(f'  ...and {len(opened) - 5} more')

    if status_changed:
        body_lines.append('**Status Changes:**')
        for sc in status_changed[:5]:
            body_lines.append(
                f'• {sc.get("key", "")} '
                f'{sc.get("from_status", "")} → {sc.get("to_status", "")} '
                f'({sc.get("changed_by", "")})'
            )
        if len(status_changed) > 5:
            body_lines.append(f'  ...and {len(status_changed) - 5} more')

    if not body_lines:
        body_lines.append('No bug updates detected.')

    return build_fact_card(
        title=f'Bug Updates — {project}',
        facts=facts,
        body_lines=body_lines,
    )


def build_pr_activity_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a GitHub PR activity polling result.
    '''
    repo = data.get('repo', 'Unknown')
    result = data.get('result', data)
    created = result.get('created', [])
    merged = result.get('merged', [])
    minutes = result.get('minutes', 30)

    facts = {
        'Repository': repo,
        'Window': f'Last {minutes} minutes',
        'New PRs': len(created),
        'Merged PRs': len(merged),
    }

    body_lines: list[str] = []
    if created:
        body_lines.append('**New PRs:**')
        for pr in created[:5]:
            draft = ' [DRAFT]' if pr.get('draft', False) else ''
            body_lines.append(
                f'• #{pr.get("number", "")} '
                f'{pr.get("title", "")}{draft} '
                f'({pr.get("author", "")})'
            )
        if len(created) > 5:
            body_lines.append(f'  ...and {len(created) - 5} more')

    if merged:
        body_lines.append('**Merged PRs:**')
        for pr in merged[:5]:
            body_lines.append(
                f'• #{pr.get("number", "")} '
                f'{pr.get("title", "")} '
                f'({pr.get("author", "")})'
            )
        if len(merged) > 5:
            body_lines.append(f'  ...and {len(merged) - 5} more')

    if not body_lines:
        body_lines.append(f'No PR activity in last {minutes} minutes.')

    return build_fact_card(
        title=f'PR Activity — {repo}',
        facts=facts,
        body_lines=body_lines,
    )


def build_naming_compliance_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a naming compliance scan result.
    '''
    repo = data.get('repo', 'Unknown')
    title_results = data.get('title_compliance', {})
    branch_results = data.get('branch_compliance', {})
    total_scanned = data.get('total_scanned', 0)

    facts = {
        'Repository': repo,
        'Total Scanned': total_scanned,
        'Title Compliant': title_results.get('compliant', 0),
        'Title Non-compliant': title_results.get('noncompliant', 0),
        'No Jira Reference': title_results.get('no_jira_count', 0),
        'Branch Compliant': branch_results.get('compliant', 0),
        'Branch Non-compliant': branch_results.get('noncompliant', 0),
    }

    body_lines: list[str] = []

    noncompliant_titles = title_results.get('noncompliant_items', [])
    if noncompliant_titles:
        body_lines.append('**Non-compliant PR Titles:**')
        for item in noncompliant_titles[:5]:
            pr = item.get('pr', {})
            body_lines.append(
                f'• #{pr.get("number", "")} '
                f'{pr.get("title", "")} '
                f'({pr.get("author", "")})'
            )
        if len(noncompliant_titles) > 5:
            body_lines.append(f'  ...and {len(noncompliant_titles) - 5} more')

    noncompliant_branches = branch_results.get('noncompliant_items', [])
    if noncompliant_branches:
        body_lines.append('**Non-compliant Branches:**')
        for item in noncompliant_branches[:5]:
            body_lines.append(
                f'• {item.get("branch", "")} '
                f'(PR #{item.get("pr_number", "")})'
            )
        if len(noncompliant_branches) > 5:
            body_lines.append(f'  ...and {len(noncompliant_branches) - 5} more')

    if not body_lines:
        body_lines.append('All PRs and branches follow naming conventions.')

    return build_fact_card(
        title=f'Naming Compliance — {repo}',
        facts=facts,
        body_lines=body_lines,
    )


def build_merge_conflicts_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a merge conflicts scan result.
    '''
    repo = data.get('repo', 'Unknown')
    conflicts = data.get('conflicting_prs', [])
    total_open = data.get('total_open_prs', 0)
    total_conflicts = data.get('total_conflicts', len(conflicts))

    facts = {
        'Repository': repo,
        'Open PRs': total_open,
        'Total Conflicts': total_conflicts,
    }

    body_lines: list[str] = []
    for item in conflicts[:8]:
        pr = item.get('pr', {})
        body_lines.append(
            f'• #{pr.get("number", "")} '
            f'{pr.get("title", "")} '
            f'({pr.get("author", "")})'
        )
    if len(conflicts) > 8:
        body_lines.append(f'  ...and {len(conflicts) - 8} more')

    if not body_lines:
        body_lines.append('No merge conflicts found.')

    return build_fact_card(
        title=f'Merge Conflicts — {repo}',
        facts=facts,
        body_lines=body_lines,
    )


def build_ci_failures_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a CI failures scan result.
    '''
    repo = data.get('repo', 'Unknown')
    failures = data.get('failing_prs', [])
    total_open = data.get('total_open_prs', 0)
    total_failures = data.get('total_failures', len(failures))

    facts = {
        'Repository': repo,
        'Open PRs': total_open,
        'Total Failures': total_failures,
    }

    body_lines: list[str] = []
    for item in failures[:8]:
        pr = item.get('pr', {})
        failed_checks = item.get('failed_checks', [])
        checks_str = ', '.join(failed_checks[:3])
        if len(failed_checks) > 3:
            checks_str += f' +{len(failed_checks) - 3} more'
        body_lines.append(
            f'• #{pr.get("number", "")} '
            f'{pr.get("title", "")} '
            f'— {checks_str} '
            f'({pr.get("author", "")})'
        )
    if len(failures) > 8:
        body_lines.append(f'  ...and {len(failures) - 8} more')

    if not body_lines:
        body_lines.append('No CI failures found.')

    return build_fact_card(
        title=f'CI Failures — {repo}',
        facts=facts,
        body_lines=body_lines,
    )


def build_stale_branches_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a stale branches scan result.
    '''
    repo = data.get('repo', 'Unknown')
    stale_branches = data.get('stale_branches', [])
    threshold = data.get('stale_days', 30)
    total_branches = data.get('total_branches', 0)
    stale_count = data.get('stale_count', len(stale_branches))

    facts = {
        'Repository': repo,
        'Threshold': f'{threshold} days',
        'Total Branches': total_branches,
        'Stale Branches': stale_count,
    }

    body_lines: list[str] = []
    for item in stale_branches[:10]:
        name = item.get('name', '')
        days = item.get('days_stale', 0)
        author = item.get('last_author', '')
        body_lines.append(
            f'• {name} — {days}d stale ({author})'
        )
    if len(stale_branches) > 10:
        body_lines.append(f'  ...and {len(stale_branches) - 10} more')

    if not body_lines:
        body_lines.append('No stale branches found.')

    return build_fact_card(
        title=f'Stale Branches — {repo}',
        facts=facts,
        body_lines=body_lines,
    )


def build_dry_run_preview_card(
    agent_id: str,
    command: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    '''
    Build an Adaptive Card previewing a dry-run result.

    Shows what WOULD happen if the user confirms execution.
    The user re-sends the same command with "execute" appended to proceed.
    '''
    display_name = agent_display_name(agent_id) or str(agent_id or '').strip().title()

    preview_facts: Dict[str, Any] = {}
    body_lines: list[str] = []

    for key, value in data.items():
        if key == 'dry_run':
            continue
        if isinstance(value, (dict, list)):
            if isinstance(value, list):
                body_lines.append(f'**{key}** ({len(value)} items):')
                for item in value[:5]:
                    if isinstance(item, dict):
                        label = (
                            item.get('ticket_key')
                            or item.get('summary')
                            or item.get('name')
                            or item.get('title')
                            or str(item)
                        )
                        body_lines.append(f'  • {label}')
                    else:
                        body_lines.append(f'  • {item}')
                if len(value) > 5:
                    body_lines.append(f'  ...and {len(value) - 5} more')
            else:
                body_lines.append(f'**{key}**: {len(value)} entries')
        else:
            preview_facts[str(key)] = value

    execute_hint = (
        f'This is a **dry-run preview**. To execute, re-send:\n\n'
        f'`@Shannon {command} ... execute`'
    )

    card_body: list[dict[str, Any]] = [
        {
            'type': 'TextBlock',
            'size': 'Large',
            'weight': 'Bolder',
            'text': f'⏸ Dry Run — {display_name} {command}',
            'wrap': True,
        },
        {
            'type': 'TextBlock',
            'text': 'No changes were made. Review the preview below.',
            'wrap': True,
            'spacing': 'Small',
            'isSubtle': True,
        },
    ]

    fact_items = _fact_entries(preview_facts)
    if fact_items:
        card_body.append({
            'type': 'FactSet',
            'facts': fact_items,
        })

    for line in body_lines:
        if str(line).strip():
            card_body.append({
                'type': 'TextBlock',
                'text': _linkify_tickets(str(line)),
                'wrap': True,
            })

    card_body.append({
        'type': 'TextBlock',
        'text': '---',
        'spacing': 'Medium',
    })
    card_body.append({
        'type': 'TextBlock',
        'text': execute_hint,
        'wrap': True,
        'weight': 'Bolder',
        'color': 'Accent',
    })

    return {
        '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
        'type': 'AdaptiveCard',
        'version': '1.4',
        'body': card_body,
    }


def build_hemingway_pr_review_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hemingway /pr-review response.
    '''
    repo = data.get('repo', '')
    pr_number = data.get('pr_number', '')
    head_branch = data.get('head_branch', '')
    impact_summary = data.get('impact_summary', '')
    files_generated = data.get('files_generated', [])
    files_committed = data.get('files_committed', False)
    commit_sha = data.get('commit_sha', '')
    dry_run = data.get('dry_run', False)

    card_title = f'Hemingway PR Review — {repo} #{pr_number}'
    if dry_run:
        card_title += ' (Dry-Run)'

    facts: Dict[str, Any] = {
        'Repository': repo,
        'PR': f'#{pr_number}',
    }
    if head_branch:
        facts['Branch'] = head_branch
    facts['Committed'] = 'Yes' if files_committed else 'No'
    if commit_sha:
        facts['Commit SHA'] = str(commit_sha)[:12]

    body_lines: list[str] = []
    if impact_summary:
        body_lines.append(f'**Impact:** {impact_summary}')

    if files_generated:
        body_lines.append('**Generated Files:**')
        for fg in files_generated[:10]:
            body_lines.append(f'• {fg.get("path", "")} ({fg.get("operation", "")})')
        if len(files_generated) > 10:
            body_lines.append(f'  ...and {len(files_generated) - 10} more')

    files_planned = data.get('files_planned', [])
    if files_planned:
        body_lines.append('**Planned Files:**')
        for fp in files_planned[:10]:
            body_lines.append(
                f'• {fp.get("source", "")} → {fp.get("target", "")} [{fp.get("doc_type", "")}]'
            )
        if len(files_planned) > 10:
            body_lines.append(f'  ...and {len(files_planned) - 10} more')

    if not body_lines:
        body_lines.append('No documentation impact detected.')

    return build_fact_card(
        title=card_title,
        facts=facts,
        body_lines=body_lines,
    )


def build_hemingway_doc_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hemingway /generate-doc response.
    '''
    doc_id = data.get('doc_id', '')
    title = data.get('title', '')
    doc_type = data.get('doc_type', '')
    confidence = data.get('confidence', '')
    created_at = data.get('created_at', '')
    patches = data.get('patches', [])
    validation = data.get('validation', {})
    warnings = data.get('warnings', [])
    content_markdown = data.get('content_markdown', '')

    facts = {
        'Doc ID': doc_id,
        'Title': title,
        'Type': doc_type,
        'Confidence': confidence,
        'Created': created_at,
    }

    body_lines: list[str] = []
    body_lines.append(f'Patches: {len(patches)}')
    is_valid = validation.get('valid', False)
    body_lines.append(f'Validation: {"valid" if is_valid else "invalid"}')
    body_lines.append(f'Warnings: {len(warnings)}')
    for warning in warnings[:3]:
        body_lines.append(f'• {warning}')

    if content_markdown:
        preview = content_markdown[:200]
        if len(content_markdown) > 200:
            preview += '...'
        body_lines.append(f'**Preview:** {preview}')

    return build_fact_card(
        title=f'Hemingway Doc — {title}',
        subtitle=f'{created_at} | {doc_id}',
        facts=facts,
        body_lines=body_lines,
    )


def build_hemingway_impact_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hemingway /impact-detect response.
    '''
    impact_id = data.get('impact_id', '')
    title = data.get('title', '')
    doc_type = data.get('doc_type', '')
    confidence = data.get('confidence', '')
    affected_targets = data.get('affected_targets', [])
    reasons = data.get('reasons', [])
    blocking_issues = data.get('blocking_issues', [])

    facts = {
        'Impact ID': impact_id,
        'Title': title,
        'Type': doc_type,
        'Confidence': confidence,
    }

    body_lines: list[str] = []
    if affected_targets:
        body_lines.append('**Affected Targets:**')
        for target in affected_targets[:5]:
            body_lines.append(f'• {target}')
        if len(affected_targets) > 5:
            body_lines.append(f'  ...and {len(affected_targets) - 5} more')

    if reasons:
        body_lines.append('**Reasons:**')
        for reason in reasons:
            body_lines.append(f'• {reason}')

    if blocking_issues:
        body_lines.append('**Blocking Issues:**')
        for issue in blocking_issues:
            body_lines.append(f'• {issue}')

    if not body_lines:
        body_lines.append('No impact detected.')

    return build_fact_card(
        title=f'Hemingway Impact — {title}',
        subtitle=impact_id or None,
        facts=facts,
        body_lines=body_lines,
    )


def build_hemingway_records_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hemingway /doc-records or /doc-record response.

    Uses the human-friendly 'records' list when available, falling back to
    raw 'data' for backward compatibility.
    '''
    # Prefer the new human-friendly records list; fall back to raw data
    records = data.get('records', [])
    if not records:
        records = data.get('data', [])
        if isinstance(records, dict):
            records = []
    total = data.get('total', len(records))

    facts = {
        'Total Records': total,
    }

    body_lines: list[str] = []
    for record in records[:10]:
        title = record.get('title', '')
        doc_type_display = record.get('doc_type_display', record.get('doc_type', ''))
        author = record.get('author', 'Hemingway')
        link = record.get('link', '')
        source = record.get('source', '')

        # Build a clean one-liner per record
        line = f'\u2022 **{title}**'
        if doc_type_display:
            line += f' [{doc_type_display}]'
        if author:
            line += f' by {author}'
        if source:
            line += f' ({source})'
        if link:
            line += f' \u2014 [View]({link})'
        body_lines.append(line)

    if len(records) > 10:
        body_lines.append(f'...and {len(records) - 10} more')

    if not body_lines:
        body_lines.append('No documentation records found.')

    return build_fact_card(
        title='Documentation Records',
        facts=facts,
        body_lines=body_lines,
    )


def build_hemingway_search_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hemingway /search-docs response.
    '''
    results = data.get('results', [])
    count = data.get('count', len(results))
    query_text = data.get('query', '')

    filters_applied: list[str] = []
    if query_text:
        filters_applied.append(f'query="{query_text}"')
    for key in ('project_key', 'doc_type', 'source_ref', 'confidence'):
        val = data.get(key)
        if val:
            filters_applied.append(f'{key}={val}')
    if data.get('published_only'):
        filters_applied.append('published_only=true')

    facts: Dict[str, Any] = {
        'Results': count,
    }
    if query_text:
        facts['Query'] = query_text
    if filters_applied:
        facts['Filters'] = ', '.join(filters_applied)

    body_lines: list[str] = []
    for record in results[:8]:
        doc_id = record.get('doc_id', '')
        title = record.get('title', '')
        doc_type_val = record.get('doc_type', '')
        project_key_val = record.get('project_key', '')
        created_at = record.get('created_at', '')
        line = f'• **{title}** [{doc_type_val}]'
        if project_key_val:
            line += f' ({project_key_val})'
        line += f' — {created_at}'
        match_context = record.get('match_context', '')
        if match_context:
            preview = match_context[:120]
            if len(match_context) > 120:
                preview += '...'
            line += f'\n  _{preview}_'
        body_lines.append(line)

    if len(results) > 8:
        body_lines.append(f'...and {len(results) - 8} more results')

    if not body_lines:
        body_lines.append('No matching documentation records found.')

    return build_fact_card(
        title='Documentation Search Results',
        facts=facts,
        body_lines=body_lines,
    )



def build_hemingway_find_card(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build an Adaptive Card for a Hemingway /find response.

    Similar to the search card but uses the human-friendly records list
    and shows the interpreted-as hint when the query was auto-classified.
    """
    # Prefer the new human-friendly records list
    records = data.get('records', [])
    if not records:
        inner = data.get('data', {})
        records = inner.get('results', []) if isinstance(inner, dict) else []
    total = data.get('total', len(records))

    inner_data = data.get('data', {}) if isinstance(data.get('data'), dict) else {}
    query_text = inner_data.get('query', '')
    interpreted_as = inner_data.get('interpreted_as', '')

    facts: Dict[str, Any] = {
        'Results': total,
    }
    if query_text:
        facts['Search'] = query_text
    if interpreted_as:
        facts['Interpreted As'] = interpreted_as

    body_lines: list[str] = []
    for record in records[:10]:
        title = record.get('title', '')
        doc_type_display = record.get('doc_type_display', record.get('doc_type', ''))
        author = record.get('author', 'Hemingway')
        link = record.get('link', '')
        source = record.get('source', '')

        line = f'\u2022 **{title}**'
        if doc_type_display:
            line += f' [{doc_type_display}]'
        if author:
            line += f' by {author}'
        if source:
            line += f' ({source})'
        if link:
            line += f' \u2014 [View]({link})'
        body_lines.append(line)

    if len(records) > 10:
        body_lines.append(f'...and {len(records) - 10} more')

    if not body_lines:
        body_lines.append('No matching documentation found.')

    return build_fact_card(
        title='Documentation Search',
        facts=facts,
        body_lines=body_lines,
    )

def build_hemingway_publication_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hemingway /publish-doc response.
    '''
    doc_id = data.get('doc_id', '')
    title = data.get('title', '')
    publications = data.get('publications', [])

    facts = {
        'Doc ID': doc_id,
        'Title': title,
        'Publications': len(publications),
    }

    body_lines: list[str] = []
    for pub in publications:
        target_type = pub.get('target_type', '')
        status = pub.get('status', '')
        target_ref = pub.get('target_ref', '')
        body_lines.append(f'• {target_type}: {status} ({target_ref})')

    if not body_lines:
        body_lines.append('No publication results.')

    return build_fact_card(
        title=f'Hemingway Publication — {title}',
        subtitle=doc_id or None,
        facts=facts,
        body_lines=body_lines,
    )


def build_hemingway_confluence_publish_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hemingway /confluence-publish response.
    '''
    dry_run = data.get('dry_run', False)
    page_id = data.get('page_id', '')
    title = data.get('title', '')
    operation = data.get('operation', '')
    space = data.get('space', '')
    link = data.get('link', '')
    attachments_uploaded = data.get('attachments_uploaded', [])
    diagrams_rendered = data.get('diagrams_rendered', 0)

    card_title = '\U0001f4c4 Confluence Publication'
    if dry_run:
        card_title += ' (Dry-Run Preview)'

    facts: Dict[str, Any] = {
        'Page ID': page_id,
        'Title': title,
        'Operation': operation,
        'Space': space,
    }
    if link:
        facts['Link'] = link

    body_lines: list[str] = []
    if dry_run:
        body_lines.append('**Preview — no changes made**')
    if attachments_uploaded:
        body_lines.append(f'Attachments uploaded: {len(attachments_uploaded)}')
    if diagrams_rendered:
        body_lines.append(f'Diagrams rendered: {diagrams_rendered}')

    if not body_lines:
        body_lines.append('Publication complete.')

    return build_fact_card(
        title=card_title,
        facts=facts,
        body_lines=body_lines,
    )


def build_drucker_summary_card(data: Dict[str, Any]) -> Dict[str, Any]:
    facts = {
        'Total Requests': data.get('total_requests', 0),
        'Total Errors': data.get('total_errors', 0),
        'Hygiene Reports': data.get('hygiene_reports', 0),
        'Hygiene Findings': data.get('hygiene_findings', 0),
    }

    pr_state = data.get('pr_reminders')
    if pr_state:
        facts['Tracked PRs'] = pr_state.get('tracked_prs', 0)

    by_cat = data.get('by_category', {})
    body_lines: list[str] = []
    if by_cat:
        body_lines.append('**Activity by Category**')
        for cat, info in sorted(by_cat.items()):
            count = info.get('request_count', 0)
            errs = info.get('error_count', 0)
            last = info.get('last_request_at', '')[:19]
            line = f'• **{cat}**: {count} requests'
            if errs:
                line += f' ({errs} errors)'
            if last:
                line += f' — last: {last}'
            body_lines.append(line)

    first = data.get('first_request_at', '')[:19]
    last = data.get('last_request_at', '')[:19]
    if first:
        body_lines.append(f'Tracking since {first}')
    if last:
        body_lines.append(f'Last activity: {last}')

    return build_fact_card(title='Drucker Stats', facts=facts, body_lines=body_lines or None)


def build_jira_query_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''Build an Adaptive Card for a Jira query result.'''
    project_key = data.get('project_key', 'Unknown')
    jql = data.get('jql', '')
    total = data.get('total', 0)
    tickets = data.get('tickets', [])
    by_status = data.get('by_status', {})
    by_type = data.get('by_type', {})

    # Build facts: Total, top 3 statuses (sorted by count desc), top 3 types
    facts: Dict[str, Any] = {'Total': total}
    sorted_statuses = sorted(by_status.items(), key=lambda x: x[1], reverse=True)[:3]
    for status_name, count in sorted_statuses:
        facts[status_name] = count
    sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:3]
    for type_name, count in sorted_types:
        facts[type_name] = count

    # Body lines: first 10 tickets
    body_lines: list[str] = []
    for ticket in tickets[:10]:
        key = ticket.get('key', '')
        status = ticket.get('status', '')
        summary = ticket.get('summary', '')
        assignee = ticket.get('assignee') or 'Unassigned'
        body_lines.append(f'• {key} [{status}] {summary} ({assignee})')
    if len(tickets) > 10:
        body_lines.append(f'...and {len(tickets) - 10} more')

    if not body_lines:
        body_lines.append('No tickets matched the query.')

    return build_fact_card(
        title=f'Jira Query — {project_key}',
        subtitle=f'{total} ticket(s) matched',
        facts=facts,
        body_lines=body_lines,
    )


def build_jira_release_status_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''Build an Adaptive Card for a Jira release status result.'''
    project_key = data.get('project_key', 'Unknown')
    releases = data.get('releases', [])
    grand_total = data.get('grand_total', 0)

    # Facts: Grand Total, then per-release totals
    facts: Dict[str, Any] = {'Grand Total': grand_total}
    for release in releases:
        name = release.get('name', '')
        release_total = release.get('total', 0)
        facts[name] = release_total

    # Body lines: for each release (max 5), show top 3 status counts
    body_lines: list[str] = []
    for release in releases[:5]:
        name = release.get('name', '')
        by_status = release.get('by_status', {})
        open_count = by_status.get('Open', 0)
        in_progress_count = by_status.get('In Progress', 0)
        closed_count = by_status.get('Closed', 0)
        body_lines.append(
            f'**{name}**: Open {open_count}, In Progress {in_progress_count}, Closed {closed_count}'
        )

    if not body_lines:
        body_lines.append('No release data available.')

    return build_fact_card(
        title=f'Release Status — {project_key}',
        subtitle=f'{grand_total} total ticket(s) across {len(releases)} release(s)',
        facts=facts,
        body_lines=body_lines,
    )


def build_jira_ticket_counts_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''Build an Adaptive Card for a Jira ticket count result.'''
    project_key = data.get('project_key', 'Unknown')
    count = data.get('count', 0)
    jql = data.get('jql', '')
    filters = data.get('filters', {})
    issue_types = filters.get('issue_types', [])
    statuses = filters.get('statuses', [])

    facts: Dict[str, Any] = {
        'Count': count,
        'Issue Types': ', '.join(issue_types) if issue_types else 'All',
        'Statuses': ', '.join(statuses) if statuses else 'All',
    }

    # Body lines: JQL truncated to 200 chars
    truncated_jql = jql[:200] if len(jql) > 200 else jql
    body_lines: list[str] = [f'JQL: {truncated_jql}']

    return build_fact_card(
        title=f'Ticket Count — {project_key}',
        facts=facts,
        body_lines=body_lines,
    )


def build_jira_status_report_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''Build an Adaptive Card for a Jira project status report.'''
    project_key = data.get('project_key', 'Unknown')
    generated_at = data.get('generated_at', '')
    total_open = data.get('total_open', 0)
    by_status = data.get('by_status', {})
    by_priority = data.get('by_priority', {})
    bugs = data.get('bugs', {})
    recently_updated = data.get('recently_updated', {})
    no_fix_version_count = data.get('no_fix_version_count', 0)

    recent_count = recently_updated.get('count', 0) if recently_updated else 0
    period_days = recently_updated.get('period_days', 0) if recently_updated else 0

    facts: Dict[str, Any] = {
        'Total Open': total_open,
        'Bugs Open': bugs.get('total_open', 0) if bugs else 0,
        'No Fix Version': no_fix_version_count,
        'Recently Updated': f'{recent_count} ({period_days}d)',
    }

    body_lines: list[str] = []

    # By Status: top 5
    sorted_statuses = sorted(by_status.items(), key=lambda x: x[1], reverse=True)[:5]
    if sorted_statuses:
        body_lines.append('**By Status:**')
        for status_name, count in sorted_statuses:
            body_lines.append(f'{status_name}: {count}')

    # By Priority: all
    if by_priority:
        body_lines.append('**By Priority:**')
        for priority_name, count in by_priority.items():
            body_lines.append(f'{priority_name}: {count}')

    # Bug Breakdown
    if bugs:
        bug_by_priority = bugs.get('by_priority', {})
        if bug_by_priority:
            body_lines.append('**Bug Breakdown:**')
            for priority_name, count in bug_by_priority.items():
                body_lines.append(f'{priority_name}: {count}')

    # Recently Updated
    if recently_updated:
        body_lines.append(f'**Recent Activity ({period_days}d):** {recent_count} tickets updated')
        recent_tickets = recently_updated.get('tickets', [])
        for ticket in recent_tickets[:5]:
            key = ticket.get('key', '')
            status = ticket.get('status', '')
            summary = ticket.get('summary', '')
            body_lines.append(f'• {key} [{status}] {summary}')

    if not body_lines:
        body_lines.append('No status data available.')

    return build_fact_card(
        title=f'Project Status — {project_key}',
        subtitle=f'Generated {generated_at}',
        facts=facts,
        body_lines=body_lines,
    )


def build_nl_query_card(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not data or not data.get('ok'):
        error = data.get('error', 'Query failed') if data else 'No data'
        return build_fact_card(
            title='Query Failed',
            subtitle=str(error),
        )

    query = data.get('query', '')
    tool_used = data.get('tool_used', 'unknown')
    tool_args = data.get('tool_args', {})
    summary = data.get('summary', '')
    result = data.get('result') or {}

    facts = {'Query': query, 'Tool': tool_used}

    if tool_args.get('jql'):
        facts['JQL'] = tool_args['jql']
    if tool_args.get('releases'):
        facts['Releases'] = ', '.join(tool_args['releases'])
    if tool_args.get('project_key'):
        facts['Project'] = tool_args['project_key']

    total = result.get('total') or result.get('grand_total') or result.get('count') or result.get('total_open')
    if total is not None:
        facts['Total'] = str(total)

    body_lines = []
    if summary:
        body_lines.append(summary)

    tickets = result.get('tickets', [])
    if tickets:
        body_lines.append('**Tickets:**')
        for ticket in tickets[:15]:
            key = ticket.get('key', '')
            status = ticket.get('status', '')
            ticket_summary = ticket.get('summary', '')
            assignee = ticket.get('assignee') or 'Unassigned'
            body_lines.append(f'• {key} [{status}] {ticket_summary} ({assignee})')
        if len(tickets) > 15:
            body_lines.append(f'...and {len(tickets) - 15} more')

    return build_fact_card(
        title='Drucker Query Result',
        subtitle=f'Tool: {tool_used}',
        facts=facts,
        body_lines=body_lines,
    )


def build_hemingway_voice_config_card(data: Dict[str, Any]) -> Dict[str, Any]:
    """Adaptive Card for Hemingway voice configuration display."""
    active = data.get('active_profile', 'default')
    config = data.get('active_config', {})
    available = data.get('available_profiles', [])

    facts: Dict[str, Any] = {'Active Profile': active}
    if config:
        if config.get('tone'):
            facts['Tone'] = config['tone']
        if config.get('audience'):
            facts['Audience'] = config['audience']
        if config.get('purpose'):
            facts['Purpose'] = config['purpose']

    body_lines: list[str] = []
    style = config.get('style_notes', '')
    if style:
        body_lines.append(str(style)[:300])
    if available:
        profiles_str = ', '.join(available)
        body_lines.append(f'**Available profiles**: {profiles_str}')

    profile_name = config.get('name', active)
    return build_fact_card(
        title='Voice Configuration',
        subtitle=f'Profile: {profile_name}',
        facts=facts,
        body_lines=body_lines or None,
    )



def _classify_doc_category(rec: Dict[str, Any]) -> str:
    source = str(rec.get('source', ''))
    source_type = str(rec.get('source_type', ''))
    doc_type = str(rec.get('doc_type', ''))

    if source_type == 'pr_review' or source.startswith('PR'):
        return 'As-Built (PR)'
    if 'confluence' in source.lower() or 'confluence' in source_type:
        return 'Confluence'
    if doc_type == 'how_to':
        return 'How-To Guide'
    if doc_type == 'user_guide':
        return 'User Guide'
    if doc_type == 'release_note_support':
        return 'Release Notes'
    if doc_type == 'engineering_reference':
        return 'Engineering Reference'
    if source == 'Repository' or source_type == 'reindex':
        return 'Repository'
    if source == 'Local':
        return 'Local'
    return 'Other'


def _get_doc_link(rec: Dict[str, Any]) -> str:
    return str(
        rec.get('file_url')
        or rec.get('pr_url')
        or rec.get('metadata', {}).get('file_url')
        or rec.get('metadata', {}).get('pr_url')
        or rec.get('request', {}).get('file_url')
        or ''
    )


def _doc_link_inline(title: str, url: str) -> dict:
    if url:
        return {
            'type': 'RichTextBlock',
            'inlines': [
                {
                    'type': 'TextRun',
                    'text': '\u2022 ',
                },
                {
                    'type': 'TextRun',
                    'text': title,
                    'selectAction': {
                        'type': 'Action.OpenUrl',
                        'url': url,
                    },
                    'color': 'Accent',
                },
            ],
        }
    return {
        'type': 'TextBlock',
        'text': f'\u2022 {title}',
        'wrap': True,
    }


def build_hemingway_nl_query_card(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not data or not data.get('ok'):
        error = data.get('error', 'Query failed') if data else 'No data'
        return build_fact_card(title='Query Failed', subtitle=str(error))

    query = data.get('query', '')
    tool_used = data.get('tool_used', 'unknown')
    summary = data.get('summary', '')
    result = data.get('result') or {}

    raw_data = result.get('data', result.get('results', []))
    if isinstance(raw_data, dict):
        records = raw_data.get('results', [])
    elif isinstance(raw_data, list):
        records = raw_data
    else:
        records = []
    if not isinstance(records, list):
        records = []

    total = (
        (raw_data.get('count') if isinstance(raw_data, dict) else None)
        or result.get('total')
        or len(records)
    )

    card_body: list = [
        {
            'type': 'TextBlock',
            'size': 'Large',
            'weight': 'Bolder',
            'text': 'Hemingway Query Result',
            'wrap': True,
        },
        {
            'type': 'TextBlock',
            'text': f'{total} document(s) found',
            'wrap': True,
            'spacing': 'Small',
            'isSubtle': True,
        },
        {
            'type': 'FactSet',
            'facts': [
                {'title': 'Query', 'value': query},
                {'title': 'Results', 'value': str(total)},
            ],
        },
    ]

    if records:
        categories: Dict[str, list] = {}
        for rec in records[:20]:
            cat = _classify_doc_category(rec)
            categories.setdefault(cat, []).append(rec)

        for cat in sorted(categories.keys()):
            card_body.append({
                'type': 'TextBlock',
                'text': f'**{cat}**',
                'wrap': True,
                'spacing': 'Medium',
                'weight': 'Bolder',
            })

            for rec in categories[cat]:
                title = rec.get('title', rec.get('doc_title', 'Untitled'))
                link = _get_doc_link(rec)
                card_body.append(_doc_link_inline(title, link))

        if total and int(total) > 20:
            card_body.append({
                'type': 'TextBlock',
                'text': '...and ' + str(int(total) - 20) + ' more',
                'wrap': True,
                'isSubtle': True,
            })
    elif summary:
        card_body.append({
            'type': 'TextBlock',
            'text': summary,
            'wrap': True,
        })

    if not records and not summary:
        card_body.append({
            'type': 'TextBlock',
            'text': 'No results found.',
            'wrap': True,
        })

    return {
        '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
        'type': 'AdaptiveCard',
        'version': '1.4',
        'body': card_body,
    }


def build_hemingway_reindex_card(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build an Adaptive Card for a Hemingway /reindex response.
    Shows how many docs were indexed vs skipped from a GitHub repo.
    """
    if not data or not data.get("ok"):
        error = data.get("error", "Reindex failed") if data else "No data"
        return build_fact_card(
            title="Reindex Failed",
            subtitle=str(error),
        )

    result = data.get("data", {})
    repo = result.get("repo", "unknown")
    branch = result.get("branch", "main")
    docs_dir = result.get("docs_dir", "docs")
    files_found = result.get("files_found", 0)
    indexed = result.get("indexed", 0)
    skipped = result.get("skipped", 0)
    errors = result.get("errors", [])

    facts = {
        "Repository": repo,
        "Branch": branch,
        "Docs Dir": docs_dir,
        "Files Found": str(files_found),
        "Indexed": str(indexed),
        "Skipped (already indexed)": str(skipped),
    }

    body_lines: List[str] = []
    if errors:
        facts["Errors"] = str(len(errors))
        for err in errors[:5]:
            body_lines.append(f"⚠️ {err}")

    return build_fact_card(
        title="📚 Docs Re-indexed",
        subtitle=f"{repo} ({branch}:{docs_dir}/)",
        facts=facts,
        body_lines=body_lines if body_lines else None,
    )
