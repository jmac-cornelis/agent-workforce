##########################################################################################
#
# Module: agents/gantt/nl_query.py
#
# Description: Natural language query translation for Gantt. Uses LLM function calling
#              to convert plain English questions into structured Gantt tool calls, execute
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
            'name': 'gantt_release_health',
            'description': (
                'Run a release health monitoring report. Analyzes bug counts, '
                'velocity trends, readiness assessment, and roadmap gap analysis '
                'for one or more releases. Use for "how healthy is the release" '
                'or "release readiness" questions.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'project_key': {
                        'type': 'string',
                        'description': 'Jira project key',
                        'default': 'STL',
                    },
                    'releases': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': (
                            'Release/fixVersion names to monitor. '
                            'Use full format like "12.2.0.x" not "12.2"'
                        ),
                    },
                    'include_gap_analysis': {
                        'type': 'boolean',
                        'description': 'Include roadmap gap analysis',
                        'default': True,
                    },
                    'include_bug_report': {
                        'type': 'boolean',
                        'description': 'Include bug status/priority breakdown',
                        'default': True,
                    },
                    'include_velocity': {
                        'type': 'boolean',
                        'description': 'Include velocity and throughput metrics',
                        'default': True,
                    },
                    'include_readiness': {
                        'type': 'boolean',
                        'description': 'Include release readiness assessment',
                        'default': True,
                    },
                },
                'required': ['project_key'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'gantt_release_tasks',
            'description': (
                'Query and count Jira tickets by fixVersion and optional status '
                'filter. Returns ticket lists with status/type breakdowns. '
                'Use for "what tickets are in release X" or "how many open '
                'tickets in 12.2" questions.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'project_key': {
                        'type': 'string',
                        'description': 'Jira project key',
                        'default': 'STL',
                    },
                    'fix_version': {
                        'type': 'string',
                        'description': (
                            'Release/fixVersion name. '
                            'Use full format like "12.2.0.x" not "12.2"'
                        ),
                    },
                    'statuses': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': (
                            'Filter by statuses. Common: Open, In Progress, '
                            'In Review, Ready, Verify, To Do, Closed, Done, Resolved'
                        ),
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Max tickets to return',
                        'default': 500,
                    },
                },
                'required': ['fix_version'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'gantt_planning_snapshot',
            'description': (
                'Create a planning snapshot from Jira backlog state. Analyzes '
                'epics, stories, dependencies, milestones, and risks. '
                'Use for "create a planning snapshot" or "what does the backlog '
                'look like" questions.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'project_key': {
                        'type': 'string',
                        'description': 'Jira project key',
                        'default': 'STL',
                    },
                    'planning_horizon_days': {
                        'type': 'integer',
                        'description': 'Planning horizon in days',
                        'default': 90,
                    },
                },
                'required': ['project_key'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'gantt_release_survey',
            'description': (
                'Run a release execution survey. Analyzes done, in-progress, '
                'and remaining work for one or more releases. '
                'Use for "release progress" or "how much work is left" questions.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'project_key': {
                        'type': 'string',
                        'description': 'Jira project key',
                        'default': 'STL',
                    },
                    'releases': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': (
                            'Release/fixVersion names to survey. '
                            'Use full format like "12.2.0.x" not "12.2"'
                        ),
                    },
                },
                'required': ['project_key'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'gantt_plan_export',
            'description': (
                'Export plan scope to an indented Excel file. Can export by '
                'epic keys (with hierarchy) or by fixVersion. '
                'Use for "export the plan" or "give me a spreadsheet" questions.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'project_key': {
                        'type': 'string',
                        'description': 'Jira project key',
                        'default': 'STL',
                    },
                    'epic_keys': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Epic ticket keys to export (e.g. ["STL-1234", "STL-5678"])',
                    },
                    'fix_version': {
                        'type': 'string',
                        'description': (
                            'Release/fixVersion name to export. '
                            'Use full format like "12.2.0.x" not "12.2"'
                        ),
                    },
                },
                'required': ['project_key'],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# System prompt for the LLM query translator
# ---------------------------------------------------------------------------

NL_SYSTEM_PROMPT = '''You are a Gantt project planning query assistant for Cornelis Networks Jira projects.
You translate plain English questions into structured tool calls for project planning,
release management, and delivery tracking.

CONVENTIONS:
- Default project: STL
- Other projects: WFR, CN
- Jira fix versions use format: "12.2.0.x", "12.3.0.x", "14.0.0.x"
  - User says "12.2" → use "12.2.0.x"
  - User says "12.1.2" → use "12.1.2.x"
  - User says "14" → use "14.0.0.x"
- Common issue types: Bug, Story, Epic, Initiative, Task, SW Release
- Common statuses: Open, In Progress, In Review, Ready, Verify, To Do, Closed, Done, Resolved

TOOL SELECTION:
- Release health / readiness / bug breakdown → gantt_release_health
- Tickets in a release / count by version+status → gantt_release_tasks
- Planning snapshot / backlog overview / dependencies → gantt_planning_snapshot
- Release progress / done vs remaining / execution survey → gantt_release_survey
- Export plan to Excel / spreadsheet → gantt_plan_export

Always call exactly one tool per query.'''


