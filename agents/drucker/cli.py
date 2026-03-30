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
