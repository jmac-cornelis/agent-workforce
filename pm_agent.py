#!/usr/bin/env python3
##########################################################################################
#
# Script name: pm_agent.py
#
# Description: CLI entry point for Cornelis Agent Pipeline.
#              Provides commands for release planning workflow.
#
# Author: Cornelis Networks
#
# Usage:
#   python pm_agent.py --help
#   python pm_agent.py --plan --project PROJ --roadmap slides.pptx
#   python pm_agent.py --analyze --project PROJ
#   python pm_agent.py --resume --session abc123
#
##########################################################################################

import argparse
import json
import logging
import re
import sys
import os
from datetime import date
from typing import Any, cast

from dotenv import load_dotenv

from core.utils import output, validate_and_repair_csv

import jira_utils
import excel_utils

jira_api = cast(Any, jira_utils)

# Load environment variables
load_dotenv()

# ****************************************************************************************
# Global data and configuration
# ****************************************************************************************

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))
log.setLevel(logging.DEBUG)

# File handler for logging
fh = logging.FileHandler('cornelis_agent.log', mode='w')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)-15s [%(funcName)25s:%(lineno)-5s] %(levelname)-8s %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)

# Output control
_quiet_mode = False


# ****************************************************************************************
# Command handlers
# ****************************************************************************************

def cmd_plan(args):
    '''
    Run the release planning workflow.
    '''
    log.debug(f'cmd_plan(project={args.project}, plan_mode={args.plan_mode})')
    
    from agents.orchestrator import ReleasePlanningOrchestrator
    from state.session import SessionManager
    from state.persistence import get_persistence
    
    output('')
    output('=' * 60)
    output('CORNELIS RELEASE PLANNING AGENT')
    output('=' * 60)
    output('')
    
    # Set up persistence
    persistence = None
    if args.save_session:
        persistence = get_persistence(args.persistence_format)
    
    session_manager = SessionManager(persistence=persistence)
    
    # Collect input files
    roadmap_files = []
    if args.roadmap:
        roadmap_files.extend(args.roadmap)
    
    # Create orchestrator and run
    orchestrator = ReleasePlanningOrchestrator()
    
    output(f'Project: {args.project}')
    output(f'Roadmap files: {len(roadmap_files)}')
    if args.org_chart:
        output(f'Org chart: {args.org_chart}')
    output('')
    
    # Run the workflow
    result = orchestrator.run({
        'project_key': args.project,
        'roadmap_files': roadmap_files,
        'org_chart_file': args.org_chart,
        'mode': args.plan_mode
    })
    
    if result.success:
        output(result.content)
        
        # Save session if requested
        if args.save_session and orchestrator.state:
            from state.session import SessionState
            session = SessionState(
                project_key=args.project,
                roadmap_files=roadmap_files,
                org_chart_file=args.org_chart,
                roadmap_data=orchestrator.state.roadmap_data,
                jira_state=orchestrator.state.jira_state,
                release_plan=orchestrator.state.release_plan,
                current_step=orchestrator.state.current_step
            )
            session_manager.current_session = session
            session_manager.save_session()
            output(f'\nSession saved: {session.session_id}')
    else:
        output(f'ERROR: {result.error}')
        return 1
    
    return 0


def cmd_analyze(args):
    '''
    Analyze Jira project state.
    '''
    log.debug(f'cmd_analyze(project={args.project}, quick={args.quick})')
    
    from agents.jira_analyst import JiraAnalystAgent
    
    output('')
    output('=' * 60)
    output('JIRA PROJECT ANALYSIS')
    output('=' * 60)
    output('')
    
    analyst = JiraAnalystAgent(project_key=args.project)
    
    if args.quick:
        # Quick analysis without LLM
        analysis = analyst.analyze_project(args.project)
        
        output(f"Project: {analysis.get('project_key')}")
        output('')
        
        summary = analysis.get('summary', {})
        output(f"Releases: {summary.get('total_releases', 0)} ({summary.get('unreleased_count', 0)} unreleased)")
        output(f"Components: {summary.get('component_count', 0)}")
        output(f"Issue Types: {summary.get('issue_type_count', 0)}")
        
        if analysis.get('errors'):
            output('\nErrors:')
            for error in analysis['errors']:
                output(f'  ! {error}')
    else:
        # Full LLM-powered analysis
        result = analyst.run(args.project)
        
        if result.success:
            output(result.content)
        else:
            output(f'ERROR: {result.error}')
            return 1
    
    return 0


def cmd_vision(args):
    '''
    Analyze roadmap files.
    '''
    log.debug(f'cmd_vision(files={args.vision})')
    
    from agents.vision_analyzer import VisionAnalyzerAgent
    
    output('')
    output('=' * 60)
    output('ROADMAP ANALYSIS')
    output('=' * 60)
    output('')
    
    analyzer = VisionAnalyzerAgent()
    
    if len(args.vision) == 1:
        result = analyzer.analyze_file(args.vision[0])
    else:
        result = analyzer.analyze_multiple(args.vision)
    
    if 'error' in result:
        output(f'ERROR: {result["error"]}')
        return 1
    
    output(f"Files analyzed: {len(result.get('files_analyzed', [args.vision[0]]))}")
    output(f"Releases found: {len(result.get('releases', []))}")
    output(f"Features found: {len(result.get('features', []))}")
    output(f"Timeline items: {len(result.get('timeline', []))}")
    
    if result.get('releases'):
        output('\nReleases:')
        for r in result['releases'][:10]:
            output(f"  - {r.get('version', 'Unknown')}")
    
    if result.get('features'):
        output('\nFeatures:')
        for f in result['features'][:10]:
            output(f"  - {f.get('text', '')[:60]}")
    
    return 0


def cmd_sessions(args):
    '''
    List or manage sessions.
    '''
    log.debug(f'cmd_sessions(list={args.list_sessions}, delete={args.delete_session})')
    
    from state.session import SessionManager
    from state.persistence import get_persistence
    
    persistence = get_persistence(args.persistence_format)
    session_manager = SessionManager(persistence=persistence)
    
    if args.delete_session:
        if session_manager.delete_session(args.delete_session):
            output(f'Deleted session: {args.delete_session}')
        else:
            output(f'Failed to delete session: {args.delete_session}')
        return 0
    
    # List sessions
    sessions = session_manager.list_sessions()
    
    output('')
    output('=' * 60)
    output('SAVED SESSIONS')
    output('=' * 60)
    output('')
    
    if not sessions:
        output('No saved sessions found.')
        return 0
    
    output(f'{"ID":<10} {"Project":<12} {"Step":<15} {"Updated":<20}')
    output('-' * 60)
    
    for session in sessions:
        output(f"{session['session_id']:<10} {session.get('project_key', 'N/A'):<12} {session.get('current_step', 'N/A'):<15} {session.get('updated_at', 'N/A')[:19]:<20}")
    
    output('')
    output(f'Total: {len(sessions)} sessions')
    
    return 0


def cmd_build_excel_map(args):
    ticket_keys = [k.upper() for k in args.ticket_keys]
    hierarchy_depth = args.hierarchy
    limit = getattr(args, 'limit', None)

    if getattr(args, 'output', None):
        output_file = args.output
    elif len(ticket_keys) == 1:
        output_file = f'{ticket_keys[0]}.xlsx'
    else:
        output_file = f'{"_".join(ticket_keys)}.xlsx'

    keep_intermediates = getattr(args, 'keep_intermediates', False)

    if not output_file.endswith('.xlsx'):
        output_file = f'{output_file}.xlsx'

    log.debug(f'cmd_build_excel_map(ticket_keys={ticket_keys}, hierarchy={args.hierarchy}, limit={limit}, output={output_file})')

    output('')
    output('=' * 60)
    output('BUILD EXCEL MAP')
    output('=' * 60)
    output(f'Root ticket(s):  {", ".join(ticket_keys)}')
    output(f'Hierarchy depth: {hierarchy_depth}')
    output(f'Output file:     {output_file}')
    if limit:
        output(f'Limit:           {limit}')
    output('')

    try:
        result = excel_utils.build_excel_map(
            ticket_keys=ticket_keys,
            hierarchy_depth=hierarchy_depth,
            limit=limit,
            output_file=output_file,
            project_key=getattr(args, 'project', None),
            keep_intermediates=keep_intermediates,
            output_callback=output,
        )

        if keep_intermediates:
            temp_dir = result.get('temp_dir')
            temp_files = result.get('temp_files', [])
            if temp_dir:
                output(f'Intermediate files kept in: {temp_dir}')
                for temp_file in temp_files:
                    output(f'  {temp_file}')

        return 0

    except Exception as e:
        log.error(f'Failed to build Excel map: {e}', exc_info=True)
        output(f'ERROR: {e}')
        return 1


