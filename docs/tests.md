# Tests — Design Reference

## Purpose
This internal document candidate was generated from authoritative source artifacts for review before publication.

## Metadata
- Documentation class: `as_built`
- Generated: `2026-04-08 14:54 UTC`
- Confidence: `medium`

## Authoritative Inputs
- `jmac-cornelis/agent-workforce:tests/test_confluence_utils_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_confluence_search_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/conftest.py` (source)
- `jmac-cornelis/agent-workforce:tests/GITHUB_TEST_COVERAGE_ANALYSIS.md` (source)
- `jmac-cornelis/agent-workforce:tests/test_confluence_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_agents_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_agent_rename_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_core_queries_coverage.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_core_tickets.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_core_reporting.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_core_utils.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_api_github_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_agent_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_cli_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_github_polling_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_learning_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_excel_utils_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_evidence_contracts_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_env_loader_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_dry_run_mcp_messaging_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_utils_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_excel_utils_coverage.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_feature_planning_orchestrator_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_file_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_gantt_cli_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_docs_search_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_gantt_agent_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_gantt_components_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_gantt_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_integration_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_phase5_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_phase5_integration_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_write_ops_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_utils_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_agent_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_api_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_cli_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_confluence_publish_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_search_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_shannon_cards_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_pr_review_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_jira_actor_policy_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_jira_identity_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_jira_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_confluence_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_jira_utils_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_markdown_to_confluence.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_coverage.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_jira_utils_coverage.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_drucker_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_gantt_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_github_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_hemingway_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_notifications_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_shannon_dry_run_flow_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_shannon_pr_cards_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_release_tracking.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_shannon_service_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_smoke.py` (source)

## Key Facts

