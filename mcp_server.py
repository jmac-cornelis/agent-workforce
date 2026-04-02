#!/usr/bin/env python3
##########################################################################################
#
# Module: mcp_server.py
#
# Description: Cornelis Jira & GitHub MCP Server.
#              Exposes Jira and GitHub tools via the Model Context Protocol (MCP)
#              so that AI assistants (Claude Desktop, Cursor, Windsurf, etc.) can
#              interact with Jira and GitHub through a standardised tool-calling
#              interface.
#
#              Transport: stdio (JSON-RPC 2.0 over stdin/stdout).
#
# Architecture:
#   MCP Client (Claude Desktop / Cursor / etc.)
#       ↓ stdio (JSON-RPC 2.0)
#   mcp_server.py
#       ↓ function calls
#   jira_utils.py (deterministic Jira API)
#       ↓ REST API
#   Jira Cloud
#
# Usage:
#   python3 mcp_server.py                    # Run as stdio MCP server
#   jira-mcp-server                          # After pipx install
#
# Author: Cornelis Networks
#
##########################################################################################

import json
import logging
import os
import sys
from typing import Any, Optional, cast

from dotenv import load_dotenv

from config.env_loader import resolve_dry_run
from config.jira_identity import get_jira_actor_email

# Load environment variables before importing jira_utils
load_dotenv()

# ---------------------------------------------------------------------------
# Logging — stdout is reserved for MCP JSON-RPC, so ALL logging goes to stderr.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s %(message)s',
    stream=sys.stderr,
)
log = logging.getLogger('jira-mcp-server')

# ---------------------------------------------------------------------------
# MCP SDK imports
# ---------------------------------------------------------------------------
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent
    try:
        from mcp.server import FastMCP
    except ImportError:
        FastMCP = None
except ImportError:
    log.error('MCP SDK not installed. Install with: pip install "mcp[cli]"')
    sys.exit(1)

# ---------------------------------------------------------------------------
# jira_utils / confluence_utils — suppress stdout output so it doesn't corrupt
# the MCP channel. The output() function in each module checks _quiet_mode
# before printing.
# ---------------------------------------------------------------------------
import jira_utils
import confluence_utils
import github_utils
from agents.drucker.agent import DruckerCoordinatorAgent
from agents.drucker.models import DruckerRequest
from agents.gantt.agent import GanttProjectPlannerAgent
from agents.gantt.models import PlanningRequest, ReleaseMonitorRequest, ReleaseSurveyRequest
from agents.hypatia.agent import HypatiaDocumentationAgent
from agents.hypatia.models import DocumentationRequest
from agents.drucker.state.report_store import DruckerReportStore
from agents.gantt.state.dependency_review_store import GanttDependencyReviewStore
from agents.gantt.state.release_monitor_store import GanttReleaseMonitorStore
from agents.gantt.state.release_survey_store import GanttReleaseSurveyStore
from agents.gantt.state.snapshot_store import GanttSnapshotStore
from agents.hypatia.state.record_store import HypatiaRecordStore

# CRITICAL: Suppress all stdout output from jira_utils.  The MCP protocol
# uses stdout exclusively for JSON-RPC 2.0 messages; any stray print()
# would corrupt the transport.
jira_utils._quiet_mode = True
confluence_utils._quiet_mode = True
github_utils._quiet_mode = True

# ---------------------------------------------------------------------------
# MCP Server instance
# ---------------------------------------------------------------------------
if FastMCP is not None:
    server = FastMCP("cornelis-jira")
else:
    server = Server("cornelis-jira")


def _tool_decorator():
    if hasattr(server, 'tool'):
        dynamic_server = cast(Any, server)
        return dynamic_server.tool()

    def _passthrough(func):
        return func

    return _passthrough


# ---------------------------------------------------------------------------
# Helper: format results as JSON text for MCP responses
# ---------------------------------------------------------------------------

def _json_result(data: Any) -> list[Any]:
    """Format *data* as a JSON ``TextContent`` list for MCP tool responses."""
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error_result(message: str) -> list[Any]:
    """Format an error message as a ``TextContent`` list."""
    return [TextContent(type="text", text=json.dumps({"error": message}, indent=2))]


def _issue_to_dict(issue: dict[str, Any]) -> dict[str, Any]:
    """Convert a raw Jira issue dict (from REST API) to a clean serialisable dict.

    The Jira REST API returns issues as nested dicts with a ``key`` and
    ``fields`` sub-dict.  This helper flattens the most useful fields into
    a simple dict suitable for returning to MCP clients.
    """
    if isinstance(issue, dict):
        key = issue.get('key', '')
        fields = issue.get('fields', {})
    elif hasattr(issue, 'key'):
        # jira-python Resource object
        key = issue.key
        fields = issue.raw.get('fields', {}) if hasattr(issue, 'raw') else {}
    else:
        return {'raw': str(issue)}

    # Extract nested field values safely
    issue_type = (fields.get('issuetype') or {}).get('name', 'N/A')
    status = (fields.get('status') or {}).get('name', 'N/A')
    priority = (fields.get('priority') or {}).get('name', 'N/A')
    assignee_obj = fields.get('assignee') or {}
    assignee = assignee_obj.get('displayName', 'Unassigned')
    reporter_obj = fields.get('reporter') or {}
    reporter = reporter_obj.get('displayName', 'Unknown')
    fix_versions = [v.get('name', '') for v in (fields.get('fixVersions') or [])]
    components = [c.get('name', '') for c in (fields.get('components') or [])]
    labels = fields.get('labels') or []

    return {
        'key': key,
        'summary': fields.get('summary', ''),
        'status': status,
        'issue_type': issue_type,
        'priority': priority,
        'assignee': assignee,
        'reporter': reporter,
        'created': (fields.get('created') or '')[:10],
        'updated': (fields.get('updated') or '')[:10],
        'fix_versions': fix_versions,
        'components': components,
        'labels': labels,
        'description': _extract_description(fields.get('description')),
    }


def _extract_description(desc: Any) -> str:
    """Best-effort extraction of plain text from a Jira description field.

    Jira Cloud uses ADF (Atlassian Document Format) for descriptions.  This
    helper walks the ADF tree and concatenates text nodes.  If the description
    is already a plain string it is returned as-is.
    """
    if desc is None:
        return ''
    if isinstance(desc, str):
        return desc

    # ADF document — walk content nodes
    parts: list[str] = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get('type') == 'text':
                parts.append(node.get('text', ''))
            for child in node.get('content', []):
                _walk(child)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(desc)
    return '\n'.join(parts) if parts else str(desc)


