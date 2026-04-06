##########################################################################################
#
# Module: agents/drucker/nl_query.py
#
# Description: Natural language query translation for Drucker. Uses LLM function calling
#              to convert plain English questions into structured Jira tool calls, execute
#              them, and summarize results.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict

log = logging.getLogger(os.path.basename(sys.argv[0]))


# ---------------------------------------------------------------------------
# OpenAI function-calling tool schemas
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'jira_query',
            'description': 'Run an arbitrary Jira JQL query. Use this when the user specifies exact JQL syntax or complex filter conditions that don\'t fit the other tools.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'jql': {'type': 'string', 'description': 'The JQL query string. Example: project = STL AND issuetype = Bug AND updated >= -24h'},
                    'project_key': {'type': 'string', 'description': 'Jira project key', 'default': 'STL'},
                    'limit': {'type': 'integer', 'description': 'Max tickets to return', 'default': 100},
                },
                'required': ['jql'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'jira_tickets',
            'description': 'Query Jira tickets with structured filters (issue type, status, date). Use when the user asks for tickets filtered by type/status/date without writing raw JQL.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'project_key': {'type': 'string', 'description': 'Jira project key', 'default': 'STL'},
                    'issue_types': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Filter by issue types: Bug, Story, Epic, Initiative, Task, SW Release'},
                    'statuses': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Include only these statuses'},
                    'exclude_statuses': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Exclude these statuses. Common: Closed, Done, Resolved'},
                    'date_filter': {'type': 'string', 'description': 'Date filter bucket: recent, last_week, last_month, last_quarter'},
                    'limit': {'type': 'integer', 'description': 'Max tickets to return', 'default': 100},
                },
                'required': ['project_key'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'jira_release_status',
            'description': 'Get ticket breakdown for one or more Jira releases/versions. Shows status, type, and priority distributions per release.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'project_key': {'type': 'string', 'description': 'Jira project key', 'default': 'STL'},
                    'releases': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Release names. Use full version format like "12.2.0.x" not "12.2"'},
                    'issue_types': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Filter by issue types'},
                    'statuses': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Filter by statuses'},
                    'limit': {'type': 'integer', 'description': 'Max tickets per release', 'default': 500},
                },
                'required': ['releases'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'jira_ticket_counts',
            'description': 'Get a fast count of tickets matching filters. No individual ticket data returned. Use for "how many" questions.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'project_key': {'type': 'string', 'description': 'Jira project key', 'default': 'STL'},
                    'issue_types': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Filter by issue types'},
                    'statuses': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Filter by statuses'},
                    'date_filter': {'type': 'string', 'description': 'Date filter: recent, last_week, last_month, last_quarter'},
                },
                'required': ['project_key'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'jira_status_report',
            'description': 'Generate a comprehensive project status report with open ticket counts, bug breakdowns, recent activity, and tickets missing fix versions. Use for broad "how is the project doing" or "give me a status report" questions.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'project_key': {'type': 'string', 'description': 'Jira project key', 'default': 'STL'},
                    'include_bugs': {'type': 'boolean', 'description': 'Include bug breakdown section', 'default': True},
                    'include_activity': {'type': 'boolean', 'description': 'Include recent activity section', 'default': True},
                    'recent_days': {'type': 'integer', 'description': 'Days to look back for recent activity', 'default': 7},
                },
                'required': ['project_key'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'github_prs',
            'description': 'Query GitHub pull requests. Use when the user asks about PRs, pull requests, code reviews, or merges. Supports filtering by state (opened/updated/merged/closed) and date.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'repo': {
                        'type': 'string',
                        'description': 'Full repository name (owner/repo). If user says just a repo name, prepend "cornelisnetworks/". Example: "cornelisnetworks/opa-psm2"',
                    },
                    'state': {
                        'type': 'string',
                        'enum': ['opened', 'updated', 'merged', 'closed', 'all'],
                        'description': 'PR activity filter. "opened"=created, "updated"=any activity, "merged"=merged, "closed"=closed without merge, "all"=any state. Default: "all"',
                    },
                    'target_date': {
                        'type': 'string',
                        'description': 'ISO date (YYYY-MM-DD) to filter on. Use current date for "today". Omit for no date filter (returns all matching PRs).',
                    },
                },
                'required': ['repo'],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# System prompt for the LLM query translator
