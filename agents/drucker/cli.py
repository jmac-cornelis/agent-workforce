##########################################################################################
#
# Module: agents/drucker/cli.py
#
# Description: Standalone CLI for Drucker Engineering Hygiene agent.
#              Provides direct access to Jira project hygiene scans, single-ticket
#              issue checks, intake reports, bug activity summaries, GitHub PR
#              hygiene analysis, and scheduled polling.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict

# Logging config - follows project convention
log = logging.getLogger(os.path.basename(sys.argv[0]))


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _print_json(data: Dict[str, Any]) -> None:
    '''Print a dict as formatted JSON to stdout.'''
    print(json.dumps(data, indent=2, default=str))


def _write_report_files(
    report: Dict[str, Any],
    summary_markdown: str,
    review_session: Dict[str, Any],
    output_base: str,
):
    '''
    Write Drucker report JSON + Markdown + review-session JSON files.
    Returns (json_path, md_path, review_path).
    '''
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() == '.md':
        output_root = output_root or str(
            report.get('project_key') or 'drucker_report'
        ).lower()
    elif output_ext.lower() != '.json':
        output_root = output_base

    json_path = output_root + '.json'
    md_path = output_root + '.md'
    review_path = output_root + '_review.json'

    os.makedirs(os.path.dirname(json_path) or '.', exist_ok=True)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(summary_markdown or '')

    with open(review_path, 'w', encoding='utf-8') as f:
        json.dump(review_session or {}, f, indent=2, default=str)

    return json_path, md_path, review_path


def _write_activity_files(
    activity: Dict[str, Any],
    summary_markdown: str,
    output_base: str,
):
    '''
    Write Drucker bug-activity JSON + Markdown files.
    Returns (json_path, md_path).
    '''
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() == '.md':
        output_root = output_root or str(
            activity.get('project') or 'drucker_bug_activity'
        ).lower()
    elif output_ext.lower() != '.json':
        output_root = output_base

    json_path = output_root + '.json'
    md_path = output_root + '.md'

    os.makedirs(os.path.dirname(json_path) or '.', exist_ok=True)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(activity, f, indent=2, default=str)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(summary_markdown or '')

    return json_path, md_path


def _write_output_files(data: dict, markdown: str, output_base: str):
    '''
    Write JSON + Markdown files from data and summary markdown.
    Returns (json_path, md_path).
    '''
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() == '.md':
        output_root = output_root or 'drucker_output'
    elif output_ext.lower() != '.json':
        output_root = output_base

    json_path = output_root + '.json'
    md_path = output_root + '.md'

    os.makedirs(os.path.dirname(json_path) or '.', exist_ok=True)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown or '')

    return json_path, md_path


def _load_env(args: argparse.Namespace) -> None:
    '''Load dotenv from --env path or default .env.'''
    from dotenv import load_dotenv
    env_path = getattr(args, 'env', None)
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()


def _print_summary(workflow_name: str, created_files: list) -> None:
    '''Print a standardised "WORKFLOW COMPLETE" banner with a file table.

    Input:
        workflow_name:  Short name shown in the banner (e.g. "drucker-hygiene").
        created_files:  List of (filepath, description) tuples.
    '''
    banner = '=' * 80
    print('')
    print(banner)
    print(f'WORKFLOW COMPLETE: {workflow_name}')
    print(banner)

    if created_files:
        max_name = max(len(f[0]) for f in created_files)
        max_name = max(max_name, 4)  # minimum column width
        row_fmt = f'{{:<4}}{{:<{max_name + 3}}}{{:<}}'

        file_table_lines = [
            '',
            banner,
            'Workflow Output Files',
            banner,
            row_fmt.format('#', 'File', 'Description'),
        ]
        for idx, (fpath, fdesc) in enumerate(created_files, 1):
            file_table_lines.append(row_fmt.format(str(idx), fpath, fdesc))
        file_table_lines.append(banner)

        print('\n'.join(file_table_lines))


# ------------------------------------------------------------------
# hygiene — Jira project hygiene scan
# ------------------------------------------------------------------

