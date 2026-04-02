##########################################################################################
#
# Module: agents/rename_registry.py
#
# Description: Canonical agent rename registry and alias helpers for the local
#              rename transition.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from typing import Dict, Optional


AGENT_RENAMES: Dict[str, Dict[str, str]] = {
    'hypatia': {
        'canonical': 'hemingway',
        'display_name': 'Hemingway',
        'legacy_display_name': 'Hypatia',
    },
    'hedy': {
        'canonical': 'humphrey',
        'display_name': 'Humphrey',
        'legacy_display_name': 'Hedy',
    },
    'brandeis': {
        'canonical': 'blackstone',
        'display_name': 'Blackstone',
        'legacy_display_name': 'Brandeis',
    },
    'babbage': {
        'canonical': 'mercator',
        'display_name': 'Mercator',
        'legacy_display_name': 'Babbage',
    },
    'linnaeus': {
        'canonical': 'bernerslee',
        'display_name': 'Berners-Lee',
        'legacy_display_name': 'Linnaeus',
    },
    'herodotus': {
        'canonical': 'pliny',
        'display_name': 'Pliny',
        'legacy_display_name': 'Herodotus',
    },
    'brooks': {
        'canonical': 'shackleton',
        'display_name': 'Shackleton',
        'legacy_display_name': 'Brooks',
    },
    'ada': {
        'canonical': 'galileo',
        'display_name': 'Galileo',
        'legacy_display_name': 'Ada',
    },
}


CANONICAL_AGENT_NAMES = {
    value['canonical'] for value in AGENT_RENAMES.values()
}


AGENT_ALIASES: Dict[str, str] = {
    **{legacy: data['canonical'] for legacy, data in AGENT_RENAMES.items()},
    **{data['canonical']: data['canonical'] for data in AGENT_RENAMES.values()},
}


def canonical_agent_name(agent_name: Optional[str]) -> Optional[str]:
    '''Resolve an agent slug to its canonical renamed slug.'''
    if not agent_name:
        return agent_name
    return AGENT_ALIASES.get(str(agent_name).strip().casefold(), str(agent_name).strip().casefold())


def is_legacy_agent_name(agent_name: Optional[str]) -> bool:
    '''Return True when *agent_name* is an old pre-rename slug.'''
    if not agent_name:
        return False
    return str(agent_name).strip().casefold() in AGENT_RENAMES


def legacy_agent_name(agent_name: Optional[str]) -> Optional[str]:
    '''Return the legacy slug for a canonical name when one exists.'''
    canonical = canonical_agent_name(agent_name)
    for legacy, data in AGENT_RENAMES.items():
        if data['canonical'] == canonical:
            return legacy
    return None


def agent_display_name(agent_name: Optional[str]) -> Optional[str]:
    '''Return the preferred user-facing display name for an agent slug.'''
    canonical = canonical_agent_name(agent_name)
    for data in AGENT_RENAMES.values():
        if data['canonical'] == canonical:
            return data['display_name']
    if canonical is None:
        return None
    return str(canonical).strip().title()