# ---------------------------------------------------------------------------

NL_SYSTEM_PROMPT = '''You are a Drucker query assistant for Cornelis Networks.
You translate plain English questions into structured tool calls for both Jira and GitHub.

JIRA CONVENTIONS:
- Default project: STL
- Jira fix versions use format: "12.2.0.x", "12.3.0.x", "14.0.0.x"
  - User says "12.2" → use "12.2.0.x"
  - User says "12.1.2" → use "12.1.2.x"
  - User says "14" → use "14.0.0.x"
- Common issue types: Bug, Story, Epic, Initiative, Task, SW Release
- Common statuses: Open, In Progress, In Review, Ready, Verify, To Do, Closed, Done, Resolved
- JQL date functions: updated >= -24h, created >= -7d, updated >= startOfWeek()
- JQL ORDER BY: updated DESC, created DESC, priority ASC

GITHUB CONVENTIONS:
- Default org: cornelisnetworks
- If user says a repo name without org, prepend "cornelisnetworks/"
- Common repos: ifs-all, opa-psm2, opa-fm, libfabric, opa-ff, cn-ai-tools
- PR states: opened (=created), updated (=any activity), merged, closed, all
- For "today" questions, use current date in YYYY-MM-DD format as target_date
- For "this week" questions, use the Monday of the current week as target_date

TOOL SELECTION:
- Jira ticket questions → jira_query, jira_tickets, jira_release_status, jira_ticket_counts, jira_status_report
- GitHub PR questions → github_prs
- "PRs created today", "merged PRs", "show me pull requests" → github_prs
- "Status report" / "how is the project" → jira_status_report

Always call exactly one tool per query.'''


# ---------------------------------------------------------------------------
# Tool executor functions — lazy imports from jira_reporting
# ---------------------------------------------------------------------------

def _exec_jira_query(args: Dict[str, Any]) -> Dict[str, Any]:
    from agents.drucker.jira_reporting import query_jql
    return query_jql(
        jql=args['jql'],
        project_key=args.get('project_key', 'STL'),
        limit=args.get('limit', 100),
    )


def _exec_jira_tickets(args: Dict[str, Any]) -> Dict[str, Any]:
    from agents.drucker.jira_reporting import query_tickets
    return query_tickets(
        project_key=args.get('project_key', 'STL'),
        issue_types=args.get('issue_types'),
        statuses=args.get('statuses'),
        exclude_statuses=args.get('exclude_statuses'),
        date_filter=args.get('date_filter'),
        limit=args.get('limit', 100),
    )


def _exec_jira_release_status(args: Dict[str, Any]) -> Dict[str, Any]:
    from agents.drucker.jira_reporting import query_release_status
    return query_release_status(
        project_key=args.get('project_key', 'STL'),
        releases=args['releases'],
        issue_types=args.get('issue_types'),
        statuses=args.get('statuses'),
        limit=args.get('limit', 500),
    )


def _exec_jira_ticket_counts(args: Dict[str, Any]) -> Dict[str, Any]:
    from agents.drucker.jira_reporting import get_ticket_counts
    return get_ticket_counts(
        project_key=args.get('project_key', 'STL'),
        issue_types=args.get('issue_types'),
        statuses=args.get('statuses'),
        date_filter=args.get('date_filter'),
    )


def _exec_jira_status_report(args: Dict[str, Any]) -> Dict[str, Any]:
    from agents.drucker.jira_reporting import get_status_report
    return get_status_report(
        project_key=args.get('project_key', 'STL'),
        include_bugs=args.get('include_bugs', True),
        include_activity=args.get('include_activity', True),
        recent_days=args.get('recent_days', 7),
    )


