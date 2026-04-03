##########################################################################################
#
# Module: agents/drucker/jira_reporting.py
#
# Description: Jira query and status reporting utilities for Drucker. Wraps jira_utils
#              functions with ticket normalization and breakdown computation.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

log = logging.getLogger(os.path.basename(sys.argv[0]))


def normalize_ticket(issue: Dict[str, Any]) -> Dict[str, Any]:
    '''Convert a raw Jira REST API issue dict to a clean normalized dict.'''
    fields = issue.get('fields', {}) or {}

    status_obj = fields.get('status') or {}
    status = status_obj.get('name', '') if isinstance(status_obj, dict) else ''

    issuetype_obj = fields.get('issuetype') or {}
    issue_type = issuetype_obj.get('name', '') if isinstance(issuetype_obj, dict) else ''

    priority_obj = fields.get('priority') or {}
    priority = priority_obj.get('name', '') if isinstance(priority_obj, dict) else ''

    assignee_obj = fields.get('assignee') or {}
    assignee = assignee_obj.get('displayName', '') if isinstance(assignee_obj, dict) else ''

    fix_versions = fields.get('fixVersions') or []
    fix_version = fix_versions[0].get('name', '') if fix_versions else ''

    components_raw = fields.get('components') or []
    components = [c.get('name', '') for c in components_raw if isinstance(c, dict)]

    labels = fields.get('labels') or []

    return {
        'key': issue.get('key', ''),
        'summary': fields.get('summary', ''),
        'status': status,
        'issue_type': issue_type,
        'priority': priority,
        'assignee': assignee,
        'created': fields.get('created', ''),
        'updated': fields.get('updated', ''),
        'fix_version': fix_version,
        'components': components,
        'labels': list(labels),
    }


