##########################################################################################
#
# Module: state/shannon_state_store.py
#
# Description: Persistence helpers for the Shannon Teams bot service.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import json
import logging
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from shannon.models import AuditRecord, ConversationReference, ConversationState

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class ShannonStateStore:
    '''
    Lightweight JSON persistence for Shannon conversation references and audit logs.
    '''

    def __init__(self, storage_dir: Optional[str] = None):
        env_dir = os.getenv('SHANNON_STATE_DIR')
        resolved_dir = storage_dir or env_dir or 'data/shannon'
        self.storage_dir = Path(resolved_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.references_path = self.storage_dir / 'conversation_references.json'
        self.audit_dir = self.storage_dir / 'audit'
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        log.debug(f'ShannonStateStore initialized: {self.storage_dir}')

    def save_conversation_reference(self, reference: ConversationReference) -> Dict[str, Any]:
        payload = self._load_references()
        if reference.agent_id:
            payload[f'agent:{reference.agent_id}'] = reference.to_dict()
        if reference.channel_id:
            payload[f'channel:{reference.channel_id}'] = reference.to_dict()
        if reference.conversation_id:
            payload[f'conversation:{reference.conversation_id}'] = reference.to_dict()
        self.references_path.write_text(
            json.dumps(payload, indent=2, default=str),
            encoding='utf-8',
        )
        return reference.to_dict()

    def get_conversation_reference(
        self,
        *,
        agent_id: str = '',
        channel_id: str = '',
        conversation_id: str = '',
    ) -> Optional[ConversationReference]:
        payload = self._load_references()

        if agent_id:
            data = payload.get(f'agent:{agent_id}')
            if data:
                return ConversationReference(**data)

        if channel_id:
            data = payload.get(f'channel:{channel_id}')
            if data:
                return ConversationReference(**data)

        if conversation_id:
            data = payload.get(f'conversation:{conversation_id}')
            if data:
                return ConversationReference(**data)

        return None

    def append_audit_record(self, record: AuditRecord) -> None:
        day = str(record.timestamp or '')[:10] or datetime.now(timezone.utc).date().isoformat()
        path = self.audit_dir / f'{day}.jsonl'
        with open(path, 'a', encoding='utf-8') as handle:
            handle.write(json.dumps(record.to_dict(), default=str) + '\n')

    def list_audit_records(
        self,
        *,
        limit: int = 100,
        event_type: Optional[str] = None,
    ) -> List[AuditRecord]:
        records: List[AuditRecord] = []
        paths = sorted(self.audit_dir.glob('*.jsonl'), reverse=True)

        for path in paths:
            try:
                with open(path, 'r', encoding='utf-8') as handle:
                    for line in handle:
                        if not line.strip():
                            continue
                        item = json.loads(line)
                        if event_type and item.get('event_type') != event_type:
                            continue
                        records.append(AuditRecord(**item))
            except Exception as exc:
                log.warning(f'Failed to read Shannon audit log {path}: {exc}')
                continue

            if limit >= 0 and len(records) >= limit:
                break

        records.sort(key=lambda item: str(item.timestamp or ''), reverse=True)
        if limit >= 0:
            return records[:limit]
        return records

    def get_audit_record(self, record_id: str) -> Optional[AuditRecord]:
        record_id = str(record_id or '').strip()
        if not record_id:
            return None

        for record in self.list_audit_records(limit=-1):
            if record.record_id == record_id:
                return record
        return None

    def compute_stats(self) -> Dict[str, Any]:
        records = self.list_audit_records(limit=-1)
        references = self._load_references()
        unique_reference_ids = {
            str(item.get('reference_id') or key)
            for key, item in references.items()
        }
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()
        one_hour_ago = now - timedelta(hours=1)

        messages_today = 0
        commands_today = 0
        notifications_today = 0
        errors_today = 0
        messages_last_hour = 0
        channels_seen: set[str] = set()
        last_activity_at = ''

        event_counter = Counter()

        for record in records:
            event_counter[record.event_type] += 1
            if record.channel_id:
                channels_seen.add(record.channel_id)

            timestamp = self._parse_timestamp(record.timestamp)
            if timestamp and (not last_activity_at or record.timestamp > last_activity_at):
                last_activity_at = record.timestamp

            if record.event_type == 'activity_received':
                if str(record.timestamp).startswith(today):
                    messages_today += 1
                if timestamp and timestamp >= one_hour_ago:
                    messages_last_hour += 1

            if record.event_type == 'decision' and str(record.timestamp).startswith(today):
                commands_today += 1

            if record.event_type == 'notification_posted' and str(record.timestamp).startswith(today):
                notifications_today += 1

            if record.status != 'ok' and str(record.timestamp).startswith(today):
                errors_today += 1

        return {
            'messages_today': messages_today,
            'commands_today': commands_today,
            'notifications_today': notifications_today,
            'errors_today': errors_today,
            'messages_last_hour': messages_last_hour,
            'conversation_reference_count': len(unique_reference_ids),
            'channel_count': len(channels_seen),
            'last_activity_at': last_activity_at,
            'event_counts': dict(event_counter),
        }

    # ── Conversation state (ephemeral, in-memory) ──────────────────────────

    _conversation_states: Dict[str, ConversationState] = {}

    def save_conversation_state(self, state: ConversationState) -> None:
        """Store a pending conversation by user_id + agent_id composite key."""
        key = f"{state.user_id}:{state.agent_id}"
        ShannonStateStore._conversation_states[key] = state
        log.debug(f"Saved conversation state: {key} command={state.command}")

    def get_conversation_state(self, user_id: str, agent_id: str) -> Optional[ConversationState]:
        """Retrieve a pending conversation if one exists for this user+agent."""
        key = f"{user_id}:{agent_id}"
        return ShannonStateStore._conversation_states.get(key)

    def clear_conversation_state(self, user_id: str, agent_id: str) -> None:
        """Remove conversation state (command completed or cancelled)."""
        key = f"{user_id}:{agent_id}"
        removed = ShannonStateStore._conversation_states.pop(key, None)
        if removed:
            log.debug(f"Cleared conversation state: {key}")

    def clear_all_conversation_states_for_user(self, user_id: str) -> None:
        """Clear all pending conversations for a user (e.g. when they switch commands)."""
        to_remove = [k for k in ShannonStateStore._conversation_states if k.startswith(f"{user_id}:")]
        for k in to_remove:
            del ShannonStateStore._conversation_states[k]
        if to_remove:
            log.debug(f"Cleared {len(to_remove)} conversation states for user {user_id}")

    def _load_references(self) -> Dict[str, Dict[str, Any]]:
        if not self.references_path.exists():
            return {}

        try:
            return json.loads(self.references_path.read_text(encoding='utf-8'))
        except Exception as exc:
            log.warning(f'Failed to load Shannon conversation references: {exc}')
            return {}

    @staticmethod
    def _parse_timestamp(value: Any) -> Optional[datetime]:
        raw = str(value or '').strip()
        if not raw:
            return None

        try:
            if raw.endswith('Z'):
                raw = raw[:-1] + '+00:00'
            return datetime.fromisoformat(raw)
        except ValueError:
            return None
