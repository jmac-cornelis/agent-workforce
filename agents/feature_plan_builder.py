##########################################################################################
#
# Module: agents/feature_plan_builder.py
#
# Description: Feature Plan Builder Agent for the Feature Planning pipeline.
#              Converts a FeatureScope into a concrete Jira project plan with
#              Epics and Stories, ready for human review and execution.
#
#              The plan is produced entirely by the LLM via a ReAct loop.
#              The agent sends the scoped work items as a structured prompt
#              and the LLM returns a JSON plan conforming to the JiraPlan
#              schema.  There is no deterministic fallback — the LLM is the
#              authoritative plan builder.
#
# Author: Cornelis Networks
#
##########################################################################################

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentConfig, AgentResponse

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class FeaturePlanBuilderAgent(BaseAgent):
    '''
    Agent that converts a FeatureScope into a Jira project plan.

    The entire plan — epic grouping, story ordering, descriptions,
    acceptance criteria — is produced by the LLM via a ReAct loop.
    The system prompt (loaded from config/prompts/feature_plan_builder.md)
    instructs the LLM on the epic-threading strategy, story format,
    and JSON output schema.

    Produces a JiraPlan with Epics and Stories, including component
    assignment, descriptions with acceptance criteria, and confidence tags.
    '''

    def __init__(self, **kwargs):
        '''
        Initialize the Feature Plan Builder Agent.

        Registers Jira and file tools for component lookup and output.
        '''
        # Load the system prompt from the .md file.  This is the sole
        # source of LLM instructions — there is no hardcoded fallback.
        instruction = self._load_prompt_file()
        if not instruction:
            raise FileNotFoundError(
                'config/prompts/feature_plan_builder.md is required but not found. '
                'The Feature Plan Builder Agent has no hardcoded fallback prompt.'
            )

        config = AgentConfig(
            name='feature_plan_builder',
            description='Converts scoped work into Jira Epics and Stories',
            instruction=instruction,
            max_iterations=20,
        )

        # The plan builder sends large prompts (full scope + Jira metadata)
        # so we need a longer LLM timeout than the default 120s.
        if 'llm' not in kwargs:
            from llm.config import get_llm_client
            kwargs['llm'] = get_llm_client(timeout=600.0)

        super().__init__(config=config, **kwargs)
        self._register_builder_tools()

        # Cache for Jira components (populated on first use)
        self._jira_components: Optional[List[Dict[str, Any]]] = None

    # ------------------------------------------------------------------
    # Tool registration
    # ------------------------------------------------------------------

    def _register_builder_tools(self) -> None:
        '''Register tools the Plan Builder needs.'''
        # Jira tools — for component lookup
        try:
            from tools.jira_tools import get_project_info, get_components
            self.register_tool(get_project_info)
            self.register_tool(get_components)
        except ImportError:
            log.warning('jira_tools not available for FeaturePlanBuilderAgent')

        # File tools — for writing output
        try:
            from tools.file_tools import write_file, write_json
            self.register_tool(write_file)
            self.register_tool(write_json)
        except ImportError:
            log.warning('file_tools not available for FeaturePlanBuilderAgent')

    # ------------------------------------------------------------------
    # Prompt loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_prompt_file() -> Optional[str]:
        '''Load the plan builder prompt from config/prompts/.'''
        prompt_path = os.path.join('config', 'prompts', 'feature_plan_builder.md')
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                log.warning(f'Failed to load feature plan builder prompt: {e}')
        return None

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self, input_data: Any) -> AgentResponse:
        '''
        Run the Feature Plan Builder Agent.

        The LLM is the authoritative plan builder.  The ReAct loop lets
        the LLM call tools (e.g. get_components) to gather Jira metadata,
        then produce a JSON plan conforming to the JiraPlan schema.

        Input:
            input_data: Dictionary containing:
                - feature_request: str — The user's feature description
                - project_key: str — Target Jira project key
                - feature_scope: dict — Output from the Scoping Agent

        Output:
            AgentResponse with a JiraPlan in metadata['jira_plan'].
        '''
        log.debug('FeaturePlanBuilderAgent.run()')

        if not isinstance(input_data, dict):
            return AgentResponse.error_response(
                'Invalid input: expected dict with feature_scope and project_key'
            )

        feature_request = input_data.get('feature_request', '')
        project_key = input_data.get('project_key', '')
        feature_scope = input_data.get('feature_scope', {})

        if not project_key:
            return AgentResponse.error_response('No project_key provided')
        if not feature_scope:
            return AgentResponse.error_response('No feature_scope provided')

        # Build the user prompt with all scope items and instructions
        user_prompt = self._build_plan_prompt(
            feature_request, project_key, feature_scope
        )

        # Run the ReAct loop — the LLM calls tools (get_components, etc.)
        # and produces the plan as JSON in its final response.
        react_response = self._run_with_tools(user_prompt, timeout=self._timeout)

        if not react_response.success:
            return AgentResponse.error_response(
                f'LLM plan generation failed: {react_response.error}'
            )

        # Parse the LLM's JSON output into a JiraPlan dict
        feature_name = feature_scope.get(
            'feature_name', feature_request[:100]
        )
        plan_dict = self._parse_llm_plan(
            react_response.content or '',
            project_key,
            feature_name,
            feature_scope,
        )

        return AgentResponse.success_response(
            content=plan_dict.get('summary_markdown', ''),
            tool_calls=react_response.tool_calls,
            iterations=react_response.iterations,
            metadata={'jira_plan': plan_dict},
        )

    # ------------------------------------------------------------------
    # LLM output parsing
    # ------------------------------------------------------------------

    def _parse_llm_plan(
        self,
        llm_output: str,
        project_key: str,
        feature_name: str,
        feature_scope: Dict[str, Any],
    ) -> Dict[str, Any]:
        '''
        Parse the LLM's text output into a JiraPlan-compatible dict.

        The LLM is instructed to emit a JSON block (```json ... ```)
        conforming to the JiraPlan schema.  This method extracts that
        block, validates it, and fills in any missing computed fields
        (total_epics, total_stories, total_tickets, summary_markdown,
        confidence_report).

        If the JSON block is missing or malformed, we attempt to build
        a minimal plan from whatever structure we can find.
        '''
        # Try to extract a JSON block from the LLM output
        plan_data = self._extract_json_block(llm_output)

        if not plan_data:
            log.warning('No JSON block found in LLM output; returning raw text')
            return {
                'project_key': project_key,
                'feature_name': feature_name,
                'epics': [],
                'total_epics': 0,
                'total_stories': 0,
                'total_tickets': 0,
                'summary_markdown': llm_output,
                'confidence_report': {},
            }

        # Ensure top-level fields are present
        plan_data.setdefault('project_key', project_key)
        plan_data.setdefault('feature_name', feature_name)
        epics = plan_data.get('epics', [])

        # Compute totals from the epics list
        total_epics = len(epics)
        total_stories = sum(len(e.get('stories', [])) for e in epics)
        total_tickets = total_epics + total_stories
        plan_data['total_epics'] = total_epics
        plan_data['total_stories'] = total_stories
        plan_data['total_tickets'] = total_tickets

        # Build summary_markdown if the LLM didn't include one
        if 'summary_markdown' not in plan_data:
            plan_data['summary_markdown'] = self._build_markdown_from_plan(
                plan_data, feature_scope
            )

        # Build confidence_report if the LLM didn't include one
        if 'confidence_report' not in plan_data:
            plan_data['confidence_report'] = self._compute_confidence_report(
                plan_data
            )

        return plan_data

    # ------------------------------------------------------------------
    # Markdown summary builder (from parsed plan dict)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_markdown_from_plan(
        plan: Dict[str, Any],
        feature_scope: Dict[str, Any],
    ) -> str:
        '''Build a human-readable Markdown summary from a plan dict.'''
        lines = [
            f'# JIRA PROJECT PLAN: {plan.get("feature_name", "?")}',
            '',
            f'**Project**: {plan.get("project_key", "?")}',
            f'**Total Epics**: {plan.get("total_epics", 0)}',
            f'**Total Stories**: {plan.get("total_stories", 0)}',
            f'**Total Tickets**: {plan.get("total_tickets", 0)}',
            '',
            '---',
            '',
        ]

        for epic in plan.get('epics', []):
            components_str = ', '.join(
                epic.get('components', [])
            ) or 'unassigned'
            lines.extend([
                f'## EPIC: {epic.get("summary", "?")}',
                f'  Components: {components_str}',
                f'  Labels: {", ".join(epic.get("labels", []))}',
                f'  Stories (in dependency order): {len(epic.get("stories", []))}',
                '',
            ])

            for story_idx, story in enumerate(epic.get('stories', []), 1):
                s_components = ', '.join(
                    story.get('components', [])
                ) or 'unassigned'
                assignee = story.get('assignee') or 'unassigned'
                lines.extend([
                    f'  ### {story_idx}. STORY: {story.get("summary", "?")}',
                    f'    Components: {s_components}',
                    f'    Assignee: {assignee}',
                    f'    Labels: {", ".join(story.get("labels", []))}',
                    f'    Confidence: {story.get("confidence", "?").upper()}',
                    f'    Complexity: {story.get("complexity", "?").upper()}',
                    f'    Acceptance Criteria: {len(story.get("acceptance_criteria", []))} items',
                ])
                deps = story.get('dependencies', [])
                if deps:
                    lines.append(f'    Dependencies: {", ".join(deps)}')
                lines.append('')

        # Confidence report
        report = plan.get('confidence_report', {})
        lines.extend([
            '---',
            '',
            '## CONFIDENCE REPORT',
            '',
        ])
        by_conf = report.get('by_confidence', {})
        for level in ('high', 'medium', 'low'):
            count = by_conf.get(level, 0)
            lines.append(f'- {level.upper()} confidence stories: {count}')

        # Open questions from scoping
        questions = feature_scope.get('open_questions', [])
        if questions:
            lines.extend([
                '',
                '## OPEN QUESTIONS',
                '',
            ])
            for q in questions:
                if isinstance(q, dict):
                    blocking = '[BLOCKING]' if q.get('blocking') else '[NON-BLOCKING]'
                    lines.append(f"- {blocking} {q.get('question', '?')}")
                    if q.get('context'):
                        lines.append(f"  Context: {q['context']}")
                else:
                    lines.append(f'- {q}')

        # Assumptions
        assumptions = feature_scope.get('assumptions', [])
        if assumptions:
            lines.extend([
                '',
                '## ASSUMPTIONS',
                '',
            ])
            for a in assumptions:
                lines.append(f'- {a}')

        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Confidence report builder (from parsed plan dict)
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_confidence_report(plan: Dict[str, Any]) -> Dict[str, Any]:
        '''Build aggregate confidence metrics from a plan dict.'''
        by_confidence: Dict[str, int] = {}
        by_complexity: Dict[str, int] = {}
        total_stories = 0
        stories_with_deps = 0

        for epic in plan.get('epics', []):
            for story in epic.get('stories', []):
                total_stories += 1
                conf = story.get('confidence', 'medium').lower()
                by_confidence[conf] = by_confidence.get(conf, 0) + 1
                comp = story.get('complexity', 'M').upper()
                by_complexity[comp] = by_complexity.get(comp, 0) + 1
                if story.get('dependencies'):
                    stories_with_deps += 1

        return {
            'total_epics': plan.get('total_epics', 0),
            'total_stories': total_stories,
            'by_confidence': by_confidence,
            'by_complexity': by_complexity,
            'stories_with_dependencies': stories_with_deps,
        }

    # ------------------------------------------------------------------
    # Internal helpers — Jira component lookup
    # ------------------------------------------------------------------

    def _get_jira_components(self, project_key: str) -> List[Dict[str, Any]]:
        '''Fetch Jira components for the project (cached).'''
        if self._jira_components is not None:
            return self._jira_components

        try:
            from tools.jira_tools import get_components
            result = get_components(project_key=project_key)
            data = result.data if hasattr(result, 'data') else result
            if isinstance(data, dict):
                self._jira_components = data.get('components', [])
                return self._jira_components
        except Exception as e:
            log.warning(f'Failed to fetch Jira components: {e}')

        self._jira_components = []
        return self._jira_components

    # ------------------------------------------------------------------
    # Internal helpers — prompt building
    # ------------------------------------------------------------------

    def _build_plan_prompt(
        self,
        feature_request: str,
        project_key: str,
        feature_scope: Dict[str, Any],
    ) -> str:
        '''
        Build the user prompt for the LLM-driven plan building.

        Presents all ticketable scope items (firmware, driver, tool)
        with their dependencies, complexity, and confidence.  Test,
        integration, and documentation items are noted as excluded.
        '''
        lines = [
            f'## Feature Request\n\n{feature_request}\n',
            f'## Target Jira Project\n\nProject key: `{project_key}`\n',
            '## Scoped Work Items\n',
        ]

        # Category display labels for the prompt
        category_labels = {
            'firmware': 'Firmware',
            'driver': 'Driver',
            'tool': 'Tools & Diagnostics',
        }

        # Categories that should NOT produce tickets
        excluded_categories = {'test', 'integration', 'documentation'}

        # Summarize scope items by category — only include categories that
        # produce tickets (firmware, driver, tool).
        for category in ('firmware', 'driver', 'tool'):
            items = feature_scope.get(f'{category}_items', [])
            if items:
                label = category_labels.get(category, category.title())
                lines.append(f'### {label} ({len(items)} items):')
                for item in items:
                    complexity = item.get('complexity', '?')
                    confidence = item.get('confidence', '?')
                    title = item.get('title', '?')
                    description = item.get('description', '')
                    deps = item.get('dependencies', [])
                    ac = item.get('acceptance_criteria', [])
                    dep_str = f' → depends on: {", ".join(deps)}' if deps else ''
                    lines.append(
                        f'- [{complexity}] {title} (Confidence: {confidence}){dep_str}'
                    )
                    if description:
                        lines.append(f'  Description: {description}')
                    if ac:
                        lines.append(f'  Acceptance criteria: {"; ".join(ac)}')
                lines.append('')

        # Note excluded items so the LLM knows they exist but should not
        # become tickets
        excluded_count = 0
        for cat in excluded_categories:
            excluded_count += len(feature_scope.get(f'{cat}_items', []))
        if excluded_count:
            lines.append(
                f'*Note: {excluded_count} test/integration/documentation items '
                f'were excluded — unit tests and docs are acceptance criteria '
                f'on coding Stories; integration/validation testing is owned '
                f'by another group.*\n'
            )

        # Open questions
        questions = feature_scope.get('open_questions', [])
        if questions:
            lines.append('### Open Questions:')
            for q in questions:
                if isinstance(q, dict):
                    lines.append(f"- {q.get('question', '?')}")
                else:
                    lines.append(f'- {q}')
            lines.append('')

        # Assumptions
        assumptions = feature_scope.get('assumptions', [])
        if assumptions:
            lines.append('### Assumptions:')
            for a in assumptions:
                lines.append(f'- {a}')
            lines.append('')

        lines.append(
            '## Instructions\n\n'
            'Please build a Jira project plan from these scoped items:\n\n'
            '1. **Look up components** — Use `get_components` to find the '
            f'project\'s component list for `{project_key}`.\n'
            '2. **Create functional-thread Epics** — Group items into Epics '
            'based on their dependency connections using the directed '
            'root-tree threading algorithm described in your system prompt.  '
            'Items connected by dependencies (even across firmware/driver/tool) '
            'belong in the same Epic.  Do NOT group by work-type.\n'
            '3. **Order Stories by dependencies** — Within each Epic, list '
            'Stories in topological order (items that must be done first '
            'appear first).\n'
            '4. **Create Stories** — One per scope item, with full descriptions '
            'and acceptance criteria.  Every Story must include "Unit tests pass" '
            'and "Code reviewed and merged" as acceptance criteria.\n'
            '5. **Do NOT create test or documentation tickets** — Those are '
            'acceptance criteria on coding Stories, not separate tickets.\n'
            '6. **Assign components** — Match scope categories to Jira components.\n'
            '7. **Produce the JSON plan** — Emit a single ```json``` code block '
            'conforming to the JSON output schema in your system prompt.\n\n'
            'This is a DRY RUN — do NOT create any tickets. Just produce the plan.'
        )

        return '\n'.join(lines)
