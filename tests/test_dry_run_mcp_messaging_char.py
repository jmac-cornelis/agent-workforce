##########################################################################################
#
# Module: tests/test_dry_run_mcp_messaging_char.py
#
# Description: Dry-run behavior tests for MCP server mutation tools and
#              messaging/notification functions.  Verifies that the default
#              dry_run=True returns preview dicts without performing actual
#              mutations.
#
# Author: Cornelis Networks
#
##########################################################################################

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _payload(result):
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].type == 'text'
    return json.loads(result[0].text)


# ===========================================================================
# Section 1: MCP Server dry-run tests (8 tests)
# ===========================================================================

# 1. create_ticket — dry-run returns preview without creating anything
@pytest.mark.asyncio
async def test_create_ticket_dry_run(import_mcp_server, monkeypatch):
    # create_ticket dry-run path does not call get_connection at all
    result = await import_mcp_server.create_ticket(
        project_key='STL', summary='Test', issue_type='Bug',
    )
    data = _payload(result)
    assert data['dry_run'] is True
    assert data['project_key'] == 'STL'
    assert data['summary'] == 'Test'
    assert data['issue_type'] == 'Bug'


# 2. update_ticket — dry-run returns field preview without touching Jira
@pytest.mark.asyncio
async def test_update_ticket_dry_run(import_mcp_server, monkeypatch):
    # update_ticket dry-run path does not call get_connection — it builds
    # the update_fields dict locally and returns a preview.
    result = await import_mcp_server.update_ticket(
        ticket_key='STL-1', summary='New',
    )
    data = _payload(result)
    assert data['dry_run'] is True
    assert data['ticket_key'] == 'STL-1'
    assert 'summary' in data['fields_would_update']


# 3. transition_ticket — dry-run returns transition preview
@pytest.mark.asyncio
async def test_transition_ticket_dry_run(import_mcp_server, monkeypatch):
    # transition_ticket dry-run still reads the issue and transitions to
    # validate the target status, so we must mock get_connection.
    jira = MagicMock()
    issue = MagicMock()
    issue.fields.status.name = 'Open'
    # str(issue.fields.status) is used for current_status in the dry-run path
    issue.fields.status.__str__ = lambda self: 'Open'
    jira.issue.return_value = issue
    jira.transitions.return_value = [
        {'id': '11', 'name': 'In Progress', 'to': {'name': 'In Progress'}},
    ]
    monkeypatch.setattr(import_mcp_server.jira_utils, 'get_connection', lambda: jira)

    result = await import_mcp_server.transition_ticket(
        ticket_key='STL-1', to_status='In Progress',
    )
    data = _payload(result)
    assert data['dry_run'] is True
    assert data['ticket_key'] == 'STL-1'
    assert data['target_status'] == 'In Progress'


# 4. add_ticket_comment — dry-run returns comment preview
@pytest.mark.asyncio
async def test_add_ticket_comment_dry_run(import_mcp_server, monkeypatch):
    # add_ticket_comment dry-run does not call get_connection
    result = await import_mcp_server.add_ticket_comment(
        ticket_key='STL-1', body='Hello',
    )
    data = _payload(result)
    assert data['dry_run'] is True
    assert data['ticket_key'] == 'STL-1'
    assert data['comment_body_length'] == len('Hello')


# 5. assign_ticket — dry-run returns assignee preview
@pytest.mark.asyncio
async def test_assign_ticket_dry_run(import_mcp_server, monkeypatch):
    # assign_ticket dry-run does not call get_connection
    result = await import_mcp_server.assign_ticket('STL-1', 'user')
    data = _payload(result)
    assert data['dry_run'] is True
    assert data['ticket_key'] == 'STL-1'
    assert data['assignee'] == 'user'


# 6. link_tickets — dry-run returns link preview
@pytest.mark.asyncio
async def test_link_tickets_dry_run(import_mcp_server, monkeypatch):
    # link_tickets dry-run does not call get_connection
    result = await import_mcp_server.link_tickets(
        'STL-1', 'STL-2', link_type='Blocks',
    )
    data = _payload(result)
    assert data['dry_run'] is True
    assert data['from_key'] == 'STL-1'
    assert data['to_key'] == 'STL-2'
    assert data['link_type'] == 'Blocks'


# 7. create_automation — dry-run returns rule preview
@pytest.mark.asyncio
async def test_create_automation_dry_run(import_mcp_server, monkeypatch):
    rule_json = json.dumps({
        'name': 'test',
        'when': {'component': 'TRIGGER'},
    })
    result = await import_mcp_server.create_automation(rule_json, 'STL')
    data = _payload(result)
    assert data['dry_run'] is True
    assert data['rule_name'] == 'test'
    assert data['project_key'] == 'STL'


