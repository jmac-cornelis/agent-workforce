##########################################################################################
#
# Module: agents/mercator/agent.py
#
# Description: Mercator Version Manager agent.
#              Maps internal Fuze build IDs to external customer-facing release
#              versions with conflict detection and lineage tracking.
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
from agents.mercator.models import (
    VersionMappingRequest,
    VersionMappingRecord,
    VersionLineageRecord,
    VersionConflict,
    CompatibilityRecord,
)

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))

# Path to the system prompt for this agent
_PROMPT_DIR = Path(__file__).parent / 'prompts'


class MercatorAgent(BaseAgent):
    '''
    Version Manager agent.

    Maps internal Fuze build identities (FuzeID) to external release versions,
    maintains deterministic version lineage, detects mapping conflicts, and
    preserves compatibility and supersession records.

    Zone: intelligence
    Phase: 3
    '''

    def __init__(self, **kwargs):
        instruction = self._load_system_prompt()
        config = AgentConfig(
            name='mercator',
            description=(
                'Maps Fuze internal build IDs to external customer-facing '
                'release versions with conflict detection and lineage tracking'
            ),
            instruction=instruction,
            max_iterations=10,
        )
        super().__init__(config=config, **kwargs)

    # ------------------------------------------------------------------
    # Prompt loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_system_prompt() -> str:
        '''Load the system prompt from prompts/system.md.'''
        prompt_path = _PROMPT_DIR / 'system.md'
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        log.warning(f'Mercator system prompt not found: {prompt_path}')
        return 'You are Mercator, the Version Manager agent for Cornelis Networks.'

    # ------------------------------------------------------------------
    # Agent entry point
    # ------------------------------------------------------------------

    def run(self, input_data: Any) -> AgentResponse:
        '''
        Run the Mercator agent with the given input.

        Input:
            input_data: A dict or string describing the version mapping task.

        Output:
            AgentResponse with version mapping results.
        '''
        return self._run_with_tools(str(input_data))

    # ------------------------------------------------------------------
    # Tools — scaffolding only, bodies are pass
    # ------------------------------------------------------------------

    def map_build_to_version(
        self,
        build_id: str,
        product: str,
        release_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        '''
        Map an internal build ID (FuzeID) to an external release version.

        Input:
            build_id: Internal Fuze build identifier.
            product: Product or release name.
            release_context: Optional release context from Humphrey.

        Output:
            Proposed or accepted version mapping record.
        '''
        pass

    def get_external_version(self, build_id: str) -> Dict[str, Any]:
        '''
        Look up external version(s) for a given internal build ID.

        Input:
            build_id: Internal Fuze build identifier.

        Output:
            External version mapping(s) for the build.
        '''
        pass

    def get_internal_builds(self, external_version: str) -> List[Dict[str, Any]]:
        '''
        Look up internal build ID(s) for a given external version.

        Input:
            external_version: Customer-facing version string.

        Output:
            List of internal builds and lineage for the external version.
        '''
        pass

    def confirm_mapping(
        self,
        mapping_id: str,
        confirmed_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        '''
        Confirm a proposed version mapping when required by policy.

        Input:
            mapping_id: ID of the proposed mapping to confirm.
            confirmed_by: Identity of the confirming user or service.

        Output:
            Confirmed mapping record.
        '''
        pass


BabbageAgent = MercatorAgent
