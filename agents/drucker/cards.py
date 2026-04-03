##########################################################################################
#
# Module: agents/drucker/cards.py
#
# Description: Adaptive Card builders for Drucker PR reminder DMs. Constructs
#              interactive cards for snooze, merge, and confirmation flows
#              delivered via Teams direct messages.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Schema constant shared by all cards
# ---------------------------------------------------------------------------

_CARD_SCHEMA = 'http://adaptivecards.io/schemas/adaptive-card.json'
_CARD_VERSION = '1.4'


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _card_envelope(body: List[Dict[str, Any]]) -> Dict[str, Any]:
    '''
    Wrap a list of body elements in a standard Adaptive Card envelope.

    Input:
        body -- list of Adaptive Card body elements.

    Output:
        Complete Adaptive Card dict with $schema, type, and version.
    '''
    return {
        '$schema': _CARD_SCHEMA,
        'type': 'AdaptiveCard',
        'version': _CARD_VERSION,
        'body': body,
    }


def _title_block(text: str) -> Dict[str, Any]:
    '''Return a Large / Bolder title TextBlock.'''
    return {
        'type': 'TextBlock',
        'size': 'Large',
        'weight': 'Bolder',
        'text': text,
        'wrap': True,
    }


def _subtitle_block(text: str) -> Dict[str, Any]:
    '''Return a subtle TextBlock suitable for subtitles.'''
    return {
        'type': 'TextBlock',
        'text': text,
        'wrap': True,
        'isSubtle': True,
    }


def _fact_set(facts: List[tuple[str, str]]) -> Dict[str, Any]:
    '''
    Build a FactSet element from a list of (title, value) pairs.

    Input:
        facts -- ordered pairs; entries with empty values are skipped.

    Output:
        FactSet dict.
    '''
    return {
        'type': 'FactSet',
        'facts': [
            {'title': title, 'value': value}
            for title, value in facts
            if value is not None and str(value) != ''
        ],
    }


def _action_open_url(title: str, url: str) -> Dict[str, Any]:
    '''Return an Action.OpenUrl element.'''
    return {
        'type': 'Action.OpenUrl',
        'title': title,
        'url': url,
    }


def _action_submit(title: str, data: Dict[str, Any]) -> Dict[str, Any]:
    '''Return an Action.Submit element.'''
    return {
        'type': 'Action.Submit',
        'title': title,
        'data': data,
    }