### Source: `jmac-cornelis/agent-workforce:tests/test_confluence_utils_char.py`
- import json
- from pathlib import Path
- from typing import Any, Optional
- import pytest
- import confluence_utils
- class _Response:
- def __init__(
- payload: Optional[dict[str, Any]] = None,
- status_code: int = 200,
- text: Optional[str] = None,

### Source: `jmac-cornelis/agent-workforce:tests/test_confluence_search_char.py`
- Module: test_confluence_search_char.py
- Description: Characterization tests for Confluence search capabilities.
- Covers search_pages_fulltext(), search_pages_by_label() in
- confluence_utils.py and their tool wrappers in tools/confluence_tools.py.
- Author: Cornelis Networks Engineering Tools
- import json
- import sys
- from types import SimpleNamespace
- from typing import Any, Dict, List, Optional
- from unittest.mock import MagicMock

### Source: `jmac-cornelis/agent-workforce:tests/conftest.py`
- import contextlib
- import io
- import sys
- import types
- from dataclasses import dataclass
- from pathlib import Path
- from types import ModuleType, SimpleNamespace
- from typing import Any, Dict, Iterable, List, Optional, cast
- import pytest
- from openpyxl import Workbook

### Source: `jmac-cornelis/agent-workforce:tests/GITHUB_TEST_COVERAGE_ANALYSIS.md`
- GitHub PR Hygiene — Test Coverage Analysis
- **Date**: 2026-03-28
- **Branch**: `feature/drucker-github-hygiene`
- **Test run**: 59 new tests, all passing (553 total pass, 2 pre-existing failures)
- | Module | Public Symbols | Tested | Coverage | Gap |
- |--------|---------------|--------|----------|-----|
- | `github_utils.py` | 22 (`__all__`) + 4 internal | 22 + 3 internal | **96%** | 3 untested (display/CLI) |
- | `tools/github_tools.py` | 11 tool functions + 1 class | 10 + 1 class | **91%** | 1 untested tool |
- | `shannon/cards.py` (PR builders) | 4 card builders | 4 | **100%** | — |
- | `agents/drucker_api.py` (GitHub endpoints) | 4 endpoints + 3 models | 4 endpoints | **100%** | — |

### Source: `jmac-cornelis/agent-workforce:tests/test_confluence_tools_char.py`
- import pytest
- from tools.confluence_tools import ConfluenceTools, search_confluence_pages
- def test_search_confluence_pages_tool_returns_toolresult(monkeypatch: pytest.MonkeyPatch):
- from tools import confluence_tools
- monkeypatch.setattr(confluence_tools, 'get_confluence', lambda: object())
- monkeypatch.setattr(
- confluence_tools,
- '_cu_search_pages',
- lambda _confluence, pattern, limit=25, space=None: [
- {'page_id': '123', 'title': 'Roadmap', 'link': 'https://example.test/page'}

### Source: `jmac-cornelis/agent-workforce:tests/test_agents_char.py`
- import json
- from types import SimpleNamespace
- import pytest
- from agents.base import AgentConfig, BaseAgent
- from llm.base import BaseLLM, LLMResponse
- from tools.base import ToolResult, tool
- class _DummyLLM(BaseLLM):
- def __init__(self, responses):
- super().__init__(model='dummy-model')
- self._responses = list(responses)

### Source: `jmac-cornelis/agent-workforce:tests/test_agent_rename_char.py`
- Module: tests/test_agent_rename_char.py
- Description: Characterization tests for the local agent rename wave.
- Verifies canonical renamed packages, legacy aliases, and
- non-deployed local config surfaces.
- Author: Cornelis Networks
- import sys
- from pathlib import Path
- def test_hemingway_exports_legacy_aliases():
- from agents.hemingway import (
- HemingwayDocumentationAgent,

### Source: `jmac-cornelis/agent-workforce:tests/test_core_queries_coverage.py`
- from types import SimpleNamespace
- from core import queries
- def test_quote_values_single_value():
- assert queries._quote_values(['Open']) == '"Open"'
- def test_quote_values_multiple_values_and_special_chars():
- values = ['In Progress', 'R&D', 'A, B']
- assert queries._quote_values(values) == '"In Progress", "R&D", "A, B"'
- def test_build_status_jql_with_empty_inputs():
- assert queries._build_status_jql(None) == ''
- assert queries._build_status_jql([]) == ''

### Source: `jmac-cornelis/agent-workforce:tests/test_core_tickets.py`
- from types import SimpleNamespace
- from core.tickets import extract_text_from_adf, issue_to_dict
- def test_issue_to_dict_resource_object_basic_fields():
- issue = SimpleNamespace(
- key='STL-501',
- id='501',
- fields=SimpleNamespace(
- summary='Resource summary',
- description='Resource description',
- issuetype=SimpleNamespace(name='Story'),

### Source: `jmac-cornelis/agent-workforce:tests/test_core_reporting.py`
- Tests for core/reporting.py
- - _next_day() helper
- - tickets_created_on() — JQL construction + issue_to_dict mapping
- - bugs_missing_field() — date-scoped and all-open variants
- - status_changes_by_actor() — REST API pagination, automation classification
- - daily_report() — composite orchestration
- - export_daily_report() — Excel and CSV export
- import csv
- import json
- import os

### Source: `jmac-cornelis/agent-workforce:tests/test_core_utils.py`
- import csv
- from typing import Any, cast
- from core import utils as core_utils
- def test_output_respects_quiet_mode_and_module_quiet_flag(capture_stdout):
- setattr(cast(Any, core_utils), '_quiet_mode', False)
- with capture_stdout() as out_visible:
- core_utils.output('visible')
- setattr(cast(Any, core_utils), '_quiet_mode', True)
- with capture_stdout() as out_hidden:
- core_utils.output('hidden')

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_api_github_char.py`
- Module: test_drucker_api_github_char.py
- Description: Characterization tests for the 4 GitHub endpoints in drucker_api.py.
- Covers POST /v1/github/pr-hygiene, POST /v1/github/pr-stale,
- POST /v1/github/pr-reviews, and GET /v1/github/prs/{owner}/{repo}.
- Author: Cornelis Networks Engineering Tools
- import sys
- from unittest.mock import MagicMock
- import pytest
- ---------------------------------------------------------------------------
- Fixtures

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_agent_char.py`
- import json
- from datetime import datetime, timezone
- from types import SimpleNamespace
- import pytest
- from agents.base import AgentResponse
- from agents.drucker.models import DruckerAction, DruckerFinding, DruckerHygieneReport, DruckerRequest
- from tools.base import ToolResult
- class _FixedDateTime(datetime):
- @classmethod
- def now(cls, tz=None):

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_cli_char.py`
- Module: tests/test_drucker_cli_char.py
- Description: Characterization tests for agents/drucker/cli.py command handlers.
- Covers all 6 subcommands: cmd_hygiene, cmd_issue_check,
- cmd_intake_report, cmd_bug_activity, cmd_github_hygiene, cmd_poll.
- Uses monkeypatch to stub agent and store dependencies — no live
- API calls.
- Author: Cornelis Networks
- import json
- import os
- import sys

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_github_polling_char.py`
- Module: tests/test_drucker_github_polling_char.py
- Description: Characterization tests for the GitHub PR hygiene polling loop
- in DruckerCoordinatorAgent.tick(). Covers the scan_type='github'
- branch: single/multi repo analysis, error handling, notification
- gating, parameter pass-through, and mixed-job scenarios.
- Author: Cornelis Networks
- import sys
- import types
- from types import SimpleNamespace
- from unittest.mock import MagicMock

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_learning_char.py`
- import pytest
- def test_drucker_learning_store_predicts_component_fix_version_and_priority():
- from agents.drucker.state.learning_store import DruckerLearningStore
- store = DruckerLearningStore(db_path=':memory:', min_observations=2)
- store.record_ticket({
- 'key': 'STL-101',
- 'summary': 'Fabric link instability',
- 'reporter': 'alice',
- 'components': ['Fabric'],
- 'fix_versions': ['12.1.0'],

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_tools_char.py`
- import pytest
- from agents.drucker.tools import (
- DruckerTools,
- create_drucker_bug_activity_report,
- create_drucker_issue_check,
- create_drucker_hygiene_report,
- create_drucker_intake_report,
- get_drucker_report,
- list_drucker_reports,
- def test_create_drucker_hygiene_report_tool_persists_report(

### Source: `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_tools_char.py`
- Module: test_dry_run_jira_tools_char.py
- Description: Characterization tests verifying dry-run (default) behavior
- for all 13 mutation functions in tools/jira_tools.py.
- Each test asserts that the function returns a ToolResult.success()
- with a preview dict containing 'dry_run': True and that NO
- actual Jira mutation occurs.
- Author: Cornelis Networks — AI Engineering Tools
- from unittest.mock import MagicMock
- import pytest
- from tools.jira_tools import JiraTools

### Source: `jmac-cornelis/agent-workforce:tests/test_excel_utils_char.py`
- import csv
- import sys
- from pathlib import Path
- from typing import Any, cast
- import openpyxl
- import excel_utils
- def test_convert_from_csv_creates_excel_structure(tmp_path):
- csv_path = tmp_path / "input.csv"
- csv_path.write_text(
- "key,status,priority,summary\n"

### Source: `jmac-cornelis/agent-workforce:tests/test_evidence_contracts_char.py`
- from core.evidence import load_evidence_bundle
- def test_load_evidence_bundle_reads_json_yaml_and_markdown(tmp_path):
- build_path = tmp_path / 'build.json'
- build_path.write_text(
- '{"evidence_type": "build", "title": "Build 101", "summary": "Green build", "facts": ["status: green"]}',
- encoding='utf-8',
- test_path = tmp_path / 'test.yaml'
- test_path.write_text(
- 'evidence_type: test\ntitle: Test Suite\nsummary: 42 tests passed\nfacts:\n - passed: 42\n',
- meeting_path = tmp_path / 'meeting_notes.md'

### Source: `jmac-cornelis/agent-workforce:tests/test_env_loader_char.py`
- Module: tests/test_env_loader_char.py
- Description: Characterization tests for config/env_loader.py.
- Validates three-tier env resolution: explicit path, config/env/ dir, .env fallback.
- Author: Cornelis Networks
- import os
- from pathlib import Path
- import pytest
- from config.env_loader import _find_env_dir, load_env
- ---------------------------------------------------------------------------
- Fixtures

### Source: `jmac-cornelis/agent-workforce:tests/test_dry_run_mcp_messaging_char.py`
- Module: tests/test_dry_run_mcp_messaging_char.py
- Description: Dry-run behavior tests for MCP server mutation tools and
- messaging/notification functions. Verifies that the default
- dry_run=True returns preview dicts without performing actual
- mutations.
- Author: Cornelis Networks
- import json
- from types import SimpleNamespace
- from unittest.mock import MagicMock
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_utils_char.py`
- Module: test_dry_run_jira_utils_char.py
- Description: Characterization tests verifying that jira_utils mutation functions
- (dashboard CRUD + gadget management + automation state) return early
- without calling Jira APIs when dry_run=True (the default).
- Author: John Macdonald
- import pytest
- from unittest.mock import MagicMock
- import jira_utils
- ---------------------------------------------------------------------------
- Fixtures

### Source: `jmac-cornelis/agent-workforce:tests/test_excel_utils_coverage.py`
- import csv
- import json
- import sys
- from argparse import Namespace
- from pathlib import Path
- from typing import Any, Optional, cast
- import openpyxl
- import pytest
- import excel_utils
- def create_test_excel(path: Path, headers: list[str], data: list[list[Any]], sheet_name: str = 'Data') -> Path:

### Source: `jmac-cornelis/agent-workforce:tests/test_feature_planning_orchestrator_char.py`
- Module: test_feature_planning_orchestrator_char.py
- Description: Characterization tests for Jira actor context in feature-plan
- execution.
- Author: Cornelis Networks — AI Engineering Tools
- import pytest
- from tools.base import ToolResult
- def test_feature_planning_execution_uses_actor_policy_for_ticket_tree_and_links(
- monkeypatch: pytest.MonkeyPatch,
- from agents.feature_planning_orchestrator import FeaturePlanningOrchestrator
- monkeypatch.setattr(

### Source: `jmac-cornelis/agent-workforce:tests/test_file_tools_char.py`
- from pathlib import Path
- from tools.file_tools import FileTools, find_in_files, read_file
- def test_read_file_supports_line_ranges(tmp_path: Path):
- sample = tmp_path / 'sample.txt'
- sample.write_text('alpha\nbeta\ngamma\ndelta', encoding='utf-8')
- result = read_file(str(sample), start_line=2, end_line=3)
- assert result.is_success
- assert result.data['content'] == 'beta\ngamma'
- assert result.data['selected_start_line'] == 2
- assert result.data['selected_end_line'] == 3

### Source: `jmac-cornelis/agent-workforce:tests/test_gantt_cli_char.py`
- Module: tests/test_gantt_cli_char.py
- Description: Characterization tests for agents/gantt/cli.py.
- Covers all 10 subcommand handlers: cmd_snapshot, cmd_snapshot_get,
- cmd_snapshot_list, cmd_release_monitor, cmd_release_monitor_get,
- cmd_release_monitor_list, cmd_release_survey, cmd_release_survey_get,
- cmd_release_survey_list, cmd_poll.
- Author: Cornelis Networks
- import json
- from types import SimpleNamespace
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_github_docs_search_char.py`
- Module: test_github_docs_search_char.py
- Description: Characterization tests for GitHub documentation search capabilities.
- Covers get_repo_readme(), list_repo_docs(), search_repo_docs() in
- github_utils.py and their tool wrappers in tools/github_tools.py.
- Author: Cornelis Networks Engineering Tools
- import sys
- from types import SimpleNamespace
- from typing import Any, Optional
- import pytest
- import github_utils

### Source: `jmac-cornelis/agent-workforce:tests/test_gantt_agent_char.py`
- import json
- from datetime import datetime, timezone
- from types import SimpleNamespace
- from unittest.mock import MagicMock
- import openpyxl
- import pytest
- from agents.base import AgentResponse
- from agents.gantt.models import (
- BugSummary,
- DependencyGraph,

### Source: `jmac-cornelis/agent-workforce:tests/test_gantt_components_char.py`
- from datetime import datetime, timezone
- from agents.gantt.models import DependencyEdge, DependencyGraph, MilestoneProposal, PlanningSnapshot
- def test_backlog_interpreter_and_dependency_mapper_normalize_and_attach_edges(
- fake_issue_resource_factory,
- from agents.gantt.components import BacklogInterpreter, DependencyMapper
- issue = fake_issue_resource_factory(
- key='STL-201',
- summary='Planner component work',
- issue_type='Story',
- status='Blocked',

### Source: `jmac-cornelis/agent-workforce:tests/test_gantt_tools_char.py`
- import pytest
- from agents.gantt.models import (
- BugSummary,
- DependencyGraph,
- PlanningSnapshot,
- ReleaseMonitorReport,
- ReleaseSurveyReleaseSummary,
- ReleaseSurveyReport,
- from agents.gantt.tools import (
- GanttTools,

### Source: `jmac-cornelis/agent-workforce:tests/test_github_integration_char.py`
- Module: tests/test_github_integration_char.py
- Description: Integration smoke tests for the GitHub PR hygiene pipeline.
- Validates analyze_repo_pr_hygiene() → card builder end-to-end.
- Author: Cornelis Networks
- from datetime import datetime, timedelta, timezone
- from types import SimpleNamespace
- import pytest
- import github_utils
- from shannon.cards import (
- build_pr_hygiene_card,

### Source: `jmac-cornelis/agent-workforce:tests/test_github_phase5_char.py`
- from datetime import datetime, timedelta, timezone
- from types import SimpleNamespace
- import pytest
- import github_utils
- ---------------------------------------------------------------------------
- Helpers — reuse patterns from test_github_utils_char.py
- def _silent_output(_message: str = '') -> None:
- return None
- def _patch_common(monkeypatch: pytest.MonkeyPatch) -> None:
- monkeypatch.setattr(github_utils, 'output', _silent_output)

### Source: `jmac-cornelis/agent-workforce:tests/test_github_tools_char.py`
- Module: tests/test_github_tools_char.py
- Description: Characterization tests for tools/github_tools.py.
- Validates all 11 tool functions and the GitHubTools collection class.
- Zero live API calls — all github_utils functions are monkeypatched.
- Author: Cornelis Networks
- import pytest
- from tools.github_tools import GitHubTools
- ****************************************************************************************
- A) Repository tools
- def test_list_repos_returns_success(monkeypatch: pytest.MonkeyPatch):

### Source: `jmac-cornelis/agent-workforce:tests/test_github_phase5_integration_char.py`
- Module: tests/test_github_phase5_integration_char.py
- Description: Characterization tests for Phase 5 scan integration layer.
- Covers tool wrappers (5), Shannon cards (10), API endpoints (5),
- and polling dispatch (3) for the extended hygiene scan features.
- Zero live API calls — all github_utils functions are monkeypatched.
- Author: Cornelis Networks
- import sys
- import types
- from unittest.mock import MagicMock
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_github_write_ops_char.py`
- Module: test_github_write_ops_char.py
- Description: Characterization tests for the 5 write operations in github_utils.py:
- get_pr_changed_files, get_file_content, create_or_update_file,
- batch_commit_files, post_pr_comment.
- Author: Cornelis Networks Engineering Tools
- from types import SimpleNamespace
- import pytest
- import github_utils
- ---------------------------------------------------------------------------
- def _silent_output(_message: str = '') -> None:

### Source: `jmac-cornelis/agent-workforce:tests/test_github_utils_char.py`
- import sys
- from datetime import datetime, timedelta, timezone
- from types import SimpleNamespace
- from typing import Any, Optional
- import pytest
- import github_utils
- ---------------------------------------------------------------------------
- Helpers — match jira_utils test pattern
- def _silent_output(_message: str = '') -> None:
- return None

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_agent_char.py`
- import json
- from types import SimpleNamespace
- import pytest
- from agents.hemingway.models import (
- DocumentationPatch,
- DocumentationRecord,
- DocumentationRequest,
- PublicationRecord,
- from agents.review_agent import ApprovalStatus, ReviewItem, ReviewSession, ReviewAgent
- from tools.base import ToolResult

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_api_char.py`
- Module: test_hemingway_api_char.py
- Description: Characterization tests for the Hemingway Documentation Agent REST API.
- Covers health, status, record retrieval, documentation generation,
- impact detection, and publication endpoints in agents/hemingway/api.py.
- Author: Cornelis Networks Engineering Tools
- import os
- import sys
- from types import SimpleNamespace
- from unittest.mock import MagicMock, patch
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_cli_char.py`
- Module: tests/test_hemingway_cli_char.py
- Description: Characterization tests for agents/hemingway/cli.py.
- Covers all three subcommands (cmd_generate, cmd_list, cmd_get)
- with monkeypatched agent and store stubs — no live API calls.
- Author: Cornelis Networks
- import json
- from types import SimpleNamespace
- import pytest
- from agents.hemingway.models import (
- DocumentationPatch,

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_confluence_publish_char.py`
- Module: test_hemingway_confluence_publish_char.py
- Description: Characterization tests for Hemingway Confluence publish functionality.
- Covers the POST /v1/docs/confluence/publish-page API endpoint,
- the confluence-publish CLI subcommand, and the Shannon card builder.
- Author: Cornelis Networks Engineering Tools
- import sys
- from types import SimpleNamespace
- from unittest.mock import MagicMock, patch
- import pytest
- from tools.base import ToolResult

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_search_char.py`
- Module: test_hemingway_search_char.py
- Description: Characterization tests for Hemingway search capabilities.
- Covers HemingwayRecordStore.search_records(), the POST /v1/docs/search
- API endpoint, and the search_hemingway_records() tool wrapper.
- Author: Cornelis Networks Engineering Tools
- import json
- import os
- import sys
- from types import SimpleNamespace
- from typing import Any, Dict, List, Optional

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_shannon_cards_char.py`
- Module: tests/test_hemingway_shannon_cards_char.py
- Description: Characterization tests for the 4 Hemingway card builders in shannon/cards.py.
- Author: Cornelis Networks
- from shannon.cards import (
- build_hemingway_doc_card,
- build_hemingway_impact_card,
- build_hemingway_records_card,
- build_hemingway_publication_card,
- ---------------------------------------------------------------------------
- def _card_schema_ok(card: dict) -> None:

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_tools_char.py`
- import pytest
- from agents.hemingway.tools import (
- HemingwayTools,
- generate_hemingway_documentation,
- get_hemingway_record,
- list_hemingway_records,
- def test_generate_hemingway_documentation_tool_persists_record(
- monkeypatch: pytest.MonkeyPatch,
- tmp_path,
- from agents.hemingway import agent as hemingway_agent_module

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_pr_review_char.py`
- Module: test_hemingway_pr_review_char.py
- Description: Characterization tests for the Hemingway POST /v1/docs/pr-review endpoint.
- Covers input validation, dry-run, doc-relevant filtering, agent run,
- batch commit, and record persistence. Updated for async job pattern.
- Author: Cornelis Networks Engineering Tools
- import sys
- import time
- from types import SimpleNamespace
- from unittest.mock import MagicMock, patch
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_jira_actor_policy_char.py`
- Module: test_jira_actor_policy_char.py
- Description: Characterization tests for Jira actor identity resolution.
- Author: Cornelis Networks — AI Engineering Tools
- import pytest
- from core.jira_actor_policy import load_actor_policy, resolve_jira_actor
- def test_resolve_jira_actor_approved_batch_uses_service_account(monkeypatch: pytest.MonkeyPatch):
- monkeypatch.setenv('JIRA_EMAIL', 'engineer@cornelisnetworks.com')
- monkeypatch.setenv('JIRA_API_TOKEN', 'token-123')
- load_actor_policy(force_reload=True)
- result = resolve_jira_actor(

### Source: `jmac-cornelis/agent-workforce:tests/test_jira_identity_char.py`
- Module: test_jira_identity_char.py
- Description: Characterization tests for Jira credential profile resolution.
- Author: Cornelis Networks — AI Engineering Tools
- import pytest
- from config.jira_identity import get_jira_credential_profile
- def test_jira_identity_uses_legacy_fallback_by_default(
- monkeypatch: pytest.MonkeyPatch,
- monkeypatch.setenv('JIRA_EMAIL', 'legacy@cornelisnetworks.com')
- monkeypatch.setenv('JIRA_API_TOKEN', 'legacy-token')
- monkeypatch.delenv('JIRA_REQUESTER_EMAIL', raising=False)

### Source: `jmac-cornelis/agent-workforce:tests/test_jira_tools_char.py`
- from unittest.mock import MagicMock
- import pytest
- from tools.jira_tools import JiraTools
- def test_get_ticket_tool_returns_comments_and_transitions(
- monkeypatch: pytest.MonkeyPatch,
- fake_issue_resource_factory,
- from tools import jira_tools
- jira = MagicMock()
- issue = fake_issue_resource_factory(
- key='STL-800',

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_confluence_char.py`
- import json
- import pytest
- def _payload(result):
- assert isinstance(result, list)
- assert len(result) == 1
- assert result[0].type == 'text'
- return json.loads(result[0].text)
- @pytest.mark.asyncio
- async def test_search_confluence_pages_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
- monkeypatch.setattr(import_mcp_server.confluence_utils, 'get_connection', lambda: object())

### Source: `jmac-cornelis/agent-workforce:tests/test_jira_utils_char.py`
- import os
- import sys
- from types import SimpleNamespace
- from typing import Any, Optional
- import pytest
- import jira_utils
- class _Response:
- def __init__(
- status_code: int = 200,
- payload: Optional[dict[str, Any]] = None,

### Source: `jmac-cornelis/agent-workforce:tests/test_markdown_to_confluence.py`
- Module: tests/test_markdown_to_confluence.py
- Description: Tests for the enhanced markdown_to_storage() converter, diagram rendering,
- convert_markdown_to_confluence() pipeline, and the agent-callable tool.
- Author: Cornelis Networks
- import html
- import os
- import textwrap
- from pathlib import Path
- from unittest.mock import patch
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_char.py`
- import json
- import sys
- from types import SimpleNamespace
- from typing import Any
- import pytest
- from unittest.mock import MagicMock
- def test_issue_to_dict_shape(import_mcp_server):
- issue = {
- 'key': 'STL-500',
- 'fields': {

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_coverage.py`
- import contextlib
- import json
- from types import SimpleNamespace
- from unittest.mock import MagicMock
- import pytest
- import requests
- class _Response:
- def __init__(self, status_code=200, payload=None, text=''):
- self.status_code = status_code
- self._payload = payload

### Source: `jmac-cornelis/agent-workforce:tests/test_jira_utils_coverage.py`
- import argparse
- import csv
- import json
- import sys
- from pathlib import Path
- from types import SimpleNamespace
- from typing import Any, cast
- from unittest.mock import MagicMock
- import openpyxl
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_drucker_char.py`
- import json
- import pytest
- def _payload(result):
- assert isinstance(result, list)
- assert len(result) == 1
- assert result[0].type == 'text'
- return json.loads(result[0].text)
- @pytest.mark.asyncio
- async def test_create_drucker_hygiene_report_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
- from agents.drucker.models import DruckerHygieneReport

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_gantt_char.py`
- import json
- import pytest
- from agents.gantt.models import (
- BugSummary,
- ReleaseMonitorReport,
- ReleaseSurveyReleaseSummary,
- ReleaseSurveyReport,
- def _payload(result):
- assert isinstance(result, list)
- assert len(result) == 1

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_github_char.py`
- Module: tests/test_mcp_server_github_char.py
- Description: Characterization tests for the 11 GitHub MCP tools in mcp_server.py.
- Validates every GitHub tool function (Tools 26-36) by stubbing
- github_utils via monkeypatch on the import_mcp_server fixture.
- Zero live API calls — all github_utils functions are monkeypatched.
- Author: Cornelis Networks
- import json
- from typing import Any
- import pytest
- ---------------------------------------------------------------------------

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_hemingway_char.py`
- import json
- import pytest
- def _payload(result):
- assert isinstance(result, list)
- assert len(result) == 1
- assert result[0].type == 'text'
- return json.loads(result[0].text)
- @pytest.mark.asyncio
- async def test_generate_hemingway_documentation_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
- from agents.hemingway.models import DocumentationPatch, DocumentationRecord

### Source: `jmac-cornelis/agent-workforce:tests/test_notifications_char.py`
- from types import SimpleNamespace
- def test_jira_comment_notifier_builds_hygiene_comment_with_suggestions():
- from agents.drucker.models import DruckerFinding
- from notifications.jira_comments import JiraCommentNotifier
- comment = JiraCommentNotifier.build_hygiene_comment(
- ticket={'key': 'STL-201', 'summary': 'Missing metadata'},
- findings=[
- DruckerFinding(
- finding_id='F001',
- ticket_key='STL-201',

### Source: `jmac-cornelis/agent-workforce:tests/test_shannon_dry_run_flow_char.py`
- Module: tests/test_shannon_dry_run_flow_char.py
- Description: Characterization tests for the Shannon two-step dry-run flow.
- Author: Cornelis Networks
- from unittest.mock import MagicMock, patch
- from shannon.cards import build_dry_run_preview_card
- from shannon.models import AgentChannelRegistration
- from shannon.service import ShannonService
- def _make_service(mock_poster=None, registry_agents=None):
- from agents.shannon.state_store import ShannonStateStore
- from shannon.registry import ShannonAgentRegistry

### Source: `jmac-cornelis/agent-workforce:tests/test_shannon_pr_cards_char.py`
- Module: tests/test_shannon_pr_cards_char.py
- Description: Characterization tests for the 4 PR card builders in shannon/cards.py.
- Author: Cornelis Networks
- from shannon.cards import (
- build_pr_hygiene_card,
- build_pr_list_card,
- build_pr_reviews_card,
- build_pr_stale_card,
- ---------------------------------------------------------------------------
- def _card_schema_ok(card: dict) -> None:

### Source: `jmac-cornelis/agent-workforce:tests/test_release_tracking.py`
- from datetime import datetime, timedelta, timezone
- from typing import Any, Mapping
- from core.release_tracking import (
- ReleaseSnapshot,
- TrackerConfig,
- assess_readiness,
- build_snapshot,
- compute_cycle_time_stats,
- compute_delta,
- compute_velocity,

### Source: `jmac-cornelis/agent-workforce:tests/test_shannon_service_char.py`
- import base64
- import hashlib
- import hmac
- import json
- from fastapi.testclient import TestClient
- from shannon.app import create_app
- from shannon.outgoing_webhook import extract_hmac_signature
- from shannon.poster import MemoryPoster
- from shannon.registry import ShannonAgentRegistry
- from shannon.service import ShannonService

### Source: `jmac-cornelis/agent-workforce:tests/test_smoke.py`
- import importlib
- def test_import_jira_utils():
- mod = importlib.import_module("jira_utils")
- assert mod is not None
- def test_import_confluence_utils():
- mod = importlib.import_module("confluence_utils")
- def test_import_excel_utils():
- mod = importlib.import_module("excel_utils")
- def test_import_mcp_server(import_mcp_server):
- assert import_mcp_server is not None
- No authoritative source facts were available.

## Publication Targets
- `repo_markdown` -> `docs/tests.md` (create)

## Source References
- `tests/`
- `jmac-cornelis/agent-workforce:tests/test_confluence_utils_char.py`
- `jmac-cornelis/agent-workforce:tests/test_confluence_search_char.py`
- `jmac-cornelis/agent-workforce:tests/conftest.py`
- `jmac-cornelis/agent-workforce:tests/GITHUB_TEST_COVERAGE_ANALYSIS.md`
- `jmac-cornelis/agent-workforce:tests/test_confluence_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_agents_char.py`
- `jmac-cornelis/agent-workforce:tests/test_agent_rename_char.py`
- `jmac-cornelis/agent-workforce:tests/test_core_queries_coverage.py`
- `jmac-cornelis/agent-workforce:tests/test_core_tickets.py`
- `jmac-cornelis/agent-workforce:tests/test_core_reporting.py`
- `jmac-cornelis/agent-workforce:tests/test_core_utils.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_api_github_char.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_agent_char.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_cli_char.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_github_polling_char.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_learning_char.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_excel_utils_char.py`
- `jmac-cornelis/agent-workforce:tests/test_evidence_contracts_char.py`
- `jmac-cornelis/agent-workforce:tests/test_env_loader_char.py`
- `jmac-cornelis/agent-workforce:tests/test_dry_run_mcp_messaging_char.py`
- `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_utils_char.py`
- `jmac-cornelis/agent-workforce:tests/test_excel_utils_coverage.py`
- `jmac-cornelis/agent-workforce:tests/test_feature_planning_orchestrator_char.py`
- `jmac-cornelis/agent-workforce:tests/test_file_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_gantt_cli_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_docs_search_char.py`
- `jmac-cornelis/agent-workforce:tests/test_gantt_agent_char.py`
- `jmac-cornelis/agent-workforce:tests/test_gantt_components_char.py`
- `jmac-cornelis/agent-workforce:tests/test_gantt_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_integration_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_phase5_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_phase5_integration_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_write_ops_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_utils_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_agent_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_api_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_cli_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_confluence_publish_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_search_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_shannon_cards_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_pr_review_char.py`
- `jmac-cornelis/agent-workforce:tests/test_jira_actor_policy_char.py`
- `jmac-cornelis/agent-workforce:tests/test_jira_identity_char.py`
- `jmac-cornelis/agent-workforce:tests/test_jira_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_confluence_char.py`
- `jmac-cornelis/agent-workforce:tests/test_jira_utils_char.py`
- `jmac-cornelis/agent-workforce:tests/test_markdown_to_confluence.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_char.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_coverage.py`
- `jmac-cornelis/agent-workforce:tests/test_jira_utils_coverage.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_drucker_char.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_gantt_char.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_github_char.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_hemingway_char.py`
- `jmac-cornelis/agent-workforce:tests/test_notifications_char.py`
- `jmac-cornelis/agent-workforce:tests/test_shannon_dry_run_flow_char.py`
- `jmac-cornelis/agent-workforce:tests/test_shannon_pr_cards_char.py`
- `jmac-cornelis/agent-workforce:tests/test_release_tracking.py`
- `jmac-cornelis/agent-workforce:tests/test_shannon_service_char.py`
- `jmac-cornelis/agent-workforce:tests/test_smoke.py`
