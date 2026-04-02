##########################################################################################
#
# Module: agents/hemingway/cli.py
#
# Description: Standalone CLI for Hemingway Documentation agent.
#              Provides direct access to documentation generation, impact analysis,
#              and review-gated publication to repo Markdown and Confluence.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from typing import Any, Dict, List

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_json(data: Dict[str, Any]) -> None:
    '''Print a dict as indented JSON to stdout.'''
    print(json.dumps(data, indent=2, default=str))


def _write_record_files(
    record: Dict[str, Any],
    review_session: Dict[str, Any],
    output_base: str,
) -> tuple:
    '''
    Write Hemingway record JSON + Markdown + review-session JSON + patch drafts.
    Mirrors _write_hemingway_record_files() from agent_cli.py so the CLI is
    self-contained.
    '''
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() == '.md':
        output_root = output_root or str(
            record.get('doc_id') or 'hemingway_record'
        ).lower()
    elif output_ext.lower() != '.json':
        output_root = output_base

    json_path = output_root + '.json'
    md_path = output_root + '.md'
    review_path = output_root + '_review.json'
    patch_dir = output_root + '_patches'

    os.makedirs(os.path.dirname(json_path) or '.', exist_ok=True)
    os.makedirs(patch_dir, exist_ok=True)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=2, default=str)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(str(record.get('summary_markdown') or ''))

    with open(review_path, 'w', encoding='utf-8') as f:
        json.dump(review_session or {}, f, indent=2, default=str)

    patch_paths: List[str] = []
    for index, patch in enumerate(record.get('patches') or [], start=1):
        title = str(patch.get('title') or patch.get('target_ref') or f'patch-{index}')
        slug = re.sub(r'[^a-z0-9]+', '-', title.casefold()).strip('-') or f'patch-{index}'
        draft_path = os.path.join(
            patch_dir,
            f'{index:02d}_{str(patch.get("patch_id") or index)}_{slug}.md',
        )
        with open(draft_path, 'w', encoding='utf-8') as f:
            f.write(str(patch.get('content_markdown') or ''))
        patch_paths.append(draft_path)

    return json_path, md_path, review_path, patch_paths


def _write_publication_file(
    publications: List[Any],
    output_base: str,
) -> str:
    '''
    Write Hemingway publication results JSON and return its path.
    Mirrors _write_hemingway_publication_file() from agent_cli.py.
    '''
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() not in ('.json', '.md'):
        output_root = output_base

    publications_path = output_root + '_publications.json'
    payload = [
        pub.to_dict() if hasattr(pub, 'to_dict') else pub
        for pub in publications
    ]

    os.makedirs(os.path.dirname(publications_path) or '.', exist_ok=True)
    with open(publications_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, default=str)

    return publications_path


# ---------------------------------------------------------------------------
# Subcommand: generate
# ---------------------------------------------------------------------------