# 8. delete_automation — dry-run returns delete preview
@pytest.mark.asyncio
async def test_delete_automation_dry_run(import_mcp_server, monkeypatch):
    result = await import_mcp_server.delete_automation('uuid-123')
    data = _payload(result)
    assert data['dry_run'] is True
    assert data['rule_uuid'] == 'uuid-123'
    assert data['action'] == 'DELETE'


# ===========================================================================
# Section 2: notify_shannon dry-run tests (2 tests)
# ===========================================================================

def test_notify_shannon_dry_run_returns_preview():
    from agents.pm_runtime import notify_shannon

    result = notify_shannon(
        agent_id='drucker',
        title='Test',
        text='Test message',
    )
    assert result['ok'] is True
    assert result['dry_run'] is True
    assert result['payload']['agent_id'] == 'drucker'


def test_notify_shannon_dry_run_includes_body_lines():
    from agents.pm_runtime import notify_shannon

    result = notify_shannon(
        agent_id='gantt',
        title='Snapshot',
        text='Planning update',
        body_lines=['line-1', 'line-2'],
    )
    assert result['dry_run'] is True
    assert result['payload']['body_lines'] == ['line-1', 'line-2']
    assert result['payload']['title'] == 'Snapshot'


def test_notify_shannon_execute_sends_request(monkeypatch):
    from agents.pm_runtime import notify_shannon

    # Verify dry_run=False actually posts
    posted = []

    class FakeResponse:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return {'ok': True}

    monkeypatch.setattr(
        'agents.pm_runtime.requests.post',
        lambda *a, **kw: (posted.append(kw), FakeResponse())[-1],
    )
    result = notify_shannon(
        agent_id='drucker', title='T', text='M', dry_run=False,
    )
    assert result['ok'] is True
    assert 'dry_run' not in result
    assert len(posted) == 1


# ===========================================================================
# Section 3: shannon/poster.py dry-run tests (3 tests)
# ===========================================================================

def _make_conversation_reference(**overrides):
    from shannon.models import ConversationReference
    defaults = {
        'conversation_id': 'conv-1',
        'channel_id': 'chan-1',
        'service_url': 'https://example.com',
    }
    defaults.update(overrides)
    return ConversationReference(**defaults)


def test_memory_poster_dry_run_does_not_store():
    from shannon.poster import MemoryPoster

    poster = MemoryPoster()
    ref = _make_conversation_reference()
    result = poster.reply_to_activity(
        ref, 'act-1', {'type': 'message', 'text': 'hi'},
    )
    # dry_run=True is default
    assert result['dry_run'] is True
    assert result['ok'] is True
    assert poster.sent == []  # Nothing stored


def test_memory_poster_execute_stores():
    from shannon.poster import MemoryPoster

    poster = MemoryPoster()
    ref = _make_conversation_reference()
    result = poster.reply_to_activity(
        ref, 'act-1', {'type': 'message', 'text': 'hi'}, dry_run=False,
    )
    assert 'dry_run' not in result or result.get('dry_run') is not True
    assert len(poster.sent) == 1


def test_workflows_poster_dry_run_does_not_post(monkeypatch):
    from shannon.poster import WorkflowsPoster

    posted = []
    monkeypatch.setattr(
        'shannon.poster.requests.post',
        lambda *a, **kw: posted.append(kw),
    )
    poster = WorkflowsPoster('https://example.com/webhook')
    ref = _make_conversation_reference()
    result = poster.reply_to_activity(
        ref, 'act-1', {'type': 'message'},
    )
    assert result['dry_run'] is True
    assert posted == []


# ===========================================================================
# Section 4: JiraCommentNotifier dry-run tests (2 tests)
# ===========================================================================

def test_jira_comment_notifier_dry_run_returns_preview():
    from notifications.jira_comments import JiraCommentNotifier

    class FakeJira:
        def comments(self, key):
            return []

    notifier = JiraCommentNotifier(FakeJira())
    result = notifier.send('STL-100', 'Test message')
    assert result['dry_run'] is True
    assert result['ticket_key'] == 'STL-100'
    assert result['would_skip'] is False


def test_jira_comment_notifier_dry_run_detects_existing():
    from notifications.jira_comments import JiraCommentNotifier

    class FakeJira:
        def comments(self, key):
            return [SimpleNamespace(body='[Drucker] Metadata review\n\nStuff')]

    notifier = JiraCommentNotifier(FakeJira())
    result = notifier.send('STL-100', 'Another message')
    assert result['dry_run'] is True
    assert result['would_skip'] is True
