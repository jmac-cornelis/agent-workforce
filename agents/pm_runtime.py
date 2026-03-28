from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, Iterable, List, Optional

import requests

log = logging.getLogger(os.path.basename(sys.argv[0]))


def normalize_csv_list(value: List[str] | str | None) -> List[str]:
    '''
    Normalize a list or comma-separated string into a clean string list.
    '''
    if value is None:
        return []

    if isinstance(value, str):
        parts = [part.strip() for part in value.split(',')]
        return [part for part in parts if part]

    return [str(part).strip() for part in value if str(part).strip()]


def notify_shannon(
    *,
    agent_id: str,
    title: str,
    text: str,
    body_lines: Optional[Iterable[str]] = None,
    shannon_base_url: Optional[str] = None,
    timeout: int = 15,
    dry_run: bool = True,
) -> Dict[str, Any]:
    '''
    Post a proactive notification through Shannon and return a structured result.
    '''
    base_url = str(
        shannon_base_url
        or os.getenv('SHANNON_API_BASE_URL')
        or 'http://localhost:8200'
    ).strip().rstrip('/')
    payload = {
        'agent_id': agent_id,
        'title': title,
        'text': text,
        'body_lines': [str(line) for line in (body_lines or []) if str(line).strip()],
    }

    if dry_run:
        return {
            'ok': True,
            'dry_run': True,
            'base_url': base_url,
            'payload': payload,
        }

    try:
        response = requests.post(
            f'{base_url}/v1/bot/notify',
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        return {
            'ok': True,
            'base_url': base_url,
            'payload': payload,
            'response': response.json(),
        }
    except Exception as e:
        log.warning(
            f'Failed to post Shannon notification for {agent_id}: {e}'
        )
        return {
            'ok': False,
            'base_url': base_url,
            'payload': payload,
            'error': str(e),
        }