def compute_breakdowns(tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
    '''Compute status/type/priority/assignee breakdowns from normalized tickets.'''
    status_counter: Counter = Counter()
    type_counter: Counter = Counter()
    priority_counter: Counter = Counter()
    assignee_counter: Counter = Counter()

    for t in tickets:
        status_counter[t.get('status', '')] += 1
        type_counter[t.get('issue_type', '')] += 1
        priority_counter[t.get('priority', '')] += 1
        assignee_counter[t.get('assignee', '') or 'Unassigned'] += 1

    return {
        'by_status': dict(status_counter),
        'by_type': dict(type_counter),
        'by_priority': dict(priority_counter),
        'by_assignee': dict(assignee_counter),
    }


def query_jql(jql: str, project_key: str = '', limit: int = 100) -> Dict[str, Any]:
    '''Run an arbitrary JQL query and return normalized tickets with breakdowns.'''
    import jira_utils

    jira = jira_utils.connect_to_jira()
    raw_issues = jira_utils.run_jql_query(jira, jql, limit=limit)

    normalized = [normalize_ticket(issue) for issue in raw_issues]
    breakdowns = compute_breakdowns(normalized)

    return {
        'project_key': project_key,
        'jql': jql,
        'total': len(normalized),
        'tickets': normalized,
        'by_status': breakdowns['by_status'],
        'by_type': breakdowns['by_type'],
        'by_priority': breakdowns['by_priority'],
        'by_assignee': breakdowns['by_assignee'],
    }


def query_tickets(
    project_key: str,
    issue_types: Optional[List[str]] = None,
    statuses: Optional[List[str]] = None,
    exclude_statuses: Optional[List[str]] = None,
    date_filter: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    '''Query tickets by project with optional filters and return normalized results.'''
    import jira_utils

    status_filter = None
    if statuses:
        status_filter = statuses
    elif exclude_statuses:
        status_filter = {'exclude': exclude_statuses}

    jira = jira_utils.connect_to_jira()
    raw_issues = jira_utils.get_tickets(
        jira, project_key,
        issue_types=issue_types,
        statuses=status_filter,
        date_filter=date_filter,
        limit=limit,
    )

    normalized = [normalize_ticket(issue) for issue in raw_issues]
    breakdowns = compute_breakdowns(normalized)

    return {
        'project_key': project_key,
        'jql': '',
        'total': len(normalized),
        'tickets': normalized,
        'by_status': breakdowns['by_status'],
        'by_type': breakdowns['by_type'],
        'by_priority': breakdowns['by_priority'],
        'by_assignee': breakdowns['by_assignee'],
    }


def query_release_status(
    project_key: str,
    releases: List[str],
    issue_types: Optional[List[str]] = None,
    statuses: Optional[List[str]] = None,
    limit: int = 500,
) -> Dict[str, Any]:
    '''Query ticket status for one or more releases.'''
    import jira_utils

    jira = jira_utils.connect_to_jira()
    release_results = []
    grand_total = 0

    for release_name in releases:
        raw_issues = jira_utils.get_release_tickets(
            jira, project_key, release_name,
            issue_types=issue_types,
            statuses=statuses,
            limit=limit,
        )
        normalized = [normalize_ticket(issue) for issue in raw_issues]
        breakdowns = compute_breakdowns(normalized)
        grand_total += len(normalized)

        release_results.append({
            'name': release_name,
            'total': len(normalized),
            'tickets': normalized,
            'by_status': breakdowns['by_status'],
            'by_type': breakdowns['by_type'],
            'by_priority': breakdowns['by_priority'],
        })

    return {
        'project_key': project_key,
        'releases': release_results,
        'grand_total': grand_total,
    }


def get_ticket_counts(
    project_key: str,
    issue_types: Optional[List[str]] = None,
    statuses: Optional[List[str]] = None,
    date_filter: Optional[str] = None,
) -> Dict[str, Any]:
    '''Get ticket counts without fetching full ticket data.'''
    import jira_utils

    jira = jira_utils.connect_to_jira()
    result = jira_utils.get_ticket_totals(
        jira, project_key,
        issue_types=issue_types,
        statuses=statuses,
        date_filter=date_filter,
    )

    return {
        'project_key': project_key,
        'count': result['count'],
        'jql': result.get('jql', ''),
        'filters': {
            'issue_types': issue_types or [],
            'statuses': statuses or [],
        },
    }


def get_status_report(
    project_key: str,
    include_bugs: bool = True,
    include_activity: bool = True,
    recent_days: int = 7,
) -> Dict[str, Any]:
    '''Generate a comprehensive status report for a project.'''
    import jira_utils

    jira = jira_utils.connect_to_jira()

    open_jql = (
        f'project = {project_key} '
        f'AND status not in (Closed, Done, Resolved) '
        f'ORDER BY created DESC'
    )
    all_open_raw = jira_utils.run_jql_query(jira, open_jql, limit=None)
    all_open = [normalize_ticket(issue) for issue in all_open_raw]
    breakdowns = compute_breakdowns(all_open)

    report: Dict[str, Any] = {
        'project_key': project_key,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_open': len(all_open),
        'by_status': breakdowns['by_status'],
        'by_type': breakdowns['by_type'],
        'by_priority': breakdowns['by_priority'],
        'by_assignee': breakdowns['by_assignee'],
    }

    if include_bugs:
        bugs = [t for t in all_open if t.get('issue_type', '').lower() == 'bug']
        bug_priority: Counter = Counter()
        bug_status: Counter = Counter()
        bug_component: Counter = Counter()
        for b in bugs:
            bug_priority[b.get('priority', '')] += 1
            bug_status[b.get('status', '')] += 1
            for comp in b.get('components', []):
                bug_component[comp] += 1
        report['bugs'] = {
            'total_open': len(bugs),
            'by_priority': dict(bug_priority),
            'by_status': dict(bug_status),
            'by_component': dict(bug_component),
        }

    if include_activity:
        jql = (
            f'project = {project_key} AND updated >= -{recent_days}d '
            f'ORDER BY updated DESC'
        )
        recent_raw = jira_utils.run_jql_query(jira, jql, limit=50)
        recent_normalized = [normalize_ticket(issue) for issue in recent_raw]
        report['recently_updated'] = {
            'count': len(recent_normalized),
            'period_days': recent_days,
            'tickets': recent_normalized[:20],
        }

    nfv_jql = (
        f'project = {project_key} AND fixVersion is EMPTY '
        f'AND status not in (Closed, Done, Resolved)'
    )
    nfv_raw = jira_utils.run_jql_query(jira, nfv_jql, limit=None)
    report['no_fix_version_count'] = len(nfv_raw)

    return report
