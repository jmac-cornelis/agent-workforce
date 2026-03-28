##########################################################################
# Module:      test_dry_run_jira_tools_char.py
# Description: Characterization tests verifying dry-run (default) behavior
#              for all 13 mutation functions in tools/jira_tools.py.
#              Each test asserts that the function returns a ToolResult.success()
#              with a preview dict containing 'dry_run': True and that NO
#              actual Jira mutation occurs.
# Author:      Cornelis Networks — AI Engineering Tools
##########################################################################

from unittest.mock import MagicMock

import pytest

from tools.jira_tools import JiraTools


# -----------------------------------------------------------------------
# 1. transition_ticket
# -----------------------------------------------------------------------
def test_transition_ticket_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    issue = MagicMock()
    issue.fields.status = MagicMock()
    issue.fields.status.__str__ = lambda self: 'Open'
    jira.issue.return_value = issue
    jira.transitions.return_value = [
        {'id': '11', 'name': 'In Progress', 'to': {'name': 'In Progress'}, 'fields': {}}
    ]

    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    result = jira_tools.transition_ticket('KEY-1', 'In Progress')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['ticket_key'] == 'KEY-1'
    assert result.data['current_status'] == 'Open'
    assert result.data['target_status'] == 'In Progress'
    jira.transition_issue.assert_not_called()
    jira.add_comment.assert_not_called()


# -----------------------------------------------------------------------
# 2. add_ticket_comment
# -----------------------------------------------------------------------
def test_add_ticket_comment_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    result = jira_tools.add_ticket_comment('KEY-1', 'Hello')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['ticket_key'] == 'KEY-1'
    assert result.data['comment_body_length'] == 5
    jira.add_comment.assert_not_called()


# -----------------------------------------------------------------------
# 3. create_ticket
# -----------------------------------------------------------------------
def test_create_ticket_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    result = jira_tools.create_ticket('STL', 'Test summary', 'Bug')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['project_key'] == 'STL'
    assert result.data['summary'] == 'Test summary'
    assert result.data['issue_type'] == 'Bug'
    jira.create_issue.assert_not_called()


# -----------------------------------------------------------------------
# 4. update_ticket
# -----------------------------------------------------------------------
def test_update_ticket_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    issue = MagicMock()
    issue.fields.summary = 'Old summary'
    jira.issue.return_value = issue

    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    result = jira_tools.update_ticket('KEY-1', summary='New')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['ticket_key'] == 'KEY-1'
    assert result.data['current_summary'] == 'Old summary'
    assert 'summary' in result.data['fields_would_update']
    issue.update.assert_not_called()


# -----------------------------------------------------------------------
# 5. create_release
# -----------------------------------------------------------------------
def test_create_release_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    result = jira_tools.create_release('STL', 'Release 1.0')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['project_key'] == 'STL'
    assert result.data['name'] == 'Release 1.0'
    jira.create_version.assert_not_called()


# -----------------------------------------------------------------------
# 6. link_tickets
# -----------------------------------------------------------------------
def test_link_tickets_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    result = jira_tools.link_tickets('KEY-1', 'KEY-2', 'Blocks')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['from'] == 'KEY-1'
    assert result.data['to'] == 'KEY-2'
    assert result.data['type'] == 'Blocks'
    jira.create_issue_link.assert_not_called()


# -----------------------------------------------------------------------
# 7. assign_ticket
# -----------------------------------------------------------------------
def test_assign_ticket_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    result = jira_tools.assign_ticket('KEY-1', 'user-1')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['ticket'] == 'KEY-1'
    assert result.data['assignee'] == 'user-1'
    jira.assign_issue.assert_not_called()


# -----------------------------------------------------------------------
# 8. create_dashboard
# -----------------------------------------------------------------------
def test_create_dashboard_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    result = jira_tools.create_dashboard('My Dashboard')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['name'] == 'My Dashboard'


# -----------------------------------------------------------------------
# 9. create_automation
# -----------------------------------------------------------------------
def test_create_automation_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    rule_json = '{"name": "test", "when": {"component": "TRIGGER"}}'
    result = jira_tools.create_automation(rule_json, project_key='STL')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['rule_name'] == 'test'
    assert result.data['project_key'] == 'STL'


# -----------------------------------------------------------------------
# 10. enable_automation
# -----------------------------------------------------------------------
def test_enable_automation_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    result = jira_tools.enable_automation('uuid-123')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['rule_uuid'] == 'uuid-123'
    assert result.data['target_state'] == 'ENABLED'


# -----------------------------------------------------------------------
# 11. disable_automation
# -----------------------------------------------------------------------
def test_disable_automation_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    result = jira_tools.disable_automation('uuid-123')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['rule_uuid'] == 'uuid-123'
    assert result.data['target_state'] == 'DISABLED'


# -----------------------------------------------------------------------
# 12. delete_automation
# -----------------------------------------------------------------------
def test_delete_automation_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools

    jira = MagicMock()
    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    result = jira_tools.delete_automation('uuid-123')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['rule_uuid'] == 'uuid-123'
    assert result.data['action'] == 'DELETE'


# -----------------------------------------------------------------------
# 13. bulk_update_tickets
# -----------------------------------------------------------------------
def test_bulk_update_tickets_dry_run_returns_preview(monkeypatch: pytest.MonkeyPatch):
    from tools import jira_tools
    import os

    jira = MagicMock()
    monkeypatch.setattr(jira_tools, 'get_jira', lambda: jira)

    monkeypatch.setattr(os.path, 'isfile', lambda path: True)

    _ju_mock = MagicMock()
    monkeypatch.setattr(jira_tools, '_ju_bulk_update_tickets', _ju_mock)

    result = jira_tools.bulk_update_tickets('input.xlsx')

    assert result.is_success
    assert result.data['dry_run'] is True
    assert result.data['status'] == 'preview'
    assert result.data['input_file'] == 'input.xlsx'
