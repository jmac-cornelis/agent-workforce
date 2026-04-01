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
            'text': f'⏸ Dry Run — {agent_id.title()} {command}',
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
                'text': str(line),
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
        'version': '1.5',
        'body': card_body,
    }


def build_hypatia_doc_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hypatia /generate-doc response.
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
        title=f'Hypatia Doc — {title}',
        subtitle=f'{created_at} | {doc_id}',
        facts=facts,
        body_lines=body_lines,
    )


def build_hypatia_impact_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hypatia /impact-detect response.
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
        title=f'Hypatia Impact — {title}',
        subtitle=impact_id or None,
        facts=facts,
        body_lines=body_lines,
    )


def build_hypatia_records_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hypatia /doc-records or /doc-record response.
    '''
    records = data.get('records', [])
    total = data.get('total', len(records))

    facts = {
        'Total Records': total,
    }

    body_lines: list[str] = []
    for record in records[:10]:
        doc_id = record.get('doc_id', '')
        title = record.get('title', '')
        doc_type = record.get('doc_type', '')
        created_at = record.get('created_at', '')
        body_lines.append(f'• **{doc_id}** {title} [{doc_type}] ({created_at})')

    if len(records) > 10:
        body_lines.append(f'  ...and {len(records) - 10} more')

    if not body_lines:
        body_lines.append('No documentation records found.')

    return build_fact_card(
        title='Hypatia Documentation Records',
        facts=facts,
        body_lines=body_lines,
    )


def build_hypatia_search_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hypatia /search-docs response.
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


def build_hypatia_publication_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hypatia /publish-doc response.
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
        title=f'Hypatia Publication — {title}',
        subtitle=doc_id or None,
        facts=facts,
        body_lines=body_lines,
    )


def build_hypatia_confluence_publish_card(data: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Build an Adaptive Card for a Hypatia /confluence-publish response.
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