def cmd_hygiene(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.drucker.agent import DruckerCoordinatorAgent
    from agents.drucker.state.report_store import DruckerReportStore

    quiet = getattr(args, 'quiet', False)

    if not quiet:
        print('')
        print('=' * 60)
        print('Drucker: Jira project hygiene scan')
        print('=' * 60)
        print('')
        print(f'Project: {args.project}')
        print(f'Include done issues: {"yes" if args.include_done else "no"}')
        print(f'Stale threshold: {args.stale_days} days')
        print('')
        print('Step 1/4: Building Jira hygiene report...')

    agent = DruckerCoordinatorAgent(project_key=args.project)
    result = agent.run({
        'project_key': args.project,
        'limit': args.limit or 200,
        'include_done': args.include_done,
        'stale_days': args.stale_days,
    })

    if not result.success:
        print(f'ERROR: {result.error}', file=sys.stderr)
        sys.exit(1)

    report = result.metadata.get('hygiene_report')
    review_session = result.metadata.get('review_session')

    if not report:
        print('ERROR: Drucker hygiene report missing from agent response', file=sys.stderr)
        sys.exit(1)

    if not quiet:
        print('Step 2/4: Persisting hygiene report...')

    store = DruckerReportStore()
    stored_summary = store.save_report(report, summary_markdown=result.content or '')

    if not quiet:
        print(f'  Stored report ID: {stored_summary["report_id"]}')
        print(f'  Stored in: {stored_summary["storage_dir"]}')

    # --json: emit JSON to stdout and exit
    if getattr(args, 'json', False):
        _print_json(report)
        sys.exit(0)

    if not quiet:
        print('Step 3/4: Writing report files...')

    output_base = args.output or f'{args.project.lower()}_drucker_hygiene.json'
    json_path, md_path, review_path = _write_report_files(
        report,
        result.content or '',
        review_session or {},
        output_base,
    )

    if not quiet:
        print(f'  Saved: {json_path}')
        print(f'  Saved: {md_path}')
        print(f'  Saved: {review_path}')

        print('Step 4/4: Reporting summary...')
        print(f'  Findings: {report.get("summary", {}).get("finding_count", 0)}')
        print(f'  Proposed actions: {report.get("summary", {}).get("action_count", 0)}')
        print(f'  Tickets with findings: {report.get("summary", {}).get("tickets_with_findings", 0)}')

        _print_summary('drucker-hygiene', [
            (stored_summary['json_path'], 'stored hygiene report JSON'),
            (stored_summary['markdown_path'], 'stored hygiene report Markdown'),
            (json_path, 'exported hygiene report JSON'),
            (md_path, 'exported hygiene report Markdown'),
            (review_path, 'review session JSON'),
        ])

    sys.exit(0)


# ------------------------------------------------------------------
# issue-check — single-ticket intake validation
# ------------------------------------------------------------------

def cmd_issue_check(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.drucker.agent import DruckerCoordinatorAgent
    from agents.drucker.state.report_store import DruckerReportStore

    quiet = getattr(args, 'quiet', False)

    if not quiet:
        print('')
        print('=' * 60)
        print('Drucker: single-ticket issue check')
        print('=' * 60)
        print('')
        print(f'Project: {args.project}')
        print(f'Ticket: {args.ticket_key}')
        print(f'Stale threshold: {args.stale_days} days')
        print('')
        print('Step 1/4: Building Drucker issue-check report...')

    agent = DruckerCoordinatorAgent(project_key=args.project)
    result = agent.run({
        'project_key': args.project,
        'ticket_key': args.ticket_key,
        'stale_days': args.stale_days,
    })

    if not result.success:
        print(f'ERROR: {result.error}', file=sys.stderr)
        sys.exit(1)

    report = result.metadata.get('hygiene_report')
    review_session = result.metadata.get('review_session')

    if not report:
        print('ERROR: Drucker issue-check report missing from agent response', file=sys.stderr)
        sys.exit(1)

    if not quiet:
        print('Step 2/4: Persisting issue-check report...')

    store = DruckerReportStore()
    stored_summary = store.save_report(report, summary_markdown=result.content or '')

    if not quiet:
        print(f'  Stored report ID: {stored_summary["report_id"]}')
        print(f'  Stored in: {stored_summary["storage_dir"]}')

    if getattr(args, 'json', False):
        _print_json(report)
        sys.exit(0)

    if not quiet:
        print('Step 3/4: Writing report files...')

    default_base = (
        f'{args.project.lower()}_{args.ticket_key.lower()}_drucker_issue_check.json'
    )
    output_base = args.output or default_base
    json_path, md_path, review_path = _write_report_files(
        report,
        result.content or '',
        review_session or {},
        output_base,
    )

    if not quiet:
        print(f'  Saved: {json_path}')
        print(f'  Saved: {md_path}')
        print(f'  Saved: {review_path}')

        print('Step 4/4: Reporting summary...')
        print(f'  Findings: {report.get("summary", {}).get("finding_count", 0)}')
        print(f'  Proposed actions: {report.get("summary", {}).get("action_count", 0)}')
        print(
            '  Tickets with findings: '
            f'{report.get("summary", {}).get("tickets_with_findings", 0)}'
        )

        _print_summary('drucker-issue-check', [
            (stored_summary['json_path'], 'stored issue-check report JSON'),
            (stored_summary['markdown_path'], 'stored issue-check report Markdown'),
            (json_path, 'exported issue-check report JSON'),
            (md_path, 'exported issue-check report Markdown'),
            (review_path, 'review session JSON'),
        ])

    sys.exit(0)


# ------------------------------------------------------------------
# intake-report — recent-ticket intake validation
# ------------------------------------------------------------------

def cmd_intake_report(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.drucker.agent import DruckerCoordinatorAgent
    from agents.drucker.state.report_store import DruckerReportStore

    quiet = getattr(args, 'quiet', False)

    if not quiet:
        print('')
        print('=' * 60)
        print('Drucker: recent-ticket intake report')
        print('=' * 60)
        print('')
        print(f'Project: {args.project}')
        print(f'Stale threshold: {args.stale_days} days')
        if args.since:
            print(f'Since: {args.since}')
        print('')
        print('Step 1/4: Building Drucker intake report...')

    agent = DruckerCoordinatorAgent(project_key=args.project)
    result = agent.run({
        'project_key': args.project,
        'limit': args.limit or 200,
        'stale_days': args.stale_days,
        'since': args.since,
        'recent_only': True,
    })

    if not result.success:
        print(f'ERROR: {result.error}', file=sys.stderr)
        sys.exit(1)

    report = result.metadata.get('hygiene_report')
    review_session = result.metadata.get('review_session')

    if not report:
        print('ERROR: Drucker intake report missing from agent response', file=sys.stderr)
        sys.exit(1)

    if not quiet:
        print('Step 2/4: Persisting intake report...')

    store = DruckerReportStore()
    stored_summary = store.save_report(report, summary_markdown=result.content or '')

    if not quiet:
        print(f'  Stored report ID: {stored_summary["report_id"]}')
        print(f'  Stored in: {stored_summary["storage_dir"]}')

    if getattr(args, 'json', False):
        _print_json(report)
        sys.exit(0)

    if not quiet:
        print('Step 3/4: Writing report files...')

    output_base = args.output or f'{args.project.lower()}_drucker_intake_report.json'
    json_path, md_path, review_path = _write_report_files(
        report,
        result.content or '',
        review_session or {},
        output_base,
    )

    if not quiet:
        print(f'  Saved: {json_path}')
        print(f'  Saved: {md_path}')
        print(f'  Saved: {review_path}')

        print('Step 4/4: Reporting summary...')
        print(f'  Findings: {report.get("summary", {}).get("finding_count", 0)}')
        print(f'  Proposed actions: {report.get("summary", {}).get("action_count", 0)}')
        print(
            '  Source tickets scanned: '
            f'{report.get("summary", {}).get("source_ticket_count", 0)}'
        )

        _print_summary('drucker-intake-report', [
            (stored_summary['json_path'], 'stored intake report JSON'),
            (stored_summary['markdown_path'], 'stored intake report Markdown'),
            (json_path, 'exported intake report JSON'),
            (md_path, 'exported intake report Markdown'),
            (review_path, 'review session JSON'),
        ])

    sys.exit(0)


# ------------------------------------------------------------------
# bug-activity — daily bug activity summary
# ------------------------------------------------------------------

def cmd_bug_activity(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.drucker.agent import DruckerCoordinatorAgent

    quiet = getattr(args, 'quiet', False)

    if not quiet:
        print('')
        print('=' * 60)
        print('Drucker: bug activity summary')
        print('=' * 60)
        print('')
        print(f'Project: {args.project}')
        print(f'Target date: {args.target_date or "today"}')
        print('')
        print('Step 1/2: Building Drucker bug activity report...')

    agent = DruckerCoordinatorAgent(project_key=args.project)
    activity = agent.analyze_bug_activity(
        project_key=args.project,
        target_date=args.target_date,
    )
    summary_markdown = agent.format_bug_activity_report(activity)

    if getattr(args, 'json', False):
        _print_json(activity)
        sys.exit(0)

    if not quiet:
        print('Step 2/2: Writing report files...')

    target_suffix = str(activity.get('date') or 'today').replace('-', '')
    output_base = (
        args.output
        or f'{args.project.lower()}_drucker_bug_activity_{target_suffix}.json'
    )
    json_path, md_path = _write_activity_files(
        activity,
        summary_markdown,
        output_base,
    )

    if not quiet:
        print(f'  Saved: {json_path}')
        print(f'  Saved: {md_path}')
        print(f'  Bugs opened: {activity.get("summary", {}).get("bugs_opened", 0)}')
        print(
            '  Status transitions: '
            f'{activity.get("summary", {}).get("status_transitions", 0)}'
        )
        print(
            '  Bugs with comments: '
            f'{activity.get("summary", {}).get("bugs_with_comments", 0)}'
        )

        _print_summary('drucker-bug-activity', [
            (json_path, 'exported bug activity JSON'),
            (md_path, 'exported bug activity Markdown'),
        ])

    sys.exit(0)


# ------------------------------------------------------------------
# github-hygiene — GitHub repository PR hygiene analysis
# ------------------------------------------------------------------

def cmd_github_hygiene(args: argparse.Namespace) -> None:
    _load_env(args)

    import github_utils

    quiet = getattr(args, 'quiet', False)

    if not quiet:
        print('')
        print('=' * 60)
        print('Drucker: GitHub PR hygiene analysis')
        print('=' * 60)
        print('')
        print(f'Repository: {args.repo}')
        print(f'Stale PR threshold: {args.stale_days} days')
        print(f'Extended scan: {"yes" if args.extended else "no"}')
        if args.extended:
            print(f'Branch stale threshold: {args.branch_stale_days} days')
        print('')
        print('Running GitHub hygiene scan...')

    if args.extended:
        report = github_utils.analyze_extended_hygiene(
            repo_name=args.repo,
            stale_days=args.stale_days,
            branch_stale_days=args.branch_stale_days,
        )
    else:
        report = github_utils.analyze_repo_pr_hygiene(
            repo_name=args.repo,
            stale_days=args.stale_days,
        )

    if getattr(args, 'json', False):
        _print_json(report)
        sys.exit(0)

    # Write output files
    output_base = args.output or f'{args.repo.replace("/", "_")}_github_hygiene.json'
    json_path, md_path = _write_output_files(
        report,
        report.get('summary', ''),
        output_base,
    )

    if not quiet:
        print(f'  Saved: {json_path}')
        print(f'  Saved: {md_path}')
        print(f'  Total open PRs: {report.get("total_open_prs", 0)}')
        print(f'  Total findings: {report.get("total_findings", 0)}')
        if args.extended:
            print(f'  Stale branches: {report.get("stale_branch_count", 0)}')

        _print_summary('drucker-github-hygiene', [
            (json_path, 'GitHub hygiene report JSON'),
            (md_path, 'GitHub hygiene report summary'),
        ])

    sys.exit(0)


def cmd_pr_reminder_scan(args: argparse.Namespace) -> None:
    _load_env(args)

    from pr_reminders import PRReminderEngine

    quiet = getattr(args, 'quiet', False)

    if not quiet:
        print('')
        print('=' * 60)
        print('Drucker: PR reminder scan')
        print('=' * 60)
        print('')
        if args.repos:
            print(f'Repos: {", ".join(args.repos)}')
        else:
            print('Repos: all configured')
        print('')
        print('Scanning for stale PRs...')

    engine = PRReminderEngine()
    result = engine.scan_repos(repos=args.repos or None)

    if getattr(args, 'json', False):
        _print_json(result)
        sys.exit(0)

    if not quiet:
        print(f'  Scanned: {result.get("scanned", 0)} PR(s)')
        print(f'  New reminders: {result.get("new", 0)}')
        print(f'  Updated: {result.get("updated", 0)}')
        print(f'  Closed: {result.get("closed", 0)}')

    sys.exit(0)


def cmd_pr_reminder_process(args: argparse.Namespace) -> None:
    _load_env(args)

    from pr_reminders import PRReminderEngine

    quiet = getattr(args, 'quiet', False)

    if not quiet:
        print('')
        print('=' * 60)
        print('Drucker: process due PR reminders')
        print('=' * 60)
        print('')
        print('Processing due reminders...')

    engine = PRReminderEngine()
    result = engine.process_due_reminders()

    if getattr(args, 'json', False):
        _print_json(result)
        sys.exit(0)

    if not quiet:
        print(f'  Due: {result.get("due", 0)}')
        print(f'  Sent: {result.get("sent", 0)}')
        print(f'  Errors: {result.get("errors", 0)}')

    sys.exit(0)


def cmd_pr_reminder_active(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.drucker.state.pr_reminder_state import PRReminderState

    quiet = getattr(args, 'quiet', False)

    if not quiet:
        print('')
        print('=' * 60)
        print('Drucker: active PR reminders')
        print('=' * 60)
        print('')

    state = PRReminderState()
    active = state.list_active(repo=args.repo, limit=args.limit)

    if getattr(args, 'json', False):
        _print_json({'active': active, 'count': len(active)})
        sys.exit(0)

    if not active:
        if not quiet:
            print('  No active PR reminders.')
    else:
        for pr in active:
            print(
                f'  {pr["repo"]}#{pr["pr_number"]} '
                f'| {pr.get("pr_title", "")[:50]} '
                f'| next: {pr.get("next_reminder_at", "n/a")} '
                f'| sent: {pr.get("reminder_count", 0)}'
            )

    sys.exit(0)


def cmd_pr_reminder_snooze(args: argparse.Namespace) -> None:
    _load_env(args)

    from pr_reminders import PRReminderEngine

    quiet = getattr(args, 'quiet', False)

    if not quiet:
        print(f'Snoozing {args.repo}#{args.pr_number} for {args.snooze_days} days...')

    engine = PRReminderEngine()
    result = engine.handle_snooze(
        repo=args.repo,
        pr_number=args.pr_number,
        snooze_days=args.snooze_days,
        snoozed_by=args.snoozed_by or '',
    )

    if getattr(args, 'json', False):
        _print_json(result)
        sys.exit(0)

    if not quiet:
        if result.get('ok'):
            print(f'  Snoozed until {result.get("snooze_until", "?")}')
        else:
            print(f'  Failed: {result.get("error", "unknown")}')

    sys.exit(0 if result.get('ok') else 1)


def cmd_pr_reminder_merge(args: argparse.Namespace) -> None:
    _load_env(args)

    from config.env_loader import resolve_dry_run
    from pr_reminders import PRReminderEngine

    quiet = getattr(args, 'quiet', False)
    is_dry_run = resolve_dry_run(args.dry_run if hasattr(args, 'dry_run') else None)

    if not quiet:
        mode_label = 'DRY RUN' if is_dry_run else 'EXECUTE'
        print(
            f'Merging {args.repo}#{args.pr_number} '
            f'via {args.merge_method} [{mode_label}]...'
        )

    engine = PRReminderEngine()
    result = engine.handle_merge_request(
        repo=args.repo,
        pr_number=args.pr_number,
        merge_method=args.merge_method,
        requested_by=args.requested_by or '',
        dry_run=is_dry_run,
    )

    if getattr(args, 'json', False):
        _print_json(result)
        sys.exit(0)

    if not quiet:
        if result.get('ok'):
            if is_dry_run:
                print(f'  Dry run OK — would merge via {args.merge_method}')
            else:
                print(f'  Merged: {result.get("sha", "")}')
        else:
            print(f'  Failed: {result.get("error", "unknown")}')

    sys.exit(0 if result.get('ok') else 1)


# ------------------------------------------------------------------
# poll — scheduled hygiene polling loop
# ------------------------------------------------------------------

def cmd_poll(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.drucker.agent import DruckerCoordinatorAgent

    quiet = getattr(args, 'quiet', False)

    if not quiet:
        print('')
        print('=' * 60)
        print('Drucker: scheduled hygiene poller')
        print('=' * 60)
        print('')
        print(f'Project: {args.project or "from polling config"}')
        if args.poll_config:
            print(f'Polling config: {args.poll_config}')
            if args.poll_job:
                print(f'Polling job: {args.poll_job}')
        else:
            print(f'Stale threshold: {args.stale_days} days')
            print(f'Recent only: {"yes" if args.recent_only else "no"}')
            if args.since:
                print(f'Since: {args.since}')
        print(f'Poll interval: {args.poll_interval} seconds')
        print(
            'Cycles: '
            f'{"continuous" if args.max_cycles == 0 else args.max_cycles}'
        )
        print(f'Notify Shannon: {"yes" if args.notify_shannon else "no"}')
        if getattr(args, 'github_repos', None):
            print(f'GitHub repos: {", ".join(args.github_repos)}')
            print(f'GitHub stale threshold: {args.github_stale_days} days')
        print('')
        print('Running scheduled Drucker poller...')

    agent = DruckerCoordinatorAgent(project_key=args.project)
    poller_spec: Dict[str, Any] = {
        'persist': True,
        'notify_shannon': args.notify_shannon,
        'shannon_base_url': args.shannon_url,
        'interval_seconds': args.poll_interval,
        'max_cycles': args.max_cycles,
    }
    if args.project:
        poller_spec['project_key'] = args.project
    if args.poll_config:
        poller_spec['config_path'] = args.poll_config
        if args.poll_job:
            poller_spec['job_name'] = args.poll_job
        if args.since:
            poller_spec['since'] = args.since
    else:
        poller_spec.update({
            'limit': args.limit or 200,
            'include_done': args.include_done,
            'stale_days': args.stale_days,
            'since': args.since,
            'recent_only': args.recent_only,
        })

    if getattr(args, 'github_repos', None):
        poller_spec['github_repos'] = args.github_repos
        poller_spec['github_stale_days'] = getattr(args, 'github_stale_days', 5)

    result = agent.run_poller(poller_spec)

    if not quiet:
        print('')
        print('Cycle summary:')
        for cycle in result.get('cycle_summaries', []):
            print(
                f'  Cycle {cycle.get("cycle_number")}: '
                f'{cycle.get("task_count", 0)} task(s), '
                f'{cycle.get("notification_count", 0)} notification(s), '
                f'{"ok" if cycle.get("ok") else "error"}'
            )
            for error in cycle.get('errors', []):
                print(f'    ERROR: {error}')

        last_tick = result.get('last_tick') or {}
        for task in last_tick.get('tasks', []):
            if task.get('job_id'):
                print(f'  Job {task.get("job_id")}:')
            if task.get('task_type') == 'hygiene_report':
                stored = task.get('stored', {})
                print(
                    '    Latest hygiene report: '
                    f'{stored.get("report_id") or task.get("report", {}).get("report_id", "")}'
                )
            if task.get('task_type') == 'ticket_intake_report':
                stored = task.get('stored', {})
                print(
                    '    Latest intake report: '
                    f'{stored.get("report_id") or task.get("report", {}).get("report_id", "")}'
                )
            if task.get('task_type') == 'github_pr_hygiene':
                repo = task.get('repo', '')
                report = task.get('report', {})
                print(f'    GitHub PR hygiene ({repo}): '
                      f'{report.get("stale_count", 0)} stale, '
                      f'{report.get("missing_review_count", 0)} missing reviews')

    sys.exit(0 if result.get('ok', False) else 1)


# ------------------------------------------------------------------
# jira-query — ad-hoc JQL query
# ------------------------------------------------------------------

def cmd_jira_query(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.drucker.jira_reporting import query_jql

    result = query_jql(
        jql=args.jql,
        project_key=args.project,
        limit=args.limit,
    )

    if getattr(args, 'json', False):
        _print_json(result)
        sys.exit(0)

    print(f'Project: {result["project_key"]}')
    print(f'JQL: {result["jql"]}')
    print(f'Total: {result["total"]}')
    print()
    if result.get('by_status'):
        print('By Status:')
        for status, count in sorted(result['by_status'].items(), key=lambda x: -x[1]):
            print(f'  {status}: {count}')
    if result.get('by_type'):
        print('By Type:')
        for itype, count in sorted(result['by_type'].items(), key=lambda x: -x[1]):
            print(f'  {itype}: {count}')
    print()
    for t in result.get('tickets', [])[:20]:
        assignee = t.get('assignee') or 'Unassigned'
        print(f'  {t["key"]}  [{t["status"]}]  {t["summary"]}  ({assignee})')
    remaining = result['total'] - min(20, len(result.get('tickets', [])))
    if remaining > 0:
        print(f'  ...and {remaining} more')

    sys.exit(0)


# ------------------------------------------------------------------
# jira-tickets — query tickets by type, status, date
# ------------------------------------------------------------------

def cmd_jira_tickets(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.drucker.jira_reporting import query_tickets

    issue_types = (
        [x.strip() for x in args.issue_types.split(',') if x.strip()]
        if args.issue_types else None
    )
    statuses = (
        [x.strip() for x in args.statuses.split(',') if x.strip()]
        if args.statuses else None
    )
    exclude_statuses = (
        [x.strip() for x in args.exclude_statuses.split(',') if x.strip()]
        if getattr(args, 'exclude_statuses', None) else None
    )

    result = query_tickets(
        project_key=args.project,
        issue_types=issue_types,
        statuses=statuses,
        exclude_statuses=exclude_statuses,
        date_filter=getattr(args, 'date_filter', None),
        limit=args.limit,
    )

    if getattr(args, 'json', False):
        _print_json(result)
        sys.exit(0)

    print(f'Project: {result["project_key"]}')
    print(f'JQL: {result["jql"]}')
    print(f'Total: {result["total"]}')
    print()
    if result.get('by_status'):
        print('By Status:')
        for status, count in sorted(result['by_status'].items(), key=lambda x: -x[1]):
            print(f'  {status}: {count}')
    if result.get('by_type'):
        print('By Type:')
        for itype, count in sorted(result['by_type'].items(), key=lambda x: -x[1]):
            print(f'  {itype}: {count}')
    print()
    for t in result.get('tickets', [])[:20]:
        assignee = t.get('assignee') or 'Unassigned'
        print(f'  {t["key"]}  [{t["status"]}]  {t["summary"]}  ({assignee})')
    remaining = result['total'] - min(20, len(result.get('tickets', [])))
    if remaining > 0:
        print(f'  ...and {remaining} more')

    sys.exit(0)


# ------------------------------------------------------------------
# jira-release-status — status breakdown by release version
# ------------------------------------------------------------------

def cmd_jira_release_status(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.drucker.jira_reporting import query_release_status

    releases = [x.strip() for x in args.releases.split(',') if x.strip()]

    result = query_release_status(
        project_key=args.project,
        releases=releases,
        limit=args.limit,
    )

    if getattr(args, 'json', False):
        _print_json(result)
        sys.exit(0)

    print(f'Project: {result.get("project_key", args.project)}')
    print()
    for rel in result.get('releases', []):
        total = rel.get('total', 0)
        print(f'Release: {rel["release"]} ({total} tickets)')
        if rel.get('by_status'):
            print('  By Status:')
            for status, count in sorted(rel['by_status'].items(), key=lambda x: -x[1]):
                print(f'    {status}: {count}')
        if rel.get('by_type'):
            print('  By Type:')
            for itype, count in sorted(rel['by_type'].items(), key=lambda x: -x[1]):
                print(f'    {itype}: {count}')
        print()

    sys.exit(0)


# ------------------------------------------------------------------
# jira-ticket-counts — fast ticket count
# ------------------------------------------------------------------

def cmd_jira_ticket_counts(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.drucker.jira_reporting import get_ticket_counts

    issue_types = (
        [x.strip() for x in args.issue_types.split(',') if x.strip()]
        if getattr(args, 'issue_types', None) else None
    )
    statuses = (
        [x.strip() for x in args.statuses.split(',') if x.strip()]
        if getattr(args, 'statuses', None) else None
    )

    result = get_ticket_counts(
        project_key=args.project,
        issue_types=issue_types,
        statuses=statuses,
        date_filter=getattr(args, 'date_filter', None),
    )

    if getattr(args, 'json', False):
        _print_json(result)
        sys.exit(0)

    print(f'Project: {result.get("project_key", args.project)}')
    print(f'Count: {result.get("count", 0)}')
    if result.get('jql'):
        print(f'JQL: {result["jql"]}')

    sys.exit(0)


# ------------------------------------------------------------------
# jira-status-report — full project status dashboard
# ------------------------------------------------------------------

def cmd_jira_status_report(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.drucker.jira_reporting import get_status_report

    include_bugs = not getattr(args, 'no_bugs', False)
    include_activity = not getattr(args, 'no_activity', False)
    recent_days = getattr(args, 'recent_days', 7)

    result = get_status_report(
        project_key=args.project,
        include_bugs=include_bugs,
        include_activity=include_activity,
        recent_days=recent_days,
    )

    if getattr(args, 'json', False):
        _print_json(result)
        sys.exit(0)

    print(f'Project Status: {result.get("project_key", args.project)}')
    if result.get('generated'):
        print(f'Generated: {result["generated"]}')
    print(f'Total Open: {result.get("total_open", 0)}')
    if result.get('no_fix_version') is not None:
        print(f'No Fix Version: {result["no_fix_version"]}')
    print()

    if result.get('by_status'):
        print('By Status:')
        for status, count in sorted(result['by_status'].items(), key=lambda x: -x[1]):
            print(f'  {status}: {count}')
        print()

    if result.get('by_type'):
        print('By Type:')
        for itype, count in sorted(result['by_type'].items(), key=lambda x: -x[1]):
            print(f'  {itype}: {count}')
        print()

    bugs = result.get('bugs')
    if bugs and include_bugs:
        print('Bugs:')
        print(f'  Total Open: {bugs.get("total_open", 0)}')
        if bugs.get('by_priority'):
            print('  By Priority:')
            for priority, count in sorted(
                bugs['by_priority'].items(), key=lambda x: -x[1]
            ):
                print(f'    {priority}: {count}')
        print()

    activity = result.get('recent_activity')
    if activity and include_activity:
        print(f'Recent Activity ({recent_days} days):')
        print(f'  {activity.get("updated_count", 0)} tickets updated')
        for t in activity.get('tickets', [])[:20]:
            assignee = t.get('assignee') or 'Unassigned'
            print(f'  {t["key"]}  [{t["status"]}]  {t["summary"]}  ({assignee})')
        remaining = activity.get('updated_count', 0) - min(
            20, len(activity.get('tickets', []))
        )
        if remaining > 0:
            print(f'  ...and {remaining} more')
        print()

    sys.exit(0)


def cmd_nl_query(args):
    _load_env(args)
    from agents.drucker.nl_query import run_nl_query

    query = ' '.join(args.query)
    project_key = args.project_key

    result = run_nl_query(query=query, project_key=project_key)

    if args.json:
        _print_json(result)
        return

    if not result.get('ok'):
        print(f'Error: {result.get("error", "Unknown error")}')
        return

    tool_used = result.get('tool_used', '')
    tool_args = result.get('tool_args', {})
    summary = result.get('summary', '')
    data = result.get('result', {})

    print(f'Tool: {tool_used}')
    if tool_args.get('jql'):
        print(f'JQL: {tool_args["jql"]}')

    total = data.get('total') or data.get('grand_total') or data.get('count') or data.get('total_open')
    if total is not None:
        print(f'Total: {total}')

    if summary:
        print(f'\n{summary}')

    if not args.quiet:
        tickets = data.get('tickets', [])
        if tickets:
            print(f'\nShowing first {min(10, len(tickets))} tickets:')
            for t in tickets[:10]:
                print(f'  {t.get("key", "")} [{t.get("status", "")}] {t.get("summary", "")}')


# ------------------------------------------------------------------
# Argument parser
# ------------------------------------------------------------------

def _add_common_args(parser: argparse.ArgumentParser) -> None:
    '''Add common arguments shared by all subcommands.'''
    parser.add_argument('--env', default=None, metavar='FILE',
                        help='Alternate .env file path')
    parser.add_argument('--quiet', action='store_true', default=False,
                        help='Suppress progress output')
    parser.add_argument('--output', default=None, metavar='FILE',
                        help='Output filename base')
    parser.add_argument('--json', action='store_true', default=False,
                        help='Output raw JSON to stdout')


def register_subcommands(subparsers) -> None:
    '''Add Drucker subcommands to an argparse subparsers group.'''

    # --- hygiene ---
    p = subparsers.add_parser('hygiene', help='Run Jira project hygiene scan')
    p.add_argument('--project', '-p', required=True, help='Jira project key')
    p.add_argument('--limit', type=int, default=200, metavar='N',
                   help='Maximum issues to fetch (default: 200)')
    p.add_argument('--include-done', action='store_true', dest='include_done',
                   help='Include done/closed issues')
    p.add_argument('--stale-days', type=int, default=14, metavar='DAYS',
                   dest='stale_days',
                   help='Days without update to consider stale (default: 14)')
    _add_common_args(p)
    p.set_defaults(func=cmd_hygiene)

    # --- issue-check ---
    p = subparsers.add_parser('issue-check', help='Single-ticket intake validation')
    p.add_argument('--project', '-p', required=True, help='Jira project key')
    p.add_argument('--ticket-key', '-t', required=True, dest='ticket_key',
                   help='Jira ticket key (e.g. STL-1234)')
    p.add_argument('--stale-days', type=int, default=14, metavar='DAYS',
                   dest='stale_days',
                   help='Days without update to consider stale (default: 14)')
    _add_common_args(p)
    p.set_defaults(func=cmd_issue_check)

    # --- intake-report ---
    p = subparsers.add_parser('intake-report', help='Recent-ticket intake validation report')
    p.add_argument('--project', '-p', required=True, help='Jira project key')
    p.add_argument('--limit', type=int, default=200, metavar='N',
                   help='Maximum issues to fetch (default: 200)')
    p.add_argument('--stale-days', type=int, default=14, metavar='DAYS',
                   dest='stale_days',
                   help='Days without update to consider stale (default: 14)')
    p.add_argument('--since', default=None, metavar='DATE',
                   help='Only include tickets created since this date (YYYY-MM-DD)')
    _add_common_args(p)
    p.set_defaults(func=cmd_intake_report)

    # --- bug-activity ---
    p = subparsers.add_parser('bug-activity', help='Daily bug activity summary')
    p.add_argument('--project', '-p', required=True, help='Jira project key')
    p.add_argument('--target-date', default=None, metavar='DATE',
                   dest='target_date',
                   help='Target date for activity (YYYY-MM-DD, default: today)')
    _add_common_args(p)
    p.set_defaults(func=cmd_bug_activity)

    # --- github-hygiene ---
    p = subparsers.add_parser('github-hygiene', help='GitHub repository PR hygiene analysis')
    p.add_argument('repo', help='GitHub repository (e.g. cornelisnetworks/opa-psm2)')
    p.add_argument('--stale-days', type=int, default=5, metavar='DAYS',
                   dest='stale_days',
                   help='Days without update to consider PR stale (default: 5)')
    p.add_argument('--branch-stale-days', type=int, default=30, metavar='DAYS',
                   dest='branch_stale_days',
                   help='Days without update to consider branch stale (default: 30)')
    p.add_argument('--extended', action='store_true', default=False,
                   help='Run extended hygiene scan (all 6 checks)')
    _add_common_args(p)
    p.set_defaults(func=cmd_github_hygiene)

    # --- poll ---
    p = subparsers.add_parser('poll', help='Scheduled hygiene polling loop')
    p.add_argument('--project', '-p', default=None,
                   help='Jira project key (or use --poll-config)')
    p.add_argument('--poll-config', default=None, metavar='FILE',
                   dest='poll_config',
                   help='Polling configuration YAML file')
    p.add_argument('--poll-job', default=None, metavar='NAME',
                   dest='poll_job',
                   help='Run only this named job from polling config')
    p.add_argument('--limit', type=int, default=200, metavar='N',
                   help='Maximum issues to fetch (default: 200)')
    p.add_argument('--include-done', action='store_true', dest='include_done',
                   help='Include done/closed issues')
    p.add_argument('--stale-days', type=int, default=14, metavar='DAYS',
                   dest='stale_days',
                   help='Days without update to consider stale (default: 14)')
    p.add_argument('--since', default=None, metavar='DATE',
                   help='Only include tickets created since this date (YYYY-MM-DD)')
    p.add_argument('--recent-only', action='store_true', dest='recent_only',
                   help='Only scan recently created tickets')
    p.add_argument('--poll-interval', type=int, default=300, metavar='SECS',
                   dest='poll_interval',
                   help='Polling interval in seconds (default: 300)')
    p.add_argument('--max-cycles', type=int, default=1, metavar='N',
                   dest='max_cycles',
                   help='Number of polling cycles, 0 for continuous (default: 1)')
    p.add_argument('--notify-shannon', action='store_true',
                   dest='notify_shannon',
                   help='Post proactive poller summaries through Shannon')
    p.add_argument('--shannon-url', default='http://localhost:8200', metavar='URL',
                   dest='shannon_url',
                   help='Shannon service base URL (default: http://localhost:8200)')
    p.add_argument('--github-repos', nargs='*', default=None, metavar='REPO',
                   dest='github_repos',
                   help='GitHub repositories to include in hygiene scan')
    p.add_argument('--github-stale-days', type=int, default=5, metavar='DAYS',
                   dest='github_stale_days',
                   help='GitHub PR stale threshold in days (default: 5)')
    _add_common_args(p)
    p.set_defaults(func=cmd_poll)

    p = subparsers.add_parser('pr-reminder-scan',
                              help='Scan repos for stale PRs and update reminder state')
    p.add_argument('--repos', nargs='*', default=None, metavar='REPO',
                   help='GitHub repos to scan (default: all configured)')
    _add_common_args(p)
    p.set_defaults(func=cmd_pr_reminder_scan)

    p = subparsers.add_parser('pr-reminder-process',
                              help='Send due PR reminders via Teams DM')
    _add_common_args(p)
    p.set_defaults(func=cmd_pr_reminder_process)

    p = subparsers.add_parser('pr-reminder-active',
                              help='List active PR reminders')
    p.add_argument('--repo', default=None, metavar='REPO',
                   help='Filter by repository')
    p.add_argument('--limit', type=int, default=50, metavar='N',
                   help='Max results (default: 50)')
    _add_common_args(p)
    p.set_defaults(func=cmd_pr_reminder_active)

    p = subparsers.add_parser('pr-reminder-snooze',
                              help='Snooze a PR reminder for N days')
    p.add_argument('repo', help='GitHub repository (owner/name)')
    p.add_argument('pr_number', type=int, help='PR number')
    p.add_argument('snooze_days', type=int, help='Days to snooze')
    p.add_argument('--snoozed-by', default=None, dest='snoozed_by',
                   help='Who requested the snooze')
    _add_common_args(p)
    p.set_defaults(func=cmd_pr_reminder_snooze)

    p = subparsers.add_parser('pr-reminder-merge',
                              help='Merge a PR on behalf of the user')
    p.add_argument('repo', help='GitHub repository (owner/name)')
    p.add_argument('pr_number', type=int, help='PR number')
    p.add_argument('--merge-method', default='squash', dest='merge_method',
                   choices=['squash', 'merge', 'rebase'],
                   help='Merge method (default: squash)')
    p.add_argument('--requested-by', default=None, dest='requested_by',
                   help='Who requested the merge')
    p.add_argument('--dry-run', action='store_true', default=None, dest='dry_run',
                   help='Preview merge without executing')
    p.add_argument('--execute', action='store_false', dest='dry_run',
                   help='Execute the merge (override DRY_RUN env)')
    _add_common_args(p)
    p.set_defaults(func=cmd_pr_reminder_merge)

    # --- Jira query & reporting commands ---
    sp_jql = subparsers.add_parser('jira-query', help='Run an ad-hoc JQL query')
    sp_jql.add_argument('--project', default='STL', help='Jira project key')
    sp_jql.add_argument('--jql', required=True, help='JQL query string')
    sp_jql.add_argument('--limit', type=int, default=100, help='Max tickets')
    _add_common_args(sp_jql)
    sp_jql.set_defaults(func=cmd_jira_query)

    sp_jt = subparsers.add_parser('jira-tickets', help='Query tickets by type, status, date')
    sp_jt.add_argument('--project', default='STL', help='Jira project key')
    sp_jt.add_argument('--issue-types', default=None, help='Comma-separated issue types')
    sp_jt.add_argument('--statuses', default=None, help='Comma-separated statuses')
    sp_jt.add_argument('--exclude-statuses', default=None, help='Comma-separated statuses to exclude')
    sp_jt.add_argument('--date-filter', default=None, help='Date range: today, week, month, year')
    sp_jt.add_argument('--limit', type=int, default=100, help='Max tickets')
    _add_common_args(sp_jt)
    sp_jt.set_defaults(func=cmd_jira_tickets)

    sp_rs = subparsers.add_parser('jira-release-status', help='Status breakdown by release version')
    sp_rs.add_argument('--project', default='STL', help='Jira project key')
    sp_rs.add_argument('--releases', required=True, help='Comma-separated release versions')
    sp_rs.add_argument('--limit', type=int, default=500, help='Max tickets per release')
    _add_common_args(sp_rs)
    sp_rs.set_defaults(func=cmd_jira_release_status)

    sp_tc = subparsers.add_parser('jira-ticket-counts', help='Fast ticket count')
    sp_tc.add_argument('--project', default='STL', help='Jira project key')
    sp_tc.add_argument('--issue-types', default=None, help='Comma-separated issue types')
    sp_tc.add_argument('--statuses', default=None, help='Comma-separated statuses')
    sp_tc.add_argument('--date-filter', default=None, help='Date range: today, week, month, year')
    _add_common_args(sp_tc)
    sp_tc.set_defaults(func=cmd_jira_ticket_counts)

    sp_sr = subparsers.add_parser('jira-status-report', help='Full project status dashboard')
    sp_sr.add_argument('--project', default='STL', help='Jira project key')
    sp_sr.add_argument('--no-bugs', action='store_true', help='Exclude bug breakdown')
    sp_sr.add_argument('--no-activity', action='store_true', help='Exclude recent activity')
    sp_sr.add_argument('--recent-days', type=int, default=7, help='Days for recent activity')
    _add_common_args(sp_sr)
    sp_sr.set_defaults(func=cmd_jira_status_report)

    p_nl = subparsers.add_parser('nl-query', help='Ask Drucker a question in plain English')
    p_nl.add_argument('query', nargs='+', help='Natural language query')
    p_nl.add_argument('--project-key', default='STL', help='Jira project key')
    p_nl.add_argument('--json', action='store_true', help='Output raw JSON')
    p_nl.add_argument('--quiet', '-q', action='store_true', help='Minimal output')
    p_nl.set_defaults(func=cmd_nl_query)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='drucker-agent',
        description='Drucker Engineering Hygiene agent CLI',
    )
    sub = parser.add_subparsers(dest='command', required=True)
    register_subcommands(sub)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print('\nInterrupted.', file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        log.debug('CLI error', exc_info=True)
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
