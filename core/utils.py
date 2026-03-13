import csv
import inspect
import logging
import re
from functools import lru_cache
from itertools import combinations
from typing import Any, Optional


def output(message: str = '', quiet_mode: bool = False) -> None:
    caller_globals: dict[str, Any] = {}
    caller_locals: dict[str, Any] = {}
    caller_file = __file__

    frame = inspect.currentframe()
    try:
        caller = frame.f_back if frame else None
        if caller is not None:
            caller_globals = caller.f_globals
            caller_locals = caller.f_locals
            caller_file = caller_globals.get('__file__', __file__)
    finally:
        del frame

    effective_quiet = bool(caller_globals.get('_quiet_mode', quiet_mode))
    logger = caller_globals.get('log')
    file_handler = caller_globals.get('fh')

    if '_quiet_mode' not in caller_globals:
        module_candidates = []
        seen_ids = set()
        for namespace in (caller_locals, caller_globals):
            for value in namespace.values():
                if not inspect.ismodule(value):
                    continue
                module_id = id(value)
                if module_id in seen_ids:
                    continue
                seen_ids.add(module_id)
                if getattr(value, 'output', None) is output:
                    module_candidates.append(value)

        for module in module_candidates:
            module_quiet = getattr(module, '_quiet_mode', None)
            module_logger = getattr(module, 'log', None)
            module_handler = getattr(module, 'fh', None)
            if module_quiet is not None or module_logger is not None or module_handler is not None:
                effective_quiet = bool(module_quiet if module_quiet is not None else quiet_mode)
                logger = module_logger if module_logger is not None else logger
                file_handler = module_handler if module_handler is not None else file_handler
                caller_file = getattr(module, '__file__', caller_file)
                break

    if message and logger is not None and file_handler is not None:
        try:
            record = logging.LogRecord(
                name=getattr(logger, 'name', __name__),
                level=logging.INFO,
                pathname=caller_file,
                lineno=0,
                msg=f'OUTPUT: {message}',
                args=(),
                exc_info=None,
                func='output',
            )
            file_handler.emit(record)
        except Exception:
            pass

    if not effective_quiet:
        print(message)