# ---------------------------------------------------------------------------
# Tool executor functions — lazy imports from Gantt agent and utilities
# ---------------------------------------------------------------------------

def _exec_gantt_release_health(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute release health monitoring via the Gantt agent."""
    from agents.gantt.agent import GanttProjectPlannerAgent
    from agents.gantt.models import ReleaseMonitorRequest
    from agents.pm_runtime import normalize_csv_list

    project_key = args.get('project_key', 'STL')
    releases = args.get('releases')

    agent = GanttProjectPlannerAgent(project_key=project_key)
    request = ReleaseMonitorRequest(
        project_key=project_key,
        releases=normalize_csv_list(releases) or None,
        include_gap_analysis=args.get('include_gap_analysis', True),
        include_bug_report=args.get('include_bug_report', True),
        include_velocity=args.get('include_velocity', True),
        include_readiness=args.get('include_readiness', True),
        compare_to_previous=True,
        output_file=f'{project_key}_release_monitor.xlsx',
    )
    report = agent.create_release_monitor(request)
    return report.to_dict()


def _exec_gantt_release_tasks(args: Dict[str, Any]) -> Dict[str, Any]:
    """Query tickets by fixVersion and optional status filter."""
    import jira_utils as _jira_utils
    from agents.pm_runtime import normalize_csv_list

    project_key = args.get('project_key', 'STL')
    fix_version = args['fix_version']
    statuses = normalize_csv_list(args.get('statuses'))
    limit = args.get('limit', 500)

    jira = _jira_utils.connect_to_jira()

    jql_parts = [
        f'project = "{project_key}"',
        f'fixVersion = "{fix_version}"',
    ]
    if statuses:
        status_list = ', '.join(f'"{s}"' for s in statuses)
        jql_parts.append(f'status IN ({status_list})')

    jql = ' AND '.join(jql_parts) + ' ORDER BY priority ASC, updated DESC'
    issues = _jira_utils.run_jql_query(jira, jql, limit=limit) or []

    # Build ticket summaries
    tickets = []
    status_breakdown: Dict[str, int] = {}
    type_breakdown: Dict[str, int] = {}

    for t in issues:
        fields = t.get('fields', {}) or {}
        status_obj = fields.get('status') or {}
        type_obj = fields.get('issuetype') or {}
        priority_obj = fields.get('priority') or {}
        assignee_obj = fields.get('assignee') or {}

        s = status_obj.get('name', '') if isinstance(status_obj, dict) else str(status_obj)
        it = type_obj.get('name', '') if isinstance(type_obj, dict) else str(type_obj)

        status_breakdown[s] = status_breakdown.get(s, 0) + 1
        type_breakdown[it] = type_breakdown.get(it, 0) + 1

        tickets.append({
            'key': t.get('key', ''),
            'summary': fields.get('summary', ''),
            'status': s,
            'issue_type': it,
            'priority': priority_obj.get('name', '') if isinstance(priority_obj, dict) else str(priority_obj),
            'assignee': assignee_obj.get('displayName', '') if isinstance(assignee_obj, dict) else str(assignee_obj),
        })

    return {
        'project_key': project_key,
        'fix_version': fix_version,
        'total_tickets': len(tickets),
        'by_status': status_breakdown,
        'by_issue_type': type_breakdown,
        'tickets': tickets,
    }


def _exec_gantt_planning_snapshot(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a planning snapshot via the Gantt agent."""
    from agents.gantt.agent import GanttProjectPlannerAgent
    from agents.gantt.models import PlanningRequest

    project_key = args.get('project_key', 'STL')
    planning_horizon_days = args.get('planning_horizon_days', 90)

    agent = GanttProjectPlannerAgent(project_key=project_key)
    request = PlanningRequest(
        project_key=project_key,
        planning_horizon_days=planning_horizon_days,
        limit=200,
        include_done=False,
    )
    snapshot = agent.create_snapshot(request)
    return snapshot.to_dict()


def _exec_gantt_release_survey(args: Dict[str, Any]) -> Dict[str, Any]:
    """Run a release execution survey via the Gantt agent."""
    from agents.gantt.agent import GanttProjectPlannerAgent
    from agents.gantt.models import ReleaseSurveyRequest
    from agents.pm_runtime import normalize_csv_list

    project_key = args.get('project_key', 'STL')
    releases = args.get('releases')

    agent = GanttProjectPlannerAgent(project_key=project_key)
    request = ReleaseSurveyRequest(
        project_key=project_key,
        releases=normalize_csv_list(releases) or None,
        survey_mode='feature_dev',
        output_file=f'{project_key}_release_survey.xlsx',
    )
    survey = agent.create_release_survey(request)
    return survey.to_dict()


def _exec_gantt_plan_export(args: Dict[str, Any]) -> Dict[str, Any]:
    """Export plan scope to Excel."""
    from agents.pm_runtime import normalize_csv_list

    project_key = args.get('project_key', 'STL')
    epic_keys = normalize_csv_list(args.get('epic_keys'))
    fix_version = args.get('fix_version')

    if epic_keys:
        # Export by epic keys using excel_utils.build_excel_map
        import excel_utils as _excel_utils
        from datetime import datetime, timezone

        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        output_path = f'data/gantt_exports/{project_key}_plan_export_{timestamp}.xlsx'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        _excel_utils.build_excel_map(
            ticket_keys=epic_keys,
            hierarchy_depth=1,
            limit=500,
            output_file=output_path,
            project_key=project_key,
        )
        return {
            'mode': 'epic_keys',
            'epic_keys': epic_keys,
            'output_file': output_path,
        }

    elif fix_version:
        # Export by fixVersion using jira_utils query + dump
        import jira_utils as _jira_utils
        from datetime import datetime, timezone

        jira = _jira_utils.connect_to_jira()
        jql = (
            f'project = "{project_key}" AND fixVersion = "{fix_version}" '
            f'ORDER BY priority ASC, updated DESC'
        )
        issues = _jira_utils.run_jql_query(jira, jql, limit=500) or []

        if not issues:
            return {
                'mode': 'fix_version',
                'fix_version': fix_version,
                'total_tickets': 0,
                'output_file': None,
                'message': 'No tickets found for the specified release',
            }

        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        release_tag = fix_version.replace('.', '-')
        output_path = f'data/gantt_exports/{project_key}_{release_tag}_{timestamp}.xlsx'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        _jira_utils.dump_tickets_to_file(
            issues,
            dump_file=output_path,
            dump_format='excel',
            table_format='indented',
        )
        return {
            'mode': 'fix_version',
            'fix_version': fix_version,
            'total_tickets': len(issues),
            'output_file': output_path,
        }

    else:
        return {
            'ok': False,
            'error': 'Provide either epic_keys or fix_version for plan export',
        }


TOOL_EXECUTORS = {
    'gantt_release_health': _exec_gantt_release_health,
    'gantt_release_tasks': _exec_gantt_release_tasks,
    'gantt_planning_snapshot': _exec_gantt_planning_snapshot,
    'gantt_release_survey': _exec_gantt_release_survey,
    'gantt_plan_export': _exec_gantt_plan_export,
}


# ---------------------------------------------------------------------------
# Result summarizer — second LLM call (no tools)
# ---------------------------------------------------------------------------

def _summarize_results(llm, query, tool_name, tool_args, result):
    """Summarize tool results into a human-readable response."""
    result_preview = json.dumps(result, default=str)
    if len(result_preview) > 8000:
        # Truncate large payloads but keep summary-level data
        preview = dict(result) if isinstance(result, dict) else {'data': str(result)[:4000]}
        for key in ('tickets', 'issues', 'items'):
            if key in preview and isinstance(preview[key], list):
                preview[key] = preview[key][:10]
                preview[f'{key}_truncated'] = True
        result_preview = json.dumps(preview, default=str)

    from llm.base import Message

    messages = [
        Message.system(
            'Summarize these Gantt project planning results concisely for the user. '
            'Be specific with numbers. Highlight key risks, blockers, and progress. '
            'Use plain English, not JSON.'
        ),
        Message.user(
            f'User asked: {query}\n'
            f'Tool: {tool_name}\n'
            f'Args: {json.dumps(tool_args)}\n'
            f'Results:\n{result_preview}'
        ),
    ]
    response = llm.chat(messages=messages, temperature=0.3, max_tokens=500)
    return response.content


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_nl_query(query: str, project_key: str = 'STL') -> Dict[str, Any]:
    """Translate a plain English query into a Gantt tool call, execute it,
    and return structured results with a natural language summary."""
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
        return {
            'ok': False,
            'error': str(e),
            'tool_used': tool_name,
            'tool_args': tool_args,
        }

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
