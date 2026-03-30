##########################################################################################
#
# Module:      test_dry_run_jira_utils_char.py
#
# Description: Characterization tests verifying that jira_utils mutation functions
#              (dashboard CRUD + gadget management + automation state) return early
#              without calling Jira APIs when dry_run=True (the default).
#
# Author:      John Macdonald
#
##########################################################################################

import pytest
from unittest.mock import MagicMock

import jira_utils


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _silent_output(monkeypatch):
    '''Suppress all output() calls during dry-run previews.'''
    monkeypatch.setattr(jira_utils, 'output', lambda *a, **kw: None)


# ---------------------------------------------------------------------------
# Dashboard operations (7 tests)
# ---------------------------------------------------------------------------

def test_create_dashboard_dry_run_returns_without_mutation():
    '''create_dashboard with default dry_run=True prints preview and returns None.'''
    jira = MagicMock()
    result = jira_utils.create_dashboard(jira, 'Test Dashboard', description='Test')
    assert result is None
    assert not jira.method_calls


def test_update_dashboard_dry_run_returns_without_mutation():
    '''update_dashboard with default dry_run=True prints preview and returns None.'''
    jira = MagicMock()
    result = jira_utils.update_dashboard(jira, '12345', name='New Name')
    assert result is None
    assert not jira.method_calls


def test_delete_dashboard_dry_run_returns_without_mutation():
    '''delete_dashboard with default dry_run=True prints preview and returns None.'''
    jira = MagicMock()
    result = jira_utils.delete_dashboard(jira, '12345')
    assert result is None
    assert not jira.method_calls


def test_copy_dashboard_dry_run_returns_without_mutation():
    '''copy_dashboard with default dry_run=True prints preview and returns None.'''
    jira = MagicMock()
    result = jira_utils.copy_dashboard(jira, '12345', 'Copy of Dashboard')
    assert result is None
    assert not jira.method_calls


def test_add_gadget_dry_run_returns_without_mutation():
    '''add_gadget with default dry_run=True prints preview and returns None.'''
    jira = MagicMock()
    result = jira_utils.add_gadget(
        jira, '12345', 'com.atlassian.jira.gadgets:filter-results-gadget'
    )
    assert result is None
    assert not jira.method_calls


def test_remove_gadget_dry_run_returns_without_mutation():
    '''remove_gadget with default dry_run=True prints preview and returns None.'''
    jira = MagicMock()
    result = jira_utils.remove_gadget(jira, '12345', '67890')
    assert result is None
    assert not jira.method_calls


def test_update_gadget_dry_run_returns_without_mutation():
    '''update_gadget with default dry_run=True prints preview and returns None.'''
    jira = MagicMock()
    result = jira_utils.update_gadget(jira, '12345', '67890', position='0,1')
    assert result is None
    assert not jira.method_calls


# ---------------------------------------------------------------------------
# Automation state operations (2 tests)
# ---------------------------------------------------------------------------

def test_enable_automation_dry_run_returns_without_mutation():
    '''enable_automation with default dry_run=True prints preview and returns None.'''
    jira = MagicMock()
    result = jira_utils.enable_automation(jira, 'uuid-abc-123')
    assert result is None
    assert not jira.method_calls


def test_disable_automation_dry_run_returns_without_mutation():
    '''disable_automation with default dry_run=True prints preview and returns None.'''
    jira = MagicMock()
    result = jira_utils.disable_automation(jira, 'uuid-abc-123')
    assert result is None
    assert not jira.method_calls