def validate_and_repair_csv(input_file: str, output_file: Optional[str] = None) -> tuple[bool, dict[str, int]]:
    with open(input_file, 'r', encoding='utf-8', newline='') as f:
        raw_rows = list(csv.reader(f))

    if len(raw_rows) < 2:
        row_count = max(len(raw_rows) - 1, 0)
        return False, {
            'total_rows': row_count,
            'ok_rows': row_count,
            'repaired_rows': 0,
            'padded_rows': 0,
            'unfixable_rows': 0,
        }

    header = raw_rows[0]
    expected = len(header)

    jira_key_re = re.compile(r'^[A-Z]{2,10}-\d+$')
    date_re = re.compile(r'^\d{4}-\d{2}-\d{2}(?:[ T].*)?$')
    version_token_re = re.compile(r'^(?:\d+\.){2,4}(?:x|\d+)$', re.IGNORECASE)
    known_values = {
        'issue_type': {
            'bug', 'story', 'task', 'epic', 'sub-task', 'subtask',
            'improvement', 'new feature', 'change request',
        },
        'status': {
            'open', 'in progress', 'closed', 'verify', 'ready',
            'to do', 'done', 'resolved', 'reopened', 'in review',
        },
        'priority': {
            'p0-stopper', 'p1-critical', 'p2-high', 'p2-major',
            'p3-medium', 'p3-minor', 'p4-low', 'p4-trivial',
            'blocker', 'critical', 'high', 'major', 'medium', 'minor', 'low', 'trivial',
        },
        'project': {'stl', 'stlsb', 'cn', 'opx'},
        'product': {'nic', 'switch'},
        'module': {'driver', 'bts', 'fw', 'opx', 'gpu'},
    }
    absorb_comma_headers = {
        'summary', 'description', 'assignee', 'fix_version', 'affects_version',
        'versions', 'todays_status', 'today_status', 'latest_comment',
        'comments', 'dependency',
    }
    penalty_headers = {'key', 'project', 'issue_type', 'status', 'priority', 'updated'}

    def normalize_header(header_name: str) -> str:
        normalized = header_name.strip().lower()
        normalized = normalized.replace(' ', '_').replace('-', '_').replace('/', '_')
        if normalized in {'issuetype', 'issue_typ'} or normalized.startswith('issue_typ'):
            return 'issue_type'
        if normalized in {'fixversions', 'fix_version_s'} or normalized.startswith('fix_ver'):
            return 'fix_version'
        if normalized in {'versions', 'affectedversion', 'affectedversions'}:
            return 'affects_version'
        if normalized in {'todaysstatus', 'todays_status'}:
            return 'todays_status'
        if normalized in {'latestcomment', 'latest_comment'}:
            return 'latest_comment'
        return normalized

    def looks_like_version_list(value: str) -> bool:
        tokens = [token.strip() for token in value.split(',') if token.strip()]
        return bool(tokens) and all(version_token_re.match(token) for token in tokens)

    def score_alignment(fields: list[str], header_list: list[str]) -> int:
        score = 0
        for i, header_name in enumerate(header_list):
            if i >= len(fields):
                break
            value = (fields[i] or '').strip()
            header_key = normalize_header(header_name)
            value_lower = value.lower()

            if header_key == 'key' and jira_key_re.match(value):
                score += 12
            elif header_key in known_values and value_lower in known_values[header_key]:
                score += 7
            elif header_key == 'updated' and date_re.match(value):
                score += 7
            elif header_key in {'fix_version', 'affects_version'} and looks_like_version_list(value):
                score += 7
            elif value and header_key in absorb_comma_headers:
                score += 2
        return score

    def score_segment(header_key: str, value: str, width: int) -> int:
        value = value.strip()
        value_lower = value.lower()
        score = 0

        if header_key in absorb_comma_headers:
            score += 2 if value else 0
            if width > 1:
                score += min(width * 3, 12)
        elif width > 1:
            score -= 8 * (width - 1)

        if header_key == 'key':
            return score + (40 if jira_key_re.match(value) else -20)
        if header_key == 'project':
            if value_lower in known_values['project'] or re.match(r'^[A-Z][A-Z0-9]{1,9}$', value):
                return score + 18
            return score - 6
        if header_key == 'issue_type':
            return score + (18 if value_lower in known_values['issue_type'] else -10)
        if header_key == 'status':
            return score + (18 if value_lower in known_values['status'] else -10)
        if header_key == 'priority':
            return score + (18 if value_lower in known_values['priority'] else -10)
        if header_key == 'updated':
            return score + (18 if date_re.match(value) else -10)
        if header_key in {'fix_version', 'affects_version'}:
            if looks_like_version_list(value):
                return score + 20
            return score - 4
        if header_key == 'assignee':
            if re.match(r'^[^,]+,\s*[^,]+(?:\s+[^,]+)?$', value):
                return score + 16
            if value:
                return score + 6
            return score - 2
        if header_key == 'dependency':
            if all(jira_key_re.match(part.strip()) for part in value.split(',') if part.strip()):
                return score + 12
            return score + (4 if value else 0)
        if header_key in {'customer', 'product', 'module', 'phase'}:
            if value and width == 1:
                return score + 8
            return score - 2
        if header_key in {'summary', 'description', 'todays_status', 'today_status', 'latest_comment', 'comments'}:
            return score + (6 if value else 0)
        return score + (2 if value else 0)

    stats = {
        'total_rows': len(raw_rows) - 1,
        'ok_rows': 0,
        'repaired_rows': 0,
        'padded_rows': 0,
        'unfixable_rows': 0,
    }
    any_changed = False

    for row_idx in range(1, len(raw_rows)):
        fields = raw_rows[row_idx]
        n = len(fields)

        if n == expected:
            stats['ok_rows'] += 1
            continue

        if n < expected:
            fields.extend([''] * (expected - n))
            raw_rows[row_idx] = fields
            stats['padded_rows'] += 1
            any_changed = True
            continue

        extra = n - expected
        best_score = -1
        best_fields = None
        fallback_fields = fields[: expected - 1]
        fallback_fields.append(','.join(fields[expected - 1 :]))

        if extra <= 4:
            merge_candidates = list(range(n - 1))
            for merge_points in combinations(merge_candidates, extra):
                candidate: list[str] = []
                i = 0
                while i < n:
                    if i in merge_points:
                        merged = fields[i]
                        while i in merge_points:
                            i += 1
                            if i < n:
                                merged += ',' + fields[i]
                        candidate.append(merged)
                    else:
                        candidate.append(fields[i])
                    i += 1

                if len(candidate) != expected:
                    continue

                score = score_alignment(candidate, header)
                if score > best_score:
                    best_score = score
                    best_fields = candidate

        normalized_header = [normalize_header(name) for name in header]

        @lru_cache(maxsize=None)
        def align_columns(header_idx: int, field_idx: int) -> tuple[int, tuple[int, ...]]:
            if header_idx == expected and field_idx == n:
                return 0, ()
            if header_idx >= expected or field_idx >= n:
                return -10**9, ()

            remaining_headers = expected - header_idx
            remaining_fields = n - field_idx
            max_width = remaining_fields - (remaining_headers - 1)
            if max_width < 1:
                return -10**9, ()

            best_local_score = -10**9
            best_widths: tuple[int, ...] = ()
            for width in range(1, max_width + 1):
                value = ','.join(fields[field_idx: field_idx + width])
                current_score = score_segment(normalized_header[header_idx], value, width)
                remainder_score, remainder_widths = align_columns(header_idx + 1, field_idx + width)
                total_score = current_score + remainder_score
                if total_score > best_local_score:
                    best_local_score = total_score
                    best_widths = (width,) + remainder_widths

            return best_local_score, best_widths

        dp_score, dp_widths = align_columns(0, 0)
        if dp_widths and len(dp_widths) == expected:
            candidate = []
            field_pos = 0
            for width in dp_widths:
                candidate.append(','.join(fields[field_pos: field_pos + width]))
                field_pos += width

            candidate_alignment_score = score_alignment(candidate, header)
            if (
                len(candidate) == expected
                and dp_score > best_score
                and (extra <= 4 or candidate_alignment_score >= 15)
            ):
                best_score = dp_score
                best_fields = candidate

        if best_fields is None:
            best_fields = fallback_fields

        if best_fields and len(best_fields) == expected:
            raw_rows[row_idx] = best_fields
            stats['repaired_rows'] += 1
            any_changed = True
        else:
            stats['unfixable_rows'] += 1

    target_file = output_file or input_file
    should_write = any_changed or (output_file is not None and output_file != input_file)

    if should_write:
        with open(target_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(raw_rows)

    return any_changed, stats


def extract_text_from_adf(adf_content: Any) -> str:
    if adf_content is None:
        return ''

    if isinstance(adf_content, str):
        return adf_content

    parts: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get('type') == 'text':
                parts.append(node.get('text', ''))
            for child in node.get('content', []):
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(adf_content)

    return '\n'.join(parts) if parts else str(adf_content)
