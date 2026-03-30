##########################################################################################
#
# Module: agents/gantt/cli.py
#
# Description: Standalone CLI for Gantt Project Planner agent.
#              Provides direct access to planning snapshots, release monitoring,
#              release surveys, and scheduled polling.
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


def _write_output_files(data: dict, markdown: str, output_base: str):
    '''
    Write JSON + Markdown files from data and summary markdown.
    Returns (json_path, md_path).
    '''
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() == '.md':
        output_root = output_root or 'gantt_output'
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


# ------------------------------------------------------------------
# snapshot — create planning snapshot
# ------------------------------------------------------------------

def cmd_snapshot(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.gantt.agent import GanttProjectPlannerAgent
    from agents.gantt.state.snapshot_store import GanttSnapshotStore

    print(f'Creating planning snapshot for {args.project}...')

    agent = GanttProjectPlannerAgent(project_key=args.project)
    result = agent.run({
        'project_key': args.project,
        'planning_horizon_days': args.planning_horizon,
        'limit': args.limit or 200,
        'include_done': args.include_done,
        'evidence_paths': list(getattr(args, 'evidence', None) or []),
    })

    if not result.success:
        print(f'ERROR: {result.error}', file=sys.stderr)
        sys.exit(1)

    snapshot = result.metadata.get('planning_snapshot')
    if not snapshot:
        print('ERROR: Gantt snapshot metadata missing from agent response', file=sys.stderr)
        sys.exit(1)

    store = GanttSnapshotStore()
    stored_summary = store.save_snapshot(snapshot, summary_markdown=result.content or '')
    print(f'  Stored snapshot ID: {stored_summary["snapshot_id"]}')
    print(f'  Stored in: {stored_summary["storage_dir"]}')

    if getattr(args, 'json', False):
        _print_json(snapshot)
        sys.exit(0)

    output_base = args.output or f'{args.project.lower()}_planning_snapshot.json'
    json_path, md_path = _write_output_files(
        snapshot,
        result.content or '',
        output_base,
    )
    print(f'  Saved: {json_path}')
    print(f'  Saved: {md_path}')
    sys.exit(0)


# ------------------------------------------------------------------
# snapshot-get — load stored snapshot
# ------------------------------------------------------------------

def cmd_snapshot_get(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.gantt.state.snapshot_store import GanttSnapshotStore

    store = GanttSnapshotStore()
    record = store.get_snapshot(args.snapshot_id, project_key=args.project)
    if not record:
        print(f'ERROR: Stored Gantt snapshot not found: {args.snapshot_id}', file=sys.stderr)
        sys.exit(1)

    snapshot = record['snapshot']
    summary = record['summary']
    summary_markdown = record['summary_markdown'] or str(
        snapshot.get('summary_markdown') or ''
    )

    print(f'  Project: {summary["project_key"]}')
    print(f'  Created at: {summary["created_at"]}')
    print(f'  Total issues: {summary["total_issues"]}')
    print(f'  Milestones: {summary["milestone_count"]}')
    print(f'  Risks: {summary["risk_count"]}')
    print(f'  Stored in: {summary["storage_dir"]}')

    if args.output:
        json_path, md_path = _write_output_files(
            snapshot,
            summary_markdown,
            args.output,
        )
        print(f'  Saved: {json_path}')
        print(f'  Saved: {md_path}')
    else:
        print('')
        print(summary_markdown or '(No summary markdown stored for this snapshot.)')

    sys.exit(0)


# ------------------------------------------------------------------
# snapshot-list — list stored snapshots
# ------------------------------------------------------------------

def cmd_snapshot_list(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.gantt.state.snapshot_store import GanttSnapshotStore

    store = GanttSnapshotStore()
    snapshots = store.list_snapshots(project_key=args.project, limit=args.limit)
    if not snapshots:
        if args.project:
            print(f'No stored Gantt snapshots found for project {args.project}.')
        else:
            print('No stored Gantt snapshots found.')
        sys.exit(0)

    print('')
    print(
        'SNAPSHOT  PROJECT  CREATED AT                  ISSUES  MILES  RISKS  BLOCKED'
    )
    print(
        '--------  -------  --------------------------  ------  -----  -----  -------'
    )
    for item in snapshots:
        print(
            f'{item["snapshot_id"]:<8}  '
            f'{item["project_key"]:<7}  '
            f'{item["created_at"]:<26}  '
            f'{item["total_issues"]:>6}  '
            f'{item["milestone_count"]:>5}  '
            f'{item["risk_count"]:>5}  '
            f'{item["blocked_issues"]:>7}'
        )

    print('')
    print(f'Total stored snapshots: {len(snapshots)}')
    sys.exit(0)


# ------------------------------------------------------------------
# release-monitor — create release health report
# ------------------------------------------------------------------

def cmd_release_monitor(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.gantt.agent import GanttProjectPlannerAgent
    from agents.gantt.models import ReleaseMonitorRequest

    print(f'Creating release monitor report for {args.project}...')

    output_base = args.output or f'{args.project.lower()}_release_monitor.json'
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() == '.md':
        output_root = output_root or 'gantt_release_monitor'
    elif output_ext.lower() != '.json':
        output_root = output_base
    xlsx_path_hint = output_root + '.xlsx'

    agent = GanttProjectPlannerAgent(project_key=args.project)
    request = ReleaseMonitorRequest(
        project_key=args.project,
        releases=[
            item.strip() for item in str(args.releases or '').split(',')
            if item.strip()
        ] or None,
        scope_label=args.scope_label or '',
        include_gap_analysis=args.include_gap_analysis,
        include_bug_report=args.include_bug_report,
        include_velocity=args.include_velocity,
        include_readiness=args.include_readiness,
        compare_to_previous=args.compare_to_previous,
        output_file=xlsx_path_hint,
    )
    report = agent.create_release_monitor(request)

    from agents.gantt.state.release_monitor_store import GanttReleaseMonitorStore
    store = GanttReleaseMonitorStore()
    stored_summary = store.save_report(
        report,
        summary_markdown=report.summary_markdown,
    )
    print(f'  Stored report ID: {stored_summary["report_id"]}')
    print(f'  Stored in: {stored_summary["storage_dir"]}')

    if getattr(args, 'json', False):
        _print_json(report.to_dict())
        sys.exit(0)

    json_path, md_path = _write_output_files(
        report.to_dict(),
        report.summary_markdown or '',
        output_base,
    )
    print(f'  Saved: {json_path}')
    print(f'  Saved: {md_path}')
    if report.output_file:
        print(f'  Saved: {report.output_file}')

    print(f'  Releases monitored: {len(report.releases_monitored)}')
    print(f'  Total bugs: {report.total_bugs}')
    print(f'  Total P0: {report.total_p0}')
    print(f'  Total P1: {report.total_p1}')
    sys.exit(0)


# ------------------------------------------------------------------
# release-monitor-get — load stored release report
# ------------------------------------------------------------------

def cmd_release_monitor_get(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.gantt.state.release_monitor_store import GanttReleaseMonitorStore

    store = GanttReleaseMonitorStore()
    record = store.get_report(args.report_id, project_key=args.project)
    if not record:
        print(
            f'ERROR: Stored Gantt release monitor report not found: {args.report_id}',
            file=sys.stderr,
        )
        sys.exit(1)

    report = record['report']
    summary = record['summary']
    summary_markdown = record['summary_markdown'] or str(
        report.get('summary_markdown') or ''
    )

    print(f'  Project: {summary["project_key"]}')
    print(f'  Created at: {summary["created_at"]}')
    print(f'  Releases: {summary["release_count"]}')
    print(f'  Total bugs: {summary["total_bugs"]}')
    print(f'  Total P0: {summary["total_p0"]}')
    print(f'  Total P1: {summary["total_p1"]}')
    print(f'  Stored in: {summary["storage_dir"]}')

    if args.output:
        json_path, md_path = _write_output_files(
            report,
            summary_markdown,
            args.output,
        )
        print(f'  Saved: {json_path}')
        print(f'  Saved: {md_path}')
    else:
        print('')
        print(summary_markdown or '(No summary markdown stored for this report.)')

    sys.exit(0)


# ------------------------------------------------------------------
# release-monitor-list — list stored release reports
# ------------------------------------------------------------------

def cmd_release_monitor_list(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.gantt.state.release_monitor_store import GanttReleaseMonitorStore

    store = GanttReleaseMonitorStore()
    reports = store.list_reports(project_key=args.project, limit=args.limit)
    if not reports:
        if args.project:
            print(f'No stored release monitor reports found for project {args.project}.')
        else:
            print('No stored release monitor reports found.')
        sys.exit(0)

    print('')
    print(
        'REPORT ID                            PROJECT  CREATED AT                  RELS  BUGS  P0  P1'
    )
    print(
        '-----------------------------------  -------  --------------------------  ----  ----  --  --'
    )
    for item in reports:
        print(
            f'{item["report_id"]:<35}  '
            f'{item["project_key"]:<7}  '
            f'{item["created_at"]:<26}  '
            f'{item["release_count"]:>4}  '
            f'{item["total_bugs"]:>4}  '
            f'{item["total_p0"]:>2}  '
            f'{item["total_p1"]:>2}'
        )

    print('')
    print(f'Total stored reports: {len(reports)}')
    sys.exit(0)


# ------------------------------------------------------------------
# release-survey — create release execution survey
# ------------------------------------------------------------------

def cmd_release_survey(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.gantt.agent import GanttProjectPlannerAgent
    from agents.gantt.models import ReleaseSurveyRequest

    print(f'Creating release survey for {args.project}...')

    output_base = args.output or f'{args.project.lower()}_release_survey.json'
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() == '.md':
        output_root = output_root or 'gantt_release_survey'
    elif output_ext.lower() != '.json':
        output_root = output_base
    xlsx_path_hint = output_root + '.xlsx'

    agent = GanttProjectPlannerAgent(project_key=args.project)
    request = ReleaseSurveyRequest(
        project_key=args.project,
        releases=[
            item.strip() for item in str(args.releases or '').split(',')
            if item.strip()
        ] or None,
        scope_label=args.scope_label or '',
        survey_mode=args.survey_mode,
        output_file=xlsx_path_hint,
    )
    survey = agent.create_release_survey(request)

    from agents.gantt.state.release_survey_store import GanttReleaseSurveyStore
    store = GanttReleaseSurveyStore()
    stored_summary = store.save_survey(
        survey,
        summary_markdown=survey.summary_markdown,
    )
    print(f'  Stored survey ID: {stored_summary["survey_id"]}')
    print(f'  Stored in: {stored_summary["storage_dir"]}')

    if getattr(args, 'json', False):
        _print_json(survey.to_dict())
        sys.exit(0)

    json_path, md_path = _write_output_files(
        survey.to_dict(),
        survey.summary_markdown or '',
        output_base,
    )
    print(f'  Saved: {json_path}')
    print(f'  Saved: {md_path}')
    if survey.output_file:
        print(f'  Saved: {survey.output_file}')

    print(f'  Releases surveyed: {len(survey.releases_surveyed)}')
    print(f'  Total tickets: {survey.total_tickets}')
    print(f'  Done: {survey.done_count}')
    print(f'  In progress: {survey.in_progress_count}')
    print(f'  Remaining: {survey.remaining_count}')
    print(f'  Blocked: {survey.blocked_count}')
    sys.exit(0)


# ------------------------------------------------------------------
# release-survey-get — load stored survey
# ------------------------------------------------------------------

def cmd_release_survey_get(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.gantt.state.release_survey_store import GanttReleaseSurveyStore

    store = GanttReleaseSurveyStore()
    record = store.get_survey(args.survey_id, project_key=args.project)
    if not record:
        print(
            f'ERROR: Stored Gantt release survey not found: {args.survey_id}',
            file=sys.stderr,
        )
        sys.exit(1)

    survey = record['survey']
    summary = record['summary']
    summary_markdown = record['summary_markdown'] or str(
        survey.get('summary_markdown') or ''
    )

    print(f'  Project: {summary["project_key"]}')
    print(f'  Created at: {summary["created_at"]}')
    print(f'  Releases: {summary["release_count"]}')
    print(f'  Total tickets: {summary["total_tickets"]}')
    print(f'  Done: {summary["done_count"]}')
    print(f'  In progress: {summary["in_progress_count"]}')
    print(f'  Remaining: {summary["remaining_count"]}')
    print(f'  Blocked: {summary["blocked_count"]}')
    print(f'  Stored in: {summary["storage_dir"]}')

    if args.output:
        json_path, md_path = _write_output_files(
            survey,
            summary_markdown,
            args.output,
        )
        print(f'  Saved: {json_path}')
        print(f'  Saved: {md_path}')
    else:
        print('')
        print(summary_markdown or '(No summary markdown stored for this survey.)')

    sys.exit(0)


# ------------------------------------------------------------------
# release-survey-list — list stored surveys
# ------------------------------------------------------------------

def cmd_release_survey_list(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.gantt.state.release_survey_store import GanttReleaseSurveyStore

    store = GanttReleaseSurveyStore()
    surveys = store.list_surveys(project_key=args.project, limit=args.limit)
    if not surveys:
        if args.project:
            print(f'No stored release surveys found for project {args.project}.')
        else:
            print('No stored release surveys found.')
        sys.exit(0)

    print('')
    print(
        'SURVEY ID                            PROJECT  CREATED AT                  RELS  TOTAL  DONE  INPR  LEFT  BLKD'
    )
    print(
        '-----------------------------------  -------  --------------------------  ----  -----  ----  ----  ----  ----'
    )
    for item in surveys:
        print(
            f'{item["survey_id"]:<35}  '
            f'{item["project_key"]:<7}  '
            f'{item["created_at"]:<26}  '
            f'{item["release_count"]:>4}  '
            f'{item["total_tickets"]:>5}  '
            f'{item["done_count"]:>4}  '
            f'{item["in_progress_count"]:>4}  '
            f'{item["remaining_count"]:>4}  '
            f'{item["blocked_count"]:>4}'
        )

    print('')
    print(f'Total stored surveys: {len(surveys)}')
    sys.exit(0)


# ------------------------------------------------------------------
# poll — scheduled planning/monitoring loop
# ------------------------------------------------------------------

def cmd_poll(args: argparse.Namespace) -> None:
    _load_env(args)

    from agents.gantt.agent import GanttProjectPlannerAgent

    print(f'Running scheduled Gantt poller for {args.project}...')
    print(f'  Planning snapshots: yes')
    print(
        '  Release monitor: '
        f'{"yes" if (args.run_release_monitor or args.releases or args.scope_label) else "no"}'
    )
    print(f'  Release survey: {"yes" if args.run_release_survey else "no"}')
    if args.run_release_survey:
        print(f'  Release survey mode: {args.survey_mode}')
    print(f'  Poll interval: {args.poll_interval} seconds')
    print(
        '  Cycles: '
        f'{"continuous" if args.max_cycles == 0 else args.max_cycles}'
    )
    print(f'  Notify Shannon: {"yes" if args.notify_shannon else "no"}')
    print('')

    agent = GanttProjectPlannerAgent(project_key=args.project)
    result = agent.run_poller({
        'project_key': args.project,
        'run_planning': True,
        'run_release_monitor': bool(
            args.run_release_monitor or args.releases or args.scope_label
        ),
        'run_release_survey': bool(args.run_release_survey),
        'planning_horizon_days': args.planning_horizon,
        'limit': args.limit or 200,
        'include_done': args.include_done,
        'policy_profile': 'default',
        'evidence_paths': list(args.evidence or []),
        'releases': args.releases,
        'scope_label': args.scope_label,
        'include_gap_analysis': args.include_gap_analysis,
        'include_bug_report': args.include_bug_report,
        'include_velocity': args.include_velocity,
        'include_readiness': args.include_readiness,
        'compare_to_previous': args.compare_to_previous,
        'survey_mode': args.survey_mode,
        'persist': True,
        'notify_shannon': args.notify_shannon,
        'shannon_base_url': args.shannon_url,
        'interval_seconds': args.poll_interval,
        'max_cycles': args.max_cycles,
    })

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
        if task.get('task_type') == 'planning_snapshot':
            stored = task.get('stored', {})
            print(
                '  Latest planning snapshot: '
                f'{stored.get("snapshot_id") or task.get("snapshot", {}).get("snapshot_id", "")}'
            )
        if task.get('task_type') == 'release_monitor':
            stored = task.get('stored', {})
            print(
                '  Latest release report: '
                f'{stored.get("report_id") or task.get("report", {}).get("report_id", "")}'
            )
        if task.get('task_type') == 'release_survey':
            stored = task.get('stored', {})
            print(
                '  Latest release survey: '
                f'{stored.get("survey_id") or task.get("survey", {}).get("survey_id", "")}'
            )

    sys.exit(0 if result.get('ok', False) else 1)


# ------------------------------------------------------------------
# Argument parser
# ------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='gantt-agent',
        description='Gantt Project Planner agent CLI',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # --- snapshot ---
    p = sub.add_parser('snapshot', help='Create a planning snapshot')
    p.add_argument('--project', required=True, help='Jira project key')
    p.add_argument('--planning-horizon', type=int, default=90, metavar='DAYS',
                   dest='planning_horizon',
                   help='Planning horizon in days (default: 90)')
    p.add_argument('--limit', type=int, default=200, metavar='N',
                   help='Maximum issues to fetch (default: 200)')
    p.add_argument('--include-done', action='store_true', dest='include_done',
                   help='Include done/closed issues')
    p.add_argument('--evidence', nargs='*', default=None, metavar='FILE',
                   help='Evidence files (JSON, YAML, Markdown, text)')
    p.add_argument('--json', action='store_true', default=False,
                   help='Output raw JSON to stdout')
    p.add_argument('--output', default=None, metavar='FILE',
                   help='Output filename base')
    p.add_argument('--env', default=None, metavar='FILE',
                   help='Alternate .env file path')
    p.set_defaults(func=cmd_snapshot)

    # --- snapshot-get ---
    p = sub.add_parser('snapshot-get', help='Load a stored planning snapshot')
    p.add_argument('--snapshot-id', required=True, dest='snapshot_id',
                   help='Stored snapshot ID')
    p.add_argument('--project', default=None, help='Optional project filter')
    p.add_argument('--output', default=None, metavar='FILE',
                   help='Export to files (JSON + Markdown)')
    p.set_defaults(func=cmd_snapshot_get)

    # --- snapshot-list ---
    p = sub.add_parser('snapshot-list', help='List stored planning snapshots')
    p.add_argument('--project', default=None, help='Optional project filter')
    p.add_argument('--limit', type=int, default=None, metavar='N',
                   help='Maximum snapshots to list')
    p.set_defaults(func=cmd_snapshot_list)

    # --- release-monitor ---
    p = sub.add_parser('release-monitor', help='Create a release health report')
    p.add_argument('--project', required=True, help='Jira project key')
    p.add_argument('--releases', default=None, metavar='CSV',
                   help='Comma-separated release names')
    p.add_argument('--scope-label', default=None, metavar='LABEL',
                   dest='scope_label',
                   help='Optional Jira scope label filter')
    p.add_argument('--no-gap-analysis', action='store_false',
                   dest='include_gap_analysis',
                   help='Disable roadmap gap analysis')
    p.add_argument('--no-bug-report', action='store_false',
                   dest='include_bug_report',
                   help='Disable bug status/priority summary')
    p.add_argument('--no-velocity', action='store_false',
                   dest='include_velocity',
                   help='Disable velocity metrics')
    p.add_argument('--no-readiness', action='store_false',
                   dest='include_readiness',
                   help='Disable readiness assessment')
    p.add_argument('--no-compare-previous', action='store_false',
                   dest='compare_to_previous',
                   help='Disable previous-report delta comparison')
    p.add_argument('--json', action='store_true', default=False,
                   help='Output raw JSON to stdout')
    p.add_argument('--output', default=None, metavar='FILE',
                   help='Output filename base')
    p.add_argument('--env', default=None, metavar='FILE',
                   help='Alternate .env file path')
    p.set_defaults(func=cmd_release_monitor)

    # --- release-monitor-get ---
    p = sub.add_parser('release-monitor-get', help='Load a stored release report')
    p.add_argument('--report-id', required=True, dest='report_id',
                   help='Stored report ID')
    p.add_argument('--project', default=None, help='Optional project filter')
    p.add_argument('--output', default=None, metavar='FILE',
                   help='Export to files (JSON + Markdown)')
    p.set_defaults(func=cmd_release_monitor_get)

    # --- release-monitor-list ---
    p = sub.add_parser('release-monitor-list', help='List stored release reports')
    p.add_argument('--project', default=None, help='Optional project filter')
    p.add_argument('--limit', type=int, default=None, metavar='N',
                   help='Maximum reports to list')
    p.set_defaults(func=cmd_release_monitor_list)

    # --- release-survey ---
    p = sub.add_parser('release-survey', help='Create a release execution survey')
    p.add_argument('--project', required=True, help='Jira project key')
    p.add_argument('--releases', default=None, metavar='CSV',
                   help='Comma-separated release names')
    p.add_argument('--scope-label', default=None, metavar='LABEL',
                   dest='scope_label',
                   help='Optional Jira scope label filter')
    p.add_argument('--survey-mode', default='feature-dev', metavar='MODE',
                   dest='survey_mode',
                   choices=['feature-dev', 'bug'],
                   help='Survey mode: feature-dev (default) or bug')
    p.add_argument('--json', action='store_true', default=False,
                   help='Output raw JSON to stdout')
    p.add_argument('--output', default=None, metavar='FILE',
                   help='Output filename base')
    p.add_argument('--env', default=None, metavar='FILE',
                   help='Alternate .env file path')
    p.set_defaults(func=cmd_release_survey)

    # --- release-survey-get ---
    p = sub.add_parser('release-survey-get', help='Load a stored release survey')
    p.add_argument('--survey-id', required=True, dest='survey_id',
                   help='Stored survey ID')
    p.add_argument('--project', default=None, help='Optional project filter')
    p.add_argument('--output', default=None, metavar='FILE',
                   help='Export to files (JSON + Markdown)')
    p.set_defaults(func=cmd_release_survey_get)

    # --- release-survey-list ---
    p = sub.add_parser('release-survey-list', help='List stored release surveys')
    p.add_argument('--project', default=None, help='Optional project filter')
    p.add_argument('--limit', type=int, default=None, metavar='N',
                   help='Maximum surveys to list')
    p.set_defaults(func=cmd_release_survey_list)

    # --- poll ---
    p = sub.add_parser('poll', help='Scheduled planning/monitoring loop')
    p.add_argument('--project', required=True, help='Jira project key')
    p.add_argument('--planning-horizon', type=int, default=90, metavar='DAYS',
                   dest='planning_horizon',
                   help='Planning horizon in days (default: 90)')
    p.add_argument('--releases', default=None, metavar='CSV',
                   help='Comma-separated release names')
    p.add_argument('--scope-label', default=None, metavar='LABEL',
                   dest='scope_label',
                   help='Optional Jira scope label filter')
    p.add_argument('--survey-mode', default='feature-dev', metavar='MODE',
                   dest='survey_mode',
                   help='Release survey mode (default: feature-dev)')
    p.add_argument('--run-release-monitor', action='store_true',
                   dest='run_release_monitor',
                   help='Include release-monitor work even when --releases is omitted')
    p.add_argument('--run-release-survey', action='store_true',
                   dest='run_release_survey',
                   help='Include release-survey work')
    p.add_argument('--include-done', action='store_true', dest='include_done',
                   help='Include done/closed issues')
    p.add_argument('--no-gap-analysis', action='store_false',
                   dest='include_gap_analysis',
                   help='Disable roadmap gap analysis')
    p.add_argument('--no-bug-report', action='store_false',
                   dest='include_bug_report',
                   help='Disable bug status/priority summary')
    p.add_argument('--no-velocity', action='store_false',
                   dest='include_velocity',
                   help='Disable velocity metrics')
    p.add_argument('--no-readiness', action='store_false',
                   dest='include_readiness',
                   help='Disable readiness assessment')
    p.add_argument('--no-compare-previous', action='store_false',
                   dest='compare_to_previous',
                   help='Disable previous-report delta comparison')
    p.add_argument('--evidence', nargs='*', default=None, metavar='FILE',
                   help='Evidence files (JSON, YAML, Markdown, text)')
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
    p.add_argument('--limit', type=int, default=200, metavar='N',
                   help='Maximum issues to fetch (default: 200)')
    p.add_argument('--output', default=None, metavar='FILE',
                   help='Output filename base')
    p.add_argument('--env', default=None, metavar='FILE',
                   help='Alternate .env file path')
    p.set_defaults(func=cmd_poll)

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