def _action_set(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    '''Wrap a list of actions in an ActionSet container.'''
    return {
        'type': 'ActionSet',
        'actions': actions,
    }


# ---------------------------------------------------------------------------
# Public card builders
# ---------------------------------------------------------------------------

def build_pr_reminder_card(
    pr_data: Dict[str, Any],
    snooze_options_days: List[int],
    merge_methods: List[str],
) -> Dict[str, Any]:
    '''
    Build an interactive PR reminder card for DM delivery.

    Input:
        pr_data            -- dict with keys: repo, pr_number, pr_title,
                              pr_url, author_github, reviewers_github,
                              created_at, reminder_count, days_open.
        snooze_options_days -- list of snooze durations in days (e.g. [2, 5, 7]).
        merge_methods       -- list of merge method names (e.g. ['squash', 'merge', 'rebase']).

    Output:
        Adaptive Card dict ready for Teams delivery.
    '''
    repo = pr_data['repo']
    pr_number = pr_data['pr_number']

    # -- body elements -------------------------------------------------------
    body: List[Dict[str, Any]] = [
        _title_block('\U0001f514 PR Reminder'),
        _subtitle_block(repo),
        _fact_set([
            ('PR', f'#{pr_number}'),
            ('Title', pr_data['pr_title']),
            ('Author', pr_data['author_github']),
            ('Reviewers', pr_data['reviewers_github']),
            ('Open', f'{pr_data["days_open"]} days'),
            ('Reminder', f'#{pr_data["reminder_count"]}'),
        ]),
    ]

    # -- snooze / open-url action row ----------------------------------------
    snooze_actions: List[Dict[str, Any]] = [
        _action_open_url('Open PR \u2197', pr_data['pr_url']),
    ]
    for days in snooze_options_days:
        snooze_actions.append(
            _action_submit(
                f'Snooze {days}d',
                {
                    'action': 'snooze',
                    'repo': repo,
                    'pr_number': pr_number,
                    'snooze_days': days,
                },
            )
        )
    body.append(_action_set(snooze_actions))

    # -- merge action row ----------------------------------------------------
    merge_actions: List[Dict[str, Any]] = [
        _action_submit(
            f'Merge ({method})',
            {
                'action': 'merge',
                'repo': repo,
                'pr_number': pr_number,
                'merge_method': method,
            },
        )
        for method in merge_methods
    ]
    body.append(_action_set(merge_actions))

    return _card_envelope(body)


def build_snooze_confirmation_card(
    repo: str,
    pr_number: int,
    pr_title: str,
    snooze_until: str,
    snoozed_by: str,
) -> Dict[str, Any]:
    '''
    Build a confirmation card after a snooze action.

    Input:
        repo         -- repository full name (e.g. 'org/repo').
        pr_number    -- pull request number.
        pr_title     -- pull request title.
        snooze_until -- human-readable date/time when reminders resume.
        snoozed_by   -- display name or handle of the user who snoozed.

    Output:
        Adaptive Card dict.
    '''
    body: List[Dict[str, Any]] = [
        _title_block('\u23f8\ufe0f PR Reminder Snoozed'),
        _subtitle_block(f'#{pr_number} \u2014 {pr_title}'),
        _fact_set([
            ('Snoozed by', snoozed_by),
            ('Resumes', snooze_until),
        ]),
        {
            'type': 'TextBlock',
            'text': 'Reminders will resume after the snooze period.',
            'wrap': True,
            'size': 'Small',
            'isSubtle': True,
        },
    ]

    return _card_envelope(body)


def build_merge_confirmation_card(
    repo: str,
    pr_number: int,
    pr_title: str,
    merge_method: str,
    merge_result: Dict[str, Any],
) -> Dict[str, Any]:
    '''
    Build a confirmation card after a merge action.

    Input:
        repo         -- repository full name.
        pr_number    -- pull request number.
        pr_title     -- pull request title.
        merge_method -- merge strategy used (squash, merge, rebase).
        merge_result -- dict with 'ok' (bool), optional 'sha' (str),
                        optional 'error' (str).

    Output:
        Adaptive Card dict.
    '''
    ok = merge_result.get('ok', False)

    # -- title reflects success or failure -----------------------------------
    title = '\u2705 PR Merged' if ok else '\u274c Merge Failed'

    # -- facts vary by outcome -----------------------------------------------
    facts: List[tuple[str, str]] = [('Method', merge_method)]
    if ok:
        facts.append(('SHA', merge_result.get('sha', 'N/A')))
    else:
        facts.append(('Error', merge_result.get('error', '')))

    body: List[Dict[str, Any]] = [
        _title_block(title),
        _subtitle_block(f'#{pr_number} \u2014 {pr_title}'),
        _fact_set(facts),
    ]

    return _card_envelope(body)


def build_merge_dry_run_card(
    repo: str,
    pr_number: int,
    pr_title: str,
    merge_method: str,
    checks_summary: Dict[str, Any],
) -> Dict[str, Any]:
    '''
    Build a preview card for merge dry-run (mutation safety).

    Input:
        repo           -- repository full name.
        pr_number      -- pull request number.
        pr_title       -- pull request title.
        merge_method   -- intended merge strategy.
        checks_summary -- dict with 'mergeable' (bool), 'ci_status' (str),
                          'review_status' (str), 'conflicts' (bool).

    Output:
        Adaptive Card dict with confirm / cancel actions.
    '''
    body: List[Dict[str, Any]] = [
        _title_block('\U0001f50d Merge Preview'),
        _subtitle_block(f'#{pr_number} \u2014 {pr_title}'),
        _fact_set([
            ('Mergeable', 'Yes' if checks_summary.get('mergeable') else 'No'),
            ('CI Status', checks_summary.get('ci_status', '')),
            ('Review Status', checks_summary.get('review_status', '')),
            ('Conflicts', 'Yes' if checks_summary.get('conflicts') else 'No'),
            ('Method', merge_method),
        ]),
        _action_set([
            _action_submit(
                'Confirm Merge',
                {
                    'action': 'merge_confirm',
                    'repo': repo,
                    'pr_number': pr_number,
                    'merge_method': merge_method,
                },
            ),
            _action_submit(
                'Cancel',
                {
                    'action': 'merge_cancel',
                    'repo': repo,
                    'pr_number': pr_number,
                },
            ),
        ]),
    ]

    return _card_envelope(body)