def _extract_and_save_files(response_text):
    '''
    Parse fenced code blocks from an LLM response and save any that specify
    a filename.

    Recognised patterns (the filename line immediately precedes the opening
    fence or is embedded in the fence info-string):

        **`path/to/file.ext`**          (bold-backtick markdown)
        `path/to/file.ext`              (backtick markdown)
        path/to/file.ext                (bare path on its own line)
        ```lang:path/to/file.ext        (colon-separated in info-string)
        ```path/to/file.ext             (info-string IS the path)

    Returns a list of (filepath, content) tuples that were written.
    '''
    saved = []

    # ---- Strategy 1: filename on the line before the opening fence ----------
    # Matches patterns like:
    #   **`somefile.py`**
    #   `somefile.py`
    #   somefile.py
    # followed by ```<optional lang>\n ... \n```
    pattern_pre = re.compile(
        r'(?:^|\n)'                          # start of string or newline
        r'[ \t]*'                            # optional leading whitespace
        r'(?:\*{0,2}`?)'                     # optional bold / backtick prefix
        r'([\w][\w./\\-]*\.\w+)'             # captured filename (must have extension)
        r'(?:`?\*{0,2})'                     # optional backtick / bold suffix
        r'[ \t]*\n'                          # end of filename line
        r'```[^\n]*\n'                       # opening fence (``` with optional info)
        r'(.*?)'                             # captured content (non-greedy)
        r'\n```',                            # closing fence
        re.DOTALL,
    )

    for m in pattern_pre.finditer(response_text):
        filepath = m.group(1).strip()
        content = m.group(2)
        if filepath and content is not None:
            saved.append((filepath, content))

    # ---- Strategy 2: filename embedded in the info-string -------------------
    # Matches ```lang:path/to/file.ext  or  ```path/to/file.ext
    # Only used for blocks NOT already captured by Strategy 1.
    pattern_info = re.compile(
        r'```'
        r'(?:[\w]+:)?'                       # optional lang: prefix
        r'([\w][\w./\\-]*\.\w+)'             # captured filename
        r'[ \t]*\n'
        r'(.*?)'                             # captured content
        r'\n```',
        re.DOTALL,
    )

    # Build a set of already-captured content spans to avoid duplicates
    captured_spans = {(m.start(), m.end()) for m in pattern_pre.finditer(response_text)}

    for m in pattern_info.finditer(response_text):
        # Skip if this block overlaps with one already captured
        if any(m.start() >= cs[0] and m.end() <= cs[1] for cs in captured_spans):
            continue
        filepath = m.group(1).strip()
        content = m.group(2)
        if filepath and content is not None:
            saved.append((filepath, content))

    # ---- Strategy 2b: filename as first line inside the code block ----------
    # Handles the pattern where the LLM places the filename as the first
    # non-empty line *inside* the fenced block (not on the fence line and
    # not on a preceding line).  Example:
    #   ```
    #   my_report.csv
    #   col1,col2,col3
    #   ...
    #   ```
    # We recognise a first line as a filename if it matches word.ext with a
    # known file extension and contains no spaces (to avoid false positives
    # on prose or data lines).
    KNOWN_EXTENSIONS = {
        'csv', 'json', 'xml', 'yaml', 'yml', 'md', 'txt', 'sql', 'html',
        'toml', 'ini', 'py', 'js', 'ts', 'sh', 'cfg', 'log', 'xlsx',
    }
    pattern_inner_name = re.compile(
        r'```[^\n]*\n'                       # opening fence (``` with optional info)
        r'(.*?)'                             # captured full content
        r'\n```',                            # closing fence
        re.DOTALL,
    )
    # Build set of already-captured spans (from Strategies 1 & 2)
    captured_spans_2b = set()
    for m in pattern_pre.finditer(response_text):
        captured_spans_2b.add((m.start(), m.end()))
    for m in pattern_info.finditer(response_text):
        if not any(m.start() >= cs[0] and m.end() <= cs[1] for cs in captured_spans_2b):
            captured_spans_2b.add((m.start(), m.end()))

    for m in pattern_inner_name.finditer(response_text):
        # Skip blocks already captured by earlier strategies
        if any(m.start() >= cs[0] and m.end() <= cs[1] for cs in captured_spans_2b):
            continue
        content = m.group(1)
        if not content or not content.strip():
            continue
        # Check if the first non-empty line looks like a filename
        lines = content.split('\n')
        first_line = ''
        first_line_idx = 0
        for i, line in enumerate(lines):
            if line.strip():
                first_line = line.strip()
                first_line_idx = i
                break
        if not first_line:
            continue
        # A filename candidate: no spaces, has a dot, extension is known
        if ' ' not in first_line and '.' in first_line:
            ext = first_line.rsplit('.', 1)[-1].lower()
            if ext in KNOWN_EXTENSIONS:
                filepath = first_line
                # Remaining lines (after the filename line) become the content
                remaining = '\n'.join(lines[first_line_idx + 1:])
                if remaining.strip():
                    saved.append((filepath, remaining))
                    log.debug(f'Strategy 2b: first-line filename "{filepath}" '
                              f'inside code block')

    # ---- Strategy 3: auto-save fallback for unnamed data blocks -------------
    # When no named files were found by Strategies 1-2, look for fenced blocks
    # whose info-string is a known data format and auto-save as llm_output.<ext>.
    # If multiple blocks share the same extension, number them (llm_output_2.csv, etc).
    AUTO_SAVE_EXTS = {
        'csv': 'csv', 'json': 'json', 'xml': 'xml', 'yaml': 'yaml',
        'yml': 'yaml', 'md': 'md', 'markdown': 'md', 'txt': 'txt',
        'sql': 'sql', 'html': 'html', 'toml': 'toml', 'ini': 'ini',
    }

    if not saved:
        # Find all fenced blocks with an info-string
        pattern_auto = re.compile(
            r'```(\w+)[ \t]*\n'              # opening fence with info-string
            r'(.*?)'                          # captured content
            r'\n```',                         # closing fence
            re.DOTALL,
        )
        ext_counts = {}  # track how many blocks per extension for numbering
        for m in pattern_auto.finditer(response_text):
            info = m.group(1).lower()
            content = m.group(2)
            if info in AUTO_SAVE_EXTS and content and content.strip():
                ext = AUTO_SAVE_EXTS[info]
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
                count = ext_counts[ext]
                # Naming: llm_output_file1.csv, llm_output_file2.csv, etc.
                filepath = f'llm_output_file{count}.{ext}'
                saved.append((filepath, content))
                log.debug(f'Auto-save fallback: {info} block -> {filepath}')

    # ---- Write files --------------------------------------------------------
    written = []
    for filepath, content in saved:
        try:
            # Create parent directories if needed
            parent = os.path.dirname(filepath)
            if parent:
                os.makedirs(parent, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                # Ensure file ends with a newline
                if content and not content.endswith('\n'):
                    f.write('\n')

            # ---- CSV validation: repair rows with wrong column count --------
            # LLMs sometimes emit CSV with unquoted commas inside fields
            # (e.g. "12.1.0.0.72,78" in a summary).  Detect and repair by
            # re-reading with the csv module and merging excess columns back
            # into the widest text field (typically 'summary').
            if filepath.lower().endswith('.csv'):
                validate_and_repair_csv(filepath)

            written.append(filepath)
            log.info(f'Saved extracted file: {filepath} ({len(content)} chars)')
        except Exception as e:
            log.warning(f'Failed to save extracted file {filepath}: {e}')
            output(f'  WARNING: could not save {filepath}: {e}')

    return written


def _invoke_llm(prompt_text, attachments=None, timeout=None, model=None):
    '''
    Send a prompt to the configured LLM with optional file attachments.

    This is the shared core logic extracted from cmd_invoke_llm() so it can
    be reused by workflow commands.

    Input:
        prompt_text: The prompt string to send.
        attachments: Optional list of file paths to attach.
        timeout: Optional timeout in seconds.
        model: Optional model name override.  When provided, this overrides
               the CORNELIS_LLM_MODEL / OPENAI_MODEL / etc. env-var default.

    Output:
        Tuple of (response_content, saved_files, token_info) where:
          - response_content: str, the full LLM response text
          - saved_files: list of file paths extracted/saved from the response
          - token_info: dict with keys prompt_tokens, completion_tokens, total_tokens,
                        model, finish_reason, elapsed, estimated_cost

    Raises:
        Exception if the LLM call fails.
    '''
    log.debug(f'Entering _invoke_llm(prompt_len={len(prompt_text)}, '
              f'attachments={attachments}, timeout={timeout}, model={model})')

    import base64
    import mimetypes
    from llm.config import get_llm_client
    from llm.base import Message

    # ---- classify attachments -----------------------------------------------
    IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'}
    TEXT_EXTS = {
        '.md', '.txt', '.csv', '.json', '.yaml', '.yml', '.xml',
        '.py', '.js', '.ts', '.html', '.css', '.sh', '.sql',
        '.log', '.cfg', '.ini', '.toml',
    }

    image_data_uris = []   # base64 data URIs for vision API
    text_blocks = []       # fenced code blocks to append to prompt

    for filepath in (attachments or []):
        if not os.path.isfile(filepath):
            output(f'WARNING: attachment not found, skipping: {filepath}')
            log.warning(f'Attachment not found: {filepath}')
            continue

        ext = os.path.splitext(filepath)[1].lower()

        if ext in IMAGE_EXTS:
            # Encode image as base64 data URI for the vision API
            mime_type = mimetypes.guess_type(filepath)[0] or 'image/png'
            with open(filepath, 'rb') as img_f:
                b64 = base64.b64encode(img_f.read()).decode('utf-8')
            data_uri = f'data:{mime_type};base64,{b64}'
            image_data_uris.append(data_uri)
            log.debug(f'Attached image: {filepath} ({mime_type})')
            output(f'  Attached image: {filepath}')
        else:
            # Attempt to read as text
            try:
                with open(filepath, 'r', encoding='utf-8') as txt_f:
                    content = txt_f.read()
                # Determine language hint for fenced block
                lang = ext.lstrip('.') if ext in TEXT_EXTS else ''
                text_blocks.append(f'\n\n--- Attachment: {os.path.basename(filepath)} ---\n```{lang}\n{content}\n```')
                log.debug(f'Attached text file: {filepath} ({len(content)} chars)')
                output(f'  Attached text: {filepath} ({len(content)} chars)')
            except (UnicodeDecodeError, IOError) as e:
                output(f'WARNING: cannot read attachment as text, skipping: {filepath} ({e})')
                log.warning(f'Cannot read attachment {filepath}: {e}')

    # ---- build final prompt with inlined text attachments -------------------
    if text_blocks:
        prompt_text = prompt_text + '\n' + ''.join(text_blocks)

    # ---- send to LLM -------------------------------------------------------
    output('')
    total_chars = len(prompt_text)
    timeout_display = f'{timeout}s' if timeout else 'default'
    output(f'Sending to LLM... ({total_chars} chars, timeout={timeout_display})')

    # Use vision client if images are present, otherwise standard client.
    # When a model override is supplied via --model, pass it through to the
    # factory so it takes precedence over the env-var default.
    if image_data_uris:
        client = get_llm_client(for_vision=True, timeout=timeout, model=model)
        log.info(f'+  Using LLM model: {client.model}')
        output(f'Using vision model: {client.model} ({len(image_data_uris)} image(s))')
        messages = [Message.user(prompt_text)]
    else:
        client = get_llm_client(timeout=timeout, model=model)
        log.info(f'+  Using LLM model: {client.model}')
        output(f'Using model: {client.model}')
        messages = [Message.user(prompt_text)]

    # ---- call LLM -----------------------------------------------------------
    # Heartbeat "Still waiting on LLM return..." messages are now emitted
    # inside CornelisLLM.chat() / chat_with_vision() themselves, so no
    # wrapper thread is needed here.
    import time as _time
    _llm_start = _time.monotonic()
    if image_data_uris:
        response = client.chat_with_vision(messages, image_data_uris)
    else:
        response = client.chat(messages)
    elapsed_total = _time.monotonic() - _llm_start

    # ---- display response ---------------------------------------------------
    output('')
    output('=' * 60)
    output('LLM RESPONSE')
    output('=' * 60)
    output('')
    output(response.content)
    output('')
    output('-' * 60)

    log.info(f'LLM response received: {len(response.content)} chars, '
             f'tokens={response.usage}')

    # ---- token usage & cost table -------------------------------------------
    prompt_tok = 0
    completion_tok = 0
    total_tok = 0
    if response.usage:
        prompt_tok = response.usage.get('prompt_tokens', 0)
        completion_tok = response.usage.get('completion_tokens', 0)
        total_tok = response.usage.get('total_tokens', 0)

    # Estimate cost using typical per-token pricing (rough approximation).
    # These rates are ballpark for GPT-4o-class models; adjust as needed.
    COST_PER_1K_PROMPT = 0.0025       # $2.50 / 1M prompt tokens
    COST_PER_1K_COMPLETION = 0.0100   # $10.00 / 1M completion tokens
    estimated_cost = (
        (prompt_tok / 1000.0) * COST_PER_1K_PROMPT
        + (completion_tok / 1000.0) * COST_PER_1K_COMPLETION
    )

    elapsed_str = f'{elapsed_total:.1f}s'

    # Build the summary box using ==== banner style
    banner = '=' * 80
    log.info(banner)
    log.info(f'  LLM totals: prompt_tokens={prompt_tok}, completion_tokens={completion_tok}')
    log.info(f'  Model: {response.model or "unknown"}')
    log.info(f'  Finish reason: {response.finish_reason or "n/a"}')
    log.info(f'  Elapsed: {elapsed_str}')
    log.info(f'  Estimated LLM cost: ${estimated_cost:.4f}')
    log.info(banner)

    # Token usage & metadata table — ==== banner style, key:  value alignment
    token_table = (
        f'\n'
        f'{banner}\n'
        f'LLM Token Usage\n'
        f'{banner}\n'
        f'{"Prompt tokens (in):":<30}  {prompt_tok:>12,}\n'
        f'{"Completion tokens (out):":<30}  {completion_tok:>12,}\n'
        f'{"Total tokens:":<30}  {total_tok:>12,}\n'
        f'{banner}\n'
        f'{"Model:":<30}  {(response.model or "unknown"):>12}\n'
        f'{"Finish reason:":<30}  {(response.finish_reason or "n/a"):>12}\n'
        f'{"Elapsed:":<30}  {elapsed_str:>12}\n'
        f'{"Estimated cost:":<30}  {f"${estimated_cost:.4f}":>12}\n'
        f'{banner}'
    )
    output(token_table)

    # ---- save full response as llm_output.md --------------------------------
    all_created_files = []   # (filepath, size_chars, source) tuples

    try:
        with open('llm_output.md', 'w', encoding='utf-8') as f:
            f.write(response.content)
            if response.content and not response.content.endswith('\n'):
                f.write('\n')
        all_created_files.append(('llm_output.md', len(response.content), 'full response'))
        log.info(f'Saved full LLM response: llm_output.md ({len(response.content)} chars)')
    except Exception as e:
        log.warning(f'Failed to save llm_output.md: {e}')
        output(f'WARNING: could not save llm_output.md: {e}')

    # ---- extract and save any file content from the response ----------------
    saved_files = _extract_and_save_files(response.content)
    for sf in saved_files:
        try:
            sz = os.path.getsize(sf)
        except OSError:
            sz = 0
        all_created_files.append((sf, sz, 'extracted'))

    # ---- file-creation summary table — ==== banner style --------------------
    if all_created_files:
        banner = '=' * 80
        max_name = max(len(f[0]) for f in all_created_files)
        max_name = max(max_name, 4)  # minimum width for header "File"
        row_fmt = f'{{:<4}}{{:<{max_name + 3}}}{{:>10}}   {{:<12}}'

        file_table_lines = [
            '',
            banner,
            'LLM Created Files',
            banner,
            row_fmt.format('#', 'File', 'Size', 'Source'),
        ]
        for idx, (fpath, fsize, fsource) in enumerate(all_created_files, 1):
            size_str = f'{fsize:,} ch' if fsize else '0 ch'
            file_table_lines.append(row_fmt.format(str(idx), fpath, size_str, fsource))
        file_table_lines.append(banner)

        file_table = '\n'.join(file_table_lines)
        output(file_table)

    # ---- build token_info dict for callers ----------------------------------
    token_info = {
        'prompt_tokens': prompt_tok,
        'completion_tokens': completion_tok,
        'total_tokens': total_tok,
        'model': response.model or 'unknown',
        'finish_reason': response.finish_reason or 'n/a',
        'elapsed': elapsed_total,
        'estimated_cost': estimated_cost,
    }

    return response.content, saved_files, token_info


def cmd_invoke_llm(args):
    '''
    Send a prompt to the configured LLM, optionally with file attachments.

    The prompt argument can be:
      - A path to a .md or .txt file whose contents become the prompt
      - An inline string used directly as the prompt

    Attachments are classified by extension:
      - Image files (.png, .jpg, .jpeg, .gif, .bmp, .webp, .svg) are sent
        via the vision API as base64-encoded images.
      - Text files (.md, .txt, .csv, .json, .yaml, .yml, .xml, .py, .js,
        .ts, .html, .css, .sh, .sql, .log, .cfg, .ini, .toml) are read
        and inlined into the prompt as fenced code blocks.
      - Other extensions are attempted as text; binary files are skipped
        with a warning.

    This is a thin wrapper around _invoke_llm() that resolves the prompt
    from args and delegates to the shared helper.
    '''
    log.debug(f'cmd_invoke_llm(prompt={args.prompt}, attachments={args.attachments})')

    # ---- resolve prompt text ------------------------------------------------
    prompt_arg = args.prompt
    if os.path.isfile(prompt_arg):
        log.debug(f'Reading prompt from file: {prompt_arg}')
        with open(prompt_arg, 'r', encoding='utf-8') as f:
            prompt_text = f.read().strip()
        output(f'Prompt loaded from {prompt_arg} ({len(prompt_text)} chars)')
    else:
        prompt_text = prompt_arg
        output(f'Using inline prompt ({len(prompt_text)} chars)')

    # ---- delegate to shared helper ------------------------------------------
    # Pass --model override if the user provided one on the CLI
    model_override = getattr(args, 'model', None)
    try:
        response_content, saved_files, token_info = _invoke_llm(
            prompt_text, attachments=args.attachments, timeout=args.timeout,
            model=model_override)
        return 0
    except Exception as e:
        log.error(f'LLM invocation failed: {e}', exc_info=True)
        output(f'ERROR: {e}')
        return 1


def cmd_workflow(args):
    '''
    Run a named workflow. Dispatches to the appropriate workflow handler.

    Input:
        args: Parsed argparse namespace with workflow_name and workflow-specific options.

    Output:
        int: Exit code (0 = success, 1 = error).

    Side Effects:
        Delegates to the workflow handler which may connect to Jira, invoke the LLM,
        and create output files.
    '''
    log.debug(f'Entering cmd_workflow(workflow_name={args.workflow_name})')

    # Registry of available workflows
    WORKFLOWS = {
        'bug-report': _workflow_bug_report,
        'drucker-bug-activity': _workflow_drucker_bug_activity,
        'drucker-hygiene': _workflow_drucker_hygiene,
        'drucker-intake-report': _workflow_drucker_intake_report,
        'drucker-issue-check': _workflow_drucker_issue_check,
        'drucker-poll': _workflow_drucker_poll,
        'feature-plan': _workflow_feature_plan,
        'gantt-poll': _workflow_gantt_poll,
        'gantt-release-monitor': _workflow_gantt_release_monitor,
        'gantt-release-monitor-get': _workflow_gantt_release_monitor_get,
        'gantt-release-monitor-list': _workflow_gantt_release_monitor_list,
        'gantt-release-survey': _workflow_gantt_release_survey,
        'gantt-release-survey-get': _workflow_gantt_release_survey_get,
        'gantt-release-survey-list': _workflow_gantt_release_survey_list,
        'gantt-snapshot': _workflow_gantt_snapshot,
        'gantt-snapshot-get': _workflow_gantt_snapshot_get,
        'gantt-snapshot-list': _workflow_gantt_snapshot_list,
        'hypatia-generate': _workflow_hypatia_generate,
    }

    handler = WORKFLOWS.get(args.workflow_name)
    if not handler:
        available = ', '.join(sorted(WORKFLOWS.keys()))
        output(f'ERROR: Unknown workflow "{args.workflow_name}". Available: {available}')
        return 1

    return handler(args)


# ---------------------------------------------------------------------------
# Shared workflow summary helper
# ---------------------------------------------------------------------------

def _print_workflow_summary(workflow_name: str, created_files: list[tuple[str, str]]):
    '''Print a standardised "WORKFLOW COMPLETE" banner with a file table.

    Input:
        workflow_name:  Short name shown in the banner (e.g. "bug-report").
        created_files:  List of (filepath, description) tuples.
    '''
    banner = '=' * 80
    output('')
    output(banner)
    output(f'WORKFLOW COMPLETE: {workflow_name}')
    output(banner)

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

        output('\n'.join(file_table_lines))

    output('')


def _workflow_bug_report(args):
    '''
    Bug report workflow: filter lookup → run filter → LLM analysis → Excel conversion.

    Steps:
      1. Connect to Jira
      2. Look up filter by name from favourite filters
      3. Run the filter to get tickets with latest comments
      4. Dump tickets to JSON file
      5. Send JSON + prompt to LLM
      6. Convert any extracted CSV to styled Excel

    Input:
        args: Parsed argparse namespace with:
            - workflow_filter: str, the Jira filter name to look up
            - workflow_prompt: str or None, path to the prompt file
            - timeout: float or None, LLM timeout in seconds
            - limit: int or None, max tickets to retrieve
            - output: str or None, output filename override

    Output:
        int: Exit code (0 = success, 1 = error).

    Side Effects:
        Creates JSON dump file, llm_output.md, extracted CSV/Excel files.
    '''
    log.debug(f'Entering _workflow_bug_report(filter={args.workflow_filter}, '
              f'prompt={args.workflow_prompt}, limit={args.limit}, timeout={args.timeout})')

    filter_name = args.workflow_filter
    prompt_path = args.workflow_prompt or 'config/prompts/cn5000_bugs_clean.md'
    all_created_files = []  # (filepath, description) tuples for final summary

    # ---- Step 1/6: Connect to Jira ------------------------------------------
    output('')
    output('=' * 60)
    output('WORKFLOW: bug-report')
    output('=' * 60)
    output('')
    output('Step 1/6: Connecting to Jira...')
    try:
        jira = jira_api.get_connection()
        log.info('Jira connection established')
    except Exception as e:
        log.error(f'Step 1/6 failed: Jira connection error: {e}', exc_info=True)
        output(f'ERROR: Failed to connect to Jira: {e}')
        return 1

    # ---- Step 2/6: Look up filter by name -----------------------------------
    output('')
    output(f'Step 2/6: Looking up filter "{filter_name}" from favourite filters...')
    try:
        filters = jira_utils.list_filters(jira, favourite_only=True)
        # Search for exact match on filter name
        matched_filter = None
        for f in filters:
            if f.get('name') == filter_name:
                matched_filter = f
                break

        if not matched_filter:
            # Show available filter names to help the user
            available_names = [f.get('name', '(unnamed)') for f in filters]
            output(f'ERROR: Filter "{filter_name}" not found in favourite filters.')
            if available_names:
                output(f'  Available favourite filters:')
                for fn in available_names:
                    output(f'    - {fn}')
            return 1

        filter_id = matched_filter.get('id')
        filter_jql = matched_filter.get('jql', '')
        log.info(f'Found filter: id={filter_id}, name={filter_name}, jql={filter_jql}')
        output(f'  Found filter ID: {filter_id}')
        output(f'  JQL: {filter_jql}')
    except Exception as e:
        log.error(f'Step 2/6 failed: Filter lookup error: {e}', exc_info=True)
        output(f'ERROR: Failed to look up filter: {e}')
        return 1

    # ---- Step 3/6: Run the filter to get tickets ----------------------------
    output('')
    output(f'Step 3/6: Running filter to retrieve tickets...')
    try:
        # Set the global _include_comments flag so run_jql_query fetches comment
        # fields and dump_tickets_to_file applies the 'latest' filter.
        jira_utils._include_comments = 'latest'
        log.info('Set _include_comments = "latest" for comment extraction')

        issues = jira_utils.run_filter(jira, filter_id, limit=args.limit)
        if not issues:
            output('WARNING: Filter returned 0 tickets. Nothing to process.')
            return 0
        log.info(f'Filter returned {len(issues)} tickets')
        output(f'  Retrieved {len(issues)} tickets')
    except Exception as e:
        log.error(f'Step 3/6 failed: Filter execution error: {e}', exc_info=True)
        output(f'ERROR: Failed to run filter: {e}')
        return 1

    # ---- Step 4/6: Dump tickets to JSON file --------------------------------
    output('')
    output(f'Step 4/6: Dumping tickets to JSON...')
    try:
        # Derive dump filename from filter name (sanitize for filesystem)
        safe_name = re.sub(r'[^\w\s-]', '', filter_name).strip().lower()
        safe_name = re.sub(r'[\s]+', '_', safe_name)
        dump_basename = args.output or safe_name or 'bug_report'
        # Strip any extension the user may have provided — we force .json here
        dump_basename = os.path.splitext(dump_basename)[0]

        dump_path = jira_api.dump_tickets_to_file(
            issues, dump_basename, 'json', include_comments='latest')
        log.info(f'Tickets dumped to: {dump_path}')
        output(f'  Saved: {dump_path}')
        all_created_files.append((dump_path, 'ticket JSON dump'))
    except Exception as e:
        log.error(f'Step 4/6 failed: Dump error: {e}', exc_info=True)
        output(f'ERROR: Failed to dump tickets: {e}')
        return 1

    # ---- Step 5/6: Send JSON + prompt to LLM --------------------------------
    output('')
    output(f'Step 5/6: Sending tickets + prompt to LLM...')
    try:
        # Read the prompt file
        if not os.path.isfile(prompt_path):
            output(f'ERROR: Prompt file not found: {prompt_path}')
            return 1
        with open(prompt_path, 'r', encoding='utf-8') as pf:
            prompt_text = pf.read().strip()
        log.info(f'Loaded prompt from {prompt_path} ({len(prompt_text)} chars)')
        output(f'  Prompt: {prompt_path} ({len(prompt_text)} chars)')

        # Pass --model override if the user provided one on the CLI
        model_override = getattr(args, 'model', None)
        response_content, saved_files, token_info = _invoke_llm(
            prompt_text, attachments=[dump_path], timeout=args.timeout,
            model=model_override)

        # Track llm_output.md if it was created
        if os.path.isfile('llm_output.md'):
            all_created_files.append(('llm_output.md', 'LLM full response'))
        for sf in saved_files:
            all_created_files.append((sf, 'LLM extracted'))

    except Exception as e:
        log.error(f'Step 5/6 failed: LLM invocation error: {e}', exc_info=True)
        output(f'ERROR: LLM invocation failed: {e}')
        return 1

    # ---- Step 6/6: Convert CSV files to styled Excel ------------------------
    output('')
    output(f'Step 6/6: Converting CSV output to Excel...')
    csv_files = [sf for sf in saved_files if sf.lower().endswith('.csv')]

    # Canonical CSV name derived from the filter / output basename.
    # We always rename the final CSV to this so the deliverable has a
    # predictable, clean filename regardless of what the LLM chose.
    canonical_csv = f'{dump_basename}.csv'

    # Deduplicate: when the LLM emits multiple CSV blocks (e.g. an original
    # and a "corrected" version), keep only the LAST one — it is typically the
    # most complete / corrected.
    #
    # Edge case: the LLM may emit multiple blocks with the SAME filename.
    # In that case the second write already overwrote the first on disk, so
    # there is only one physical file.  We must NOT os.remove() it because
    # that would delete the surviving copy.  We also must not strip ALL
    # tracking entries for that name — we need to keep exactly one.
    if len(csv_files) > 1:
        keep = csv_files[-1]           # last CSV is the corrected one
        discard = csv_files[:-1]
        log.info(f'LLM emitted {len(csv_files)} CSV files; keeping last: {keep}')

        # Collect unique discard paths that differ from keep — safe to delete
        unique_discard = set(d for d in discard if d != keep)
        same_name_count = sum(1 for d in discard if d == keep)
        if same_name_count:
            log.info(f'{same_name_count} duplicate(s) share the same filename as keep ({keep}); skipping remove')

        for d in unique_discard:
            try:
                os.remove(d)
                log.info(f'Removed duplicate CSV: {d}')
            except OSError as rm_err:
                log.warning(f'Could not remove {d}: {rm_err}')

        # Rebuild tracking lists: remove ALL csv entries, then re-add the
        # single keep entry.  This avoids the problem where same-name
        # duplicates cause the keep entry to be removed too.
        discard_set = set(csv_files)  # all csv filenames (including keep)
        all_created_files[:] = [
            (f, desc) for f, desc in all_created_files if f not in discard_set]
        all_created_files.append((keep, 'LLM extracted'))
        saved_files = [sf for sf in saved_files if sf not in discard_set]
        saved_files.append(keep)

        csv_files = [keep]
        output(f'  Deduplicated: keeping {keep}')

    # Rename the surviving CSV to the canonical name so the deliverable
    # filename is predictable (e.g. sw_1211_p0p1_bugs.csv) regardless of
    # whatever name the LLM invented for the file.
    if len(csv_files) == 1 and csv_files[0] != canonical_csv:
        keep = csv_files[0]
        try:
            os.rename(keep, canonical_csv)
            log.info(f'Renamed {keep} -> {canonical_csv}')
            # Update tracking lists
            all_created_files[:] = [
                (canonical_csv if f == keep else f, desc)
                for f, desc in all_created_files]
            saved_files = [
                canonical_csv if sf == keep else sf for sf in saved_files]
            csv_files = [canonical_csv]
            output(f'  Renamed: {keep} -> {canonical_csv}')
        except OSError as ren_err:
            log.warning(f'Could not rename {keep} -> {canonical_csv}: {ren_err}')

    if not csv_files:
        output('  No CSV files found in LLM output — skipping Excel conversion.')
        log.info('No CSV files to convert to Excel')
    else:
        # Pass the Jira base URL so ticket-key cells become clickable links
        # in the Excel output (e.g. https://cornelisnetworks.atlassian.net/browse/STL-76582).
        jira_base_url = getattr(jira_utils, 'JIRA_URL', None)
        dashboard_columns = getattr(args, 'dashboard_columns', None)
        for csv_path in csv_files:
            try:
                xlsx_path = excel_utils.convert_from_csv(
                    csv_path, jira_base_url=jira_base_url,
                    dashboard_columns=dashboard_columns)
                log.info(f'Converted {csv_path} -> {xlsx_path}')
                output(f'  Converted: {csv_path} -> {xlsx_path}')
                all_created_files.append((xlsx_path, 'Excel workbook'))
            except Exception as e:
                log.error(f'Excel conversion failed for {csv_path}: {e}', exc_info=True)
                output(f'  WARNING: Failed to convert {csv_path} to Excel: {e}')

    _print_workflow_summary('bug-report', all_created_files)
    return 0


def _workflow_feature_plan(args):
    '''
    Feature planning workflow: research → HW analysis → scoping → Jira plan.

    Takes a high-level feature request and produces a Jira project plan with
    Epics and Stories.  Dry-run by default; use --execute to create tickets.

    Input:
        args: Parsed argparse namespace with:
            - project: Jira project key
            - feature: Feature description string
            - docs: Optional list of document paths
            - output: Optional output file path
            - execute: Whether to create tickets in Jira

    Output:
        int: Exit code (0 = success, 1 = error).
    '''
    log.debug('Entering _workflow_feature_plan()')

    project_key = args.project
    plan_file = getattr(args, 'plan_file', None)
    execute = getattr(args, 'execute', False)
    initiative_key = getattr(args, 'initiative', None)
    force = getattr(args, 'force', False)
    cleanup_csv = getattr(args, 'cleanup', None)

    # ------------------------------------------------------------------
    # Cleanup path: --cleanup CSV deletes all tickets listed in the CSV
    # produced by a previous --execute run.  Dry-run by default; add
    # --execute to actually delete.  The CSV is already in child-first
    # order so parents are deleted last.
    # ------------------------------------------------------------------
    if cleanup_csv:
        output('Feature Planning Workflow — Cleanup (Leave No Trace)')
        output(f'  CSV file:  {cleanup_csv}')
        output(f'  Execute:   {"YES — will DELETE tickets" if execute else "DRY RUN"}')
        if force:
            output(f'  Force:     YES — skip confirmation prompt')
        output('')

        if not os.path.isfile(cleanup_csv):
            output(f'ERROR: Cleanup CSV not found: {cleanup_csv}')
            return 1

        try:
            jira = jira_api.get_connection()
            jira_utils.bulk_delete_tickets(
                jira,
                input_file=cleanup_csv,
                delete_subtasks=True,
                dry_run=not execute,
                force=force,
            )
            return 0
        except Exception as e:
            output(f'ERROR: Cleanup failed: {e}')
            log.error(f'Cleanup error: {e}', exc_info=True)
            return 1

    # ------------------------------------------------------------------
    # Fast path: --plan-file loads a previously generated plan.json and
    # optionally pushes it into Jira (--execute).  No LLM / agentic
    # phases are invoked.
    # ------------------------------------------------------------------
    if plan_file:
        output(f'Feature Planning Workflow — Execute from Plan File')
        output(f'  Project:      {project_key}')
        output(f'  Plan file:    {plan_file}')
        if initiative_key:
            output(f'  Initiative:   {initiative_key} (supplied)')
        else:
            output(f'  Initiative:   (will be auto-created on --execute)')
        output(f'  Force:        {"YES — skip duplicate prompts" if force else "no (interactive)"}')
        output(f'  Execute:      {"YES — will create Jira tickets" if execute else "DRY RUN"}')
        output('')

        try:
            from agents.feature_planning_orchestrator import FeaturePlanningOrchestrator

            orchestrator = FeaturePlanningOrchestrator()
            response = orchestrator.run({
                'project_key': project_key,
                'feature_request': '',          # not needed for execute-plan
                'mode': 'execute-plan',
                'plan_file': plan_file,
                'execute': execute,
                'initiative_key': initiative_key,
                'force': force,
                'feature_tag': getattr(args, 'feature_tag', None),
                'timeout': getattr(args, 'timeout', None),
            })

            if response.success:
                output(response.content)

                # Surface the created_tickets.csv path if it was produced
                csv_path = response.metadata.get('created_csv_path', '')
                if csv_path and os.path.isfile(csv_path):
                    output(f'\nCreated tickets CSV: {csv_path}')

                # If this was a dry-run, remind the user
                if not execute:
                    output('')
                    output('This was a DRY RUN. To create tickets in Jira, '
                           're-run with --execute.')
                return 0
            else:
                output(f'ERROR: {response.error}')
                return 1

        except ImportError as e:
            output(f'ERROR: Missing dependency: {e}')
            log.error(f'Import error: {e}', exc_info=True)
            return 1
        except Exception as e:
            output(f'ERROR: Plan execution failed: {e}')
            log.error(f'Plan execution error: {e}', exc_info=True)
            return 1

    # ------------------------------------------------------------------
    # Standard path: agentic workflow (research → HW → scoping → plan)
    # ------------------------------------------------------------------

    # --feature-prompt FILE takes precedence over --feature "string"
    feature_prompt_file = getattr(args, 'feature_prompt', None)
    if feature_prompt_file:
        log.info(f'Reading feature prompt from file: {feature_prompt_file}')
        with open(feature_prompt_file, 'r', encoding='utf-8') as fp:
            feature_request = fp.read().strip()
        if not feature_request:
            output(f'ERROR: Feature prompt file is empty: {feature_prompt_file}')
            return 1
        log.info(f'Feature prompt loaded: {len(feature_request)} chars from {feature_prompt_file}')
    else:
        feature_request = args.feature
    doc_paths = args.docs or []
    scope_doc = getattr(args, 'scope_doc', None) or ''

    # Determine the workflow mode:
    #   --scope-doc  → 'scope-to-plan' (skip research/HW/scoping, jump to plan)
    #   default      → 'full' (run all phases)
    mode = 'scope-to-plan' if scope_doc else 'full'

    # Resolve the output directory.
    #
    # The standard subdir structure is:  plans/<PROJECT>-<slug>/
    # --output-dir ROOT  → ROOT/plans/<PROJECT>-<slug>/
    # --output FILE      → dirname(FILE)  (explicit path, no slug)
    # (neither)          → plans/<PROJECT>-<slug>/  (relative to cwd)
    explicit_output_dir = getattr(args, 'output_dir', None)
    output_file = args.output or 'feature_plan.json'

    # Build the <PROJECT>-<slug> component used by the standard layout.
    # When using --feature-prompt, derive slug from the filename stem
    # (the full file content would be too long for a directory name).
    if feature_prompt_file:
        slug = os.path.splitext(os.path.basename(feature_prompt_file))[0].lower()
    else:
        slug = feature_request[:40].lower()
    slug = slug.replace(' ', '-').replace('/', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    slug = slug.strip('-')
    plans_subdir = os.path.join('plans', f'{project_key}-{slug}')

    if explicit_output_dir:
        # --output-dir ROOT → ROOT/plans/<PROJECT>-<slug>/
        output_dir = os.path.join(explicit_output_dir, plans_subdir)
    else:
        output_dir = os.path.dirname(output_file)

    if not output_dir:
        # Default: plans/<PROJECT>-<slug>/ relative to cwd
        output_dir = plans_subdir

    output(f'Feature Planning Workflow')
    output(f'  Project:  {project_key}')
    if feature_prompt_file:
        output(f'  Prompt:   {feature_prompt_file} ({len(feature_request)} chars)')
    else:
        output(f'  Feature:  {feature_request}')
    output(f'  Mode:     {mode}')
    output(f'  Output:   {output_dir}/')
    if scope_doc:
        output(f'  Scope:    {scope_doc}')
    if doc_paths:
        output(f'  Docs:     {len(doc_paths)} file(s)')
        for dp in doc_paths:
            output(f'            - {dp}')
    if initiative_key:
        output(f'  Initiative: {initiative_key} (supplied)')
    else:
        output(f'  Initiative: (will be auto-created on --execute)')
    output(f'  Force:    {"YES — skip duplicate prompts" if force else "no (interactive)"}')
    output(f'  Execute:  {"YES — will create Jira tickets" if execute else "DRY RUN"}')
    output('')

    try:
        from agents.feature_planning_orchestrator import FeaturePlanningOrchestrator

        output('Starting workflow...')
        orchestrator = FeaturePlanningOrchestrator(output_dir=output_dir)

        response = orchestrator.run({
            'feature_request': feature_request,
            'project_key': project_key,
            'doc_paths': doc_paths,
            'mode': mode,
            'execute': execute,
            'initiative_key': initiative_key,
            'force': force,
            'scope_doc': scope_doc,
            'output_dir': output_dir,
            'feature_tag': getattr(args, 'feature_tag', None),
            'timeout': args.timeout,
        })

        if response.success:
            output(response.content)

            # Save the plan to JSON inside the output directory
            jira_plan = response.metadata.get('state', {}).get('jira_plan')
            # Track all output files for the summary table
            all_created_files: list[tuple[str, str]] = []

            # Include intermediate files created by the orchestrator
            # (research.json, hw_profile.json, scope.json, debug/*.md)
            intermediate_files = getattr(orchestrator, '_created_files', [])
            for ifile in intermediate_files:
                if os.path.exists(ifile):
                    basename = os.path.basename(ifile)
                    if 'debug' in ifile:
                        all_created_files.append((ifile, f'Debug: {basename}'))
                    else:
                        desc_map = {
                            'research.json': 'Research findings',
                            'hw_profile.json': 'Hardware profile',
                            'scope.json': 'Feature scope',
                        }
                        all_created_files.append(
                            (ifile, desc_map.get(basename, f'Intermediate: {basename}'))
                        )

            if jira_plan:
                import json
                # Place plan files in the output directory
                os.makedirs(output_dir, exist_ok=True)
                json_path = os.path.join(output_dir, 'plan.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(jira_plan, f, indent=2)
                output(f'Saving plan to: {json_path}')
                all_created_files.append((json_path, 'Feature plan JSON'))

                # Also save Markdown summary
                md_path = os.path.join(output_dir, 'plan.md')
                markdown = jira_plan.get('summary_markdown', '')
                if markdown:
                    with open(md_path, 'w', encoding='utf-8') as f:
                        f.write(markdown)
                    output(f'Markdown saved to: {md_path}')
                    all_created_files.append((md_path, 'Markdown summary'))

                # Export plan to CSV (indented format)
                csv_path = ''
                try:
                    from tools.plan_export_tools import plan_to_csv as _plan_to_csv
                    csv_basename = os.path.join(output_dir, 'plan')
                    csv_result = cast(Any, _plan_to_csv(json_path, output_path=csv_basename))
                    csv_data = getattr(csv_result, 'data', None)
                    if csv_data:
                        csv_path = csv_data.get('output_path', '')
                        if csv_path:
                            output(f'CSV saved to: {csv_path}')
                            all_created_files.append((csv_path, 'Jira CSV (indented)'))
                    else:
                        csv_error = getattr(csv_result, 'error', None)
                        if csv_error:
                            log.warning(f'CSV export warning: {csv_error}')
                except Exception as csv_err:
                    log.warning(f'CSV export failed (plan JSON still saved): {csv_err}')

                # Convert CSV to Excel workbook via excel_utils
                if csv_path:
                    try:
                        xlsx_path = excel_utils.convert_from_csv(csv_path)
                        log.info(f'Converted {csv_path} -> {xlsx_path}')
                        output(f'Excel saved to: {xlsx_path}')
                        all_created_files.append((xlsx_path, 'Excel workbook'))
                    except Exception as xlsx_err:
                        log.warning(f'Excel conversion failed: {xlsx_err}')
                        output(f'  WARNING: Excel conversion failed: {xlsx_err}')

            # Surface the created_tickets.csv path if execution produced one
            created_csv = response.metadata.get('created_csv_path', '')
            if created_csv and os.path.isfile(created_csv):
                all_created_files.append((created_csv, 'Created tickets (for --cleanup)'))

            # Report blocking status
            if response.metadata.get('blocked'):
                questions = response.metadata.get('blocking_questions', [])
                output(f'\n⚠️  Workflow blocked by {len(questions)} question(s).')
                output('Answer the questions above and re-run to continue.')
                return 1

            output('')
            if not execute:
                output('This was a DRY RUN. To create tickets in Jira, re-run with --execute.')

            _print_workflow_summary('feature-plan', all_created_files)
            return 0
        else:
            output(f'ERROR: {response.error}')
            return 1

    except ImportError as e:
        output(f'ERROR: Missing dependency for feature planning: {e}')
        log.error(f'Import error: {e}', exc_info=True)
        return 1
    except Exception as e:
        output(f'ERROR: Feature planning failed: {e}')
        log.error(f'Feature planning error: {e}', exc_info=True)
        return 1


def _workflow_gantt_snapshot(args):
    '''
    Gantt workflow: Jira backlog -> planning snapshot JSON + Markdown summary.
    '''
    log.debug(
        f'Entering _workflow_gantt_snapshot(project={args.project}, '
        f'planning_horizon={args.planning_horizon}, limit={args.limit}, '
        f'include_done={args.include_done})'
    )

    from agents.gantt_agent import GanttProjectPlannerAgent
    from state.gantt_snapshot_store import GanttSnapshotStore

    output('')
    output('=' * 60)
    output('WORKFLOW: gantt-snapshot')
    output('=' * 60)
    output('')
    output(f'Project: {args.project}')
    output(f'Planning horizon: {args.planning_horizon} days')
    output(f'Include done issues: {"yes" if args.include_done else "no"}')
    output('')
    output('Step 1/3: Building planning snapshot...')

    agent = GanttProjectPlannerAgent(project_key=args.project)
    result = agent.run({
        'project_key': args.project,
        'planning_horizon_days': args.planning_horizon,
        'limit': args.limit or 200,
        'include_done': args.include_done,
        'evidence_paths': list(getattr(args, 'evidence', None) or []),
    })

    if not result.success:
        output(f'ERROR: {result.error}')
        return 1

    snapshot = result.metadata.get('planning_snapshot')
    if not snapshot:
        output('ERROR: Gantt snapshot metadata missing from agent response')
        return 1

    output('Step 2/4: Persisting planning snapshot...')

    store = GanttSnapshotStore()
    stored_summary = store.save_snapshot(snapshot, summary_markdown=result.content or '')

    output(f'  Stored snapshot ID: {stored_summary["snapshot_id"]}')
    output(f'  Stored in: {stored_summary["storage_dir"]}')

    output('Step 3/4: Writing planning snapshot files...')

    output_base = args.output or f'{args.project.lower()}_planning_snapshot.json'
    json_path, md_path = _write_gantt_snapshot_files(
        snapshot,
        result.content or '',
        output_base,
    )

    output(f'  Saved: {json_path}')
    output(f'  Saved: {md_path}')

    output('Step 4/4: Reporting summary...')
    _print_workflow_summary('gantt-snapshot', [
        (stored_summary['json_path'], 'stored snapshot JSON'),
        (stored_summary['markdown_path'], 'stored snapshot Markdown'),
        (json_path, 'planning snapshot JSON'),
        (md_path, 'planning snapshot Markdown'),
    ])
    return 0


def _workflow_gantt_snapshot_get(args):
    '''
    Gantt workflow: load a persisted planning snapshot and display/export it.
    '''
    log.debug(
        f'Entering _workflow_gantt_snapshot_get(snapshot_id={args.snapshot_id}, '
        f'project={args.project})'
    )

    from state.gantt_snapshot_store import GanttSnapshotStore

    output('')
    output('=' * 60)
    output('WORKFLOW: gantt-snapshot-get')
    output('=' * 60)
    output('')
    output(f'Snapshot ID: {args.snapshot_id}')
    if args.project:
        output(f'Project: {args.project}')
    output('')
    output('Step 1/2: Loading stored planning snapshot...')

    store = GanttSnapshotStore()
    record = store.get_snapshot(args.snapshot_id, project_key=args.project)
    if not record:
        output(f'ERROR: Stored Gantt snapshot not found: {args.snapshot_id}')
        return 1

    snapshot = record['snapshot']
    summary = record['summary']
    summary_markdown = record['summary_markdown'] or str(
        snapshot.get('summary_markdown') or ''
    )

    output(f'  Project: {summary["project_key"]}')
    output(f'  Created at: {summary["created_at"]}')
    output(f'  Total issues: {summary["total_issues"]}')
    output(f'  Milestones: {summary["milestone_count"]}')
    output(f'  Risks: {summary["risk_count"]}')
    output(f'  Stored in: {summary["storage_dir"]}')

    created_files = []
    if args.output:
        output('Step 2/2: Writing exported snapshot files...')
        json_path, md_path = _write_gantt_snapshot_files(
            snapshot,
            summary_markdown,
            args.output,
        )
        output(f'  Saved: {json_path}')
        output(f'  Saved: {md_path}')
        created_files.extend([
            (json_path, 'exported planning snapshot JSON'),
            (md_path, 'exported planning snapshot Markdown'),
        ])
    else:
        output('Step 2/2: Rendering stored snapshot summary...')
        output('')
        output(summary_markdown or '(No summary markdown stored for this snapshot.)')

    if created_files:
        _print_workflow_summary('gantt-snapshot-get', created_files)

    return 0


def _workflow_gantt_snapshot_list(args):
    '''
    Gantt workflow: list persisted planning snapshots.
    '''
    log.debug(
        f'Entering _workflow_gantt_snapshot_list(project={args.project}, limit={args.limit})'
    )

    from state.gantt_snapshot_store import GanttSnapshotStore

    output('')
    output('=' * 60)
    output('WORKFLOW: gantt-snapshot-list')
    output('=' * 60)
    output('')
    if args.project:
        output(f'Project filter: {args.project}')
    if args.limit:
        output(f'Limit: {args.limit}')
    output('')
    output('Loading stored planning snapshots...')

    store = GanttSnapshotStore()
    snapshots = store.list_snapshots(project_key=args.project, limit=args.limit)
    if not snapshots:
        if args.project:
            output(f'No stored Gantt snapshots found for project {args.project}.')
        else:
            output('No stored Gantt snapshots found.')
        return 0

    output('')
    output(
        'SNAPSHOT  PROJECT  CREATED AT                  ISSUES  MILES  RISKS  BLOCKED'
    )
    output(
        '--------  -------  --------------------------  ------  -----  -----  -------'
    )
    for item in snapshots:
        output(
            f'{item["snapshot_id"]:<8}  '
            f'{item["project_key"]:<7}  '
            f'{item["created_at"]:<26}  '
            f'{item["total_issues"]:>6}  '
            f'{item["milestone_count"]:>5}  '
            f'{item["risk_count"]:>5}  '
            f'{item["blocked_issues"]:>7}'
        )

    output('')
    output(f'Total stored snapshots: {len(snapshots)}')
    return 0


def _workflow_gantt_release_monitor(args):
    '''
    Gantt workflow: release health monitoring -> durable report + exports.
    '''
    log.debug(
        f'Entering _workflow_gantt_release_monitor(project={args.project}, '
        f'releases={args.releases}, scope_label={args.scope_label})'
    )

    from agents.gantt_agent import GanttProjectPlannerAgent
    from agents.gantt_models import ReleaseMonitorRequest
    from state.gantt_release_monitor_store import GanttReleaseMonitorStore

    output('')
    output('=' * 60)
    output('WORKFLOW: gantt-release-monitor')
    output('=' * 60)
    output('')
    output(f'Project: {args.project}')
    if args.releases:
        output(f'Releases: {args.releases}')
    if args.scope_label:
        output(f'Scope label: {args.scope_label}')
    output(f'Gap analysis: {"yes" if args.include_gap_analysis else "no"}')
    output(f'Velocity: {"yes" if args.include_velocity else "no"}')
    output(f'Readiness: {"yes" if args.include_readiness else "no"}')
    output('')
    output('Step 1/4: Building release monitor report...')

    output_base = args.output or f'{args.project.lower()}_release_monitor.json'
    json_path_hint, md_path_hint, xlsx_path_hint = _resolve_gantt_release_monitor_paths(
        output_base,
    )

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

    output('Step 2/4: Persisting release monitor report...')

    store = GanttReleaseMonitorStore()
    stored_summary = store.save_report(
        report,
        summary_markdown=report.summary_markdown,
    )

    output(f'  Stored report ID: {stored_summary["report_id"]}')
    output(f'  Stored in: {stored_summary["storage_dir"]}')

    output('Step 3/4: Writing report files...')
    json_path, md_path = _write_gantt_release_monitor_files(
        report.to_dict(),
        report.summary_markdown or '',
        output_base,
    )

    output(f'  Saved: {json_path}')
    output(f'  Saved: {md_path}')
    if report.output_file:
        output(f'  Saved: {report.output_file}')

    output('Step 4/4: Reporting summary...')
    output(f'  Releases monitored: {len(report.releases_monitored)}')
    output(f'  Total bugs: {report.total_bugs}')
    output(f'  Total P0: {report.total_p0}')
    output(f'  Total P1: {report.total_p1}')

    created_files = [
        (stored_summary['json_path'], 'stored release monitor JSON'),
        (stored_summary['markdown_path'], 'stored release monitor Markdown'),
        (json_path, 'exported release monitor JSON'),
        (md_path, 'exported release monitor Markdown'),
    ]
    if report.output_file:
        created_files.append((report.output_file, 'release monitor workbook'))

    _print_workflow_summary('gantt-release-monitor', created_files)
    return 0


def _workflow_gantt_release_monitor_get(args):
    '''
    Gantt workflow: load a persisted release-monitor report and display/export it.
    '''
    log.debug(
        f'Entering _workflow_gantt_release_monitor_get(report_id={args.report_id}, '
        f'project={args.project})'
    )

    from state.gantt_release_monitor_store import GanttReleaseMonitorStore

    output('')
    output('=' * 60)
    output('WORKFLOW: gantt-release-monitor-get')
    output('=' * 60)
    output('')
    output(f'Report ID: {args.report_id}')
    if args.project:
        output(f'Project: {args.project}')
    output('')
    output('Step 1/2: Loading stored release monitor report...')

    store = GanttReleaseMonitorStore()
    record = store.get_report(args.report_id, project_key=args.project)
    if not record:
        output(f'ERROR: Stored Gantt release monitor report not found: {args.report_id}')
        return 1

    report = record['report']
    summary = record['summary']
    summary_markdown = record['summary_markdown'] or str(
        report.get('summary_markdown') or ''
    )

    output(f'  Project: {summary["project_key"]}')
    output(f'  Created at: {summary["created_at"]}')
    output(f'  Releases: {summary["release_count"]}')
    output(f'  Total bugs: {summary["total_bugs"]}')
    output(f'  Total P0: {summary["total_p0"]}')
    output(f'  Total P1: {summary["total_p1"]}')
    output(f'  Stored in: {summary["storage_dir"]}')

    created_files = []
    if args.output:
        output('Step 2/2: Writing exported report files...')
        json_path, md_path = _write_gantt_release_monitor_files(
            report,
            summary_markdown,
            args.output,
        )
        output(f'  Saved: {json_path}')
        output(f'  Saved: {md_path}')
        created_files.extend([
            (json_path, 'exported release monitor JSON'),
            (md_path, 'exported release monitor Markdown'),
        ])
    else:
        output('Step 2/2: Rendering stored report summary...')
        output('')
        output(summary_markdown or '(No summary markdown stored for this report.)')

    if created_files:
        _print_workflow_summary('gantt-release-monitor-get', created_files)

    return 0


def _workflow_gantt_release_monitor_list(args):
    '''
    Gantt workflow: list persisted release-monitor reports.
    '''
    log.debug(
        f'Entering _workflow_gantt_release_monitor_list(project={args.project}, '
        f'limit={args.limit})'
    )

    from state.gantt_release_monitor_store import GanttReleaseMonitorStore

    output('')
    output('=' * 60)
    output('WORKFLOW: gantt-release-monitor-list')
    output('=' * 60)
    output('')
    if args.project:
        output(f'Project filter: {args.project}')
    if args.limit:
        output(f'Limit: {args.limit}')
    output('')
    output('Loading stored release monitor reports...')

    store = GanttReleaseMonitorStore()
    reports = store.list_reports(project_key=args.project, limit=args.limit)
    if not reports:
        if args.project:
            output(f'No stored release monitor reports found for project {args.project}.')
        else:
            output('No stored release monitor reports found.')
        return 0

    output('')
    output(
        'REPORT ID                            PROJECT  CREATED AT                  RELS  BUGS  P0  P1'
    )
    output(
        '-----------------------------------  -------  --------------------------  ----  ----  --  --'
    )
    for item in reports:
        output(
            f'{item["report_id"]:<35}  '
            f'{item["project_key"]:<7}  '
            f'{item["created_at"]:<26}  '
            f'{item["release_count"]:>4}  '
            f'{item["total_bugs"]:>4}  '
            f'{item["total_p0"]:>2}  '
            f'{item["total_p1"]:>2}'
        )

    output('')
    output(f'Total stored reports: {len(reports)}')
    return 0


def _workflow_gantt_release_survey(args):
    '''
    Gantt workflow: release execution survey -> durable survey + exports.
    '''
    log.debug(
        f'Entering _workflow_gantt_release_survey(project={args.project}, '
        f'releases={args.releases}, scope_label={args.scope_label}, '
        f'survey_mode={args.survey_mode})'
    )

    from agents.gantt_agent import GanttProjectPlannerAgent
    from agents.gantt_models import ReleaseSurveyRequest
    from state.gantt_release_survey_store import GanttReleaseSurveyStore

    output('')
    output('=' * 60)
    output('WORKFLOW: gantt-release-survey')
    output('=' * 60)
    output('')
    output(f'Project: {args.project}')
    if args.releases:
        output(f'Releases: {args.releases}')
    if args.scope_label:
        output(f'Scope label: {args.scope_label}')
    output(f'Survey mode: {args.survey_mode}')
    output('')
    output('Step 1/4: Building release survey...')

    output_base = args.output or f'{args.project.lower()}_release_survey.json'
    json_path_hint, md_path_hint, xlsx_path_hint = _resolve_gantt_release_survey_paths(
        output_base,
    )

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

    output('Step 2/4: Persisting release survey...')

    store = GanttReleaseSurveyStore()
    stored_summary = store.save_survey(
        survey,
        summary_markdown=survey.summary_markdown,
    )

    output(f'  Stored survey ID: {stored_summary["survey_id"]}')
    output(f'  Stored in: {stored_summary["storage_dir"]}')

    output('Step 3/4: Writing survey files...')
    json_path, md_path = _write_gantt_release_survey_files(
        survey.to_dict(),
        survey.summary_markdown or '',
        output_base,
    )

    output(f'  Saved: {json_path}')
    output(f'  Saved: {md_path}')
    if survey.output_file:
        output(f'  Saved: {survey.output_file}')

    output('Step 4/4: Reporting summary...')
    output(f'  Releases surveyed: {len(survey.releases_surveyed)}')
    output(f'  Total tickets: {survey.total_tickets}')
    output(f'  Done: {survey.done_count}')
    output(f'  In progress: {survey.in_progress_count}')
    output(f'  Remaining: {survey.remaining_count}')
    output(f'  Blocked: {survey.blocked_count}')

    created_files = [
        (stored_summary['json_path'], 'stored release survey JSON'),
        (stored_summary['markdown_path'], 'stored release survey Markdown'),
        (json_path, 'exported release survey JSON'),
        (md_path, 'exported release survey Markdown'),
    ]
    if survey.output_file:
        created_files.append((survey.output_file, 'release survey workbook'))

    _print_workflow_summary('gantt-release-survey', created_files)
    return 0


def _workflow_gantt_release_survey_get(args):
    '''
    Gantt workflow: load a persisted release-survey report and display/export it.
    '''
    log.debug(
        f'Entering _workflow_gantt_release_survey_get(survey_id={args.survey_id}, '
        f'project={args.project})'
    )

    from state.gantt_release_survey_store import GanttReleaseSurveyStore

    output('')
    output('=' * 60)
    output('WORKFLOW: gantt-release-survey-get')
    output('=' * 60)
    output('')
    output(f'Survey ID: {args.survey_id}')
    if args.project:
        output(f'Project: {args.project}')
    output('')
    output('Step 1/2: Loading stored release survey...')

    store = GanttReleaseSurveyStore()
    record = store.get_survey(args.survey_id, project_key=args.project)
    if not record:
        output(f'ERROR: Stored Gantt release survey not found: {args.survey_id}')
        return 1

    survey = record['survey']
    summary = record['summary']
    summary_markdown = record['summary_markdown'] or str(
        survey.get('summary_markdown') or ''
    )

    output(f'  Project: {summary["project_key"]}')
    output(f'  Created at: {summary["created_at"]}')
    output(f'  Releases: {summary["release_count"]}')
    output(f'  Total tickets: {summary["total_tickets"]}')
    output(f'  Done: {summary["done_count"]}')
    output(f'  In progress: {summary["in_progress_count"]}')
    output(f'  Remaining: {summary["remaining_count"]}')
    output(f'  Blocked: {summary["blocked_count"]}')
    output(f'  Stored in: {summary["storage_dir"]}')

    created_files = []
    if args.output:
        output('Step 2/2: Writing exported survey files...')
        json_path, md_path = _write_gantt_release_survey_files(
            survey,
            summary_markdown,
            args.output,
        )
        output(f'  Saved: {json_path}')
        output(f'  Saved: {md_path}')
        created_files.extend([
            (json_path, 'exported release survey JSON'),
            (md_path, 'exported release survey Markdown'),
        ])
    else:
        output('Step 2/2: Rendering stored survey summary...')
        output('')
        output(summary_markdown or '(No summary markdown stored for this survey.)')

    if created_files:
        _print_workflow_summary('gantt-release-survey-get', created_files)

    return 0


def _workflow_gantt_release_survey_list(args):
    '''
    Gantt workflow: list persisted release-survey reports.
    '''
    log.debug(
        f'Entering _workflow_gantt_release_survey_list(project={args.project}, '
        f'limit={args.limit})'
    )

    from state.gantt_release_survey_store import GanttReleaseSurveyStore

    output('')
    output('=' * 60)
    output('WORKFLOW: gantt-release-survey-list')
    output('=' * 60)
    output('')
    if args.project:
        output(f'Project filter: {args.project}')
    if args.limit:
        output(f'Limit: {args.limit}')
    output('')
    output('Loading stored release surveys...')

    store = GanttReleaseSurveyStore()
    surveys = store.list_surveys(project_key=args.project, limit=args.limit)
    if not surveys:
        if args.project:
            output(f'No stored release surveys found for project {args.project}.')
        else:
            output('No stored release surveys found.')
        return 0

    output('')
    output(
        'SURVEY ID                            PROJECT  CREATED AT                  RELS  TOTAL  DONE  INPR  LEFT  BLKD'
    )
    output(
        '-----------------------------------  -------  --------------------------  ----  -----  ----  ----  ----  ----'
    )
    for item in surveys:
        output(
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

    output('')
    output(f'Total stored surveys: {len(surveys)}')
    return 0


def _workflow_drucker_hygiene(args):
    '''
    Drucker workflow: Jira project hygiene analysis -> durable report + review session.
    '''
    log.debug(
        f'Entering _workflow_drucker_hygiene(project={args.project}, '
        f'limit={args.limit}, include_done={args.include_done}, stale_days={args.stale_days})'
    )

    from agents.drucker_agent import DruckerCoordinatorAgent
    from state.drucker_report_store import DruckerReportStore

    output('')
    output('=' * 60)
    output('WORKFLOW: drucker-hygiene')
    output('=' * 60)
    output('')
    output(f'Project: {args.project}')
    output(f'Include done issues: {"yes" if args.include_done else "no"}')
    output(f'Stale threshold: {args.stale_days} days')
    output('')
    output('Step 1/4: Building Jira hygiene report...')

    agent = DruckerCoordinatorAgent(project_key=args.project)
    result = agent.run({
        'project_key': args.project,
        'limit': args.limit or 200,
        'include_done': args.include_done,
        'stale_days': args.stale_days,
    })

    if not result.success:
        output(f'ERROR: {result.error}')
        return 1

    report = result.metadata.get('hygiene_report')
    review_session = result.metadata.get('review_session')

    if not report:
        output('ERROR: Drucker hygiene report missing from agent response')
        return 1

    output('Step 2/4: Persisting hygiene report...')

    store = DruckerReportStore()
    stored_summary = store.save_report(report, summary_markdown=result.content or '')

    output(f'  Stored report ID: {stored_summary["report_id"]}')
    output(f'  Stored in: {stored_summary["storage_dir"]}')

    output('Step 3/4: Writing report files...')

    output_base = args.output or f'{args.project.lower()}_drucker_hygiene.json'
    json_path, md_path, review_path = _write_drucker_report_files(
        report,
        result.content or '',
        review_session or {},
        output_base,
    )

    output(f'  Saved: {json_path}')
    output(f'  Saved: {md_path}')
    output(f'  Saved: {review_path}')

    output('Step 4/4: Reporting summary...')
    output(f'  Findings: {report.get("summary", {}).get("finding_count", 0)}')
    output(f'  Proposed actions: {report.get("summary", {}).get("action_count", 0)}')
    output(f'  Tickets with findings: {report.get("summary", {}).get("tickets_with_findings", 0)}')

    _print_workflow_summary('drucker-hygiene', [
        (stored_summary['json_path'], 'stored hygiene report JSON'),
        (stored_summary['markdown_path'], 'stored hygiene report Markdown'),
        (json_path, 'exported hygiene report JSON'),
        (md_path, 'exported hygiene report Markdown'),
        (review_path, 'review session JSON'),
    ])
    return 0


def _workflow_drucker_issue_check(args):
    '''
    Drucker workflow: single-ticket intake validation -> durable report + review session.
    '''
    log.debug(
        f'Entering _workflow_drucker_issue_check(project={args.project}, '
        f'ticket_key={args.ticket_key}, stale_days={args.stale_days})'
    )

    from agents.drucker_agent import DruckerCoordinatorAgent
    from state.drucker_report_store import DruckerReportStore

    output('')
    output('=' * 60)
    output('WORKFLOW: drucker-issue-check')
    output('=' * 60)
    output('')
    output(f'Project: {args.project}')
    output(f'Ticket: {args.ticket_key}')
    output(f'Stale threshold: {args.stale_days} days')
    output('')
    output('Step 1/4: Building Drucker issue-check report...')

    agent = DruckerCoordinatorAgent(project_key=args.project)
    result = agent.run({
        'project_key': args.project,
        'ticket_key': args.ticket_key,
        'stale_days': args.stale_days,
    })

    if not result.success:
        output(f'ERROR: {result.error}')
        return 1

    report = result.metadata.get('hygiene_report')
    review_session = result.metadata.get('review_session')

    if not report:
        output('ERROR: Drucker issue-check report missing from agent response')
        return 1

    output('Step 2/4: Persisting issue-check report...')

    store = DruckerReportStore()
    stored_summary = store.save_report(report, summary_markdown=result.content or '')

    output(f'  Stored report ID: {stored_summary["report_id"]}')
    output(f'  Stored in: {stored_summary["storage_dir"]}')

    output('Step 3/4: Writing report files...')

    default_base = (
        f'{args.project.lower()}_{args.ticket_key.lower()}_drucker_issue_check.json'
    )
    output_base = args.output or default_base
    json_path, md_path, review_path = _write_drucker_report_files(
        report,
        result.content or '',
        review_session or {},
        output_base,
    )

    output(f'  Saved: {json_path}')
    output(f'  Saved: {md_path}')
    output(f'  Saved: {review_path}')

    output('Step 4/4: Reporting summary...')
    output(f'  Findings: {report.get("summary", {}).get("finding_count", 0)}')
    output(f'  Proposed actions: {report.get("summary", {}).get("action_count", 0)}')
    output(
        '  Tickets with findings: '
        f'{report.get("summary", {}).get("tickets_with_findings", 0)}'
    )

    _print_workflow_summary('drucker-issue-check', [
        (stored_summary['json_path'], 'stored issue-check report JSON'),
        (stored_summary['markdown_path'], 'stored issue-check report Markdown'),
        (json_path, 'exported issue-check report JSON'),
        (md_path, 'exported issue-check report Markdown'),
        (review_path, 'review session JSON'),
    ])
    return 0


def _workflow_drucker_intake_report(args):
    '''
    Drucker workflow: recent-ticket intake validation -> durable report + review session.
    '''
    log.debug(
        f'Entering _workflow_drucker_intake_report(project={args.project}, '
        f'limit={args.limit}, stale_days={args.stale_days}, since={args.since})'
    )

    from agents.drucker_agent import DruckerCoordinatorAgent
    from state.drucker_report_store import DruckerReportStore

    output('')
    output('=' * 60)
    output('WORKFLOW: drucker-intake-report')
    output('=' * 60)
    output('')
    output(f'Project: {args.project}')
    output(f'Stale threshold: {args.stale_days} days')
    if args.since:
        output(f'Since: {args.since}')
    output('')
    output('Step 1/4: Building Drucker intake report...')

    agent = DruckerCoordinatorAgent(project_key=args.project)
    result = agent.run({
        'project_key': args.project,
        'limit': args.limit or 200,
        'stale_days': args.stale_days,
        'since': args.since,
        'recent_only': True,
    })

    if not result.success:
        output(f'ERROR: {result.error}')
        return 1

    report = result.metadata.get('hygiene_report')
    review_session = result.metadata.get('review_session')

    if not report:
        output('ERROR: Drucker intake report missing from agent response')
        return 1

    output('Step 2/4: Persisting intake report...')

    store = DruckerReportStore()
    stored_summary = store.save_report(report, summary_markdown=result.content or '')

    output(f'  Stored report ID: {stored_summary["report_id"]}')
    output(f'  Stored in: {stored_summary["storage_dir"]}')

    output('Step 3/4: Writing report files...')

    output_base = args.output or f'{args.project.lower()}_drucker_intake_report.json'
    json_path, md_path, review_path = _write_drucker_report_files(
        report,
        result.content or '',
        review_session or {},
        output_base,
    )

    output(f'  Saved: {json_path}')
    output(f'  Saved: {md_path}')
    output(f'  Saved: {review_path}')

    output('Step 4/4: Reporting summary...')
    output(f'  Findings: {report.get("summary", {}).get("finding_count", 0)}')
    output(f'  Proposed actions: {report.get("summary", {}).get("action_count", 0)}')
    output(
        '  Source tickets scanned: '
        f'{report.get("summary", {}).get("source_ticket_count", 0)}'
    )

    _print_workflow_summary('drucker-intake-report', [
        (stored_summary['json_path'], 'stored intake report JSON'),
        (stored_summary['markdown_path'], 'stored intake report Markdown'),
        (json_path, 'exported intake report JSON'),
        (md_path, 'exported intake report Markdown'),
        (review_path, 'review session JSON'),
    ])
    return 0


def _workflow_drucker_bug_activity(args):
    '''
    Drucker workflow: daily bug activity summary.
    '''
    log.debug(
        f'Entering _workflow_drucker_bug_activity(project={args.project}, '
        f'target_date={args.target_date})'
    )

    from agents.drucker_agent import DruckerCoordinatorAgent

    output('')
    output('=' * 60)
    output('WORKFLOW: drucker-bug-activity')
    output('=' * 60)
    output('')
    output(f'Project: {args.project}')
    output(f'Target date: {args.target_date or "today"}')
    output('')
    output('Step 1/2: Building Drucker bug activity report...')

    agent = DruckerCoordinatorAgent(project_key=args.project)
    activity = agent.analyze_bug_activity(
        project_key=args.project,
        target_date=args.target_date,
    )
    summary_markdown = agent.format_bug_activity_report(activity)

    output('Step 2/2: Writing report files...')

    target_suffix = str(activity.get('date') or 'today').replace('-', '')
    output_base = (
        args.output
        or f'{args.project.lower()}_drucker_bug_activity_{target_suffix}.json'
    )
    json_path, md_path = _write_drucker_activity_files(
        activity,
        summary_markdown,
        output_base,
    )

    output(f'  Saved: {json_path}')
    output(f'  Saved: {md_path}')
    output(f'  Bugs opened: {activity.get("summary", {}).get("bugs_opened", 0)}')
    output(
        '  Status transitions: '
        f'{activity.get("summary", {}).get("status_transitions", 0)}'
    )
    output(
        '  Bugs with comments: '
        f'{activity.get("summary", {}).get("bugs_with_comments", 0)}'
    )

    _print_workflow_summary('drucker-bug-activity', [
        (json_path, 'exported bug activity JSON'),
        (md_path, 'exported bug activity Markdown'),
    ])
    return 0


def _workflow_gantt_poll(args):
    '''
    Gantt workflow: run one or more scheduled planning/release-monitor cycles.
    '''
    log.debug(
        f'Entering _workflow_gantt_poll(project={args.project}, '
        f'max_cycles={args.max_cycles}, poll_interval={args.poll_interval})'
    )

    from agents.gantt_agent import GanttProjectPlannerAgent

    output('')
    output('=' * 60)
    output('WORKFLOW: gantt-poll')
    output('=' * 60)
    output('')
    output(f'Project: {args.project}')
    output(f'Planning snapshots: yes')
    output(
        'Release monitor: '
        f'{"yes" if (args.run_release_monitor or args.releases or args.scope_label) else "no"}'
    )
    output(f'Release survey: {"yes" if args.run_release_survey else "no"}')
    if args.run_release_survey:
        output(f'Release survey mode: {args.survey_mode}')
    output(f'Poll interval: {args.poll_interval} seconds')
    output(
        'Cycles: '
        f'{"continuous" if args.max_cycles == 0 else args.max_cycles}'
    )
    output(f'Notify Shannon: {"yes" if args.notify_shannon else "no"}')
    output('')
    output('Running scheduled Gantt poller...')

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

    output('')
    output('Cycle summary:')
    for cycle in result.get('cycle_summaries', []):
        output(
            f'  Cycle {cycle.get("cycle_number")}: '
            f'{cycle.get("task_count", 0)} task(s), '
            f'{cycle.get("notification_count", 0)} notification(s), '
            f'{"ok" if cycle.get("ok") else "error"}'
        )
        for error in cycle.get('errors', []):
            output(f'    ERROR: {error}')

    last_tick = result.get('last_tick') or {}
    for task in last_tick.get('tasks', []):
        if task.get('task_type') == 'planning_snapshot':
            stored = task.get('stored', {})
            output(
                '  Latest planning snapshot: '
                f'{stored.get("snapshot_id") or task.get("snapshot", {}).get("snapshot_id", "")}'
            )
        if task.get('task_type') == 'release_monitor':
            stored = task.get('stored', {})
            output(
                '  Latest release report: '
                f'{stored.get("report_id") or task.get("report", {}).get("report_id", "")}'
            )
        if task.get('task_type') == 'release_survey':
            stored = task.get('stored', {})
            output(
                '  Latest release survey: '
                f'{stored.get("survey_id") or task.get("survey", {}).get("survey_id", "")}'
            )

    return 0 if result.get('ok', False) else 1


def _workflow_drucker_poll(args):
    '''
    Drucker workflow: run one or more scheduled hygiene cycles.
    '''
    log.debug(
        f'Entering _workflow_drucker_poll(project={args.project}, '
        f'max_cycles={args.max_cycles}, poll_interval={args.poll_interval})'
    )

    from agents.drucker_agent import DruckerCoordinatorAgent

    output('')
    output('=' * 60)
    output('WORKFLOW: drucker-poll')
    output('=' * 60)
    output('')
    output(f'Project: {args.project or "from polling config"}')
    if args.poll_config:
        output(f'Polling config: {args.poll_config}')
        if args.poll_job:
            output(f'Polling job: {args.poll_job}')
    else:
        output(f'Stale threshold: {args.stale_days} days')
        output(f'Recent only: {"yes" if args.recent_only else "no"}')
        if args.since:
            output(f'Since: {args.since}')
    output(f'Poll interval: {args.poll_interval} seconds')
    output(
        'Cycles: '
        f'{"continuous" if args.max_cycles == 0 else args.max_cycles}'
    )
    output(f'Notify Shannon: {"yes" if args.notify_shannon else "no"}')
    if getattr(args, 'github_repos', None):
        output(f'GitHub repos: {", ".join(args.github_repos)}')
        output(f'GitHub stale threshold: {args.github_stale_days} days')
    output('')
    output('Running scheduled Drucker poller...')

    agent = DruckerCoordinatorAgent(project_key=args.project)
    poller_spec = {
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

    output('')
    output('Cycle summary:')
    for cycle in result.get('cycle_summaries', []):
        output(
            f'  Cycle {cycle.get("cycle_number")}: '
            f'{cycle.get("task_count", 0)} task(s), '
            f'{cycle.get("notification_count", 0)} notification(s), '
            f'{"ok" if cycle.get("ok") else "error"}'
        )
        for error in cycle.get('errors', []):
            output(f'    ERROR: {error}')

    last_tick = result.get('last_tick') or {}
    for task in last_tick.get('tasks', []):
        if task.get('job_id'):
            output(f'  Job {task.get("job_id")}:')
        if task.get('task_type') == 'hygiene_report':
            stored = task.get('stored', {})
            output(
                '    Latest hygiene report: '
                f'{stored.get("report_id") or task.get("report", {}).get("report_id", "")}'
            )
        if task.get('task_type') == 'ticket_intake_report':
            stored = task.get('stored', {})
            output(
                '    Latest intake report: '
                f'{stored.get("report_id") or task.get("report", {}).get("report_id", "")}'
            )
        if task.get('task_type') == 'github_pr_hygiene':
            repo = task.get('repo', '')
            report = task.get('report', {})
            output(f'    GitHub PR hygiene ({repo}): '
                   f'{report.get("stale_count", 0)} stale, '
                   f'{report.get("missing_review_count", 0)} missing reviews')

    return 0 if result.get('ok', False) else 1


def _workflow_hypatia_generate(args):
    '''
    Hypatia workflow: build a source-grounded documentation record and stage
    review-gated publication targets for repo Markdown and Confluence.
    '''
    log.debug(
        f'Entering _workflow_hypatia_generate(project={args.project}, '
        f'doc_title={args.doc_title}, doc_type={args.doc_type}, execute={args.execute})'
    )

    from agents.hypatia_agent import HypatiaDocumentationAgent
    from state.hypatia_record_store import HypatiaRecordStore

    output('')
    output('=' * 60)
    output('WORKFLOW: hypatia-generate')
    output('=' * 60)
    output('')
    output(f'Document title: {args.doc_title or args.confluence_title or "auto"}')
    output(f'Document class: {args.doc_type}')
    output(f'Project: {args.project or "n/a"}')
    output(f'Source files: {len(args.docs or [])}')
    output(f'Publish approved changes now: {"yes" if args.execute else "no"}')
    output('')
    output('Step 1/4: Generating documentation plan...')

    agent = HypatiaDocumentationAgent(project_key=args.project)
    request = {
        'title': args.doc_title or '',
        'doc_type': args.doc_type,
        'project_key': args.project or '',
        'summary': args.doc_summary or '',
        'source_paths': list(args.docs or []),
        'evidence_paths': list(getattr(args, 'evidence', None) or []),
        'target_file': args.target_file,
        'confluence_title': args.confluence_title,
        'confluence_page': args.confluence_page,
        'confluence_space': args.confluence_space,
        'confluence_parent_id': args.confluence_parent_id,
        'version_message': args.version_message,
        'validation_profile': getattr(args, 'validation_profile', 'default'),
    }

    record, review_session = agent.plan_documentation(
        agent._normalize_request(request)
    )

    output('Step 2/4: Persisting documentation record...')

    store = HypatiaRecordStore()
    stored_summary = store.save_record(record, summary_markdown=record.summary_markdown)

    output(f'  Stored document ID: {stored_summary["doc_id"]}')
    output(f'  Stored in: {stored_summary["storage_dir"]}')

    output('Step 3/4: Writing documentation artifacts...')

    output_base = args.output or f'{record.doc_id}_hypatia_record.json'
    json_path, md_path, review_path, patch_paths = _write_hypatia_record_files(
        record.to_dict(),
        review_session.to_dict(),
        output_base,
    )

    output(f'  Saved: {json_path}')
    output(f'  Saved: {md_path}')
    output(f'  Saved: {review_path}')
    if patch_paths:
        output(f'  Saved patch drafts: {len(patch_paths)}')

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

    output('Step 4/4: Review and publication summary...')
    output(f'  Patches: {len(record.patches)}')
    output(f'  Validation status: {"valid" if record.validation.get("valid") else "blocked"}')
    output(f'  Warnings: {len(record.warnings)}')

    if args.execute:
        if not record.validation.get('valid'):
            output('ERROR: Hypatia record has blocking validation issues; refusing to publish.')
            return 1

        agent.review_agent.approve_all(review_session)
        publications = agent.publish_approved(review_session)
        store.record_publications(record.doc_id, publications)

        publications_path = _write_hypatia_publication_file(
            publications,
            output_base,
        )
        created_files.append((publications_path, 'publication results JSON'))

        output(f'  Published targets: {sum(1 for item in publications if item.status == "published")}')
        output(f'  Publication log: {publications_path}')

    _print_workflow_summary('hypatia-generate', created_files)
    return 0


def _write_gantt_snapshot_files(
    snapshot: dict[str, Any],
    summary_markdown: str,
    output_base: str,
):
    '''
    Write snapshot JSON + Markdown files and return their paths.
    '''
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() == '.md':
        output_root = output_root or str(
            snapshot.get('project_key') or 'gantt_snapshot'
        ).lower()
    elif output_ext.lower() != '.json':
        output_root = output_base

    json_path = output_root + '.json'
    md_path = output_root + '.md'

    os.makedirs(os.path.dirname(json_path) or '.', exist_ok=True)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, default=str)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(summary_markdown or '')

    return json_path, md_path


def _resolve_gantt_release_monitor_paths(output_base: str) -> tuple[str, str, str]:
    '''
    Resolve JSON, Markdown, and xlsx paths for release-monitor workflow output.
    '''
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() == '.md':
        output_root = output_root or 'gantt_release_monitor'
    elif output_ext.lower() != '.json':
        output_root = output_base

    return output_root + '.json', output_root + '.md', output_root + '.xlsx'


def _write_gantt_release_monitor_files(
    report: dict[str, Any],
    summary_markdown: str,
    output_base: str,
):
    '''
    Write release-monitor report JSON + Markdown files and return their paths.
    '''
    json_path, md_path, _xlsx_path = _resolve_gantt_release_monitor_paths(output_base)

    os.makedirs(os.path.dirname(json_path) or '.', exist_ok=True)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(summary_markdown or '')

    return json_path, md_path


def _resolve_gantt_release_survey_paths(output_base: str) -> tuple[str, str, str]:
    '''
    Resolve JSON, Markdown, and xlsx paths for release-survey workflow output.
    '''
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() == '.md':
        output_root = output_root or 'gantt_release_survey'
    elif output_ext.lower() != '.json':
        output_root = output_base

    return output_root + '.json', output_root + '.md', output_root + '.xlsx'


def _write_gantt_release_survey_files(
    survey: dict[str, Any],
    summary_markdown: str,
    output_base: str,
):
    '''
    Write release-survey report JSON + Markdown files and return their paths.
    '''
    json_path, md_path, _xlsx_path = _resolve_gantt_release_survey_paths(output_base)

    os.makedirs(os.path.dirname(json_path) or '.', exist_ok=True)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(survey, f, indent=2, default=str)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(summary_markdown or '')

    return json_path, md_path


def _write_drucker_report_files(
    report: dict[str, Any],
    summary_markdown: str,
    review_session: dict[str, Any],
    output_base: str,
):
    '''
    Write Drucker report JSON + Markdown + review-session JSON files.
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


def _write_drucker_activity_files(
    activity: dict[str, Any],
    summary_markdown: str,
    output_base: str,
):
    '''
    Write Drucker bug-activity JSON + Markdown files.
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


def _write_hypatia_record_files(
    record: dict[str, Any],
    review_session: dict[str, Any],
    output_base: str,
):
    '''
    Write Hypatia record JSON + Markdown + review-session JSON + patch drafts.
    '''
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() == '.md':
        output_root = output_root or str(
            record.get('doc_id') or 'hypatia_record'
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

    patch_paths: list[str] = []
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


def _write_hypatia_publication_file(
    publications: list[Any],
    output_base: str,
) -> str:
    '''
    Write Hypatia publication results JSON and return its path.
    '''
    output_root, output_ext = os.path.splitext(output_base)
    if output_ext.lower() not in ('.json', '.md'):
        output_root = output_base

    publications_path = output_root + '_publications.json'
    payload = [
        publication.to_dict() if hasattr(publication, 'to_dict') else publication
        for publication in publications
    ]

    os.makedirs(os.path.dirname(publications_path) or '.', exist_ok=True)
    with open(publications_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, default=str)

    return publications_path


def cmd_resume(args):
    '''
    Resume a saved session.
    '''
    log.debug(f'cmd_resume(session={args.resume})')
    
    from state.session import SessionManager
    from state.persistence import get_persistence
    from agents.orchestrator import ReleasePlanningOrchestrator
    
    persistence = get_persistence(args.persistence_format)
    session_manager = SessionManager(persistence=persistence)
    
    session = session_manager.resume_session(args.resume)
    
    if not session:
        output(f'Session not found: {args.session}')
        return 1
    
    output('')
    output('=' * 60)
    output(f'RESUMING SESSION: {session.session_id}')
    output('=' * 60)
    output('')
    output(f'Project: {session.project_key}')
    output(f'Current step: {session.current_step}')
    output(f'Completed steps: {", ".join(session.completed_steps) or "None"}')
    output('')
    
    # Create orchestrator with session state
    orchestrator = ReleasePlanningOrchestrator()
    orchestrator.state.project_key = session.project_key
    orchestrator.state.roadmap_data = session.roadmap_data
    orchestrator.state.jira_state = session.jira_state
    orchestrator.state.release_plan = session.release_plan
    orchestrator.state.current_step = session.current_step
    
    # Determine what to do based on current step
    if session.current_step == 'analysis':
        output('Resuming from analysis step...')
        result = orchestrator._run_planning()
    elif session.current_step == 'planning':
        output('Plan is ready for review.')
        output(orchestrator._format_plan())
        result = None
    elif session.current_step == 'review':
        output('Resuming review...')
        result = orchestrator._run_execution()
    else:
        output(f'Unknown step: {session.current_step}')
        return 1
    
    if result:
        if result.success:
            output(result.content)
        else:
            output(f'ERROR: {result.error}')
            return 1
    
    return 0


# ****************************************************************************************
# Argument handling
# ****************************************************************************************

def handle_args():
    '''
    Parse and validate command line arguments.
    All commands use -- style flags (e.g. --invoke-llm, --build-excel-map).
    '''
    global _quiet_mode
    
    parser = argparse.ArgumentParser(
        description='Cornelis Agent Pipeline - Release Planning Automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s --plan --project PROJ --roadmap slides.pptx
  %(prog)s --analyze --project PROJ --quick
  %(prog)s --vision roadmap.png roadmap2.xlsx
  %(prog)s --workflow gantt-snapshot --project STL
  %(prog)s --workflow gantt-snapshot --project STL --planning-horizon 120 --output stl_snapshot.json
  %(prog)s --workflow gantt-snapshot --project STL --evidence build.json test.yaml
  %(prog)s --workflow gantt-snapshot-list --project STL
  %(prog)s --workflow gantt-snapshot-get --snapshot-id a1b2c3d4
  %(prog)s --workflow gantt-release-monitor --project STL --releases 12.1.1.x,12.2.0.x
  %(prog)s --workflow gantt-release-monitor --project STL --scope-label CN6000 --output stl_release_monitor.json
  %(prog)s --workflow gantt-release-monitor-list --project STL
  %(prog)s --workflow gantt-release-monitor-get --report-id 12345678-1234-1234-1234-123456789abc
  %(prog)s --workflow gantt-release-survey --project STL --releases 12.2.0.x --scope-label CN6000
  %(prog)s --workflow gantt-release-survey-list --project STL
  %(prog)s --workflow gantt-release-survey-get --survey-id 12345678-1234-1234-1234-123456789abc
  %(prog)s --workflow gantt-poll --project STL --run-release-monitor --releases 12.1.1.x --max-cycles 2 --poll-interval 60
  %(prog)s --workflow drucker-bug-activity --project STL --target-date 2026-03-25
  %(prog)s --workflow drucker-hygiene --project STL
  %(prog)s --workflow drucker-hygiene --project STL --stale-days 21 --output stl_hygiene.json
  %(prog)s --workflow drucker-intake-report --project STL --since "2026-03-24 00:00"
  %(prog)s --workflow drucker-issue-check --project STL --ticket-key STL-12345
  %(prog)s --workflow drucker-poll --poll-config config/drucker_polling.yaml --project STL --max-cycles 2
  %(prog)s --workflow drucker-poll --project STL --max-cycles 2 --poll-interval 300 --notify-shannon
  %(prog)s --workflow drucker-poll --project STL --recent-only --max-cycles 2 --poll-interval 300
  %(prog)s --workflow hypatia-generate --doc-title "STL Build Notes" --docs README.md AGENTS.md
  %(prog)s --workflow hypatia-generate --doc-title "Fabric Bring-Up Guide" --doc-type how_to --docs docs/source.md --target-file docs/fabric-bring-up.md
  %(prog)s --workflow hypatia-generate --doc-title "Release Notes Support" --docs notes.md --evidence release.json --doc-validation strict
  %(prog)s --workflow hypatia-generate --doc-title "STL Weekly Summary" --docs README.md --confluence-title "STL Weekly Summary" --confluence-space ENG
  %(prog)s --build-excel-map STL-74071
  %(prog)s --build-excel-map STL-74071 STL-76297 --hierarchy 2 --output my_map.xlsx
  %(prog)s --invoke-llm prompt.md
  %(prog)s --invoke-llm "Summarize this data" --attachments data.csv
  %(prog)s --invoke-llm prompt.md --attachments screenshot.png report.csv
  %(prog)s --sessions --list-sessions
  %(prog)s --resume abc123
  %(prog)s --workflow feature-plan --project STL --feature "Add PQC device support"
  %(prog)s --workflow feature-plan --project STL --feature "Add PQC device" --docs spec.pdf --execute
  %(prog)s --workflow feature-plan --project STLSB --feature-prompt RedfishRDE.md
  %(prog)s --workflow feature-plan --project STLSB --feature-prompt RedfishRDE.md --output-dir /tmp/out
  %(prog)s --workflow feature-plan --project STL --feature "Add PQC device" --scope-doc scope.json
  %(prog)s --workflow feature-plan --project STL --feature "Add PQC device" --scope-doc scope.md --execute
  %(prog)s --env .env_sandbox --workflow feature-plan --project STLSB --feature "Redfish RDE" --scope-doc RedfishRDE.md
  %(prog)s --workflow feature-plan --project STLSB --plan-file plans/STLSB-redfish/plan.json
  %(prog)s --workflow feature-plan --project STLSB --plan-file plans/STLSB-redfish/plan.json --execute
  %(prog)s --workflow feature-plan --project STL --plan-file plan.json --initiative STL-74071 --execute
        '''
    )
    
    # Global options
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Suppress output to stdout')
    parser.add_argument('--env', default=None, metavar='FILE',
                       help='Path to a .env file to load (overrides the default .env). '
                            'Example: --env .env_sandbox')
    parser.add_argument('--persistence-format', choices=['json', 'sqlite', 'both'],
                       default='json', help='Session persistence format')
    
    # ---- Command flags (mutually exclusive) ------------------------------------
    # --plan: Run release planning workflow
    parser.add_argument('--plan', action='store_true',
                       help='Run release planning workflow')
    # --analyze: Analyze Jira project
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze Jira project')
    # --vision: Analyze roadmap files (takes 1+ file paths)
    parser.add_argument('--vision', nargs='+', default=None, metavar='FILE',
                       help='Analyze roadmap file(s)')
    # --sessions: Manage saved sessions
    parser.add_argument('--sessions', action='store_true',
                       help='Manage saved sessions')
    # --build-excel-map: Build multi-sheet Excel map (takes 1+ ticket keys)
    parser.add_argument('--build-excel-map', nargs='+', default=None, metavar='TICKET',
                       dest='build_excel_map',
                       help='Build multi-sheet Excel map from root ticket key(s)')
    # --invoke-llm: Send a prompt to the configured LLM (takes prompt text or file path)
    parser.add_argument('--invoke-llm', default=None, metavar='PROMPT',
                       dest='invoke_llm',
                       help='Send a prompt (text or .md/.txt file path) to the configured LLM')
    # --resume: Resume a saved session (takes session ID)
    parser.add_argument('--resume', default=None, metavar='SESSION_ID',
                       help='Resume a saved session by ID')
    # --workflow: Run a named multi-step workflow
    parser.add_argument('--workflow', default=None, metavar='NAME',
                       dest='workflow_name',
                       help='Run a named workflow (e.g. "bug-report")')
    
    # ---- Options for --workflow ------------------------------------------------
    parser.add_argument('--filter', default=None, metavar='NAME',
                       dest='workflow_filter',
                       help='Jira filter name to look up (used by --workflow bug-report)')
    parser.add_argument('--prompt', default=None, metavar='FILE',
                       dest='workflow_prompt',
                       help='Prompt file for LLM step (used by --workflow bug-report, '
                            'default: config/prompts/cn5000_bugs_clean.md)')
    parser.add_argument('--d-columns', nargs='+', default=None, metavar='COL',
                       dest='dashboard_columns',
                       help='Column names for the Excel Dashboard sheet '
                            '(used by --workflow bug-report). Each named column '
                            'gets a COUNTIF-based pivot table. Names are '
                            'case-insensitive. '
                            'Example: --d-columns Phase Customer Product Module Priority')
    
    # ---- Options for --workflow feature-plan -----------------------------------
    parser.add_argument('--feature', default=None, metavar='TEXT',
                       help='Feature description for --workflow feature-plan '
                            '(e.g. "Add PQC device support to CN5000 board")')
    parser.add_argument('--feature-prompt', default=None, metavar='FILE',
                       dest='feature_prompt',
                       help='Markdown file with a rich feature prompt. '
                            'When provided, its content is used as the feature '
                            'request and takes precedence over --feature. '
                            'Used by --workflow feature-plan.')
    parser.add_argument('--scope-doc', default=None, metavar='FILE',
                       dest='scope_doc',
                       help='Pre-existing scope document (JSON, Markdown, PDF, DOCX). '
                            'Skips research/HW-analysis/scoping phases and jumps '
                            'straight to Jira plan generation. '
                            'Used by --workflow feature-plan.')
    parser.add_argument('--docs', nargs='*', default=None, metavar='FILE',
                       help='Spec documents / datasheets for --workflow feature-plan')
    parser.add_argument('--plan-file', default=None, metavar='FILE',
                       dest='plan_file',
                       help='Path to a previously generated plan.json. '
                            'Loads the plan and prints a summary (dry-run). '
                            'Combine with --execute to push tickets into Jira. '
                            'Skips all agentic phases. '
                            'Used by --workflow feature-plan.')
    parser.add_argument('--initiative', default=None, metavar='KEY',
                       help='Optional existing Initiative ticket key (e.g. STL-74071). '
                            'If supplied, the ticket is validated as type Initiative '
                            'and all created Epics become its children. '
                            'If omitted, a new Initiative is auto-created from the '
                            'plan feature name. '
                            'Used by --workflow feature-plan.')
    parser.add_argument('--execute', action='store_true',
                       help='Actually create Jira tickets (default: dry-run). '
                            'Used by --workflow feature-plan.')
    parser.add_argument('--force', action='store_true',
                       help='Skip duplicate-ticket confirmation prompts. '
                            'Without --force, the agent pauses and asks before '
                            'creating a ticket whose summary already exists in '
                            'the project. Used by --workflow feature-plan.')
    parser.add_argument('--feature-tag', default=None, metavar='TAG',
                       dest='feature_tag',
                       help='Override the auto-generated [Tag] prefix for Epic '
                            'summaries. E.g. --feature-tag "[K8s]". '
                            'During dry-run the computed tags are shown so you '
                            'can decide whether to override. '
                            'Used by --workflow feature-plan.')
    parser.add_argument('--cleanup', default=None, metavar='CSV',
                       help='Delete all tickets listed in a created_tickets.csv '
                            'file (produced by --execute). Dry-run by default; '
                            'add --execute to actually delete. Children are '
                            'deleted before parents. '
                            'Used by --workflow feature-plan.')
    parser.add_argument('--output-dir', default=None, metavar='DIR',
                       dest='output_dir',
                       help='Root directory for output. The standard '
                            'plans/<PROJECT>-<slug>/ subdir is created '
                            'inside it. Default root: current directory. '
                            'Used by --workflow feature-plan.')
    parser.add_argument('--planning-horizon', type=int, default=90, metavar='DAYS',
                       dest='planning_horizon',
                       help='Planning horizon in days for --workflow gantt-snapshot '
                            '(default: 90).')
    parser.add_argument('--releases', default=None, metavar='CSV',
                       dest='releases',
                       help='Comma-separated release names for --workflow gantt-release-monitor, '
                            '--workflow gantt-release-survey, and --workflow gantt-poll.')
    parser.add_argument('--scope-label', default=None, metavar='LABEL',
                       dest='scope_label',
                       help='Optional scope label for --workflow gantt-release-monitor, '
                            '--workflow gantt-release-survey, and --workflow gantt-poll.')
    parser.add_argument('--survey-mode', default='feature-dev', metavar='MODE',
                       dest='survey_mode',
                       help='Release survey mode for --workflow gantt-release-survey '
                            'and --workflow gantt-poll. Use "feature-dev" '
                            '(exclude bugs) or "bug" (only bugs).')
    parser.add_argument('--run-release-monitor', action='store_true',
                       dest='run_release_monitor',
                       help='Include release-monitor work during --workflow gantt-poll '
                            'even when --releases is omitted.')
    parser.add_argument('--run-release-survey', action='store_true',
                       dest='run_release_survey',
                       help='Include release-survey work during --workflow gantt-poll.')
    parser.add_argument('--include-done', action='store_true',
                       dest='include_done',
                       help='Include done/closed issues in --workflow gantt-snapshot, '
                            '--workflow gantt-poll, and Drucker workflows.')
    parser.add_argument('--snapshot-id', default=None, metavar='ID',
                       dest='snapshot_id',
                       help='Stored snapshot ID for --workflow gantt-snapshot-get.')
    parser.add_argument('--report-id', default=None, metavar='ID',
                       dest='report_id',
                       help='Stored report ID for --workflow gantt-release-monitor-get.')
    parser.add_argument('--survey-id', default=None, metavar='ID',
                       dest='survey_id',
                       help='Stored survey ID for --workflow gantt-release-survey-get.')
    parser.add_argument('--no-gap-analysis', action='store_false',
                       dest='include_gap_analysis',
                       help='Disable roadmap gap analysis for --workflow gantt-release-monitor.')
    parser.add_argument('--no-bug-report', action='store_false',
                       dest='include_bug_report',
                       help='Disable bug status/priority summary for --workflow gantt-release-monitor.')
    parser.add_argument('--no-velocity', action='store_false',
                       dest='include_velocity',
                       help='Disable velocity metrics for --workflow gantt-release-monitor.')
    parser.add_argument('--no-readiness', action='store_false',
                       dest='include_readiness',
                       help='Disable readiness assessment for --workflow gantt-release-monitor.')
    parser.add_argument('--no-compare-previous', action='store_false',
                       dest='compare_to_previous',
                       help='Disable previous-report delta comparison for --workflow gantt-release-monitor.')
    parser.add_argument('--stale-days', type=int, default=30, metavar='DAYS',
                       dest='stale_days',
                       help='Stale-ticket threshold in days for Drucker workflows '
                            '(default: 30).')
    parser.add_argument('--ticket-key', default=None, metavar='KEY',
                       dest='ticket_key',
                       help='Specific Jira ticket key for --workflow drucker-issue-check.')
    parser.add_argument('--target-date', default=None, metavar='YYYY-MM-DD',
                       dest='target_date',
                       help='Target date for --workflow drucker-bug-activity '
                            '(defaults to today).')
    parser.add_argument('--since', default=None, metavar='WHEN',
                       dest='since',
                       help='Optional checkpoint override for --workflow drucker-poll '
                            'when using --recent-only or --workflow drucker-intake-report. '
                            'Accepts ISO timestamps or "YYYY-MM-DD HH:MM".')
    parser.add_argument('--recent-only', action='store_true',
                       dest='recent_only',
                       help='Use recent-ticket intake scanning during --workflow drucker-poll '
                            'instead of full-project hygiene scans.')
    parser.add_argument('--poll-config', default=None, metavar='FILE',
                       dest='poll_config',
                       help='YAML config for --workflow drucker-poll. '
                            'Defines named Drucker polling jobs.')
    parser.add_argument('--poll-job', default=None, metavar='NAME',
                       dest='poll_job',
                       help='Optional job ID from --poll-config for --workflow drucker-poll.')
    parser.add_argument('--poll-interval', type=int, default=300, metavar='SECS',
                       dest='poll_interval',
                       help='Polling interval in seconds for --workflow gantt-poll '
                            'and --workflow drucker-poll (default: 300).')
    parser.add_argument('--max-cycles', type=int, default=1, metavar='N',
                       dest='max_cycles',
                       help='Number of polling cycles for --workflow gantt-poll '
                            'and --workflow drucker-poll. Use 0 for continuous mode '
                            '(default: 1).')
    parser.add_argument('--notify-shannon', action='store_true',
                       dest='notify_shannon',
                       help='Post proactive poller summaries through Shannon.')
    parser.add_argument('--shannon-url', default=None, metavar='URL',
                       dest='shannon_url',
                       help='Base URL for the Shannon service when using '
                            '--notify-shannon (default: SHANNON_API_BASE_URL or '
                            'http://localhost:8200).')
    parser.add_argument('--github-repos', nargs='*', default=None, metavar='REPO',
                       dest='github_repos',
                       help='GitHub repos for PR hygiene polling (format: owner/repo). '
                            'If provided, enables GitHub PR hygiene scanning in '
                            '--workflow drucker-poll.')
    parser.add_argument('--github-stale-days', type=int, default=5, metavar='DAYS',
                       dest='github_stale_days',
                       help='Stale PR threshold in days for GitHub PR hygiene '
                            'polling (default: 5).')
    parser.add_argument('--evidence', nargs='*', default=None, metavar='FILE',
                       help='Evidence files (JSON, YAML, Markdown, text) for workflows '
                            'that can consume build/test/release/meeting context such as '
                            '--workflow gantt-snapshot and --workflow hypatia-generate.')
    parser.add_argument('--doc-title', default=None, metavar='TEXT',
                       dest='doc_title',
                       help='Document title for --workflow hypatia-generate.')
    parser.add_argument('--doc-type',
                       choices=['as_built', 'engineering_reference', 'how_to', 'release_note_support', 'user_guide'],
                       default='engineering_reference',
                       dest='doc_type',
                       help='Documentation class for --workflow hypatia-generate '
                            '(default: engineering_reference).')
    parser.add_argument('--doc-summary', default=None, metavar='TEXT',
                       dest='doc_summary',
                       help='Optional purpose/scope summary for --workflow hypatia-generate.')
    parser.add_argument('--target-file', default=None, metavar='FILE',
                       dest='target_file',
                       help='Repo-owned Markdown target for --workflow hypatia-generate. '
                            'Defaults to docs/<slug>.md if omitted.')
    parser.add_argument('--confluence-title', default=None, metavar='TITLE',
                       dest='confluence_title',
                       help='Confluence page title for --workflow hypatia-generate. '
                            'With --confluence-space and without --confluence-page, '
                            'this creates a page target.')
    parser.add_argument('--confluence-page', default=None, metavar='PAGE',
                       dest='confluence_page',
                       help='Confluence page ID or exact title to update for '
                            '--workflow hypatia-generate.')
    parser.add_argument('--confluence-space', default=None, metavar='SPACE',
                       dest='confluence_space',
                       help='Confluence space key or ID for --workflow hypatia-generate.')
    parser.add_argument('--confluence-parent-id', default=None, metavar='PAGE_ID',
                       dest='confluence_parent_id',
                       help='Parent page ID when creating a Confluence target for '
                            '--workflow hypatia-generate.')
    parser.add_argument('--version-message', default=None, metavar='TEXT',
                       dest='version_message',
                       help='Optional Confluence version message for --workflow hypatia-generate.')
    parser.add_argument('--doc-validation',
                       choices=['default', 'strict', 'sphinx'],
                       default='default',
                       dest='validation_profile',
                       help='Validation profile for --workflow hypatia-generate '
                            '(default, strict, or sphinx).')
    
    # ---- Options for --plan ----------------------------------------------------
    parser.add_argument('--project', '-p', default=None,
                       help='Jira project key (used by --plan, --analyze, --build-excel-map)')
    parser.add_argument('--roadmap', '-r', action='append', default=None,
                       help='Roadmap file(s) to analyze (used by --plan)')
    parser.add_argument('--org-chart', default=None,
                       help='Organization chart file, draw.io (used by --plan)')
    parser.add_argument('--plan-mode', choices=['full', 'analyze', 'plan'],
                       default='full',
                       help='Workflow mode for --plan (default: full)')
    parser.add_argument('--save-session', action='store_true',
                       help='Save session for later resumption (used by --plan)')
    
    # ---- Options for --analyze -------------------------------------------------
    parser.add_argument('--quick', action='store_true',
                       help='Quick analysis without LLM (used by --analyze)')
    
    # ---- Options for --sessions ------------------------------------------------
    parser.add_argument('--list-sessions', action='store_true',
                       help='List all sessions (used by --sessions)')
    parser.add_argument('--delete-session', default=None, metavar='ID',
                       help='Delete a session by ID (used by --sessions)')
    
    # ---- Options for --build-excel-map -----------------------------------------
    parser.add_argument('--hierarchy', type=int, default=1,
                       help='Depth for related issue traversal (default: 1, used by --build-excel-map)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Max tickets per step (used by --build-excel-map) or '
                            'max snapshots to show (used by --workflow gantt-snapshot-list).')
    parser.add_argument('--output', '-o', default=None,
                       help='Output filename (used by --build-excel-map and selected workflows such as gantt-snapshot, gantt-release-monitor, drucker-hygiene, and hypatia-generate)')
    parser.add_argument('--keep-intermediates', action='store_true',
                       help='Keep temp files instead of cleaning up (used by --build-excel-map)')
    
    # ---- Options for --invoke-llm ----------------------------------------------
    parser.add_argument('--attachments', '-a', nargs='*', default=None,
                       help='File(s) to attach (images via vision API, text inlined; used by --invoke-llm)')
    parser.add_argument('--timeout', type=float, default=None,
                       help='LLM request timeout in seconds (default: 120; used by --invoke-llm)')
    
    # ---- Global LLM model override ---------------------------------------------
    # Allows the user (or a Jenkins Choice Parameter) to select a model at
    # run-time without editing the .env file.  Overrides CORNELIS_LLM_MODEL /
    # OPENAI_MODEL / etc.
    parser.add_argument('--model', '-m', default=None, metavar='MODEL',
                       help='LLM model name override (e.g. developer-opus, gpt-4o). '
                            'Overrides the env-var default for this run.')
    
    # ---- Global verbose flag ---------------------------------------------------
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose (debug-level) logging to stdout')
    
    args = parser.parse_args()
    
    if args.quiet:
        _quiet_mode = True
    
    # ---- Load custom env file (--env) early, before anything reads env vars ----
    # The default .env was already loaded at import time (line 31) with
    # override=False.  When --env is provided we reload from that file with
    # override=True so its values take precedence.
    if args.env:
        if not os.path.exists(args.env):
            parser.error(f'--env file not found: {args.env}')
        load_dotenv(dotenv_path=args.env, override=True)
        log.info(f'Loaded env file: {args.env}')

        # jira_utils.JIRA_URL was captured at import time from the default
        # .env.  Now that --env has overridden os.environ, refresh the
        # module-level URL and drop any cached connection so the next call
        # to get_connection() uses the correct server.
        jira_utils.JIRA_URL = os.getenv('JIRA_URL', jira_utils.DEFAULT_JIRA_URL)
        jira_api.reset_connection()
        log.info(f'Refreshed jira_utils.JIRA_URL -> {jira_utils.JIRA_URL}')
    
    # ---- Verbose mode: add a stdout handler so debug messages appear on console
    if args.verbose:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(logging.Formatter(
            '%(asctime)-15s [%(funcName)25s:%(lineno)-5s] %(levelname)-8s %(message)s'))
        log.addHandler(sh)
        log.debug('Verbose mode enabled (--verbose)')
    
    # ---- Determine which command was requested ---------------------------------
    # Count how many command flags were set to enforce mutual exclusivity
    commands = []
    if args.plan:
        commands.append('plan')
    if args.analyze:
        commands.append('analyze')
    if args.vision is not None:
        commands.append('vision')
    if args.sessions:
        commands.append('sessions')
    if args.build_excel_map is not None:
        commands.append('build-excel-map')
    if args.invoke_llm is not None:
        commands.append('invoke-llm')
    if args.resume is not None:
        commands.append('resume')
    if args.workflow_name is not None:
        commands.append('workflow')
    
    if len(commands) == 0:
        parser.print_help()
        sys.exit(1)
    
    if len(commands) > 1:
        parser.error(f'Only one command may be specified at a time. Got: {", ".join("--" + c for c in commands)}')
    
    command = commands[0]
    
    # ---- Command-specific validation -------------------------------------------
    if command == 'plan':
        if not args.project:
            parser.error('--plan requires --project')
    
    if command == 'analyze':
        if not args.project:
            parser.error('--analyze requires --project')
    
    if command == 'workflow':
        if args.evidence:
            for evidence_path in args.evidence:
                if not os.path.isfile(evidence_path):
                    parser.error(f'--evidence file not found: {evidence_path}')

        if args.workflow_name == 'bug-report':
            if not args.workflow_filter:
                parser.error('--workflow bug-report requires --filter "FILTER_NAME"')
        elif args.workflow_name == 'feature-plan':
            # --cleanup only needs the CSV file — skip all other validation
            cleanup_csv = getattr(args, 'cleanup', None)
            if cleanup_csv:
                if not os.path.isfile(cleanup_csv):
                    parser.error(f'--cleanup CSV not found: {cleanup_csv}')
            else:
                if not args.project:
                    parser.error('--workflow feature-plan requires --project PROJECT_KEY')
                # --plan-file bypasses the agentic flow; no --feature needed
                plan_file = getattr(args, 'plan_file', None)
                if plan_file:
                    if not os.path.isfile(plan_file):
                        parser.error(f'--plan-file not found: {plan_file}')
                elif not args.feature and not args.feature_prompt:
                    # Require at least one of --feature or --feature-prompt
                    parser.error('--workflow feature-plan requires --feature "DESCRIPTION" '
                                 'or --feature-prompt FILE (or --plan-file FILE)')
                # Validate that the prompt file exists when specified
                if args.feature_prompt and not os.path.isfile(args.feature_prompt):
                    parser.error(f'--feature-prompt file not found: {args.feature_prompt}')
        elif args.workflow_name == 'gantt-snapshot':
            if not args.project:
                parser.error('--workflow gantt-snapshot requires --project PROJECT_KEY')
        elif args.workflow_name == 'gantt-release-monitor':
            if not args.project:
                parser.error('--workflow gantt-release-monitor requires --project PROJECT_KEY')
        elif args.workflow_name == 'gantt-release-survey':
            if not args.project:
                parser.error('--workflow gantt-release-survey requires --project PROJECT_KEY')
        elif args.workflow_name == 'gantt-release-monitor-get':
            if not args.report_id:
                parser.error('--workflow gantt-release-monitor-get requires --report-id ID')
        elif args.workflow_name == 'gantt-release-survey-get':
            if not args.survey_id:
                parser.error('--workflow gantt-release-survey-get requires --survey-id ID')
        elif args.workflow_name == 'gantt-release-monitor-list':
            pass
        elif args.workflow_name == 'gantt-release-survey-list':
            pass
        elif args.workflow_name == 'gantt-poll':
            if not args.project:
                parser.error('--workflow gantt-poll requires --project PROJECT_KEY')
        elif args.workflow_name == 'gantt-snapshot-get':
            if not args.snapshot_id:
                parser.error('--workflow gantt-snapshot-get requires --snapshot-id ID')
        elif args.workflow_name == 'gantt-snapshot-list':
            pass
        elif args.workflow_name == 'drucker-hygiene':
            if not args.project:
                parser.error('--workflow drucker-hygiene requires --project PROJECT_KEY')
        elif args.workflow_name == 'drucker-bug-activity':
            if not args.project:
                parser.error('--workflow drucker-bug-activity requires --project PROJECT_KEY')
        elif args.workflow_name == 'drucker-intake-report':
            if not args.project:
                parser.error('--workflow drucker-intake-report requires --project PROJECT_KEY')
        elif args.workflow_name == 'drucker-issue-check':
            if not args.project:
                parser.error('--workflow drucker-issue-check requires --project PROJECT_KEY')
            if not args.ticket_key:
                parser.error('--workflow drucker-issue-check requires --ticket-key KEY')
        elif args.workflow_name == 'drucker-poll':
            if not args.project and not args.poll_config:
                parser.error(
                    '--workflow drucker-poll requires --project PROJECT_KEY '
                    'or --poll-config FILE'
                )
            if args.poll_config and not os.path.isfile(args.poll_config):
                parser.error(f'--poll-config file not found: {args.poll_config}')
        elif args.workflow_name == 'hypatia-generate':
            if args.docs:
                for source_path in args.docs:
                    if not os.path.isfile(source_path):
                        parser.error(f'--docs source file not found: {source_path}')

            if not args.doc_title and not args.confluence_title and not args.target_file:
                parser.error(
                    '--workflow hypatia-generate requires --doc-title TEXT '
                    '(or a title-bearing target such as --confluence-title or --target-file)'
                )

            if args.confluence_title and not args.confluence_page and not args.confluence_space:
                parser.error(
                    '--workflow hypatia-generate requires --confluence-space '
                    'when creating a Confluence page with --confluence-title'
                )
        if args.max_cycles < 0:
            parser.error('--max-cycles must be >= 0')
        if args.max_cycles == 0 and args.poll_interval <= 0:
            parser.error('Continuous polling requires --poll-interval > 0')
    
    # ---- Map ticket_keys for build-excel-map compatibility ---------------------
    # cmd_build_excel_map expects args.ticket_keys
    if command == 'build-excel-map':
        args.ticket_keys = args.build_excel_map
    
    # ---- Map prompt for invoke-llm compatibility -------------------------------
    # cmd_invoke_llm expects args.prompt
    if command == 'invoke-llm':
        args.prompt = args.invoke_llm
    
    # ---- Map session for resume compatibility ----------------------------------
    # cmd_resume expects args.resume (already set)
    
    # ---- Store resolved command name for dispatch ------------------------------
    args.command = command
    
    # ---- Startup logging box ---------------------------------------------------
    log.info('++++++++++++++++++++++++++++++++++++++++++++++')
    log.info(f'+  {os.path.basename(sys.argv[0])}')
    log.info(f'+  Python Version: {sys.version.split()[0]}')
    log.info(f'+  Today is: {date.today()}')
    log.info(f'+  Command: --{command}')
    # Command-specific details in the startup box
    if command == 'plan':
        log.info(f'+  Project: {args.project}')
        log.info(f'+  Plan mode: {args.plan_mode}')
        if args.roadmap:
            log.info(f'+  Roadmap files: {len(args.roadmap)}')
        if args.org_chart:
            log.info(f'+  Org chart: {args.org_chart}')
    elif command == 'analyze':
        log.info(f'+  Project: {args.project}')
        if args.quick:
            log.info(f'+  Quick mode: yes')
    elif command == 'vision':
        log.info(f'+  Files: {len(args.vision)}')
        for vf in args.vision:
            log.info(f'+    - {vf}')
    elif command == 'sessions':
        if args.list_sessions:
            log.info(f'+  Action: list')
        elif args.delete_session:
            log.info(f'+  Action: delete {args.delete_session}')
    elif command == 'build-excel-map':
        keys_str = ', '.join(k.upper() for k in args.ticket_keys)
        log.info(f'+  Root ticket(s): {keys_str}')
        log.info(f'+  Hierarchy depth: {args.hierarchy}')
        default_out = f'{args.ticket_keys[0].upper()}.xlsx' if len(args.ticket_keys) == 1 else f'{"_".join(k.upper() for k in args.ticket_keys)}.xlsx'
        log.info(f'+  Output file: {args.output or default_out}')
    elif command == 'invoke-llm':
        prompt_display = args.prompt if len(args.prompt) <= 60 else args.prompt[:57] + '...'
        log.info(f'+  Prompt: {prompt_display}')
        if args.attachments:
            log.info(f'+  Attachments: {len(args.attachments)} file(s)')
            for att in args.attachments:
                log.info(f'+    - {att}')
        if args.timeout:
            log.info(f'+  Timeout: {args.timeout}s')
    elif command == 'resume':
        log.info(f'+  Session: {args.resume}')
    elif command == 'workflow':
        log.info(f'+  Workflow: {args.workflow_name}')
        if args.workflow_name == 'feature-plan':
            log.info(f'+  Project: {args.project}')
            plan_file_arg = getattr(args, 'plan_file', None)
            if plan_file_arg:
                log.info(f'+  Plan file: {plan_file_arg}')
            if args.feature_prompt:
                log.info(f'+  Feature prompt: {args.feature_prompt}')
            if args.feature:
                feature_display = args.feature if len(args.feature) <= 60 else args.feature[:57] + '...'
                log.info(f'+  Feature: {feature_display}')
            if args.docs:
                log.info(f'+  Docs: {len(args.docs)} file(s)')
                for dp in args.docs:
                    log.info(f'+    - {dp}')
            initiative_arg = getattr(args, 'initiative', None)
            if initiative_arg:
                log.info(f'+  Initiative: {initiative_arg}')
            if args.execute:
                log.info(f'+  Execute: YES (will create Jira tickets)')
            else:
                log.info(f'+  Execute: DRY RUN')
            if args.output_dir:
                log.info(f'+  Output dir: {args.output_dir}')
            elif args.output:
                log.info(f'+  Output: {args.output}')
        elif args.workflow_name == 'gantt-snapshot':
            log.info(f'+  Project: {args.project}')
            log.info(f'+  Planning horizon: {args.planning_horizon} days')
            log.info(f'+  Include done: {"yes" if args.include_done else "no"}')
            if args.evidence:
                log.info(f'+  Evidence files: {len(args.evidence)}')
                for evidence_path in args.evidence:
                    log.info(f'+    - {evidence_path}')
            if args.output:
                log.info(f'+  Output: {args.output}')
        elif args.workflow_name == 'gantt-release-monitor':
            log.info(f'+  Project: {args.project}')
            if args.releases:
                log.info(f'+  Releases: {args.releases}')
            if args.scope_label:
                log.info(f'+  Scope label: {args.scope_label}')
            log.info(f'+  Gap analysis: {"yes" if args.include_gap_analysis else "no"}')
            log.info(f'+  Velocity: {"yes" if args.include_velocity else "no"}')
            log.info(f'+  Readiness: {"yes" if args.include_readiness else "no"}')
            if args.output:
                log.info(f'+  Output: {args.output}')
        elif args.workflow_name == 'gantt-release-survey':
            log.info(f'+  Project: {args.project}')
            if args.releases:
                log.info(f'+  Releases: {args.releases}')
            if args.scope_label:
                log.info(f'+  Scope label: {args.scope_label}')
            log.info(f'+  Survey mode: {args.survey_mode}')
            if args.output:
                log.info(f'+  Output: {args.output}')
        elif args.workflow_name == 'gantt-release-monitor-get':
            log.info(f'+  Report ID: {args.report_id}')
            if args.project:
                log.info(f'+  Project: {args.project}')
            if args.output:
                log.info(f'+  Output: {args.output}')
        elif args.workflow_name == 'gantt-release-survey-get':
            log.info(f'+  Survey ID: {args.survey_id}')
            if args.project:
                log.info(f'+  Project: {args.project}')
            if args.output:
                log.info(f'+  Output: {args.output}')
        elif args.workflow_name == 'gantt-release-monitor-list':
            if args.project:
                log.info(f'+  Project: {args.project}')
        elif args.workflow_name == 'gantt-release-survey-list':
            if args.project:
                log.info(f'+  Project: {args.project}')
        elif args.workflow_name == 'gantt-poll':
            log.info(f'+  Project: {args.project}')
            log.info(f'+  Poll interval: {args.poll_interval}s')
            log.info(
                '+  Max cycles: '
                f'{"continuous" if args.max_cycles == 0 else args.max_cycles}'
            )
            log.info(
                '+  Release survey: '
                f'{"yes" if args.run_release_survey else "no"}'
            )
            if args.run_release_survey:
                log.info(f'+  Survey mode: {args.survey_mode}')
        elif args.workflow_name == 'gantt-snapshot-get':
            log.info(f'+  Snapshot ID: {args.snapshot_id}')
            if args.project:
                log.info(f'+  Project: {args.project}')
            if args.output:
                log.info(f'+  Output: {args.output}')
        elif args.workflow_name == 'gantt-snapshot-list':
            if args.project:
                log.info(f'+  Project: {args.project}')
        elif args.workflow_name == 'drucker-hygiene':
            log.info(f'+  Project: {args.project}')
            log.info(f'+  Stale days: {args.stale_days}')
            log.info(f'+  Include done: {"yes" if args.include_done else "no"}')
            if args.output:
                log.info(f'+  Output: {args.output}')
        elif args.workflow_name == 'drucker-bug-activity':
            log.info(f'+  Project: {args.project}')
            log.info(f'+  Target date: {args.target_date or "today"}')
            if args.output:
                log.info(f'+  Output: {args.output}')
        elif args.workflow_name == 'drucker-intake-report':
            log.info(f'+  Project: {args.project}')
            log.info(f'+  Stale days: {args.stale_days}')
            if args.since:
                log.info(f'+  Since: {args.since}')
            if args.output:
                log.info(f'+  Output: {args.output}')
        elif args.workflow_name == 'drucker-issue-check':
            log.info(f'+  Project: {args.project}')
            log.info(f'+  Ticket: {args.ticket_key}')
            log.info(f'+  Stale days: {args.stale_days}')
            if args.output:
                log.info(f'+  Output: {args.output}')
        elif args.workflow_name == 'drucker-poll':
            if args.project:
                log.info(f'+  Project: {args.project}')
            if args.poll_config:
                log.info(f'+  Poll config: {args.poll_config}')
            if args.poll_job:
                log.info(f'+  Poll job: {args.poll_job}')
            log.info(f'+  Poll interval: {args.poll_interval}s')
            log.info(f'+  Recent only: {"yes" if args.recent_only else "no"}')
            if args.since:
                log.info(f'+  Since: {args.since}')
            log.info(
                '+  Max cycles: '
                f'{"continuous" if args.max_cycles == 0 else args.max_cycles}'
            )
        elif args.workflow_name == 'hypatia-generate':
            log.info(f'+  Document title: {args.doc_title or args.confluence_title or "auto"}')
            log.info(f'+  Document class: {args.doc_type}')
            log.info(f'+  Validation: {args.validation_profile}')
            if args.project:
                log.info(f'+  Project: {args.project}')
            if args.docs:
                log.info(f'+  Docs: {len(args.docs)} file(s)')
                for dp in args.docs:
                    log.info(f'+    - {dp}')
            if args.evidence:
                log.info(f'+  Evidence files: {len(args.evidence)}')
                for evidence_path in args.evidence:
                    log.info(f'+    - {evidence_path}')
            if args.target_file:
                log.info(f'+  Target file: {args.target_file}')
            if args.confluence_page:
                log.info(f'+  Confluence page: {args.confluence_page}')
            if args.confluence_title:
                log.info(f'+  Confluence title: {args.confluence_title}')
            if args.confluence_space:
                log.info(f'+  Confluence space: {args.confluence_space}')
            log.info(f'+  Execute: {"YES" if args.execute else "DRY RUN"}')
            if args.output:
                log.info(f'+  Output: {args.output}')
        if args.workflow_filter:
            log.info(f'+  Filter: {args.workflow_filter}')
        if args.workflow_prompt:
            log.info(f'+  Prompt: {args.workflow_prompt}')
        if args.timeout:
            log.info(f'+  Timeout: {args.timeout}s')
        if args.limit:
            log.info(f'+  Limit: {args.limit}')
    log.info('++++++++++++++++++++++++++++++++++++++++++++++')
    
    return args


# ****************************************************************************************
# Main
# ****************************************************************************************

def main():
    '''
    Entrypoint for the CLI.
    Dispatches to the appropriate cmd_* handler based on args.command.
    '''
    args = handle_args()
    log.debug('Entering main()')
    
    # Dispatch table: command name -> handler function
    dispatch = {
        'plan':            cmd_plan,
        'analyze':         cmd_analyze,
        'vision':          cmd_vision,
        'sessions':        cmd_sessions,
        'build-excel-map': cmd_build_excel_map,
        'invoke-llm':      cmd_invoke_llm,
        'resume':          cmd_resume,
        'workflow':         cmd_workflow,
    }
    
    handler = dispatch.get(args.command)
    if not handler:
        output(f'ERROR: Unknown command: {args.command}')
        sys.exit(1)
    
    try:
        exit_code = handler(args)
        
    except KeyboardInterrupt:
        output('\nOperation cancelled.')
        exit_code = 130
        
    except Exception as e:
        log.error(f'Unexpected error: {e}', exc_info=True)
        output(f'ERROR: {e}')
        exit_code = 1
    
    log.info('Operation complete.')
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
