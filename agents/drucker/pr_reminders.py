##########################################################################################
#
# Module: agents/drucker/pr_reminders.py
#
# Description: Core PR reminder engine. Orchestrates repo scanning, reminder
#              scheduling, Teams user resolution, DM delivery via Graph API,
#              and snooze / merge action handling.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

import github_utils
from agents.drucker.cards import (
    build_merge_confirmation_card,
    build_merge_dry_run_card,
    build_pr_reminder_card,
    build_snooze_confirmation_card,
)
from agents.drucker.state.pr_reminder_state import PRReminderState
from agents.shannon.graph_client import TeamsGraphClient

log = logging.getLogger(os.path.basename(sys.argv[0]))


# ---------------------------------------------------------------------------
# Project root resolution — walk up from this file until we find config/
# ---------------------------------------------------------------------------

def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / 'config' / 'identity_map.yaml').is_file():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent.parent


class PRReminderEngine:
    '''Orchestrates PR reminder scanning, scheduling, delivery, and actions.'''

    def __init__(
        self,
        config_path: Optional[str] = None,
        identity_map_path: Optional[str] = None,
        state_db_path: Optional[str] = None,
    ) -> None:
        # -- Load PR reminders config ----------------------------------------
        if config_path is None:
            config_path = str(
                Path(__file__).resolve().parent / 'config' / 'pr_reminders.yaml'
            )
        with open(config_path, 'r') as fh:
            self._config: Dict[str, Any] = yaml.safe_load(fh) or {}

        # -- Load identity map -----------------------------------------------
        if identity_map_path is None:
            identity_map_path = str(
                _find_project_root() / 'config' / 'identity_map.yaml'
            )
        with open(identity_map_path, 'r') as fh:
            self._identity_map: Dict[str, Any] = yaml.safe_load(fh) or {}

        # -- State store -----------------------------------------------------
        self._state = PRReminderState(
            db_path=state_db_path or 'data/drucker_pr_reminder_state.db'
        )

        # -- Graph client (reads env vars automatically) ---------------------
        self._graph = TeamsGraphClient()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _parse_iso(iso_str: str) -> datetime:
        '''Parse an ISO-8601 datetime string to a timezone-aware datetime.'''
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def _days_open(created_at_iso: str) -> int:
        '''Compute how many days a PR has been open.'''
        created = datetime.fromisoformat(created_at_iso)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - created
        return max(0, delta.days)

    def _get_config_for_repo(self, repo: str) -> Dict[str, Any]:
        '''Return merged config (defaults + repo-specific overrides) for a repo.

        Repo entries in the config may override reminder_days, notify,
        snooze_options_days, merge_methods, or enabled.  Any key not
        overridden falls back to the top-level defaults section.
        '''
        defaults = dict(self._config.get('defaults', {}))

        # Search for a repo-specific entry
        for entry in self._config.get('repos', []):
            if entry.get('repo') == repo:
                # Merge: repo-specific keys override defaults
                merged = dict(defaults)
                for key, value in entry.items():
                    if key != 'repo':
                        merged[key] = value
                return merged

        return defaults

    def _run_async(self, coro: Any) -> Any:
        '''Bridge async Graph API calls into sync context.

        Tries to use the running event loop if available (e.g. inside an
        async framework), otherwise falls back to asyncio.run().
        '''
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We are inside an already-running loop (e.g. FastAPI).
            # Create a new loop in a thread to avoid deadlock.
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=30)
        else:
            return asyncio.run(coro)

    # ------------------------------------------------------------------
    # 1. scan_repos
    # ------------------------------------------------------------------

    def scan_repos(self) -> Dict[str, Any]:
        '''Scan all configured repos for open PRs, upsert into state, schedule reminders.

        Returns:
            {repos_scanned: int, prs_tracked: int, new_prs: int}
        '''
        repos_config = self._config.get('repos', [])
        repos_scanned = 0
        prs_tracked = 0
        new_prs = 0

        for entry in repos_config:
            repo_name = entry.get('repo')
            if not repo_name:
                continue

            repo_cfg = self._get_config_for_repo(repo_name)
            if not repo_cfg.get('enabled', True):
                log.info(f'Skipping disabled repo: {repo_name}')
                continue

            repos_scanned += 1

            try:
                open_prs = github_utils.list_pull_requests(
                    repo_name, state='open', limit=100
                )
            except Exception as exc:
                log.error(f'Failed to list PRs for {repo_name}: {exc}')
                continue

            for pr in open_prs:
                prs_tracked += 1

                # Upsert into state store
                reviewers_str = ','.join(pr.get('requested_reviewers', []))
                row = self._state.upsert_pr(
                    repo=repo_name,
                    pr_number=pr['number'],
                    pr_title=pr.get('title', ''),
                    pr_url=pr.get('html_url', ''),
                    author_github=pr.get('author', ''),
                    reviewers_github=reviewers_str,
                    created_at=pr.get('created_at', ''),
                )

                # For new PRs (never reminded): schedule first reminder
                if row.get('first_reminded_at') is None and row.get('next_reminder_at') is None:
                    new_prs += 1
                    next_at = self.compute_next_reminder(
                        repo=repo_name,
                        pr_number=pr['number'],
                        pr_created_at=pr.get('created_at', ''),
                        current_reminder_count=0,
                    )
                    if next_at:
                        self._state.schedule_next_reminder(
                            repo=repo_name,
                            pr_number=pr['number'],
                            next_at=next_at,
                        )

        log.info(
            f'scan_repos complete: repos={repos_scanned}, '
            f'prs_tracked={prs_tracked}, new_prs={new_prs}'
        )
        return {
            'repos_scanned': repos_scanned,
            'prs_tracked': prs_tracked,
            'new_prs': new_prs,
        }

    # ------------------------------------------------------------------
    # 2. compute_next_reminder
    # ------------------------------------------------------------------

    def compute_next_reminder(
        self,
        repo: str,
        pr_number: int,
        pr_created_at: str,
        current_reminder_count: int,
    ) -> Optional[str]:
        '''Compute the next reminder datetime for a PR.

        Uses the repo-specific or default reminder_days schedule.
        If current_reminder_count exceeds the schedule length, the last
        interval is repeated indefinitely.

        Returns:
            ISO datetime string, or None if reminders are disabled.
        '''
        repo_cfg = self._get_config_for_repo(repo)
        reminder_days: List[int] = repo_cfg.get('reminder_days', [])

        if not reminder_days:
            return None

        if current_reminder_count < len(reminder_days):
            # Use the scheduled day offset from PR creation
            days_offset = reminder_days[current_reminder_count]
        else:
            # Past the schedule: repeat the last interval from now
            last_interval = reminder_days[-1]
            if len(reminder_days) >= 2:
                last_interval = reminder_days[-1] - reminder_days[-2]
            # Schedule relative to now, not creation
            next_dt = self._utc_now() + timedelta(days=last_interval)
            return next_dt.isoformat()

        # Schedule relative to PR creation date
        try:
            created_dt = self._parse_iso(pr_created_at)
        except (ValueError, TypeError):
            log.warning(
                f'Invalid created_at for {repo}#{pr_number}: {pr_created_at}'
            )
            return None

        next_dt = created_dt + timedelta(days=days_offset)

        # If the computed time is already in the past, schedule for now
        if next_dt <= self._utc_now():
            next_dt = self._utc_now() + timedelta(minutes=1)

        return next_dt.isoformat()

    # ------------------------------------------------------------------
    # 3. get_due_reminders
    # ------------------------------------------------------------------

    def get_due_reminders(self) -> List[Dict[str, Any]]:
        '''Return all PRs due for a reminder, including freshly unsnoozed ones.'''
        # Reactivate any expired snoozes first
        unsnoozed = self._state.unsnooze_expired()
        if unsnoozed:
            log.info(f'Unsnoozed {unsnoozed} PRs whose snooze window expired')

        due = self._state.get_due_reminders()
        log.info(f'Found {len(due)} PRs due for reminders')
        return due

    # ------------------------------------------------------------------
    # 4. resolve_teams_user
    # ------------------------------------------------------------------

    def resolve_teams_user(self, github_username: str) -> Optional[Dict[str, str]]:
        '''Look up a GitHub username in the identity map.

        Returns:
            {'name': ..., 'teams_email': ...} or None if not found.
        '''
        users = self._identity_map.get('users', {})
        entry = users.get(github_username)

        if entry is None:
            log.warning(
                f'GitHub user "{github_username}" not found in identity map'
            )
            return None

        return {
            'name': entry.get('name', github_username),
            'teams_email': entry.get('teams_email', ''),
        }

    # ------------------------------------------------------------------
    # 5. send_reminder_dm
    # ------------------------------------------------------------------

    def send_reminder_dm(
        self,
        pr_data: Dict[str, Any],
        target_github_user: str,
    ) -> Dict[str, Any]:
        '''Send a PR reminder DM to one user via Teams.

        Args:
            pr_data: State row dict for the PR (from state store).
            target_github_user: GitHub login of the target user.

        Returns:
            {ok: bool, target: str, chat_id: str, error: str or None}
        '''
        repo = pr_data.get('repo', '')
        pr_number = pr_data.get('pr_number', 0)

        # -- Resolve Teams identity ------------------------------------------
        teams_user = self.resolve_teams_user(target_github_user)
        if not teams_user or not teams_user.get('teams_email'):
            return {
                'ok': False,
                'target': target_github_user,
                'chat_id': '',
                'error': f'No Teams email for GitHub user: {target_github_user}',
            }

        email = teams_user['teams_email']

        # -- Build the card --------------------------------------------------
        repo_cfg = self._get_config_for_repo(repo)
        days_open = self._days_open(pr_data.get('created_at', ''))

        card_data = {
            'repo': repo,
            'pr_number': pr_number,
            'pr_title': pr_data.get('pr_title', ''),
            'pr_url': pr_data.get('pr_url', ''),
            'author_github': pr_data.get('author_github', ''),
            'reviewers_github': pr_data.get('reviewers_github', ''),
            'created_at': pr_data.get('created_at', ''),
            'reminder_count': pr_data.get('reminder_count', 0) + 1,
            'days_open': days_open,
        }

        card = build_pr_reminder_card(
            pr_data=card_data,
            snooze_options_days=repo_cfg.get('snooze_options_days', [2, 5, 7]),
            merge_methods=repo_cfg.get('merge_methods', ['squash', 'merge', 'rebase']),
        )

        # -- Deliver via Graph API -------------------------------------------
        try:
            async def _deliver() -> Dict[str, Any]:
                user_info = await self._graph.resolve_user_by_email(email)
                user_id = user_info['id']
                chat = await self._graph.create_one_on_one_chat(user_id)
                chat_id = chat['id']
                await self._graph.send_chat_adaptive_card(
                    chat_id=chat_id,
                    card=card,
                    summary=f'PR Reminder: {repo}#{pr_number}',
                )
                return {'chat_id': chat_id}

            result = self._run_async(_deliver())
            chat_id = result['chat_id']

        except Exception as exc:
            log.error(
                f'Failed to send DM for {repo}#{pr_number} to {email}: {exc}'
            )
            return {
                'ok': False,
                'target': target_github_user,
                'chat_id': '',
                'error': str(exc),
            }

        # -- Record in state store -------------------------------------------
        self._state.record_reminder(
            repo=repo,
            pr_number=pr_number,
            target_user=target_github_user,
        )

        # -- Schedule next reminder ------------------------------------------
        updated_row = self._state.get_pr(repo, pr_number)
        current_count = updated_row.get('reminder_count', 1) if updated_row else 1
        next_at = self.compute_next_reminder(
            repo=repo,
            pr_number=pr_number,
            pr_created_at=pr_data.get('created_at', ''),
            current_reminder_count=current_count,
        )
        if next_at:
            self._state.schedule_next_reminder(
                repo=repo,
                pr_number=pr_number,
                next_at=next_at,
            )

        log.info(
            f'Sent PR reminder DM for {repo}#{pr_number} to '
            f'{target_github_user} ({email}), chat_id={chat_id}'
        )
        return {
            'ok': True,
            'target': target_github_user,
            'chat_id': chat_id,
            'error': None,
        }

    # ------------------------------------------------------------------
    # 6. process_due_reminders
    # ------------------------------------------------------------------

    def process_due_reminders(self) -> Dict[str, Any]:
        '''Main entry point for the poller. Scan repos, send due reminders.

        Returns:
            {reminders_sent: int, errors: list, prs_processed: int}
        '''
        # Refresh PR state from GitHub
        self.scan_repos()

        # Collect due reminders
        due = self.get_due_reminders()

        reminders_sent = 0
        errors: List[str] = []
        prs_processed = 0

        for pr_data in due:
            prs_processed += 1
            repo = pr_data.get('repo', '')
            pr_number = pr_data.get('pr_number', 0)
            repo_cfg = self._get_config_for_repo(repo)
            notify_targets = repo_cfg.get('notify', ['author', 'reviewers'])

            # Determine who to notify
            targets: List[str] = []
            if 'author' in notify_targets:
                author = pr_data.get('author_github', '')
                if author:
                    targets.append(author)

            if 'reviewers' in notify_targets:
                reviewers_str = pr_data.get('reviewers_github', '')
                if reviewers_str:
                    for reviewer in reviewers_str.split(','):
                        reviewer = reviewer.strip()
                        if reviewer and reviewer not in targets:
                            targets.append(reviewer)

            if not targets:
                log.warning(
                    f'No notification targets for {repo}#{pr_number}, skipping'
                )
                continue

            # Send DM to each target
            for target in targets:
                result = self.send_reminder_dm(pr_data, target)
                if result.get('ok'):
                    reminders_sent += 1
                else:
                    errors.append(
                        f'{repo}#{pr_number}->{target}: {result.get("error", "unknown")}'
                    )

        log.info(
            f'process_due_reminders complete: sent={reminders_sent}, '
            f'errors={len(errors)}, prs_processed={prs_processed}'
        )
        return {
            'reminders_sent': reminders_sent,
            'errors': errors,
            'prs_processed': prs_processed,
        }

    # ------------------------------------------------------------------
    # 7. handle_snooze
    # ------------------------------------------------------------------

    def handle_snooze(
        self,
        repo: str,
        pr_number: int,
        snooze_days: int,
        snoozed_by: str,
    ) -> Dict[str, Any]:
        '''Handle a snooze callback from Teams.

        Returns:
            {ok: True, snooze_until: str, card: dict}
        '''
        snooze_until_dt = self._utc_now() + timedelta(days=snooze_days)
        snooze_until = snooze_until_dt.isoformat()

        self._state.snooze_pr(
            repo=repo,
            pr_number=pr_number,
            snooze_until=snooze_until,
            snoozed_by=snoozed_by,
        )

        # Fetch PR title for the confirmation card
        pr_row = self._state.get_pr(repo, pr_number)
        pr_title = pr_row.get('pr_title', '') if pr_row else ''

        card = build_snooze_confirmation_card(
            repo=repo,
            pr_number=pr_number,
            pr_title=pr_title,
            snooze_until=snooze_until,
            snoozed_by=snoozed_by,
        )

        log.info(
            f'Snoozed {repo}#{pr_number} until {snooze_until} by {snoozed_by}'
        )
        return {
            'ok': True,
            'snooze_until': snooze_until,
            'card': card,
        }

    # ------------------------------------------------------------------
    # 8. handle_merge_request
    # ------------------------------------------------------------------

    def handle_merge_request(
        self,
        repo: str,
        pr_number: int,
        merge_method: str,
        requested_by: str,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        '''Handle a merge request from Teams.

        In dry_run mode, returns a preview card with PR status.
        In live mode, attempts the merge and returns a confirmation card.

        Returns:
            {ok: bool, card: dict, error: str or None}
        '''
        # Fetch current PR title from state for card display
        pr_row = self._state.get_pr(repo, pr_number)
        pr_title = pr_row.get('pr_title', '') if pr_row else ''

        if dry_run:
            # -- Dry run: fetch PR status and build preview card --------------
            try:
                pr_detail = github_utils.get_pull_request(repo, pr_number)
            except Exception as exc:
                log.error(f'Failed to get PR detail for {repo}#{pr_number}: {exc}')
                return {
                    'ok': False,
                    'card': {},
                    'error': f'Failed to fetch PR: {exc}',
                }

            checks_summary = {
                'mergeable': pr_detail.get('mergeable', False),
                'ci_status': 'approved' if pr_detail.get('approved') else 'pending',
                'review_status': (
                    f'{pr_detail.get("review_count", 0)} reviews, '
                    f'{"approved" if pr_detail.get("approved") else "not approved"}'
                ),
                'conflicts': not pr_detail.get('mergeable', False),
            }

            card = build_merge_dry_run_card(
                repo=repo,
                pr_number=pr_number,
                pr_title=pr_title or str(pr_detail.get('title', '')),
                merge_method=merge_method,
                checks_summary=checks_summary,
            )

            return {
                'ok': True,
                'card': card,
                'error': None,
            }

        # -- Live merge -------------------------------------------------------
        try:
            gh = github_utils.get_connection()
            gh_repo = gh.get_repo(repo)
            gh_pr = gh_repo.get_pull(pr_number)
            merge_result = gh_pr.merge(merge_method=merge_method)

            # Mark as merged in state
            self._state.mark_closed(repo, pr_number, action='merged')

            card = build_merge_confirmation_card(
                repo=repo,
                pr_number=pr_number,
                pr_title=pr_title,
                merge_method=merge_method,
                merge_result={
                    'ok': True,
                    'sha': getattr(merge_result, 'sha', 'N/A'),
                },
            )

            log.info(
                f'Merged {repo}#{pr_number} via {merge_method} '
                f'by {requested_by}'
            )
            return {
                'ok': True,
                'card': card,
                'error': None,
            }

        except Exception as exc:
            log.error(
                f'Merge failed for {repo}#{pr_number} ({merge_method}): {exc}'
            )

            card = build_merge_confirmation_card(
                repo=repo,
                pr_number=pr_number,
                pr_title=pr_title,
                merge_method=merge_method,
                merge_result={
                    'ok': False,
                    'error': str(exc),
                },
            )

            return {
                'ok': False,
                'card': card,
                'error': str(exc),
            }
