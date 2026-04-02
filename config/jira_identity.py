##########################################################################################
#
# Module: config/jira_identity.py
#
# Description: Jira actor identity and credential profile helpers.
#
# Author: Cornelis Networks
#
##########################################################################################

import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

try:
    from config.env_loader import load_env
except ImportError:
    load_env = None

if load_env is not None:
    load_env()
else:
    load_dotenv(override=False)

log = logging.getLogger(os.path.basename(sys.argv[0]))

REQUESTER = 'requester'
SERVICE_ACCOUNT = 'service_account'
DRAFT_ONLY = 'draft_only'

_VALID_ACTOR_MODES = {REQUESTER, SERVICE_ACCOUNT, DRAFT_ONLY}


@dataclass
class JiraCredentialProfile:
    '''
    Resolved Jira credential profile for one actor mode.
    '''
    actor_mode: str
    email: Optional[str]
    api_token: Optional[str]
    email_env: Optional[str]
    token_env: Optional[str]
    source: str


def _env_flag_enabled(name: str, default: bool = True) -> bool:
    '''
    Parse a boolean feature flag from the environment.
    '''
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    normalized = str(raw).strip().lower()
    if normalized in ('1', 'true', 'yes', 'on'):
        return True
    if normalized in ('0', 'false', 'no', 'off'):
        return False
    return default


def is_legacy_fallback_enabled() -> bool:
    '''
    Return True when legacy JIRA_EMAIL/JIRA_API_TOKEN fallback is allowed.
    '''
    return _env_flag_enabled('JIRA_ENABLE_LEGACY_FALLBACK', default=True)


def normalize_actor_mode(actor_mode: Optional[str]) -> str:
    '''
    Normalize an actor mode to a supported value.
    '''
    if not actor_mode:
        return REQUESTER
    normalized = str(actor_mode).strip().lower()
    if normalized not in _VALID_ACTOR_MODES:
        return REQUESTER
    return normalized


def _resolve_profile(
    actor_mode: str,
    explicit_email_key: str,
    explicit_token_key: str,
) -> JiraCredentialProfile:
    '''
    Resolve one actor profile from explicit or legacy Jira env vars.
    '''
    normalized = normalize_actor_mode(actor_mode)
    explicit_email_raw = os.getenv(explicit_email_key)
    explicit_token_raw = os.getenv(explicit_token_key)
    explicit_email = (explicit_email_raw or '').strip() or None
    explicit_token = (explicit_token_raw or '').strip() or None

    if explicit_email is not None or explicit_token is not None:
        source = f'{explicit_email_key}/{explicit_token_key}'
        return JiraCredentialProfile(
            actor_mode=normalized,
            email=explicit_email,
            api_token=explicit_token,
            email_env=explicit_email_key,
            token_env=explicit_token_key,
            source=source,
        )

    if not is_legacy_fallback_enabled():
        return JiraCredentialProfile(
            actor_mode=normalized,
            email=None,
            api_token=None,
            email_env=explicit_email_key,
            token_env=explicit_token_key,
            source=f'{explicit_email_key}/{explicit_token_key} (legacy fallback disabled)',
        )

    return JiraCredentialProfile(
        actor_mode=normalized,
        email=os.getenv('JIRA_EMAIL') or None,
        api_token=os.getenv('JIRA_API_TOKEN') or None,
        email_env='JIRA_EMAIL',
        token_env='JIRA_API_TOKEN',
        source='JIRA_EMAIL/JIRA_API_TOKEN',
    )


def get_jira_credential_profile(actor_mode: Optional[str] = None) -> JiraCredentialProfile:
    '''
    Resolve the Jira credential profile for one actor mode.

    `draft_only` uses requester credentials for preview/read operations.
    '''
    normalized = normalize_actor_mode(actor_mode)

    if normalized == SERVICE_ACCOUNT:
        return _resolve_profile(
            SERVICE_ACCOUNT,
            'JIRA_SERVICE_EMAIL',
            'JIRA_SERVICE_API_TOKEN',
        )

    if normalized == DRAFT_ONLY:
        profile = _resolve_profile(
            REQUESTER,
            'JIRA_REQUESTER_EMAIL',
            'JIRA_REQUESTER_API_TOKEN',
        )
        profile.actor_mode = DRAFT_ONLY
        profile.source = f'{profile.source} (draft preview)'
        return profile

    return _resolve_profile(
        REQUESTER,
        'JIRA_REQUESTER_EMAIL',
        'JIRA_REQUESTER_API_TOKEN',
    )


def has_jira_credentials(actor_mode: Optional[str] = None) -> bool:
    '''
    Return True when a complete Jira credential pair is available.
    '''
    profile = get_jira_credential_profile(actor_mode)
    return bool(profile.email and profile.api_token)


def get_jira_actor_email(actor_mode: Optional[str] = None) -> Optional[str]:
    '''
    Return the Jira email associated with one actor mode.
    '''
    return get_jira_credential_profile(actor_mode).email


def get_jira_credentials_for_actor(actor_mode: Optional[str] = None) -> tuple[str, str]:
    '''
    Return the Jira credential pair for one actor mode.
    '''
    profile = get_jira_credential_profile(actor_mode)
    if not profile.email:
        raise ValueError(
            f'{profile.email_env} environment variable not set for actor '
            f'"{profile.actor_mode}"'
        )
    if not profile.api_token:
        raise ValueError(
            f'{profile.token_env} environment variable not set for actor '
            f'"{profile.actor_mode}"'
        )

    log.debug(
        'Resolved Jira credentials for actor %s from %s (%s)',
        profile.actor_mode,
        profile.source,
        profile.email,
    )
    return profile.email, profile.api_token
