##########################################################################
# Module:      test_jira_actor_policy_char.py
# Description: Characterization tests for Jira actor identity resolution.
# Author:      Cornelis Networks — AI Engineering Tools
##########################################################################

import pytest

from core.jira_actor_policy import load_actor_policy, resolve_jira_actor


def test_resolve_jira_actor_approved_batch_uses_service_account(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('JIRA_EMAIL', 'engineer@cornelisnetworks.com')
    monkeypatch.setenv('JIRA_API_TOKEN', 'token-123')
    load_actor_policy(force_reload=True)

    result = resolve_jira_actor(
        action_class='ticket_tree_create',
        trigger='interactive',
        risk='low',
        approval_required=True,
        approved=True,
        requested_by='pm@cornelisnetworks.com',
    )

    assert result.actor_mode == 'service_account'
    assert result.policy_rule == 'approved_system_batch_apply'
    assert result.requested_by == 'pm@cornelisnetworks.com'
    assert result.executed_by == 'engineer@cornelisnetworks.com'


def test_resolve_jira_actor_sensitive_change_without_requester_creds_falls_back(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv('JIRA_EMAIL', raising=False)
    monkeypatch.delenv('JIRA_API_TOKEN', raising=False)
    monkeypatch.delenv('JIRA_REQUESTER_EMAIL', raising=False)
    monkeypatch.delenv('JIRA_REQUESTER_API_TOKEN', raising=False)
    monkeypatch.setenv('JIRA_SERVICE_EMAIL', 'scm@cornelisnetworks.com')
    monkeypatch.setenv('JIRA_SERVICE_API_TOKEN', 'svc-token')
    load_actor_policy(force_reload=True)

    result = resolve_jira_actor(
        action_class='status_transition',
        trigger='interactive',
        risk='sensitive',
        approval_required=True,
        approved=True,
        requested_by='pm@cornelisnetworks.com',
    )

    assert result.actor_mode == 'draft_only'
    assert result.policy_rule.endswith('fallback_no_requester_credentials')
    assert result.executed_by is None


def test_resolve_jira_actor_polling_defaults_requested_by_to_service_account(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv('JIRA_EMAIL', raising=False)
    monkeypatch.delenv('JIRA_API_TOKEN', raising=False)
    monkeypatch.setenv('JIRA_SERVICE_EMAIL', 'scm@cornelisnetworks.com')
    monkeypatch.setenv('JIRA_SERVICE_API_TOKEN', 'svc-token')
    load_actor_policy(force_reload=True)

    result = resolve_jira_actor(
        action_class='metadata_sync',
        trigger='polling',
        risk='low',
        approval_required=False,
        approved=False,
    )

    assert result.actor_mode == 'service_account'
    assert result.policy_rule == 'deterministic_low_risk_write'
    assert result.requested_by == 'scm@cornelisnetworks.com'
    assert result.executed_by == 'scm@cornelisnetworks.com'
