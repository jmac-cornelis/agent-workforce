##########################################################################################
#
# Module: agents/workforce/linnaeus/agent.py
#
# Description: Linnaeus Traceability agent.
#              Maintains exact, queryable relationships between requirements,
#              Jira issues, commits, builds, tests, releases, and versions.
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
from agents.linnaeus.models import (
    TraceabilityRecord,
    RelationshipEdge,
    TraceQuery,
    CoverageGapRecord,
    TraceAssertion,
)

log = logging.getLogger(os.path.basename(sys.argv[0]))

_PROMPT_DIR = Path(__file__).parent / 'prompts'


class LinnaeusAgent(BaseAgent):
    '''
    Traceability agent.

    Establishes and serves the authoritative relationship graph across
    Jira issues, commits, builds, tests, releases, and version mappings.

    Zone: intelligence
    Phase: 3
    '''

    def __init__(self, **kwargs):
        instruction = self._load_system_prompt()
        config = AgentConfig(
            name='linnaeus',
            description=(
                'Maintains exact queryable relationships between requirements, '
                'issues, commits, builds, tests, releases, and versions'
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
        log.warning(f'Linnaeus system prompt not found: {prompt_path}')
        return 'You are Linnaeus, the Traceability agent for Cornelis Networks.'

    def run(self, input_data: Any) -> AgentResponse:
        '''
        Run the Linnaeus agent.

        Input:
            input_data: A dict or string describing the traceability task.

        Output:
            AgentResponse with traceability results.
        '''
        return self._run_with_tools(str(input_data))

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def assert_trace(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        edge_type: str,
        evidence_source: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Assert a traceability relationship between two records.

        Input:
            source_type: Type of source record (issue, build, test, etc.).
            source_id: Identifier of the source record.
            target_type: Type of target record.
            target_id: Identifier of the target record.
            edge_type: Relationship type (e.g. issue_affects_build).
            evidence_source: Where the evidence came from.

        Output:
            Stored TraceAssertion record.
        '''
        pass

    def get_trace_view(
        self,
        record_type: str,
        record_id: str,
    ) -> Dict[str, Any]:
        '''
        Get a trace view centered on a specific record.

        Input:
            record_type: Type of record (issue, build, release, requirement).
            record_id: Identifier of the record.

        Output:
            Trace view with related records across all dimensions.
        '''
        pass

    def get_coverage_gaps(
        self,
        project: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        '''
        Get missing-link findings in critical traceability chains.

        Input:
            project: Optional project scope filter.
            severity: Optional severity filter.

        Output:
            List of coverage gap records.
        '''
        pass

    def query_builds(self, build_id: str) -> Dict[str, Any]:
        '''
        Query traceability for a specific build.

        Input:
            build_id: Internal build identifier.

        Output:
            Related issues, tests, releases, and external versions.
        '''
        pass

    def query_issues(self, jira_key: str) -> Dict[str, Any]:
        '''
        Query traceability for a specific Jira issue.

        Input:
            jira_key: Jira issue key.

        Output:
            Linked builds, tests, release relevance, and gap flags.
        '''
        pass