def cmd_generate(args: argparse.Namespace) -> None:
    '''
    Generate source-grounded documentation via HemingwayDocumentationAgent.
    Mirrors _workflow_hemingway_generate() from agent_cli.py as a standalone CLI.
    '''
    from dotenv import load_dotenv
    load_dotenv(args.env if hasattr(args, 'env') and args.env else None)

    from agents.hemingway.agent import HemingwayDocumentationAgent
    from agents.hemingway.state.record_store import HemingwayRecordStore

    use_json = getattr(args, 'json', False)

    # -- Step 1: plan documentation ------------------------------------------
    if not use_json:
        print('=' * 60)
        print('HYPATIA: generate')
        print('=' * 60)
        print()
        print(f'Document title : {args.doc_title or args.confluence_title or "auto"}')
        print(f'Document class : {args.doc_type}')
        print(f'Project        : {args.project or "n/a"}')
        print(f'Source files   : {len(args.docs or [])}')
        print(f'Publish now    : {"yes" if args.execute else "no"}')
        print()
        print('Step 1/4: Generating documentation plan...')

    agent = HemingwayDocumentationAgent(project_key=args.project)
    request = {
        'title': args.doc_title or '',
        'doc_type': args.doc_type,
        'project_key': args.project or '',
        'summary': args.doc_summary or '',
        'source_paths': list(args.docs or []),
        'evidence_paths': list(args.evidence or []),
        'target_file': args.target_file,
        'confluence_title': args.confluence_title,
        'confluence_page': args.confluence_page,
        'confluence_space': args.confluence_space,
        'confluence_parent_id': args.confluence_parent_id,
        'version_message': args.version_message,
        'validation_profile': args.doc_validation,
    }

    record, review_session = agent.plan_documentation(
        agent._normalize_request(request)
    )

    # -- Step 2: persist record ----------------------------------------------
    if not use_json:
        print('Step 2/4: Persisting documentation record...')

    store = HemingwayRecordStore()
    stored_summary = store.save_record(record, summary_markdown=record.summary_markdown)

    if not use_json:
        print(f'  Stored document ID: {stored_summary["doc_id"]}')
        print(f'  Stored in: {stored_summary["storage_dir"]}')

    # -- Step 3: write artifact files ----------------------------------------
    if not use_json:
        print('Step 3/4: Writing documentation artifacts...')

    output_base = args.output or f'{record.doc_id}_hemingway_record.json'
    json_path, md_path, review_path, patch_paths = _write_record_files(
        record.to_dict(),
        review_session.to_dict(),
        output_base,
    )

    if not use_json:
        print(f'  Saved: {json_path}')
        print(f'  Saved: {md_path}')
        print(f'  Saved: {review_path}')
        if patch_paths:
            print(f'  Saved patch drafts: {len(patch_paths)}')

    created_files = [
        (stored_summary['json_path'], 'stored documentation record JSON'),
        (stored_summary['markdown_path'], 'stored documentation summary Markdown'),
        (json_path, 'exported documentation record JSON'),
        (md_path, 'exported documentation summary Markdown'),
        (review_path, 'review session JSON'),
    ]
    created_files.extend(
        (path, 'documentation patch draft Markdown')
        for path in patch_paths
    )

    # -- Step 4: review / publication summary --------------------------------
    if not use_json:
        print('Step 4/4: Review and publication summary...')
        print(f'  Patches: {len(record.patches)}')
        print(f'  Validation status: {"valid" if record.validation.get("valid") else "blocked"}')
        print(f'  Warnings: {len(record.warnings)}')

    if args.execute:
        if not record.validation.get('valid'):
            msg = 'ERROR: Hemingway record has blocking validation issues; refusing to publish.'
            if use_json:
                _print_json({'error': msg})
            else:
                print(msg)
            sys.exit(1)

        agent.review_agent.approve_all(review_session)
        publications = agent.publish_approved(review_session)
        store.record_publications(record.doc_id, publications)

        publications_path = _write_publication_file(publications, output_base)
        created_files.append((publications_path, 'publication results JSON'))

        if not use_json:
            published_count = sum(1 for item in publications if item.status == 'published')
            print(f'  Published targets: {published_count}')
            print(f'  Publication log: {publications_path}')

    # -- summary output ------------------------------------------------------
    if use_json:
        _print_json({
            'doc_id': record.doc_id,
            'title': record.title,
            'doc_type': record.doc_type,
            'project_key': record.project_key,
            'patch_count': len(record.patches),
            'warning_count': len(record.warnings),
            'validation_valid': bool(record.validation.get('valid')),
            'execute': args.execute,
            'created_files': [
                {'path': path, 'description': desc}
                for path, desc in created_files
            ],
        })
    else:
        print()
        print('-' * 60)
        print('Created files:')
        for path, desc in created_files:
            print(f'  {path}  ({desc})')
        print('-' * 60)

    sys.exit(0)


# ---------------------------------------------------------------------------
# Subcommand: confluence-publish
# ---------------------------------------------------------------------------