def _normalize_transition(transition: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Jira transition payload for MCP responses."""
    transition_fields = transition.get('fields', {}) or {}
    normalized_fields = []
    for field_key, field_info in sorted(
        transition_fields.items(),
        key=lambda item: (not item[1].get('required', False), item[1].get('name', item[0])),
    ):
        normalized_fields.append({
            'key': field_key,
            'name': field_info.get('name', field_key),
            'required': bool(field_info.get('required', False)),
            'type': field_info.get('schema', {}).get('type', 'unknown'),
        })

    return {
        'id': str(transition.get('id', '') or ''),
        'name': transition.get('name', ''),
        'to': (transition.get('to') or {}).get('name', ''),
        'fields': normalized_fields,
    }


def _match_transition(transitions: list[dict[str, Any]], target_status: str) -> Optional[dict[str, Any]]:
    """Match a transition by name or destination status."""
    target = target_status.casefold()
    for transition in transitions:
        if str(transition.get('name', '')).casefold() == target:
            return transition
        if str((transition.get('to') or {}).get('name', '')).casefold() == target:
            return transition
    return None


def _normalize_comment(comment: Any) -> dict[str, Any]:
    """Normalize Jira comment objects or raw comment payloads."""
    if isinstance(comment, dict):
        author = comment.get('author') or {}
        return {
            'id': str(comment.get('id', '') or ''),
            'author': author.get('displayName', ''),
            'author_id': author.get('accountId', ''),
            'created': comment.get('created', ''),
            'updated': comment.get('updated', ''),
            'body': _extract_description(comment.get('body')),
        }

    author = getattr(comment, 'author', None)
    return {
        'id': str(getattr(comment, 'id', '') or ''),
        'author': getattr(author, 'displayName', '') if author else '',
        'author_id': getattr(author, 'accountId', '') if author else '',
        'created': getattr(comment, 'created', '') or '',
        'updated': getattr(comment, 'updated', '') or '',
        'body': _extract_description(getattr(comment, 'body', None)),
    }


def _normalize_changelog(issue: Any) -> list[dict[str, Any]]:
    """Normalize Jira changelog histories."""
    raw = getattr(issue, 'raw', {}) if hasattr(issue, 'raw') else {}
    changelog = raw.get('changelog', {}) if isinstance(raw, dict) else {}
    histories = changelog.get('histories', []) if isinstance(changelog, dict) else []
    normalized = []
    for history in histories:
        author = history.get('author') or {}
        normalized.append({
            'id': str(history.get('id', '') or ''),
            'author': author.get('displayName', ''),
            'author_id': author.get('accountId', ''),
            'created': history.get('created', ''),
            'items': [
                {
                    'field': item.get('field', ''),
                    'from': item.get('fromString', ''),
                    'to': item.get('toString', ''),
                }
                for item in (history.get('items') or [])
            ],
        })
    return normalized


def _get_ticket_payload(
    jira: Any,
    ticket_key: str,
    include_comments: bool = False,
    include_changelog: bool = False,
    include_transitions: bool = False,
) -> dict[str, Any]:
    """Fetch a Jira issue and expand optional details."""
    issue = jira.issue(
        ticket_key,
        fields='*all',
        expand='changelog' if include_changelog else None,
    )
    payload = _issue_to_dict(issue)

    raw = getattr(issue, 'raw', {}) if hasattr(issue, 'raw') else {}
    fields = raw.get('fields', {}) if isinstance(raw, dict) else {}

    if include_comments:
        comment_block = fields.get('comment', {})
        comments = comment_block.get('comments', []) if isinstance(comment_block, dict) else []
        payload['comments'] = [_normalize_comment(comment) for comment in comments]

    if include_changelog:
        payload['changelog'] = _normalize_changelog(issue)

    if include_transitions:
        transitions = jira.transitions(ticket_key, expand='transitions.fields')
        payload['transitions'] = [_normalize_transition(transition) for transition in transitions]

    return payload


def _page_to_dict(page: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Confluence page payload to a small serialisable dict."""
    result = {
        'id': page.get('id') or page.get('page_id') or '',
        'page_id': page.get('page_id') or page.get('id') or '',
        'title': page.get('title', ''),
        'link': page.get('link') or page.get('url') or '',
        'url': page.get('url') or page.get('link') or '',
        'space_id': page.get('space_id', ''),
        'space_key': page.get('space_key', ''),
        'version': page.get('version'),
        'status': page.get('status', ''),
    }
    if 'body_markdown' in page:
        result['body_markdown'] = page.get('body_markdown')
    if 'body_storage' in page:
        result['body_storage'] = page.get('body_storage')
    if 'labels' in page:
        result['labels'] = page.get('labels')
    if 'attachments' in page:
        result['attachments'] = page.get('attachments')
    if 'depth' in page:
        result['depth'] = page.get('depth')
    if 'parent_id' in page:
        result['parent_id'] = page.get('parent_id')
    if 'dry_run' in page:
        result['dry_run'] = page.get('dry_run')
    if 'output_file' in page:
        result['output_file'] = page.get('output_file')
    return result


def _snapshot_record_to_dict(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize a stored Gantt snapshot record for MCP responses."""
    return {
        'snapshot': record.get('snapshot'),
        'summary': record.get('summary'),
        'summary_markdown': record.get('summary_markdown', ''),
    }


def _release_monitor_record_to_dict(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize a stored Gantt release-monitor record for MCP responses."""
    return {
        'report': record.get('report'),
        'summary': record.get('summary'),
        'summary_markdown': record.get('summary_markdown', ''),
    }


def _release_survey_record_to_dict(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize a stored Gantt release-survey record for MCP responses."""
    return {
        'survey': record.get('survey'),
        'summary': record.get('summary'),
        'summary_markdown': record.get('summary_markdown', ''),
    }


# ---------------------------------------------------------------------------
# Tool 1: search_tickets — Run a JQL query
# ---------------------------------------------------------------------------

@_tool_decorator()
async def search_tickets(jql: str, limit: int = 50) -> list[Any]:
    """Search Jira tickets using a JQL query.

    Args:
        jql: JQL query string (e.g. 'project = STL AND status = Open').
        limit: Maximum number of tickets to return (default: 50).
    """
    try:
        jira = jira_utils.get_connection()
        issues = jira_utils.run_jql_query(jira, jql, limit=limit)
        result = [_issue_to_dict(issue) for issue in (issues or [])]
        return _json_result(result)
    except Exception as e:
        log.error(f'search_tickets failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 2: get_ticket — Get a single ticket's details
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_ticket(
    ticket_key: str,
    include_comments: bool = False,
    include_changelog: bool = False,
    include_transitions: bool = False,
) -> list[Any]:
    """Get detailed information for a single Jira ticket.

    Args:
        ticket_key: The Jira issue key (e.g. 'STL-1234').
        include_comments: Whether to include parsed comments.
        include_changelog: Whether to include changelog history.
        include_transitions: Whether to include current workflow transitions.
    """
    try:
        jira = jira_utils.get_connection()
        return _json_result(
            _get_ticket_payload(
                jira,
                ticket_key,
                include_comments=include_comments,
                include_changelog=include_changelog,
                include_transitions=include_transitions,
            )
        )
    except Exception as e:
        if any(token in str(e).lower() for token in ('not found', 'does not exist', '404')):
            return _error_result(f'Ticket {ticket_key} not found')
        log.error(f'get_ticket failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Jira capability sync tools
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_project_fields(
    project_key: str,
    issue_types: Optional[list[str]] = None,
) -> list[Any]:
    """Get create, edit, and transition field metadata for Jira issue types.

    Args:
        project_key: Jira project key (e.g. 'STL').
        issue_types: Optional list of issue types to inspect.
    """
    try:
        jira = jira_utils.get_connection()
        result = jira_utils.get_project_fields(jira, project_key, issue_type_names=issue_types)
        return _json_result(result)
    except Exception as e:
        log.error(f'get_project_fields failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def list_transitions(ticket_key: str) -> list[Any]:
    """List currently available Jira workflow transitions for a ticket."""
    try:
        jira = jira_utils.get_connection()
        transitions = jira.transitions(ticket_key, expand='transitions.fields')
        return _json_result([_normalize_transition(transition) for transition in transitions])
    except Exception as e:
        log.error(f'list_transitions failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def transition_ticket(
    ticket_key: str,
    to_status: str,
    comment: Optional[str] = None,
    fields: Optional[dict[str, Any]] = None,
    dry_run: Optional[bool] = None,
) -> list[Any]:
    """Transition a Jira ticket to a new status.

    Args:
        ticket_key: Jira issue key.
        to_status: Transition name or destination status name.
        comment: Optional comment to add after the transition.
        fields: Optional transition field payload.
        dry_run: Preview only — do not apply the transition.
    """
    try:
        jira = jira_utils.get_connection()
        issue = jira.issue(ticket_key)
        transitions = jira.transitions(issue, expand='transitions.fields')
        target = _match_transition(transitions, to_status)
        if target is None:
            available = [transition.get('name', '') for transition in transitions]
            return _error_result(
                f'Cannot transition to "{to_status}". Available transitions: {available}'
            )

        if resolve_dry_run(dry_run):
            current_status = str(getattr(issue.fields, 'status', ''))
            return _json_result({
                'dry_run': True,
                'ticket_key': ticket_key,
                'current_status': current_status,
                'target_status': to_status,
                'transition': _normalize_transition(target),
                'comment_would_add': comment is not None,
                'fields_would_set': list(fields.keys()) if fields else [],
            })

        transition_kwargs: dict[str, Any] = {}
        if fields:
            transition_kwargs['fields'] = fields
        jira.transition_issue(issue, target['id'], **transition_kwargs)

        if comment:
            jira.add_comment(issue, comment)

        result = _get_ticket_payload(jira, ticket_key)
        result['transition'] = _normalize_transition(target)
        if comment:
            result['comment_added'] = True
        return _json_result(result)
    except Exception as e:
        log.error(f'transition_ticket failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def add_ticket_comment(ticket_key: str, body: str, dry_run: Optional[bool] = None) -> list[Any]:
    """Add a comment to a Jira ticket.

    Args:
        ticket_key: Jira issue key.
        body: Comment body text.
        dry_run: Preview only — do not post the comment.
    """
    try:
        if resolve_dry_run(dry_run):
            return _json_result({
                'dry_run': True,
                'ticket_key': ticket_key,
                'comment_body_length': len(body),
                'comment_body_preview': body[:200],
            })
        jira = jira_utils.get_connection()
        issue = jira.issue(ticket_key)
        comment = jira.add_comment(issue, body)
        return _json_result({
            'ticket_key': ticket_key,
            'comment': _normalize_comment(comment),
        })
    except Exception as e:
        log.error(f'add_ticket_comment failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Confluence tools
# ---------------------------------------------------------------------------

@_tool_decorator()
async def search_confluence_pages(
    pattern: str,
    limit: int = 25,
    space: Optional[str] = None,
) -> list[Any]:
    """Search Confluence pages by title pattern.

    Args:
        pattern: Title search pattern.
        limit: Maximum number of results to return.
        space: Optional Confluence space key or numeric ID.
    """
    try:
        confluence = confluence_utils.get_connection()
        pages = confluence_utils.search_pages(
            confluence,
            pattern=pattern,
            limit=limit,
            space=space,
        )
        return _json_result([_page_to_dict(page) for page in pages])
    except Exception as e:
        log.error(f'search_confluence_pages failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def search_confluence_fulltext(
    query: str,
    limit: int = 25,
    space: Optional[str] = None,
) -> list[Any]:
    """Search Confluence pages by body content (full-text search).

    Args:
        query: Full-text search query to match against page body content.
        limit: Maximum number of results to return.
        space: Optional Confluence space key or numeric ID.
    """
    try:
        confluence = confluence_utils.get_connection()
        pages = confluence_utils.search_pages_fulltext(
            confluence,
            query=query,
            limit=limit,
            space=space,
        )
        return _json_result([_page_to_dict(page) for page in pages])
    except Exception as e:
        log.error(f'search_confluence_fulltext failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def search_confluence_by_label(
    label: str,
    limit: int = 25,
    space: Optional[str] = None,
) -> list[Any]:
    """Search Confluence pages by label.

    Args:
        label: Label name to search for.
        limit: Maximum number of results to return.
        space: Optional Confluence space key or numeric ID.
    """
    try:
        confluence = confluence_utils.get_connection()
        pages = confluence_utils.search_pages_by_label(
            confluence,
            label=label,
            limit=limit,
            space=space,
        )
        return _json_result([_page_to_dict(page) for page in pages])
    except Exception as e:
        log.error(f'search_confluence_by_label failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def get_confluence_page(
    page_id_or_title: str,
    space: Optional[str] = None,
    include_body: bool = False,
) -> list[Any]:
    """Get a Confluence page by page ID or exact title.

    Args:
        page_id_or_title: Existing page ID or exact page title.
        space: Optional Confluence space key or numeric ID.
        include_body: Whether to include the page body in the response.
    """
    try:
        confluence = confluence_utils.get_connection()
        page = confluence_utils.get_page(
            confluence,
            page_id_or_title=page_id_or_title,
            space=space,
            include_body=include_body,
        )
        return _json_result(_page_to_dict(page))
    except Exception as e:
        log.error(f'get_confluence_page failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def create_confluence_page(
    title: str,
    input_file: str,
    space: Optional[str] = None,
    parent_id: Optional[str] = None,
    version_message: Optional[str] = None,
    dry_run: bool = False,
) -> list[Any]:
    """Create a Confluence page from a Markdown file.

    Args:
        title: Title for the new page.
        input_file: Markdown file to publish.
        space: Optional Confluence space key or numeric ID.
        parent_id: Optional parent page ID.
        version_message: Optional Confluence version history message.
        dry_run: Return a publish preview without creating the page.
    """
    try:
        confluence = confluence_utils.get_connection()
        page = confluence_utils.create_page(
            confluence,
            title=title,
            input_file=input_file,
            space=space,
            parent_id=parent_id,
            version_message=version_message,
            dry_run=dry_run,
        )
        result = _page_to_dict(page)
        result['message'] = 'Page preview generated successfully' if dry_run else 'Page created successfully'
        return _json_result(result)
    except Exception as e:
        log.error(f'create_confluence_page failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def update_confluence_page(
    page_id_or_title: str,
    input_file: str,
    space: Optional[str] = None,
    version_message: Optional[str] = None,
    dry_run: bool = False,
) -> list[Any]:
    """Update a Confluence page from a Markdown file.

    Args:
        page_id_or_title: Existing page ID or exact page title.
        input_file: Markdown file to publish.
        space: Optional Confluence space key or numeric ID for title disambiguation.
        version_message: Optional Confluence version history message.
        dry_run: Return a publish preview without updating the page.
    """
    try:
        confluence = confluence_utils.get_connection()
        page = confluence_utils.update_page(
            confluence,
            page_id_or_title=page_id_or_title,
            input_file=input_file,
            space=space,
            version_message=version_message,
            dry_run=dry_run,
        )
        result = _page_to_dict(page)
        result['message'] = 'Page preview generated successfully' if dry_run else 'Page updated successfully'
        return _json_result(result)
    except Exception as e:
        log.error(f'update_confluence_page failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def append_to_confluence_page(
    page_id_or_title: str,
    input_file: str,
    space: Optional[str] = None,
    version_message: Optional[str] = None,
    dry_run: bool = False,
) -> list[Any]:
    """Append Markdown content to an existing Confluence page."""
    try:
        confluence = confluence_utils.get_connection()
        page = confluence_utils.append_page(
            confluence,
            page_id_or_title=page_id_or_title,
            input_file=input_file,
            space=space,
            version_message=version_message,
            dry_run=dry_run,
        )
        result = _page_to_dict(page)
        result['message'] = 'Page preview generated successfully' if dry_run else 'Page appended successfully'
        return _json_result(result)
    except Exception as e:
        log.error(f'append_to_confluence_page failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def update_confluence_section(
    page_id_or_title: str,
    heading: str,
    input_file: str,
    space: Optional[str] = None,
    version_message: Optional[str] = None,
    dry_run: bool = False,
) -> list[Any]:
    """Replace a section under a heading in an existing Confluence page."""
    try:
        confluence = confluence_utils.get_connection()
        page = confluence_utils.update_page_section(
            confluence,
            page_id_or_title=page_id_or_title,
            heading=heading,
            input_file=input_file,
            space=space,
            version_message=version_message,
            dry_run=dry_run,
        )
        result = _page_to_dict(page)
        result['message'] = (
            'Page preview generated successfully' if dry_run else 'Page section updated successfully'
        )
        return _json_result(result)
    except Exception as e:
        log.error(f'update_confluence_section failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def list_confluence_children(
    page_id_or_title: str,
    space: Optional[str] = None,
    recursive: bool = False,
    max_depth: Optional[int] = None,
) -> list[Any]:
    """List child pages for a Confluence page."""
    try:
        confluence = confluence_utils.get_connection()
        rows = (
            confluence_utils.build_page_tree(
                confluence,
                page_id_or_title=page_id_or_title,
                space=space,
                max_depth=max_depth,
            )
            if recursive else
            confluence_utils.list_page_children(
                confluence,
                page_id_or_title=page_id_or_title,
                space=space,
                recursive=False,
            )
        )
        return _json_result([_page_to_dict(row) for row in rows])
    except Exception as e:
        log.error(f'list_confluence_children failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def export_confluence_page(
    page_id_or_title: str,
    output_file: str,
    space: Optional[str] = None,
) -> list[Any]:
    """Export a Confluence page to a Markdown file.

    Args:
        page_id_or_title: Existing page ID or exact page title.
        output_file: Output Markdown file path.
        space: Optional Confluence space key or numeric ID.
    """
    try:
        confluence = confluence_utils.get_connection()
        page = confluence_utils.export_page_to_markdown(
            confluence,
            page_id_or_title=page_id_or_title,
            output_file=output_file,
            space=space,
        )
        result = _page_to_dict(page)
        result['output_file'] = page.get('output_file', output_file)
        result['message'] = 'Page exported successfully'
        return _json_result(result)
    except Exception as e:
        log.error(f'export_confluence_page failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def convert_markdown_to_confluence(
    markdown_text: str,
    render_diagrams: bool = True,
) -> list[Any]:
    """Convert Markdown text to Confluence storage XHTML with diagram rendering.

    This is the primary "markdown to confluence" conversion tool.  It performs
    the full pipeline:

    1. Render diagrams (mermaid fenced blocks, etc.) to PNG images when
       *render_diagrams* is True and the appropriate CLI tools (e.g. ``mmdc``)
       are available on PATH.
    2. Convert the (possibly rewritten) Markdown to Confluence storage XHTML
       using the enhanced converter which supports: headings, paragraphs,
       fenced code blocks, pipe tables, nested lists, task lists, blockquotes,
       GitHub admonitions, horizontal rules, images, bold, italic,
       strikethrough, inline code, and links.

    Args:
        markdown_text: The Markdown content to convert.
        render_diagrams: Whether to render diagram fenced blocks (mermaid)
                         to PNG images.  Defaults to True.
    """
    try:
        result = confluence_utils.convert_markdown_to_confluence(
            markdown_text,
            render_diagrams_flag=render_diagrams,
        )
        return _json_result({
            'storage': result['storage'],
            'attachments': result.get('attachments', []),
            'diagrams_rendered': result.get('diagrams_rendered', 0),
            'diagram_errors': result.get('diagram_errors', []),
            'message': 'Markdown converted to Confluence storage XHTML successfully',
        })
    except Exception as e:
        log.error(f'convert_markdown_to_confluence failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Gantt planning tools
# ---------------------------------------------------------------------------

@_tool_decorator()
async def create_gantt_snapshot(
    project_key: str,
    planning_horizon_days: int = 90,
    limit: int = 200,
    include_done: bool = False,
    backlog_jql: Optional[str] = None,
    policy_profile: str = 'default',
    evidence_paths: Optional[list[str]] = None,
    persist: bool = True,
) -> list[Any]:
    """Create a Gantt planning snapshot from Jira backlog state."""
    try:
        agent = GanttProjectPlannerAgent(project_key=project_key)
        request = PlanningRequest(
            project_key=project_key,
            planning_horizon_days=planning_horizon_days,
            limit=limit,
            include_done=include_done,
            backlog_jql=backlog_jql,
            policy_profile=policy_profile,
            evidence_paths=list(evidence_paths or []),
        )
        snapshot = agent.create_snapshot(request)
        result = {
            'snapshot': snapshot.to_dict(),
        }
        if persist:
            result['stored'] = GanttSnapshotStore().save_snapshot(
                snapshot,
                summary_markdown=snapshot.summary_markdown,
            )
        return _json_result(result)
    except Exception as e:
        log.error(f'create_gantt_snapshot failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def get_gantt_snapshot(
    snapshot_id: str,
    project_key: Optional[str] = None,
) -> list[Any]:
    """Get a persisted Gantt planning snapshot by snapshot ID."""
    try:
        record = GanttSnapshotStore().get_snapshot(snapshot_id, project_key=project_key)
        if not record:
            return _error_result(f'Gantt snapshot {snapshot_id} not found')
        return _json_result(_snapshot_record_to_dict(record))
    except Exception as e:
        log.error(f'get_gantt_snapshot failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def list_gantt_snapshots(
    project_key: Optional[str] = None,
    limit: int = 20,
) -> list[Any]:
    """List persisted Gantt planning snapshots."""
    try:
        rows = GanttSnapshotStore().list_snapshots(project_key=project_key, limit=limit)
        return _json_result(rows)
    except Exception as e:
        log.error(f'list_gantt_snapshots failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def review_gantt_dependency(
    project_key: str,
    source_key: str,
    target_key: str,
    relationship: str = 'blocks',
    accepted: bool = True,
    note: Optional[str] = None,
    reviewer: Optional[str] = None,
) -> list[Any]:
    """Accept or reject an inferred Gantt dependency edge."""
    try:
        record = GanttDependencyReviewStore().record_review(
            project_key=project_key,
            source_key=source_key,
            target_key=target_key,
            relationship=relationship,
            accepted=accepted,
            note=note,
            reviewer=reviewer,
        )
        return _json_result(record)
    except Exception as e:
        log.error(f'review_gantt_dependency failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def list_gantt_dependency_reviews(
    project_key: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
) -> list[Any]:
    """List stored Gantt dependency review decisions."""
    try:
        rows = GanttDependencyReviewStore().list_reviews(
            project_key=project_key,
            status=status,
            limit=limit,
        )
        return _json_result(rows)
    except Exception as e:
        log.error(f'list_gantt_dependency_reviews failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def create_release_monitor(
    project_key: str = 'STL',
    releases: Optional[str] = None,
    scope_label: Optional[str] = None,
    include_gap_analysis: bool = True,
    include_bug_report: bool = True,
    include_velocity: bool = True,
    include_readiness: bool = True,
    compare_to_previous: bool = True,
    output_file: Optional[str] = None,
    persist: bool = True,
) -> list[Any]:
    """Generate a Gantt release-monitor report."""
    try:
        parsed_releases = (
            [item.strip() for item in releases.split(',') if item.strip()]
            if releases else None
        )
        request = ReleaseMonitorRequest(
            project_key=project_key,
            releases=parsed_releases,
            scope_label=scope_label or '',
            include_gap_analysis=include_gap_analysis,
            include_bug_report=include_bug_report,
            include_velocity=include_velocity,
            include_readiness=include_readiness,
            compare_to_previous=compare_to_previous,
            output_file=output_file or f'{project_key}_release_monitor.xlsx',
        )
        agent = GanttProjectPlannerAgent(project_key=project_key)
        report = agent.create_release_monitor(request)
        result = {
            'report': report.to_dict(),
        }
        if persist:
            result['stored'] = GanttReleaseMonitorStore().save_report(
                report,
                summary_markdown=report.summary_markdown,
            )
        return _json_result(result)
    except Exception as e:
        log.error(f'create_release_monitor failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def get_gantt_release_monitor_report(
    report_id: str,
    project_key: Optional[str] = None,
) -> list[Any]:
    """Get a persisted Gantt release-monitor report by report ID."""
    try:
        record = GanttReleaseMonitorStore().get_report(
            report_id,
            project_key=project_key,
        )
        if not record:
            return _error_result(
                f'Gantt release monitor report {report_id} not found'
            )
        return _json_result(_release_monitor_record_to_dict(record))
    except Exception as e:
        log.error(f'get_gantt_release_monitor_report failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def list_gantt_release_monitor_reports(
    project_key: Optional[str] = None,
    limit: int = 20,
) -> list[Any]:
    """List persisted Gantt release-monitor reports."""
    try:
        rows = GanttReleaseMonitorStore().list_reports(
            project_key=project_key,
            limit=limit,
        )
        return _json_result(rows)
    except Exception as e:
        log.error(f'list_gantt_release_monitor_reports failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def create_release_survey(
    project_key: str = 'STL',
    releases: Optional[str] = None,
    scope_label: Optional[str] = None,
    survey_mode: str = 'feature_dev',
    output_file: Optional[str] = None,
    persist: bool = True,
) -> list[Any]:
    """Generate a Gantt release-survey report."""
    try:
        parsed_releases = (
            [item.strip() for item in releases.split(',') if item.strip()]
            if releases else None
        )
        request = ReleaseSurveyRequest(
            project_key=project_key,
            releases=parsed_releases,
            scope_label=scope_label or '',
            survey_mode=survey_mode,
            output_file=output_file or f'{project_key}_release_survey.xlsx',
        )
        agent = GanttProjectPlannerAgent(project_key=project_key)
        survey = agent.create_release_survey(request)
        result = {
            'survey': survey.to_dict(),
        }
        if persist:
            result['stored'] = GanttReleaseSurveyStore().save_survey(
                survey,
                summary_markdown=survey.summary_markdown,
            )
        return _json_result(result)
    except Exception as e:
        log.error(f'create_release_survey failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def get_gantt_release_survey(
    survey_id: str,
    project_key: Optional[str] = None,
) -> list[Any]:
    """Get a persisted Gantt release-survey report by survey ID."""
    try:
        record = GanttReleaseSurveyStore().get_survey(
            survey_id,
            project_key=project_key,
        )
        if not record:
            return _error_result(f'Gantt release survey {survey_id} not found')
        return _json_result(_release_survey_record_to_dict(record))
    except Exception as e:
        log.error(f'get_gantt_release_survey failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def list_gantt_release_surveys(
    project_key: Optional[str] = None,
    limit: int = 20,
) -> list[Any]:
    """List persisted Gantt release-survey reports."""
    try:
        rows = GanttReleaseSurveyStore().list_surveys(
            project_key=project_key,
            limit=limit,
        )
        return _json_result(rows)
    except Exception as e:
        log.error(f'list_gantt_release_surveys failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Drucker hygiene tools
# ---------------------------------------------------------------------------

@_tool_decorator()
async def create_drucker_hygiene_report(
    project_key: str,
    limit: int = 200,
    include_done: bool = False,
    stale_days: int = 30,
    jql: Optional[str] = None,
    label_prefix: str = 'drucker',
    persist: bool = True,
) -> list[Any]:
    """Create a Drucker Jira hygiene report and review session."""
    try:
        agent = DruckerCoordinatorAgent(project_key=project_key)
        request = DruckerRequest(
            project_key=project_key,
            limit=limit,
            include_done=include_done,
            stale_days=stale_days,
            jql=jql,
            label_prefix=label_prefix,
        )
        report = agent.analyze_project_hygiene(request)
        review_session = agent.create_review_session(report)
        result = {
            'report': report.to_dict(),
            'review_session': review_session.to_dict(),
        }
        if persist:
            result['stored'] = DruckerReportStore().save_report(
                report,
                summary_markdown=report.summary_markdown,
            )
        return _json_result(result)
    except Exception as e:
        log.error(f'create_drucker_hygiene_report failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def create_drucker_issue_check(
    project_key: str,
    ticket_key: str,
    stale_days: int = 30,
    label_prefix: str = 'drucker',
    persist: bool = True,
) -> list[Any]:
    """Run a Drucker issue-check for a specific Jira ticket."""
    try:
        agent = DruckerCoordinatorAgent(project_key=project_key)
        request = DruckerRequest(
            project_key=project_key,
            ticket_key=ticket_key,
            stale_days=stale_days,
            label_prefix=label_prefix,
        )
        report = agent.analyze_ticket_hygiene(request)
        review_session = agent.create_review_session(report)
        result = {
            'report': report.to_dict(),
            'review_session': review_session.to_dict(),
        }
        if persist:
            result['stored'] = DruckerReportStore().save_report(
                report,
                summary_markdown=report.summary_markdown,
            )
        return _json_result(result)
    except Exception as e:
        log.error(f'create_drucker_issue_check failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def create_drucker_intake_report(
    project_key: str,
    limit: int = 200,
    stale_days: int = 30,
    since: Optional[str] = None,
    label_prefix: str = 'drucker',
    persist: bool = True,
) -> list[Any]:
    """Run a Drucker recent-ticket intake report."""
    try:
        agent = DruckerCoordinatorAgent(project_key=project_key)
        request = DruckerRequest(
            project_key=project_key,
            limit=limit,
            stale_days=stale_days,
            since=since,
            recent_only=True,
            label_prefix=label_prefix,
        )
        report = agent.analyze_recent_ticket_intake(request)
        review_session = agent.create_review_session(report)
        result = {
            'report': report.to_dict(),
            'review_session': review_session.to_dict(),
        }
        if persist:
            result['stored'] = DruckerReportStore().save_report(
                report,
                summary_markdown=report.summary_markdown,
            )
        return _json_result(result)
    except Exception as e:
        log.error(f'create_drucker_intake_report failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def create_drucker_bug_activity_report(
    project_key: str,
    target_date: Optional[str] = None,
) -> list[Any]:
    """Run a Drucker bug activity report."""
    try:
        agent = DruckerCoordinatorAgent(project_key=project_key)
        result = agent.analyze_bug_activity(
            project_key=project_key,
            target_date=target_date,
        )
        return _json_result(result)
    except Exception as e:
        log.error(f'create_drucker_bug_activity_report failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def get_drucker_report(
    report_id: str,
    project_key: Optional[str] = None,
) -> list[Any]:
    """Get a persisted Drucker hygiene report by report ID."""
    try:
        record = DruckerReportStore().get_report(report_id, project_key=project_key)
        if not record:
            return _error_result(f'Drucker report {report_id} not found')
        return _json_result(record)
    except Exception as e:
        log.error(f'get_drucker_report failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def list_drucker_reports(
    project_key: Optional[str] = None,
    limit: int = 20,
) -> list[Any]:
    """List persisted Drucker hygiene reports."""
    try:
        rows = DruckerReportStore().list_reports(project_key=project_key, limit=limit)
        return _json_result(rows)
    except Exception as e:
        log.error(f'list_drucker_reports failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Hypatia documentation tools
# ---------------------------------------------------------------------------

@_tool_decorator()
async def generate_hypatia_documentation(
    title: str,
    doc_type: str = 'engineering_reference',
    project_key: str = '',
    summary: str = '',
    source_paths: Optional[list[str]] = None,
    source_refs: Optional[list[str]] = None,
    evidence_paths: Optional[list[str]] = None,
    target_file: Optional[str] = None,
    confluence_title: Optional[str] = None,
    confluence_page: Optional[str] = None,
    confluence_space: Optional[str] = None,
    confluence_parent_id: Optional[str] = None,
    version_message: Optional[str] = None,
    validation_profile: str = 'default',
    persist: bool = True,
) -> list[Any]:
    """Generate a Hypatia documentation record and review session."""
    try:
        agent = HypatiaDocumentationAgent(project_key=project_key or None)
        request = DocumentationRequest(
            title=title,
            doc_type=doc_type,
            project_key=project_key,
            summary=summary,
            source_paths=list(source_paths or []),
            source_refs=list(source_refs or []),
            evidence_paths=list(evidence_paths or []),
            target_file=target_file,
            confluence_title=confluence_title,
            confluence_page=confluence_page,
            confluence_space=confluence_space,
            confluence_parent_id=confluence_parent_id,
            version_message=version_message,
            validation_profile=validation_profile,
        )
        record, review_session = agent.plan_documentation(request)
        result = {
            'record': record.to_dict(),
            'review_session': review_session.to_dict(),
        }
        if persist:
            result['stored'] = HypatiaRecordStore().save_record(
                record,
                summary_markdown=record.summary_markdown,
            )
        return _json_result(result)
    except Exception as e:
        log.error(f'generate_hypatia_documentation failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def get_hypatia_record(doc_id: str) -> list[Any]:
    """Get a persisted Hypatia documentation record by document ID."""
    try:
        record = HypatiaRecordStore().get_record(doc_id)
        if not record:
            return _error_result(f'Hypatia record {doc_id} not found')
        return _json_result(record)
    except Exception as e:
        log.error(f'get_hypatia_record failed: {e}')
        return _error_result(str(e))


@_tool_decorator()
async def list_hypatia_records(
    doc_type: Optional[str] = None,
    limit: int = 20,
) -> list[Any]:
    """List persisted Hypatia documentation records."""
    try:
        rows = HypatiaRecordStore().list_records(doc_type=doc_type, limit=limit)
        return _json_result(rows)
    except Exception as e:
        log.error(f'list_hypatia_records failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 3: create_ticket — Create a new Jira ticket
# ---------------------------------------------------------------------------

@_tool_decorator()
async def create_ticket(
    project_key: str,
    summary: str,
    issue_type: str,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    priority: Optional[str] = None,
    fix_version: Optional[str] = None,
    labels: Optional[str] = None,
    parent_key: Optional[str] = None,
    dry_run: Optional[bool] = None,
) -> list[Any]:
    """Create a new Jira ticket.

    Args:
        project_key: Jira project key (e.g. 'STL').
        summary: Issue summary / title.
        issue_type: Issue type name (e.g. Task, Bug, Story, Epic).
        description: Optional plain-text description.
        assignee: Optional assignee accountId.
        priority: Optional priority name (e.g. 'High', 'Medium').
        fix_version: Optional fix-version name to set.
        labels: Optional comma-separated label string (e.g. 'backend,urgent').
        parent_key: Optional parent issue key for sub-tasks or child issues.
        dry_run: Preview only — do not create the ticket.
    """
    try:
        labels_list = [l.strip() for l in labels.split(',')] if labels else None
        fix_versions_list = [fix_version] if fix_version else None

        if resolve_dry_run(dry_run):
            return _json_result({
                'dry_run': True,
                'project_key': project_key,
                'summary': summary,
                'issue_type': issue_type,
                'description': description[:200] if description else None,
                'assignee': assignee,
                'priority': priority,
                'fix_version': fix_version,
                'labels': labels_list,
                'parent_key': parent_key,
            })

        jira = jira_utils.get_connection()
        jira_utils.create_ticket(
            jira,
            project_key=project_key,
            summary=summary,
            issue_type=issue_type,
            description=description,
            assignee=assignee,
            fix_versions=fix_versions_list,
            labels=labels_list,
            parent_key=parent_key,
            dry_run=False,
        )

        issues = jira_utils.run_jql_query(
            jira,
            f'project = "{project_key}" AND summary ~ "{summary}" ORDER BY created DESC',
            limit=1,
        )
        if issues:
            result = _issue_to_dict(issues[0])
            result['message'] = 'Ticket created successfully'
            return _json_result(result)
        return _json_result({'message': 'Ticket created successfully (could not retrieve key)'})
    except Exception as e:
        log.error(f'create_ticket failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 4: update_ticket — Update fields on an existing ticket
# ---------------------------------------------------------------------------

@_tool_decorator()
async def update_ticket(
    ticket_key: str,
    summary: Optional[str] = None,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    priority: Optional[str] = None,
    fix_version: Optional[str] = None,
    labels: Optional[str] = None,
    description: Optional[str] = None,
    dry_run: Optional[bool] = None,
) -> list[Any]:
    """Update fields on an existing Jira ticket.

    Only the fields you provide will be changed; others are left untouched.

    Args:
        ticket_key: The Jira issue key (e.g. 'STL-1234').
        summary: New summary text.
        status: New status name to transition to (e.g. 'In Progress').
        assignee: New assignee accountId.
        priority: New priority name (e.g. 'High').
        fix_version: Fix-version name to set (replaces existing).
        labels: Comma-separated labels to set (replaces existing).
        description: New plain-text description.
        dry_run: Preview only — do not apply updates.
    """
    try:
        update_fields: dict[str, Any] = {}
        if summary is not None:
            update_fields['summary'] = summary
        if priority is not None:
            update_fields['priority'] = {'name': priority}
        if assignee is not None:
            update_fields['assignee'] = {'accountId': assignee}
        if fix_version is not None:
            update_fields['fixVersions'] = [{'name': fix_version}]
        if labels is not None:
            update_fields['labels'] = [l.strip() for l in labels.split(',')]
        if description is not None:
            update_fields['description'] = description

        if resolve_dry_run(dry_run):
            return _json_result({
                'dry_run': True,
                'ticket_key': ticket_key,
                'fields_would_update': list(update_fields.keys()),
                'status_would_transition': status,
            })

        jira = jira_utils.get_connection()
        issue = jira.issue(ticket_key)

        if description is not None:
            update_fields['description'] = jira_utils._adf_from_text(description)

        if update_fields:
            issue.update(fields=update_fields)

        if status is not None:
            transitions = jira.transitions(issue)
            target = None
            for t in transitions:
                if t['name'].lower() == status.lower():
                    target = t
                    break
                # Also match by destination status name
                to_status = t.get('to', {}).get('name', '')
                if to_status.lower() == status.lower():
                    target = t
                    break
            if target:
                jira.transition_issue(issue, target['id'])
            else:
                available = [t['name'] for t in transitions]
                return _error_result(
                    f'Cannot transition to "{status}". '
                    f'Available transitions: {available}'
                )

        # Fetch the updated issue to return current state
        issues = jira_utils.run_jql_query(jira, f'key = "{ticket_key}"', limit=1)
        result = _issue_to_dict(issues[0]) if issues else {'key': ticket_key}
        result['message'] = 'Ticket updated successfully'
        return _json_result(result)
    except Exception as e:
        log.error(f'update_ticket failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 5: list_filters — List Jira saved filters
# ---------------------------------------------------------------------------

@_tool_decorator()
async def list_filters(favourite_only: bool = False) -> list[Any]:
    """List accessible Jira saved filters.

    Args:
        favourite_only: If true, return only the user's starred/favourite filters.
    """
    try:
        jira = jira_utils.get_connection()
        # list_filters prints to stdout (suppressed) but doesn't return data.
        # We need to call the REST API directly to get structured data.
        email, api_token = jira_utils.get_jira_credentials()

        if favourite_only:
            import requests
            response = requests.get(
                f'{jira_utils.JIRA_URL}/rest/api/3/filter/favourite',
                auth=(email, api_token),
                headers={'Accept': 'application/json'},
            )
        else:
            import requests
            response = requests.get(
                f'{jira_utils.JIRA_URL}/rest/api/3/filter/search',
                auth=(email, api_token),
                headers={'Accept': 'application/json'},
                params={'maxResults': 100, 'expand': 'description,jql,owner'},
            )

        if response.status_code != 200:
            return _error_result(f'Jira API error: {response.status_code} - {response.text}')

        data = response.json()
        filters_raw = data if isinstance(data, list) else data.get('values', [])

        result = []
        for f in filters_raw:
            result.append({
                'id': f.get('id'),
                'name': f.get('name', ''),
                'owner': (f.get('owner') or {}).get('displayName', 'Unknown'),
                'jql': f.get('jql', ''),
                'description': f.get('description', ''),
                'favourite': f.get('favourite', False),
            })
        return _json_result(result)
    except Exception as e:
        log.error(f'list_filters failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 6: run_filter — Run a saved Jira filter by ID
# ---------------------------------------------------------------------------

@_tool_decorator()
async def run_filter(filter_id: str, limit: int = 50) -> list[Any]:
    """Run a saved Jira filter by its ID and return matching tickets.

    Args:
        filter_id: The numeric filter ID (e.g. '12345').
        limit: Maximum number of tickets to return (default: 50).
    """
    try:
        jira = jira_utils.get_connection()
        # Fetch the filter's JQL first
        email, api_token = jira_utils.get_jira_credentials()
        import requests
        response = requests.get(
            f'{jira_utils.JIRA_URL}/rest/api/3/filter/{filter_id}',
            auth=(email, api_token),
            headers={'Accept': 'application/json'},
        )
        if response.status_code == 404:
            return _error_result(f'Filter {filter_id} not found')
        if response.status_code != 200:
            return _error_result(f'Jira API error: {response.status_code} - {response.text}')

        filter_data = response.json()
        jql = filter_data.get('jql', '')
        if not jql:
            return _error_result(f'Filter {filter_id} has no JQL query')

        # Execute the JQL
        issues = jira_utils.run_jql_query(jira, jql, limit=limit)
        result = {
            'filter_id': filter_id,
            'filter_name': filter_data.get('name', ''),
            'jql': jql,
            'tickets': [_issue_to_dict(issue) for issue in (issues or [])],
        }
        return _json_result(result)
    except Exception as e:
        log.error(f'run_filter failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 7: get_releases — Get project releases/versions
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_releases(project_key: str, pattern: Optional[str] = None) -> list[Any]:
    """Get releases (versions) for a Jira project.

    Args:
        project_key: Jira project key (e.g. 'STL').
        pattern: Optional glob pattern to filter releases (e.g. '12.*').
    """
    try:
        jira = jira_utils.get_connection()
        jira_utils.validate_project(jira, project_key)
        versions = jira.project_versions(project_key)

        # Apply pattern filtering if provided
        if pattern:
            filtered = []
            for v in versions:
                if jira_utils.match_pattern_with_exclusions(v.name, pattern):
                    filtered.append(v)
            versions = filtered

        result = []
        for v in versions:
            result.append({
                'name': v.name,
                'id': v.id,
                'released': getattr(v, 'released', False),
                'archived': getattr(v, 'archived', False),
                'release_date': getattr(v, 'releaseDate', None) or '',
                'description': getattr(v, 'description', '') or '',
            })
        return _json_result(result)
    except Exception as e:
        log.error(f'get_releases failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 8: get_release_tickets — Get tickets for a specific release
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_release_tickets(
    project_key: str,
    release_name: str,
    limit: int = 50,
) -> list[Any]:
    """Get tickets associated with a specific release/version.

    Args:
        project_key: Jira project key (e.g. 'STL').
        release_name: Release/version name (case-insensitive) or glob pattern (e.g. '12.1*').
        limit: Maximum number of tickets to return (default: 50).
    """
    try:
        jira = jira_utils.get_connection()
        # Build JQL for the release
        jql = f'project = "{project_key}" AND fixVersion = "{release_name}" ORDER BY key ASC'
        issues = jira_utils.run_jql_query(jira, jql, limit=limit)
        result = {
            'project': project_key,
            'release': release_name,
            'tickets': [_issue_to_dict(issue) for issue in (issues or [])],
        }
        return _json_result(result)
    except Exception as e:
        log.error(f'get_release_tickets failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 9: get_children — Get child ticket hierarchy
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_children(root_key: str, limit: int = 50) -> list[Any]:
    """Get the child ticket hierarchy for a given Jira issue.

    Recursively retrieves all child issues (sub-tasks, stories under epics, etc.).

    Args:
        root_key: The parent issue key to start from (e.g. 'STL-100').
        limit: Maximum number of tickets to return including the root (default: 50).
    """
    try:
        jira = jira_utils.get_connection()
        # Use the internal _get_children_data for structured data
        ordered = jira_utils._get_children_data(jira, root_key, limit=limit)
        result = []
        for item in ordered:
            entry = _issue_to_dict(item['issue'])
            entry['depth'] = item.get('depth', 0)
            result.append(entry)
        return _json_result(result)
    except Exception as e:
        log.error(f'get_children failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 10: get_related — Get related tickets via link traversal
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_related(root_key: str, depth: Optional[int] = None, limit: int = 50) -> list[Any]:
    """Get related tickets for a given issue via link and child traversal.

    Related includes linked issues (issuelinks) and children discovered
    via JQL ``parent = "<key>"``.

    Args:
        root_key: The issue key to start from (e.g. 'STL-100').
        depth: Traversal depth (None for direct-only, -1 for unlimited).
        limit: Maximum number of tickets to return including the root (default: 50).
    """
    try:
        jira = jira_utils.get_connection()
        # Use the internal _get_related_data for structured data
        ordered = jira_utils._get_related_data(jira, root_key, hierarchy=depth, limit=limit)
        result = []
        for item in ordered:
            entry = _issue_to_dict(item['issue'])
            entry['depth'] = item.get('depth', 0)
            entry['via'] = item.get('via', '')
            entry['relation'] = item.get('relation', '')
            entry['from_key'] = item.get('from_key', '')
            result.append(entry)
        return _json_result(result)
    except Exception as e:
        log.error(f'get_related failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 11: get_project_info — Get project metadata
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_project_info(project_key: str) -> list[Any]:
    """Get metadata for a Jira project (name, lead, description, issue types, etc.).

    Args:
        project_key: Jira project key (e.g. 'STL').
    """
    try:
        jira = jira_utils.get_connection()
        project = jira_utils.validate_project(jira, project_key)

        result = {
            'key': project.key,
            'name': project.name,
            'lead': getattr(project, 'lead', {}).get('displayName', 'Unknown')
                    if isinstance(getattr(project, 'lead', None), dict)
                    else str(getattr(project, 'lead', 'Unknown')),
            'description': getattr(project, 'description', '') or '',
            'project_type': getattr(project, 'projectTypeKey', ''),
        }

        # Fetch issue types for this project
        try:
            meta = jira.createmeta(
                projectKeys=project_key,
                expand='projects.issuetypes',
            )
            projects = meta.get('projects', [])
            if projects:
                issue_types = [it.get('name', '') for it in projects[0].get('issuetypes', [])]
                result['issue_types'] = issue_types
        except Exception:
            # createmeta may not be available; skip gracefully
            pass

        return _json_result(result)
    except Exception as e:
        log.error(f'get_project_info failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 12: get_components — Get project components
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_components(project_key: str) -> list[Any]:
    """Get the components defined for a Jira project.

    Args:
        project_key: Jira project key (e.g. 'STL').
    """
    try:
        jira = jira_utils.get_connection()
        jira_utils.validate_project(jira, project_key)
        components = jira.project_components(project_key)

        result = []
        for c in components:
            result.append({
                'name': c.name,
                'id': c.id,
                'lead': getattr(c, 'lead', {}).get('displayName', '')
                        if isinstance(getattr(c, 'lead', None), dict)
                        else str(getattr(c, 'lead', '')),
                'description': getattr(c, 'description', '') or '',
            })
        return _json_result(result)
    except Exception as e:
        log.error(f'get_components failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 13: assign_ticket — Assign a ticket to a user
# ---------------------------------------------------------------------------

@_tool_decorator()
async def assign_ticket(ticket_key: str, assignee: str, dry_run: Optional[bool] = None) -> list[Any]:
    """Assign a Jira ticket to a user.

    Args:
        ticket_key: The Jira issue key (e.g. 'STL-1234').
        assignee: The accountId, display name, email, or username of the user
                  to assign, or 'unassigned' to clear.  Human-readable values
                  are automatically resolved to accountIds via UserResolver.
        dry_run: Preview only — do not change the assignee.
    """
    try:
        if resolve_dry_run(dry_run):
            return _json_result({
                'dry_run': True,
                'ticket_key': ticket_key,
                'assignee': assignee,
            })
        jira = jira_utils.get_connection()
        issue = jira.issue(ticket_key)

        if assignee.lower() == 'unassigned':
            issue.update(fields={'assignee': None})
        else:
            # Resolve human-readable assignee to accountId if needed
            resolver = jira_utils.get_user_resolver()
            # Extract project key from the ticket key (e.g. "STL" from "STL-1234")
            project_key = ticket_key.split('-')[0] if '-' in ticket_key else ''
            resolved_id = resolver.resolve(assignee, project_key=project_key)
            if resolved_id:
                issue.update(fields={'assignee': {'accountId': resolved_id}})
            else:
                return _error_result(
                    f'Could not resolve assignee "{assignee}" to a Jira accountId'
                )

        return _json_result({
            'key': ticket_key,
            'assignee': assignee,
            'message': f'Ticket {ticket_key} assigned to {assignee}',
        })
    except Exception as e:
        log.error(f'assign_ticket failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 14: link_tickets — Link two Jira tickets
# ---------------------------------------------------------------------------

@_tool_decorator()
async def link_tickets(from_key: str, to_key: str, link_type: str = 'Relates', dry_run: Optional[bool] = None) -> list[Any]:
    """Create a link between two Jira tickets.

    Args:
        from_key: Source issue key (e.g. 'STL-100').
        to_key: Target issue key (e.g. 'STL-200').
        link_type: Link type name (e.g. 'Relates', 'Blocks', 'is blocked by',
                   'Cloners', 'Duplicate'). Default: 'Relates'.
        dry_run: Preview only — do not create the link.
    """
    try:
        if resolve_dry_run(dry_run):
            return _json_result({
                'dry_run': True,
                'from_key': from_key,
                'to_key': to_key,
                'link_type': link_type,
            })
        jira = jira_utils.get_connection()
        jira.create_issue_link(
            type=link_type,
            inwardIssue=from_key,
            outwardIssue=to_key,
        )
        return _json_result({
            'from_key': from_key,
            'to_key': to_key,
            'link_type': link_type,
            'message': f'Linked {from_key} → {to_key} ({link_type})',
        })
    except Exception as e:
        log.error(f'link_tickets failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 15: list_dashboards — List Jira dashboards
# ---------------------------------------------------------------------------

@_tool_decorator()
async def list_dashboards() -> list[Any]:
    """List accessible Jira dashboards."""
    try:
        jira = jira_utils.get_connection()
        email, api_token = jira_utils.get_jira_credentials()

        import requests
        all_dashboards = []
        start_at = 0

        while True:
            response = requests.get(
                f'{jira_utils.JIRA_URL}/rest/api/3/dashboard/search',
                auth=(email, api_token),
                headers={'Accept': 'application/json'},
                params={'maxResults': 100, 'startAt': start_at},
            )
            if response.status_code != 200:
                return _error_result(f'Jira API error: {response.status_code} - {response.text}')

            data = response.json()
            dashboards = data.get('values', [])
            all_dashboards.extend(dashboards)

            # Check for more pages
            if data.get('startAt', 0) + len(dashboards) >= data.get('total', 0):
                break
            start_at += len(dashboards)

        result = []
        for d in all_dashboards:
            owner = d.get('owner', {})
            result.append({
                'id': d.get('id'),
                'name': d.get('name', ''),
                'owner': owner.get('displayName', 'Unknown') if isinstance(owner, dict) else str(owner),
                'view_url': d.get('view', ''),
            })
        return _json_result(result)
    except Exception as e:
        log.error(f'list_dashboards failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 16: get_tickets_created_on — Tickets created on a specific date
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_tickets_created_on(project_key: str, date: str = '') -> list[Any]:
    """Get all tickets created on a specific date.

    Args:
        project_key: Jira project key (e.g. 'STL').
        date: Target date YYYY-MM-DD (defaults to today if empty).
    """
    try:
        from datetime import date as _date
        from core.reporting import tickets_created_on

        jira = jira_utils.get_connection()
        target_date = date or _date.today().isoformat()
        tickets = tickets_created_on(jira, project_key, target_date)
        return _json_result({
            'date': target_date,
            'project': project_key,
            'count': len(tickets),
            'tickets': tickets,
        })
    except Exception as e:
        log.error(f'get_tickets_created_on failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 17: find_bugs_missing_field — Bugs missing a required field
# ---------------------------------------------------------------------------

@_tool_decorator()
async def find_bugs_missing_field(
    project_key: str,
    field: str = 'affectedVersion',
    date: str = '',
) -> list[Any]:
    """Find bugs missing a required field (e.g. affectedVersion, fixVersion).

    Args:
        project_key: Jira project key (e.g. 'STL').
        field: JQL field name to check (default: affectedVersion).
        date: If given, only flag bugs created on this date (YYYY-MM-DD).
    """
    try:
        from core.reporting import bugs_missing_field

        jira = jira_utils.get_connection()
        target_date = date or None
        result = bugs_missing_field(jira, project_key, field=field,
                                    target_date=target_date)
        return _json_result(result)
    except Exception as e:
        log.error(f'find_bugs_missing_field failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 18: get_status_changes — Status transitions by actor type
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_status_changes(project_key: str, date: str = '') -> list[Any]:
    """Get status transitions for a date, split by automation vs human.

    Args:
        project_key: Jira project key (e.g. 'STL').
        date: Target date YYYY-MM-DD (defaults to today if empty).
    """
    try:
        from datetime import date as _date
        from core.reporting import status_changes_by_actor

        target_date = date or _date.today().isoformat()
        result = status_changes_by_actor(project_key, target_date)
        return _json_result(result)
    except Exception as e:
        log.error(f'get_status_changes failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 19: daily_report — Full composite daily report
# ---------------------------------------------------------------------------

@_tool_decorator()
async def daily_report(
    project_key: str,
    date: str = '',
    export_path: str = '',
    export_format: str = 'excel',
) -> list[Any]:
    """Run a full daily report: created tickets, missing fields, status changes.

    Args:
        project_key: Jira project key (e.g. 'STL').
        date: Target date YYYY-MM-DD (defaults to today if empty).
        export_path: If provided, export report to this file path.
        export_format: Export format: 'excel' or 'csv' (default: excel).
    """
    try:
        from datetime import date as _date
        from core.reporting import daily_report as _daily_report
        from core.reporting import export_daily_report

        jira = jira_utils.get_connection()
        target_date = date or _date.today().isoformat()
        report = _daily_report(jira, project_key, target_date)

        response: dict[str, Any] = {
            'date': target_date,
            'project': project_key,
            'created_count': len(report.get('created_tickets', [])),
            'flagged_bugs_count': len(report.get('bugs_missing_field', {}).get('flagged', [])),
            'automation_changes': len(report.get('status_changes', {}).get('automation', [])),
            'human_changes': len(report.get('status_changes', {}).get('human', [])),
            'report': report,
        }

        if export_path:
            path = export_daily_report(report, export_path, fmt=export_format)
            response['export_path'] = path

        return _json_result(response)
    except Exception as e:
        log.error(f'daily_report failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 20: list_automations — List Jira automation rules
# ---------------------------------------------------------------------------

@_tool_decorator()
async def list_automations(project_key: str = '', state: str = '') -> list[Any]:
    """List Jira automation rules, optionally filtered by project or state.

    Args:
        project_key: Optional project key to filter rules.
        state: Optional state filter: 'ENABLED' or 'DISABLED'.
    """
    try:
        jira = jira_utils.get_connection()
        email, api_token = jira_utils.get_jira_credentials()
        base_url = jira_utils._get_automation_base_url()

        import requests
        all_rules = []
        offset = 0

        while True:
            params = {'limit': 100, 'offset': offset}
            if state:
                params['ruleState'] = state

            response = requests.get(
                f'{base_url}/rule/summary',
                auth=(email, api_token),
                headers={'Accept': 'application/json'},
                params=params,
            )
            if response.status_code != 200:
                return _error_result(f'Automation API error: {response.status_code} - {response.text}')

            data = response.json()
            rules = data.get('results', [])
            all_rules.extend(rules)

            total = data.get('total', len(all_rules))
            if offset + len(rules) >= total or len(rules) == 0:
                break
            offset += len(rules)

        result = []
        for r in all_rules:
            if project_key:
                projects = r.get('projects', [])
                project_keys = [p.get('projectKey', '') for p in projects]
                if project_key not in project_keys:
                    continue
            result.append({
                'id': r.get('id'),
                'name': r.get('name', ''),
                'state': r.get('state', ''),
                'enabled': r.get('enabled', False),
            })
        return _json_result(result)
    except Exception as e:
        log.error(f'list_automations failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 21: get_automation — Get full Jira automation rule config
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_automation(rule_uuid: str) -> list[Any]:
    """Get the full configuration of a Jira automation rule.

    Args:
        rule_uuid: UUID of the automation rule to retrieve.
    """
    try:
        jira = jira_utils.get_connection()
        email, api_token = jira_utils.get_jira_credentials()
        base_url = jira_utils._get_automation_base_url()

        import requests
        response = requests.get(
            f'{base_url}/rule/{rule_uuid}',
            auth=(email, api_token),
            headers={'Accept': 'application/json'},
        )
        if response.status_code == 404:
            return _error_result(f'Automation rule not found: {rule_uuid}')
        if response.status_code != 200:
            return _error_result(f'Automation API error: {response.status_code} - {response.text}')

        rule = response.json()
        return _json_result(rule)
    except Exception as e:
        log.error(f'get_automation failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 22: create_automation — Create a Jira automation rule from JSON
# ---------------------------------------------------------------------------

@_tool_decorator()
async def create_automation(rule_json: str, project_key: str = '', dry_run: Optional[bool] = None) -> list[Any]:
    """Create a new Jira automation rule from a JSON payload.

    Args:
        rule_json: JSON string defining the automation rule configuration.
        project_key: Optional project key to scope the rule to.
        dry_run: Preview only — do not create the rule.
    """
    try:
        import json as _json
        payload = _json.loads(rule_json)
    except Exception as e:
        return _error_result(f'Invalid JSON payload: {e}')

    try:
        if resolve_dry_run(dry_run):
            return _json_result({
                'dry_run': True,
                'rule_name': payload.get('name', ''),
                'project_key': project_key,
                'payload_keys': list(payload.keys()),
            })

        jira = jira_utils.get_connection()
        email, api_token = jira_utils.get_jira_credentials()
        base_url = jira_utils._get_automation_base_url()

        import requests
        response = requests.post(
            f'{base_url}/rule',
            auth=(email, api_token),
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            json=payload,
        )
        if response.status_code not in (200, 201):
            return _error_result(f'Automation API error: {response.status_code} - {response.text}')

        created = response.json()
        return _json_result(created)
    except Exception as e:
        log.error(f'create_automation failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 23: enable_automation — Enable a Jira automation rule
# ---------------------------------------------------------------------------

@_tool_decorator()
async def enable_automation(rule_uuid: str, dry_run: Optional[bool] = None) -> list[Any]:
    """Enable a Jira automation rule.

    Args:
        rule_uuid: UUID of the automation rule to enable.
        dry_run: Preview only — do not change the rule state.
    """
    try:
        if resolve_dry_run(dry_run):
            return _json_result({
                'dry_run': True,
                'rule_uuid': rule_uuid,
                'target_state': 'ENABLED',
            })
        jira = jira_utils.get_connection()
        email, api_token = jira_utils.get_jira_credentials()
        base_url = jira_utils._get_automation_base_url()

        import requests
        response = requests.put(
            f'{base_url}/rule/{rule_uuid}/state',
            auth=(email, api_token),
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            json={'ruleState': 'ENABLED'},
        )
        if response.status_code == 404:
            return _error_result(f'Automation rule not found: {rule_uuid}')
        if response.status_code not in (200, 204):
            return _error_result(f'Automation API error: {response.status_code} - {response.text}')

        return _json_result({'rule_uuid': rule_uuid, 'state': 'ENABLED'})
    except Exception as e:
        log.error(f'enable_automation failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 24: disable_automation — Disable a Jira automation rule
# ---------------------------------------------------------------------------

@_tool_decorator()
async def disable_automation(rule_uuid: str, dry_run: Optional[bool] = None) -> list[Any]:
    """Disable a Jira automation rule.

    Args:
        rule_uuid: UUID of the automation rule to disable.
        dry_run: Preview only — do not change the rule state.
    """
    try:
        if resolve_dry_run(dry_run):
            return _json_result({
                'dry_run': True,
                'rule_uuid': rule_uuid,
                'target_state': 'DISABLED',
            })
        jira = jira_utils.get_connection()
        email, api_token = jira_utils.get_jira_credentials()
        base_url = jira_utils._get_automation_base_url()

        import requests
        response = requests.put(
            f'{base_url}/rule/{rule_uuid}/state',
            auth=(email, api_token),
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            json={'ruleState': 'DISABLED'},
        )
        if response.status_code == 404:
            return _error_result(f'Automation rule not found: {rule_uuid}')
        if response.status_code not in (200, 204):
            return _error_result(f'Automation API error: {response.status_code} - {response.text}')

        return _json_result({'rule_uuid': rule_uuid, 'state': 'DISABLED'})
    except Exception as e:
        log.error(f'disable_automation failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 25: delete_automation — Delete a Jira automation rule
# ---------------------------------------------------------------------------

@_tool_decorator()
async def delete_automation(rule_uuid: str, dry_run: Optional[bool] = None) -> list[Any]:
    """Delete a Jira automation rule.

    Args:
        rule_uuid: UUID of the automation rule to delete.
        dry_run: Preview only — do not delete the rule.
    """
    try:
        if resolve_dry_run(dry_run):
            return _json_result({
                'dry_run': True,
                'rule_uuid': rule_uuid,
                'action': 'DELETE',
            })
        jira = jira_utils.get_connection()
        email, api_token = jira_utils.get_jira_credentials()
        base_url = jira_utils._get_automation_base_url()

        import requests
        response = requests.delete(
            f'{base_url}/rule/{rule_uuid}',
            auth=(email, api_token),
            headers={'Accept': 'application/json'},
        )
        if response.status_code == 404:
            return _error_result(f'Automation rule not found: {rule_uuid}')
        if response.status_code not in (200, 204):
            return _error_result(f'Automation API error: {response.status_code} - {response.text}')

        return _json_result({'rule_uuid': rule_uuid, 'deleted': True})
    except Exception as e:
        log.error(f'delete_automation failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 26: list_github_repos — List GitHub repositories
# ---------------------------------------------------------------------------

@_tool_decorator()
async def list_github_repos(org: Optional[str] = None, limit: int = 50) -> list[Any]:
    '''List GitHub repositories, optionally filtered by organization.

    Args:
        org: GitHub organization name (optional; lists authenticated user repos if omitted).
        limit: Maximum number of repos to return (default: 50).
    '''
    try:
        github_utils.get_connection()
        repos = github_utils.list_repos(org=org, limit=limit)
        return _json_result(repos)
    except Exception as e:
        log.error(f'list_github_repos failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 27: get_github_repo — Get detailed info for a GitHub repository
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_github_repo(repo_full_name: str) -> list[Any]:
    '''Get detailed information for a GitHub repository.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
    '''
    try:
        github_utils.get_connection()
        info = github_utils.get_repo_info(repo_full_name)
        return _json_result(info)
    except Exception as e:
        log.error(f'get_github_repo failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 28: validate_github_repo — Validate a GitHub repository exists
# ---------------------------------------------------------------------------

@_tool_decorator()
async def validate_github_repo(repo_full_name: str) -> list[Any]:
    '''Validate that a GitHub repository exists and is accessible.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
    '''
    try:
        github_utils.get_connection()
        result = github_utils.validate_repo(repo_full_name)
        return _json_result(result)
    except Exception as e:
        log.error(f'validate_github_repo failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 29: list_github_pull_requests — List PRs for a repository
# ---------------------------------------------------------------------------

@_tool_decorator()
async def list_github_pull_requests(repo_full_name: str, state: str = 'open', sort: str = 'created', direction: str = 'desc', limit: int = 50) -> list[Any]:
    '''List pull requests for a GitHub repository.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        state: PR state filter — 'open', 'closed', or 'all' (default: 'open').
        sort: Sort field — 'created', 'updated', or 'popularity' (default: 'created').
        direction: Sort direction — 'asc' or 'desc' (default: 'desc').
        limit: Maximum number of PRs to return (default: 50).
    '''
    try:
        github_utils.get_connection()
        prs = github_utils.list_pull_requests(repo_full_name, state=state, sort=sort, direction=direction, limit=limit)
        return _json_result(prs)
    except Exception as e:
        log.error(f'list_github_pull_requests failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 30: get_github_pull_request — Get details for a single PR
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_github_pull_request(repo_full_name: str, pr_number: int) -> list[Any]:
    '''Get detailed information for a single GitHub pull request.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        pr_number: Pull request number.
    '''
    try:
        github_utils.get_connection()
        pr = github_utils.get_pull_request(repo_full_name, pr_number)
        return _json_result(pr)
    except Exception as e:
        log.error(f'get_github_pull_request failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 31: get_github_pr_reviews — Get reviews for a PR
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_github_pr_reviews(repo_full_name: str, pr_number: int) -> list[Any]:
    '''Get reviews for a GitHub pull request.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        pr_number: Pull request number.
    '''
    try:
        github_utils.get_connection()
        reviews = github_utils.get_pr_reviews(repo_full_name, pr_number)
        return _json_result(reviews)
    except Exception as e:
        log.error(f'get_github_pr_reviews failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 32: get_github_pr_review_requests — Get pending review requests
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_github_pr_review_requests(repo_full_name: str, pr_number: int) -> list[Any]:
    '''Get pending review requests for a GitHub pull request.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        pr_number: Pull request number.
    '''
    try:
        github_utils.get_connection()
        requests = github_utils.get_pr_review_requests(repo_full_name, pr_number)
        return _json_result(requests)
    except Exception as e:
        log.error(f'get_github_pr_review_requests failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 33: find_stale_github_prs — Find stale pull requests
# ---------------------------------------------------------------------------

@_tool_decorator()
async def find_stale_github_prs(repo_full_name: str, stale_days: int = 5) -> list[Any]:
    '''Find stale pull requests in a GitHub repository.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        stale_days: Number of days without activity to consider a PR stale (default: 5).
    '''
    try:
        github_utils.get_connection()
        stale = github_utils.analyze_pr_staleness(repo_full_name, stale_days=stale_days)
        return _json_result(stale)
    except Exception as e:
        log.error(f'find_stale_github_prs failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 34: find_github_prs_missing_reviews — Find PRs missing reviews
# ---------------------------------------------------------------------------

@_tool_decorator()
async def find_github_prs_missing_reviews(repo_full_name: str) -> list[Any]:
    '''Find pull requests missing reviews in a GitHub repository.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
    '''
    try:
        github_utils.get_connection()
        missing = github_utils.analyze_missing_reviews(repo_full_name)
        return _json_result(missing)
    except Exception as e:
        log.error(f'find_github_prs_missing_reviews failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 35: analyze_github_pr_hygiene — Full PR hygiene analysis
# ---------------------------------------------------------------------------

@_tool_decorator()
async def analyze_github_pr_hygiene(repo_full_name: str, stale_days: int = 5) -> list[Any]:
    '''Run a full PR hygiene analysis on a GitHub repository.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        stale_days: Number of days without activity to consider a PR stale (default: 5).
    '''
    try:
        github_utils.get_connection()
        hygiene = github_utils.analyze_repo_pr_hygiene(repo_full_name, stale_days=stale_days)
        return _json_result(hygiene)
    except Exception as e:
        log.error(f'analyze_github_pr_hygiene failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 36: get_github_rate_limit — Check GitHub API rate limit status
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_github_rate_limit() -> list[Any]:
    '''Check the current GitHub API rate limit status.

    Args:
        (none)
    '''
    try:
        rate = github_utils.get_rate_limit()
        return _json_result(rate)
    except Exception as e:
        log.error(f'get_github_rate_limit failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 37: check_naming_compliance — Check branch/PR naming conventions
# ---------------------------------------------------------------------------

@_tool_decorator()
async def check_naming_compliance(repo_full_name: str, ticket_patterns: str = '') -> list[Any]:
    '''Check branch and PR title naming compliance against Jira ticket conventions.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/ifs-all').
        ticket_patterns: Comma-separated regex patterns (default: STL/STLSW pattern).
    '''
    try:
        github_utils.get_connection()
        patterns = [p.strip() for p in ticket_patterns.split(',') if p.strip()] if ticket_patterns else None
        result = github_utils.analyze_naming_compliance(repo_full_name, ticket_patterns=patterns)
        return _json_result(result)
    except Exception as e:
        log.error(f'check_naming_compliance failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 38: check_merge_conflicts — Find PRs with merge conflicts
# ---------------------------------------------------------------------------

@_tool_decorator()
async def check_merge_conflicts(repo_full_name: str) -> list[Any]:
    '''Find open pull requests with merge conflicts.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/ifs-all').
    '''
    try:
        github_utils.get_connection()
        result = github_utils.analyze_merge_conflicts(repo_full_name)
        return _json_result(result)
    except Exception as e:
        log.error(f'check_merge_conflicts failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 39: check_ci_failures — Find PRs with failing CI checks
# ---------------------------------------------------------------------------

@_tool_decorator()
async def check_ci_failures(repo_full_name: str) -> list[Any]:
    '''Find open pull requests with failing CI checks.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/ifs-all').
    '''
    try:
        github_utils.get_connection()
        result = github_utils.analyze_ci_failures(repo_full_name)
        return _json_result(result)
    except Exception as e:
        log.error(f'check_ci_failures failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 40: check_stale_branches — Find stale branches
# ---------------------------------------------------------------------------

@_tool_decorator()
async def check_stale_branches(repo_full_name: str, stale_days: int = 30) -> list[Any]:
    '''Find stale branches with no recent activity and no open PRs.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/ifs-all').
        stale_days: Number of days without activity to consider a branch stale (default: 30).
    '''
    try:
        github_utils.get_connection()
        result = github_utils.analyze_stale_branches(repo_full_name, stale_days=stale_days)
        return _json_result(result)
    except Exception as e:
        log.error(f'check_stale_branches failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 41: analyze_extended_hygiene — Comprehensive extended hygiene scan
# ---------------------------------------------------------------------------

@_tool_decorator()
async def analyze_extended_hygiene(repo_full_name: str, stale_days: int = 5, branch_stale_days: int = 30) -> list[Any]:
    '''Run comprehensive extended hygiene analysis including all scan types.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/ifs-all').
        stale_days: Number of days without activity to consider a PR stale (default: 5).
        branch_stale_days: Number of days without activity to consider a branch stale (default: 30).
    '''
    try:
        github_utils.get_connection()
        result = github_utils.analyze_extended_hygiene(
            repo_full_name, stale_days=stale_days, branch_stale_days=branch_stale_days,
        )
        return _json_result(result)
    except Exception as e:
        log.error(f'analyze_extended_hygiene failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 42: get_github_repo_readme — Get README for a GitHub repository
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_github_repo_readme(repo_name: str) -> list[Any]:
    '''Get the README content for a GitHub repository.

    Args:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
    '''
    try:
        github_utils.get_connection()
        result = github_utils.get_repo_readme(repo_name)
        return _json_result(result)
    except Exception as e:
        log.error(f'get_github_repo_readme failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 43: list_github_repo_docs — List documentation files in a repository
# ---------------------------------------------------------------------------

@_tool_decorator()
async def list_github_repo_docs(repo_name: str, path: str = 'docs', extensions: Optional[str] = None) -> list[Any]:
    '''List documentation files in a GitHub repository directory.

    Args:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        path: Directory path to search (default: 'docs').
        extensions: Comma-separated file extensions to include (default: '.md,.rst,.txt').
    '''
    try:
        github_utils.get_connection()
        ext_list = [e.strip() for e in extensions.split(',') if e.strip()] if extensions else None
        result = github_utils.list_repo_docs(repo_name, path=path, extensions=ext_list)
        return _json_result(result)
    except Exception as e:
        log.error(f'list_github_repo_docs failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 44: search_github_repo_docs — Search documentation files in a repository
# ---------------------------------------------------------------------------

@_tool_decorator()
async def search_github_repo_docs(repo_name: str, query: str, extensions: Optional[str] = None) -> list[Any]:
    '''Search documentation files in a GitHub repository by content query.

    Args:
        repo_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        query: Search query string to match in file contents.
        extensions: Comma-separated file extensions to search (default: '.md,.rst,.txt').
    '''
    try:
        github_utils.get_connection()
        ext_list = [e.strip() for e in extensions.split(',') if e.strip()] if extensions else None
        result = github_utils.search_repo_docs(repo_name, query, extensions=ext_list)
        return _json_result(result)
    except Exception as e:
        log.error(f'search_github_repo_docs failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 45: get_github_pr_changed_files — Get files changed in a PR
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_github_pr_changed_files(repo_full_name: str, pr_number: int) -> list[Any]:
    '''Get the list of files changed in a GitHub pull request.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        pr_number: Pull request number.
    '''
    try:
        github_utils.get_connection()
        files = github_utils.get_pr_changed_files(repo_full_name, pr_number)
        return _json_result(files)
    except Exception as e:
        log.error(f'get_github_pr_changed_files failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 46: get_github_file_content — Get file content from a repository
# ---------------------------------------------------------------------------

@_tool_decorator()
async def get_github_file_content(repo_full_name: str, path: str, branch: str = 'main') -> list[Any]:
    '''Get the content of a file from a GitHub repository.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        path: File path within the repository.
        branch: Branch name (default: 'main').
    '''
    try:
        github_utils.get_connection()
        result = github_utils.get_file_content(repo_full_name, path, branch=branch)
        if result is None:
            return _json_result({'found': False, 'path': path, 'branch': branch})
        result['found'] = True
        return _json_result(result)
    except Exception as e:
        log.error(f'get_github_file_content failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 47: create_or_update_github_file — Create or update a file (mutation)
# ---------------------------------------------------------------------------

@_tool_decorator()
async def create_or_update_github_file(
    repo_full_name: str,
    path: str,
    content: str,
    message: str,
    branch: str = 'main',
    dry_run: bool = True,
) -> list[Any]:
    '''Create or update a single file in a GitHub repository.

    MUTATION — dry-run by default.  Pass dry_run=false to execute.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        path: File path within the repository.
        content: File content as a string.
        message: Commit message.
        branch: Target branch (default: 'main').
        dry_run: Preview only — do not commit (default: true).
    '''
    try:
        github_utils.get_connection()
        if resolve_dry_run(dry_run):
            existing = github_utils.get_file_content(repo_full_name, path, branch=branch)
            operation = 'update' if existing else 'create'
            return _json_result({
                'dry_run': True,
                'repo': repo_full_name,
                'path': path,
                'branch': branch,
                'operation': operation,
                'content_length': len(content),
            })
        result = github_utils.create_or_update_file(
            repo_full_name, path, content, message, branch=branch, dry_run=False,
        )
        return _json_result(result)
    except Exception as e:
        log.error(f'create_or_update_github_file failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 48: batch_commit_github_files — Atomic multi-file commit (mutation)
# ---------------------------------------------------------------------------

@_tool_decorator()
async def batch_commit_github_files(
    repo_full_name: str,
    files: str,
    message: str,
    branch: str = 'main',
    dry_run: bool = True,
) -> list[Any]:
    '''Atomically commit multiple files to a GitHub repository via the Git Tree API.

    MUTATION — dry-run by default.  Pass dry_run=false to execute.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        files: JSON array of objects with 'path' and 'content' keys.
        message: Commit message.
        branch: Target branch (default: 'main').
        dry_run: Preview only — do not commit (default: true).
    '''
    import json as _json
    try:
        github_utils.get_connection()
        file_list = _json.loads(files) if isinstance(files, str) else files
        if resolve_dry_run(dry_run):
            return _json_result({
                'dry_run': True,
                'repo': repo_full_name,
                'branch': branch,
                'file_count': len(file_list),
                'files': [{'path': f['path'], 'content_length': len(f['content'])} for f in file_list],
            })
        result = github_utils.batch_commit_files(
            repo_full_name, file_list, message, branch=branch, dry_run=False,
        )
        return _json_result(result)
    except Exception as e:
        log.error(f'batch_commit_github_files failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Tool 49: post_github_pr_comment — Post a comment on a PR (mutation)
# ---------------------------------------------------------------------------

@_tool_decorator()
async def post_github_pr_comment(
    repo_full_name: str,
    pr_number: int,
    body: str,
    dry_run: bool = True,
) -> list[Any]:
    '''Post a comment on a GitHub pull request.

    MUTATION — dry-run by default.  Pass dry_run=false to execute.

    Args:
        repo_full_name: Full repository name (e.g. 'cornelisnetworks/opa-psm2').
        pr_number: Pull request number.
        body: Comment body text.
        dry_run: Preview only — do not post the comment (default: true).
    '''
    try:
        github_utils.get_connection()
        if resolve_dry_run(dry_run):
            return _json_result({
                'dry_run': True,
                'repo': repo_full_name,
                'pr_number': pr_number,
                'body_length': len(body),
                'body_preview': body[:200],
            })
        result = github_utils.post_pr_comment(
            repo_full_name, pr_number, body, dry_run=False,
        )
        return _json_result(result)
    except Exception as e:
        log.error(f'post_github_pr_comment failed: {e}')
        return _error_result(str(e))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Run the Cornelis Jira MCP server over stdio."""
    log.info('Starting Cornelis Jira MCP server...')

    jira_url = os.environ.get('JIRA_URL', '')
    jira_email = (
        get_jira_actor_email('service_account')
        or get_jira_actor_email('requester')
        or os.environ.get('JIRA_EMAIL', '')
    )
    if not jira_url or not jira_email:
        log.warning('JIRA_URL or JIRA_EMAIL not set — tools will fail until configured')
    else:
        log.info(f'Jira URL: {jira_url}')
        log.info(f'Jira user: {jira_email}')

    if hasattr(server, 'tool'):
        dynamic_server = cast(Any, server)
        dynamic_server.run(transport='stdio')
        return

    import asyncio

    async def _run_lowlevel() -> None:
        lowlevel_server = cast(Any, server)
        async with stdio_server() as (read_stream, write_stream):
            await lowlevel_server.run(read_stream, write_stream, lowlevel_server.create_initialization_options())

    asyncio.run(_run_lowlevel())


def run():
    """Synchronous entry point for console_scripts (pyproject.toml)."""
    main()


if __name__ == '__main__':
    run()
