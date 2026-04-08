# Shannon — Design Reference

## Purpose
This internal document candidate was generated from authoritative source artifacts for review before publication.

## Metadata
- Documentation class: `as_built`
- Generated: `2026-04-08 14:46 UTC`
- Confidence: `medium`

## Authoritative Inputs
- `jmac-cornelis/agent-workforce:shannon/registry.py` (source)
- `jmac-cornelis/agent-workforce:shannon/cards.py` (source)
- `jmac-cornelis/agent-workforce:shannon/models.py` (source)
- `jmac-cornelis/agent-workforce:shannon/app.py` (source)
- `jmac-cornelis/agent-workforce:shannon/__init__.py` (source)
- `jmac-cornelis/agent-workforce:shannon/poster.py` (source)
- `jmac-cornelis/agent-workforce:shannon/outgoing_webhook.py` (source)
- `jmac-cornelis/agent-workforce:shannon/notification_router.py` (source)
- `jmac-cornelis/agent-workforce:shannon/service.py` (source)

## Key Facts

### Source: `jmac-cornelis/agent-workforce:shannon/registry.py`
- Module: shannon/registry.py
- Description: Agent/channel registry loading for the Shannon Teams bot.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path
- from typing import Dict, List, Optional
- import yaml

### Source: `jmac-cornelis/agent-workforce:shannon/cards.py`
- Module: shannon/cards.py
- Description: Adaptive Card builders for Shannon Teams responses.
- Author: Cornelis Networks
- from __future__ import annotations
- import re
- from typing import Any, Dict, Iterable, Optional
- from agents.rename_registry import agent_display_name
- _JIRA_BASE = 'https://cornelisnetworks.atlassian.net/browse'
- _TICKET_RE = re.compile(r'(?<!\[)(?<!/)\b([A-Z][A-Z0-9]+-\d+)\b')
- def _linkify_tickets(text: str) -> str:

### Source: `jmac-cornelis/agent-workforce:shannon/models.py`
- Module: shannon/models.py
- Description: Data models for the Shannon Teams bot service.
- Author: Cornelis Networks
- from __future__ import annotations
- import re
- import uuid
- from dataclasses import asdict, dataclass, field
- from datetime import datetime, timezone
- from typing import Any, Dict, List, Optional
- def utc_now_iso() -> str:

### Source: `jmac-cornelis/agent-workforce:shannon/app.py`
- Module: shannon/app.py
- Description: FastAPI application for the Shannon Teams bot service.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from typing import Any, Dict, List, Optional
- from dotenv import load_dotenv
- load_dotenv()

### Source: `jmac-cornelis/agent-workforce:shannon/__init__.py`
- Module: shannon/__init__.py
- Description: Shannon Teams bot service package.
- Author: Cornelis Networks
- __all__ = []

### Source: `jmac-cornelis/agent-workforce:shannon/poster.py`
- Module: shannon/poster.py
- Description: Posting adapters for sending Shannon replies to Teams.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from typing import Any, Dict, List, Optional
- import requests
- from config.env_loader import resolve_dry_run

### Source: `jmac-cornelis/agent-workforce:shannon/outgoing_webhook.py`
- Module: shannon/outgoing_webhook.py
- Description: Helpers for Microsoft Teams Outgoing Webhook authentication
- and response handling.
- Author: Cornelis Networks
- from __future__ import annotations
- import base64
- import hashlib
- import hmac
- from typing import Optional
- def extract_hmac_signature(authorization_header: Optional[str]) -> str:

### Source: `jmac-cornelis/agent-workforce:shannon/notification_router.py`
- Unified notification router — dispatches to Teams DM and email.
- router = NotificationRouter()
- await router.notify(
- agent_id='drucker',
- title='PR Reminders Sent',
- text='3 reminders sent',
- body_lines=['PR #42: stale 7 days', 'PR #55: stale 3 days'],
- target_users=['jmac-cornelis'], # GitHub logins, or None for all
- Delivery channels are controlled per-user in config/identity_map.yaml:
- notify_via: [teams_dm, email]

### Source: `jmac-cornelis/agent-workforce:shannon/service.py`
- Module: shannon/service.py
- Description: Core Shannon service logic for Teams command handling and
- notification posting.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- import re as re_mod
- import threading
- No authoritative source facts were available.

## Publication Targets
- `repo_markdown` -> `docs/shannon.md` (create)

## Source References
- `shannon/`
- `jmac-cornelis/agent-workforce:shannon/registry.py`
- `jmac-cornelis/agent-workforce:shannon/cards.py`
- `jmac-cornelis/agent-workforce:shannon/models.py`
- `jmac-cornelis/agent-workforce:shannon/app.py`
- `jmac-cornelis/agent-workforce:shannon/__init__.py`
- `jmac-cornelis/agent-workforce:shannon/poster.py`
- `jmac-cornelis/agent-workforce:shannon/outgoing_webhook.py`
- `jmac-cornelis/agent-workforce:shannon/notification_router.py`
- `jmac-cornelis/agent-workforce:shannon/service.py`
