##########################################################################################
#
# Module: agents/workforce/herodotus/agent.py
#
# Description: Herodotus Knowledge Capture agent.
#              Ingests Teams meeting transcripts and produces structured
#              summaries, decisions, and action items.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentConfig, AgentResponse
from agents.herodotus.models import (
    MeetingRecord,
    TranscriptRecord,
    MeetingSummaryRecord,
    ActionItemDraft,
    DecisionRecord,
)

log = logging.getLogger(os.path.basename(sys.argv[0]))

_PROMPT_DIR = Path(__file__).parent / 'prompts'


class HerodotusAgent(BaseAgent):
    '''
    Knowledge Capture agent.

    Ingests Microsoft Teams meeting transcripts, produces structured
    technical summaries, extracts decisions and action items, and
    preserves human rationale as durable records.

    Zone: intelligence
    Phase: 4
    '''

    def __init__(self, **kwargs):
        instruction = self._load_system_prompt()
        config = AgentConfig(
            name='herodotus',
            description=(
                'Ingests Teams meeting transcripts and produces structured '
                'summaries, decisions, and action items'
            ),
            instruction=instruction,
            max_iterations=10,
        )
        super().__init__(config=config, **kwargs)

    @staticmethod
    def _load_system_prompt() -> str:
        prompt_path = _PROMPT_DIR / 'system.md'
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        log.warning(f'Herodotus system prompt not found: {prompt_path}')
        return 'You are Herodotus, the Knowledge Capture agent for Cornelis Networks.'

    def run(self, input_data: Any) -> AgentResponse:
        '''
        Run the Herodotus agent.

        Input:
            input_data: A dict or string describing the knowledge capture task.

        Output:
            AgentResponse with meeting summary results.
        '''
        return self._run_with_tools(str(input_data))

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def ingest_meeting(
        self,
        meeting_id: str,
        transcript_ref: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        '''
        Ingest a meeting transcript and metadata.

        Input:
            meeting_id: Teams meeting identifier.
            transcript_ref: URI or reference to the transcript.
            metadata: Meeting metadata (title, organizer, attendees, etc.).

        Output:
            MeetingRecord with ingest status.
        '''
        pass

    def summarize_meeting(self, meeting_id: str) -> Dict[str, Any]:
        '''
        Generate a structured summary for an ingested meeting.

        Input:
            meeting_id: Meeting identifier to summarize.

        Output:
            MeetingSummaryRecord with decisions, actions, and open questions.
        '''
        pass

    def extract_actions(self, meeting_id: str) -> List[Dict[str, Any]]:
        '''
        Extract action items from a meeting transcript.

        Input:
            meeting_id: Meeting identifier.

        Output:
            List of ActionItemDraft records.
        '''
        pass

    def publish_summary(
        self,
        meeting_id: str,
        target: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Publish an approved meeting summary to configured targets.

        Input:
            meeting_id: Meeting identifier.
            target: Optional specific publication target.

        Output:
            Publication status record.
        '''
        pass