def cmd_confluence_publish(args: argparse.Namespace) -> None:
    '''
    Publish a Markdown file to Confluence with optional diagram rendering.
    Uses confluence tools for create/update/append/section-update operations.
    '''
    from dotenv import load_dotenv
    load_dotenv(args.env if hasattr(args, 'env') and args.env else None)

    # Lazy imports — keep CLI startup fast
    from tools.confluence_tools import (
        create_confluence_page,
        update_confluence_page,
        append_to_confluence_page,
        update_confluence_section,
    )

    use_json = getattr(args, 'json', False)
    dry_run = not args.execute
    render_diagrams = not args.no_diagrams

    # Map operation to tool function
    op_map = {
        'create': create_confluence_page,
        'update': update_confluence_page,
        'append': append_to_confluence_page,
        'update_section': update_confluence_section,
    }
    tool_fn = op_map.get(args.operation)
    if tool_fn is None:
        msg = f'Unknown operation: {args.operation}'
        if use_json:
            _print_json({'error': msg})
        else:
            print(msg, file=sys.stderr)
        sys.exit(1)

    if not use_json:
        print('=' * 60)
        print('HYPATIA: confluence-publish')
        print('=' * 60)
        print()
        print(f'Input file     : {args.input_file}')
        print(f'Title          : {args.title}')
        print(f'Operation      : {args.operation}')
        print(f'Space          : {args.space or "default"}')
        print(f'Render diagrams: {"yes" if render_diagrams else "no"}')
        print(f'Dry run        : {"yes" if dry_run else "no"}')
        print()

    # Build keyword arguments based on operation
    kwargs: Dict[str, Any] = {
        'input_file': args.input_file,
        'dry_run': dry_run,
    }

    if args.operation == 'create':
        kwargs['title'] = args.title
        if args.space:
            kwargs['space'] = args.space
        if args.parent_id:
            kwargs['parent_id'] = args.parent_id
        if args.version_message:
            kwargs['version_message'] = args.version_message
    elif args.operation in ('update', 'append'):
        kwargs['page_id_or_title'] = args.page_id or args.title
        if args.space:
            kwargs['space'] = args.space
        if args.version_message:
            kwargs['version_message'] = args.version_message
    elif args.operation == 'update_section':
        kwargs['page_id_or_title'] = args.page_id or args.title
        kwargs['heading'] = args.heading or ''
        if args.space:
            kwargs['space'] = args.space
        if args.version_message:
            kwargs['version_message'] = args.version_message

    # Execute the tool function
    result = tool_fn(**kwargs)

    # Extract result data from ToolResult
    if hasattr(result, 'data'):
        data = result.data if result.data is not None else {}
    elif isinstance(result, dict):
        data = result
    else:
        data = {}

    if use_json:
        _print_json({
            'operation': args.operation,
            'title': args.title,
            'input_file': args.input_file,
            'dry_run': dry_run,
            'render_diagrams': render_diagrams,
            'result': data,
        })
    else:
        if hasattr(result, 'success') and not result.success:
            print(f'ERROR: {result.error or "unknown error"}', file=sys.stderr)
            sys.exit(1)

        print('Result:')
        if isinstance(data, dict):
            for key, value in data.items():
                print(f'  {key}: {value}')
        else:
            print(f'  {data}')
        print()
        if dry_run:
            print('This was a dry-run preview. Use --execute to publish.')

    sys.exit(0)


# ---------------------------------------------------------------------------
# Subcommand: list
# ---------------------------------------------------------------------------

def cmd_list(args: argparse.Namespace) -> None:
    '''List stored Hemingway documentation records.'''
    from dotenv import load_dotenv
    load_dotenv()

    from agents.hemingway.state.record_store import HemingwayRecordStore

    store = HemingwayRecordStore()
    records = store.list_records(limit=args.limit)

    # Optional project filter (store.list_records does not filter by project)
    if args.project:
        records = [
            r for r in records
            if str(r.get('project_key') or '') == args.project
        ]

    use_json = getattr(args, 'json', False)
    if use_json:
        _print_json({'records': records, 'count': len(records)})
    else:
        if not records:
            print('No stored documentation records found.')
            sys.exit(0)

        print(f'{"doc_id":<12} {"doc_type":<24} {"title":<36} {"created_at"}')
        print('-' * 100)
        for r in records:
            print(
                f'{r.get("doc_id", ""):<12} '
                f'{r.get("doc_type", ""):<24} '
                f'{r.get("title", ""):<36} '
                f'{r.get("created_at", "")}'
            )

    sys.exit(0)


# ---------------------------------------------------------------------------
# Subcommand: get
# ---------------------------------------------------------------------------