def _exec_github_prs(args: Dict[str, Any]) -> Dict[str, Any]:
    '''Execute a GitHub PR query using github_utils.'''
    import github_utils

    repo = args['repo']
    state = args.get('state', 'all')
    target_date = args.get('target_date')

    if target_date:
        # Date-filtered query
        prs = github_utils.list_todays_prs(
            repo,
            state=state,
            target_date=target_date,
        )
    else:
        # No date filter — map state to GitHub API state
        api_state_map = {
            'opened': 'open',
            'updated': 'all',
            'merged': 'closed',
            'closed': 'closed',
            'all': 'all',
        }
        api_state = api_state_map.get(state, 'all')
        prs = github_utils.list_pull_requests(
            repo,
            state=api_state,
            limit=100,
        )
        # Post-filter merged if needed
        if state == 'merged':
            prs = [p for p in prs if p.get('merged_at')]
        elif state == 'closed':
            prs = [p for p in prs if not p.get('merged_at')]

    return {
        'repo': repo,
        'state': state,
        'target_date': target_date or 'no date filter',
        'prs': prs,
        'total': len(prs),
    }


TOOL_EXECUTORS = {
    'jira_query': _exec_jira_query,
    'jira_tickets': _exec_jira_tickets,
    'jira_release_status': _exec_jira_release_status,
    'jira_ticket_counts': _exec_jira_ticket_counts,
    'jira_status_report': _exec_jira_status_report,
    'github_prs': _exec_github_prs,
}


# ---------------------------------------------------------------------------
# Result summarizer — second LLM call (no tools)
# ---------------------------------------------------------------------------

def _summarize_results(llm, query, tool_name, tool_args, result):
    result_preview = json.dumps(result, default=str)
    if len(result_preview) > 8000:
        # Include breakdowns but truncate ticket lists
        preview = dict(result)
        if 'tickets' in preview:
            preview['tickets'] = preview['tickets'][:10]
            preview['tickets_truncated'] = True
        result_preview = json.dumps(preview, default=str)

    from llm.base import Message

    messages = [
        Message.system('Summarize these Jira query results concisely for the user. Be specific with numbers. Use plain English, not JSON.'),
        Message.user(f'User asked: {query}\nTool: {tool_name}\nArgs: {json.dumps(tool_args)}\nResults:\n{result_preview}'),
    ]
    response = llm.chat(messages=messages, temperature=0.3, max_tokens=500)
    return response.content


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_nl_query(query: str, project_key: str = 'STL') -> Dict[str, Any]:
    '''Translate a plain English query into a Drucker tool call, execute it,
    and return structured results with a natural language summary.'''
    from llm.cornelis_llm import CornelisLLM
    from llm.base import Message

    llm = CornelisLLM(model='developer-sonnet')

    messages = [
        Message.system(NL_SYSTEM_PROMPT),
        Message.user(query),
    ]

    response = llm.chat(messages=messages, temperature=0.1, tools=TOOL_SCHEMAS)

    raw = response.raw_response
    choice = raw.choices[0]

    # If the LLM chose not to call a tool, return its text response directly
    if not hasattr(choice.message, 'tool_calls') or not choice.message.tool_calls:
        return {
            'ok': True,
            'query': query,
            'tool_used': None,
            'tool_args': {},
            'result': None,
            'summary': response.content,
        }

    tool_call = choice.message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

    # Inject project_key default
    if 'project_key' not in tool_args:
        tool_args['project_key'] = project_key

    # Execute the selected tool
    executor = TOOL_EXECUTORS.get(tool_name)
    if not executor:
        return {'ok': False, 'error': f'Unknown tool: {tool_name}'}

    try:
        result = executor(tool_args)
    except Exception as e:
        log.error(f'NL query tool execution failed: {tool_name} — {e}')
        return {'ok': False, 'error': str(e), 'tool_used': tool_name, 'tool_args': tool_args}

    # Summarize with second LLM call
    summary = _summarize_results(llm, query, tool_name, tool_args, result)

    return {
        'ok': True,
        'query': query,
        'project_key': tool_args.get('project_key', project_key),
        'tool_used': tool_name,
        'tool_args': tool_args,
        'result': result,
        'summary': summary,
    }
