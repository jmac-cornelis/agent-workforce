##########################################################################
# Module:      test_jira_identity_char.py
# Description: Characterization tests for Jira credential profile resolution.
# Author:      Cornelis Networks — AI Engineering Tools
##########################################################################

import pytest

from config.jira_identity import get_jira_credential_profile


def test_jira_identity_uses_legacy_fallback_by_default(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv('JIRA_EMAIL', 'legacy@cornelisnetworks.com')
    monkeypatch.setenv('JIRA_API_TOKEN', 'legacy-token')
    monkeypatch.delenv('JIRA_REQUESTER_EMAIL', raising=False)
    monkeypatch.delenv('JIRA_REQUESTER_API_TOKEN', raising=False)
    monkeypatch.delenv('JIRA_ENABLE_LEGACY_FALLBACK', raising=False)

    profile = get_jira_credential_profile('requester')

    assert profile.email == 'legacy@cornelisnetworks.com'
    assert profile.api_token == 'legacy-token'
    assert profile.source == 'JIRA_EMAIL/JIRA_API_TOKEN'


def test_jira_identity_can_disable_legacy_fallback_for_requester(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv('JIRA_EMAIL', 'legacy@cornelisnetworks.com')
    monkeypatch.setenv('JIRA_API_TOKEN', 'legacy-token')
    monkeypatch.delenv('JIRA_REQUESTER_EMAIL', raising=False)
    monkeypatch.delenv('JIRA_REQUESTER_API_TOKEN', raising=False)
    monkeypatch.setenv('JIRA_ENABLE_LEGACY_FALLBACK', 'false')

    profile = get_jira_credential_profile('requester')

    assert profile.email is None
    assert profile.api_token is None
    assert profile.email_env == 'JIRA_REQUESTER_EMAIL'
    assert profile.token_env == 'JIRA_REQUESTER_API_TOKEN'
    assert 'legacy fallback disabled' in profile.source


def test_jira_identity_service_account_still_uses_explicit_service_credentials(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv('JIRA_ENABLE_LEGACY_FALLBACK', 'false')
    monkeypatch.setenv('JIRA_SERVICE_EMAIL', 'scm@cornelisnetworks.com')
    monkeypatch.setenv('JIRA_SERVICE_API_TOKEN', 'svc-token')

    profile = get_jira_credential_profile('service_account')

    assert profile.email == 'scm@cornelisnetworks.com'
    assert profile.api_token == 'svc-token'
    assert profile.source == 'JIRA_SERVICE_EMAIL/JIRA_SERVICE_API_TOKEN'