def cmd_get(args: argparse.Namespace) -> None:
    '''Load a stored Hemingway documentation record by ID.'''
    from dotenv import load_dotenv
    load_dotenv()

    from agents.hemingway.state.record_store import HemingwayRecordStore

    store = HemingwayRecordStore()
    result = store.get_record(args.doc_id)

    if result is None:
        msg = f'No documentation record found for doc_id={args.doc_id}'
        if getattr(args, 'json', False):
            _print_json({'error': msg})
        else:
            print(msg)
        sys.exit(1)

    # Optional project filter
    record_project = str(result.get('record', {}).get('project_key') or '')
    if args.project and record_project != args.project:
        msg = (
            f'Record {args.doc_id} belongs to project {record_project!r}, '
            f'not {args.project!r}'
        )
        if getattr(args, 'json', False):
            _print_json({'error': msg})
        else:
            print(msg)
        sys.exit(1)

    use_json = getattr(args, 'json', False)

    # Export to file if requested
    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result['record'], f, indent=2, default=str)
        if not use_json:
            print(f'Exported record {args.doc_id} to {args.output}')
        else:
            _print_json({
                'doc_id': args.doc_id,
                'exported_to': args.output,
            })
        sys.exit(0)

    if use_json:
        _print_json(result['record'])
    else:
        summary = result.get('summary_markdown') or ''
        if summary:
            print(summary)
        else:
            _print_json(result['record'])

    sys.exit(0)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def register_subcommands(subparsers) -> None:
    '''Add Hemingway subcommands to an argparse subparsers group.'''

    # --- generate -----------------------------------------------------------
    p = subparsers.add_parser(
        'generate',
        help='Generate source-grounded documentation (primary workflow)',
    )
    p.add_argument('--doc-title', default=None, help='Document title')
    p.add_argument(
        '--doc-type',
        default='engineering_reference',
        choices=['as_built', 'engineering_reference', 'how_to',
                 'release_note_support', 'user_guide'],
        help='Document class (default: engineering_reference)',
    )
    p.add_argument('--doc-summary', default=None, help='Purpose/scope summary')
    p.add_argument('--docs', nargs='*', default=[], help='Source documents / datasheets')
    p.add_argument('--evidence', nargs='*', default=[], help='Evidence files (JSON, YAML, Markdown)')
    p.add_argument('--target-file', default=None, help='Repo-owned Markdown target')
    p.add_argument('--confluence-title', default=None, help='Confluence page title')
    p.add_argument('--confluence-page', default=None, help='Confluence page ID or title to update')
    p.add_argument('--confluence-space', default=None, help='Confluence space key or ID')
    p.add_argument('--confluence-parent-id', default=None, help='Parent page ID for new pages')
    p.add_argument('--version-message', default=None, help='Confluence version message')
    p.add_argument(
        '--doc-validation',
        default='default',
        choices=['default', 'strict', 'sphinx'],
        help='Validation profile (default: default)',
    )
    p.add_argument(
        '--execute',
        action='store_true',
        default=False,
        help='Actually publish approved changes (default: dry-run preview)',
    )
    p.add_argument('--project', '-p', default=None, help='Jira project key (optional)')
    p.add_argument('--output', default=None, help='Output filename')
    p.add_argument('--json', action='store_true', default=False, help='JSON output format')
    p.add_argument('--env', default=None, help='Alternate .env file')
    p.set_defaults(func=cmd_generate)

    # --- confluence-publish --------------------------------------------------
    p = subparsers.add_parser(
        'confluence-publish',
        help='Publish a Markdown file to Confluence with diagram rendering',
    )
    p.add_argument('--input-file', required=True, help='Path to Markdown file')
    p.add_argument('--title', required=True, help='Confluence page title')
    p.add_argument('--space', default=None, help='Confluence space key or ID')
    p.add_argument('--parent-id', default=None, help='Parent page ID (for create)')
    p.add_argument('--page-id', default=None, help='Page ID or title (for update/append/section-update)')
    p.add_argument(
        '--operation',
        default='create',
        choices=['create', 'update', 'append', 'update_section'],
        help='Publish operation (default: create)',
    )
    p.add_argument('--heading', default=None, help='Section heading (for update_section operation)')
    p.add_argument('--version-message', default=None, help='Version comment')
    p.add_argument('--no-diagrams', action='store_true', default=False, help='Skip diagram rendering')
    p.add_argument(
        '--execute',
        action='store_true',
        default=False,
        help='Actually publish (default: dry-run preview)',
    )
    p.add_argument('--json', action='store_true', default=False, help='JSON output')
    p.add_argument('--env', default=None, help='Alternate .env file')
    p.set_defaults(func=cmd_confluence_publish)

    # --- list ---------------------------------------------------------------
    p = subparsers.add_parser('list', help='List stored documentation records')
    p.add_argument('--project', '-p', default=None, help='Filter by project')
    p.add_argument('--limit', type=int, default=20, help='Max records (default: 20)')
    p.add_argument('--json', action='store_true', default=False, help='JSON output')
    p.set_defaults(func=cmd_list)

    # --- get ----------------------------------------------------------------
    p = subparsers.add_parser('get', help='Load a stored documentation record')
    p.add_argument('--doc-id', required=True, help='Document record ID')
    p.add_argument('--project', '-p', default=None, help='Project filter')
    p.add_argument('--output', default=None, help='Export to file')
    p.add_argument('--json', action='store_true', default=False, help='JSON output')
    p.set_defaults(func=cmd_get)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='hemingway-agent',
        description='Hemingway Documentation agent CLI',
    )
    sub = parser.add_subparsers(dest='command', required=True)
    register_subcommands(sub)
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    '''Parse arguments, load environment, and dispatch to the appropriate subcommand.'''
    parser = build_parser()
    args = parser.parse_args()

    # Load alternate .env if specified on generate subcommand
    if hasattr(args, 'env') and args.env:
        from dotenv import load_dotenv
        load_dotenv(args.env)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print('\nInterrupted.')
        sys.exit(130)
    except Exception as exc:
        log.error(f'Hemingway CLI error: {exc}', exc_info=True)
        if getattr(args, 'json', False):
            _print_json({'error': str(exc)})
        else:
            print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
