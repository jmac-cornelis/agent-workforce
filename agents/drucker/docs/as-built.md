# Drucker — Design Reference

## Purpose
This internal document candidate was generated from authoritative source artifacts for review before publication.

## Metadata
- Documentation class: `as_built`
- Generated: `2026-04-08 14:46 UTC`
- Confidence: `medium`

## Authoritative Inputs
- `jmac-cornelis/agent-workforce:agents/drucker/config/polling.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/cli.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/cards.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/config/monitor.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/config/pr_reminders.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/docs/as-built.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/docs/config.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/docs/state.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/jira_reporting.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/docs/docs.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/pr_reminders.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/state/activity_counter.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/nl_query.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/state/learning_store.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/state/monitor_state.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/state/pr_reminder_state.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/state/report_store.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/tools.py` (source)

## Key Facts

### Source: `jmac-cornelis/agent-workforce:agents/drucker/config/polling.yaml`
- defaults:
- project_key: ''
- limit: 200
- include_done: false
- stale_days: 30
- label_prefix: drucker
- persist: true
- notify_shannon: true
- github_stale_days: 5
- github_repos:

### Source: `jmac-cornelis/agent-workforce:agents/drucker/README.md`
- Drucker Engineering Hygiene Agent
- Overview
- The Drucker Engineering Hygiene Agent is the most feature-rich implemented agent. It automates Jira ticket hygiene and GitHub pull request lifecycle management, ensuring compliance and visibility across engineering workflows.
- Quick Start
- The Drucker Agent monitors Jira and GitHub to ensure tickets and pull requests adhere to engineering standards. It operates in a safe, dry-run mode by default, allowing you to preview changes before execution.
- You can interact with Drucker through Teams chat (via `@Shannon`), REST API endpoints, or CLI commands.
- Dry-Run Safety
- **All mutation operations default to dry-run mode.** This means Drucker will report on findings but will not modify Jira tickets or GitHub PRs unless explicitly instructed.
- To override dry-run mode and execute changes:
- **Shannon:** Append `execute` to the command.

### Source: `jmac-cornelis/agent-workforce:agents/drucker/cli.py`
- Module: agents/drucker/cli.py
- Description: Standalone CLI for Drucker Engineering Hygiene agent.
- Provides direct access to Jira project hygiene scans, single-ticket
- issue checks, intake reports, bug activity summaries, GitHub PR
- hygiene analysis, and scheduled polling.
- Author: Cornelis Networks
- from __future__ import annotations
- import argparse
- import json
- import logging

### Source: `jmac-cornelis/agent-workforce:agents/drucker/cards.py`
- Module: agents/drucker/cards.py
- Description: Adaptive Card builders for Drucker PR reminder DMs. Constructs
- interactive cards for snooze, merge, and confirmation flows
- delivered via Teams direct messages.
- Author: Cornelis Networks
- from __future__ import annotations
- from typing import Any, Dict, List, Optional
- ---------------------------------------------------------------------------
- Schema constant shared by all cards
- _CARD_SCHEMA = 'http://adaptivecards.io/schemas/adaptive-card.json'

### Source: `jmac-cornelis/agent-workforce:agents/drucker/api.py`
- from __future__ import annotations
- import logging
- import os
- import sys
- from datetime import datetime, timezone
- from typing import Any, Dict, List, Optional
- from config.env_loader import load_env
- load_env()
- from fastapi import FastAPI, HTTPException, Query
- from pydantic import BaseModel

### Source: `jmac-cornelis/agent-workforce:agents/drucker/agent.py`
- Module: agents/drucker_agent.py
- Description: Drucker Jira Coordinator agent.
- Produces deterministic Jira hygiene reports, ticket-level
- remediation suggestions, and review-gated Jira write-back plans.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- import time

### Source: `jmac-cornelis/agent-workforce:agents/drucker/config/monitor.yaml`
- project: ''
- poll_interval_minutes: 5
- validation_rules:
- required:
- assignee
- fix_versions
- components
- description
- priority
- learning:

### Source: `jmac-cornelis/agent-workforce:agents/drucker/config/pr_reminders.yaml`
- defaults:
- reminder_days: [5, 8, 10, 15]
- notify: [author, reviewers]
- channels: [teams_dm]
- snooze_options_days: [2, 5, 7]
- merge_methods: [squash, merge, rebase]
- enabled: true
- repo: jmac-cornelis/agent-workforce
- reminder_days: [3, 5, 8, 12]
- repo: cornelisnetworks/ifs-all

### Source: `jmac-cornelis/agent-workforce:agents/drucker/docs/PLAN.md`
- Drucker Engineering Hygiene Agent Plan
- Drucker should be the engineering hygiene agent for both Jira workflow coordination and GitHub PR lifecycle management for the platform. Its v1 Jira job is to keep Jira operationally coherent: triage incoming issues, enforce workflow hygiene, route work to the right owners or queues, and apply evidence-backed status nudges based on build, test, release, and traceability signals. For GitHub, it scans PRs for staleness, missing reviews, and lifecycle issues.
- Drucker should not replace Jira or GitHub as systems of record. It should make both cleaner, more current, and more trustworthy.
- Namesake
- Drucker is named for Peter Drucker, the management thinker who focused on making knowledge work visible, measurable, and effective. We use his name for the engineering hygiene agent because Drucker identifies drift, missing structure, and workflow breakdowns, then helps the organization operate with more clarity and discipline.
- Product definition
- consume Jira issue events and scheduled hygiene checks
- consume GitHub PR state from configured repositories via scheduled polling
- detect missing required metadata, stale workflow state, and routing mistakes
- detect stale PRs, missing review requests, and PR lifecycle anomalies

### Source: `jmac-cornelis/agent-workforce:agents/drucker/docs/as-built.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Drucker Engineering Hygiene Agent"
- date: "2026-04-08"
- status: "draft"
- Drucker Engineering Hygiene Agent — Design Reference
- 1. Module Overview
- The Drucker Engineering Hygiene Agent is a deterministic-first automation system that monitors Jira ticket quality and GitHub pull request lifecycle health across the Cornelis Networks engineering organization. Named after management theorist Peter Drucker, the agent identifies workflow drift, missing metadata, stale work, and routing mistakes in both Jira and GitHub, then produces actionable hygiene reports with review-gated remediation proposals. Drucker operates in dry-run mode by default, ensuring all mutation operations are previewed before execution. It exposes a REST API (port 8201), integrates with the Shannon Teams bot for interactive commands, and runs scheduled polling jobs for continuous hygiene monitoring. The agent is the most feature-rich implemented agent in the workforce, combining Jira ticket validation, GitHub PR staleness detection, PR reminder DMs via Teams, natural language query translation, and a learning subsystem that observes ticket-intake patterns to suggest metadata for new issues.
- 2. What Changed
- Drucker was a Jira-only hygiene agent with three core workflows: full project hygiene scans, single-ticket intake validation, and recent-ticket intake reports.
- GitHub PR hygiene was a planned feature but not implemented.

### Source: `jmac-cornelis/agent-workforce:agents/drucker/docs/config.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Drucker Agent Configuration"
- date: "2026-04-08"
- status: "draft"
- Module Overview
- The Drucker agent configuration module consists of three YAML configuration files that control automated project management hygiene monitoring across Jira and GitHub. The `polling.yaml` file defines scheduled jobs for scanning Jira tickets and GitHub pull requests, `monitor.yaml` specifies validation rules for different Jira issue types, and `pr_reminders.yaml` configures reminder schedules for stale pull requests. Together, these configurations enable the Drucker agent to monitor 23+ Cornelis Networks repositories, validate ticket hygiene, detect stale work, and send automated notifications through Teams channels and direct messages.
- What Changed
- **Before:** The configuration included test repositories (`jmac-cornelis/agent-workforce`, `cornelisnetworks/opa-psm3`) in the default GitHub repository list. The `github-hygiene-scan` and `github-extended-scan` jobs were disabled (`enabled: false`). The `github-pr-reminders` job included the test repository in its monitored repos list.
- **After:** Test repositories have been removed from all repository lists in `polling.yaml`. Both GitHub hygiene scan jobs are now enabled (`enabled: true`), activating stale PR detection, missing review checks, naming convention validation, merge conflict detection, and stale branch monitoring. The `github-pr-reminders` job no longer monitors test repositories.
- **Impact:** The Drucker agent now actively monitors only production repositories for hygiene issues. GitHub hygiene scans will run on schedule, generating notifications for stale PRs (>5 days), missing reviews, and other issues. PR reminder notifications will be sent to authors and reviewers at 3, 7, and 14-day intervals for production repositories only. Teams will receive more focused notifications without test repository noise.

### Source: `jmac-cornelis/agent-workforce:agents/drucker/docs/state.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Drucker State Layer"
- date: "2026-04-03"
- status: "draft"
- Module Overview
- The `agents/drucker/state/` package provides the persistence layer for the Drucker agent — a Jira hygiene and PR review automation system within the Cornelis Networks agent workforce. The package contains five SQLite-backed and filesystem-backed stores, each responsible for a distinct domain of durable state: API request activity counters, ticket-intake learning patterns, intake-monitor checkpoints, PR reminder lifecycle tracking, and hygiene report artifact storage. Every SQLite store follows a consistent architectural pattern — thread-safe access via `threading.RLock`, `sqlite3.Row`-based row factories, `check_same_thread=False` connections, automatic parent-directory creation, and an explicit `close()` lifecycle method. The filesystem store (`DruckerReportStore`) persists JSON and Markdown report artifacts to a configurable directory tree. Together, these stores give Drucker durable, crash-recoverable state without requiring an external database server.
- What Changed
- **Before:** The state layer consisted of three stores: `DruckerLearningStore` (keyword/reporter pattern learning), `DruckerMonitorState` (intake checkpoint tracking), and `DruckerReportStore` (hygiene report persistence).
- **After:** Two new SQLite stores were added: `ActivityCounter` for tracking per-category API request and error counts with timestamps, and `PRReminderState` for managing the full PR reminder lifecycle including scheduling, snoozing, unsnoozing, and action history.
- **Impact:** Drucker now has observability into its own API usage patterns via `ActivityCounter`, and can autonomously track and escalate stale pull requests via `PRReminderState`. Consumers of the Drucker API (e.g., the `pr-reminders` and activity/status endpoints) depend on these new stores. Existing stores (`DruckerLearningStore`, `DruckerMonitorState`, `DruckerReportStore`) are unchanged.

### Source: `jmac-cornelis/agent-workforce:agents/drucker/jira_reporting.py`
- Module: agents/drucker/jira_reporting.py
- Description: Jira query and status reporting utilities for Drucker. Wraps jira_utils
- functions with ticket normalization and breakdown computation.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from collections import Counter
- from datetime import datetime, timezone

### Source: `jmac-cornelis/agent-workforce:agents/drucker/models.py`
- Module: agents/drucker_models.py
- Description: Data models for the Drucker Jira Coordinator agent.
- Defines hygiene findings, proposed Jira actions, and durable
- project hygiene reports.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- import uuid

### Source: `jmac-cornelis/agent-workforce:agents/drucker/docs/docs.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Drucker Engineering Hygiene Agent"
- date: "2026-04-08"
- status: "draft"
- Drucker Engineering Hygiene Agent — Design Reference
- Module Overview
- Drucker is a deterministic-first engineering hygiene agent that monitors Jira ticket quality and GitHub pull request lifecycle health across the Cornelis Networks organization. Named after management theorist Peter Drucker, the agent identifies workflow drift, missing metadata, stale work, and routing mistakes in both Jira and GitHub, then produces actionable hygiene reports with review-gated remediation proposals. Drucker operates in dry-run mode by default, ensuring all mutation operations are previewed before execution. It exposes a REST API (port 8201), integrates with the Shannon Teams bot for interactive commands, and runs scheduled polling jobs for continuous hygiene monitoring. The agent combines Jira ticket validation, GitHub PR staleness detection, PR reminder DMs via Teams, natural language query translation, and a learning subsystem that observes ticket-intake patterns to suggest metadata for new issues.
- What Changed
- Drucker was a Jira-only hygiene agent with three core workflows: full project hygiene scans, single-ticket intake validation, and recent-ticket intake reports.
- GitHub PR hygiene was a planned feature but not implemented.

### Source: `jmac-cornelis/agent-workforce:agents/drucker/pr_reminders.py`
- Module: agents/drucker/pr_reminders.py
- Description: Core PR reminder engine. Orchestrates repo scanning, reminder
- scheduling, Teams user resolution, DM delivery via Graph API,
- and snooze / merge action handling.
- Author: Cornelis Networks
- from __future__ import annotations
- import asyncio
- import logging
- import os
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/drucker/state/activity_counter.py`
- Module: state/activity_counter.py
- Description: SQLite-backed persistent counter for all Drucker API request activity.
- Tracks request counts, error counts, and first/last timestamps by
- endpoint category (hygiene, jira, github, nl, pr-reminders).
- Author: Cornelis Networks
- from __future__ import annotations
- import sqlite3
- import threading
- from datetime import datetime, timezone
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/drucker/nl_query.py`
- Module: agents/drucker/nl_query.py
- Description: Natural language query translation for Drucker. Uses LLM function calling
- to convert plain English questions into structured Jira tool calls, execute
- them, and summarize results.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/drucker/prompts/system.md`
- Drucker Engineering Hygiene Agent
- You are Drucker, an engineering hygiene agent specialized in project hygiene across Jira and GitHub, operational coherence, and review-gated write-back.
- Your Role
- You examine engineering project state across Jira and GitHub and produce:
- 1. Project-level hygiene summaries (Jira tickets and GitHub PRs)
- 2. Ticket-level and PR-level findings with evidence
- 3. Suggested remediation actions
- 4. Safe, reviewable Jira write-back plans
- 5. GitHub PR lifecycle notifications (stale PRs, missing reviews)
- Operating Principles

### Source: `jmac-cornelis/agent-workforce:agents/drucker/state/learning_store.py`
- Module: state/drucker_learning_store.py
- Description: Drucker-owned learning store for ticket-intake suggestions.
- Tracks keyword/component patterns, reporter field habits, and
- basic observation history for review-gated metadata suggestions.
- Author: Cornelis Networks
- from __future__ import annotations
- import hashlib
- import json
- import logging
- import os

### Source: `jmac-cornelis/agent-workforce:agents/drucker/state/monitor_state.py`
- Module: state/drucker_monitor_state.py
- Description: Checkpoint and processed-ticket persistence for Drucker intake
- monitoring. Tracks recent polling cursors and validation history
- without performing any Jira writes.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import sqlite3
- import threading
- from datetime import datetime, timezone

### Source: `jmac-cornelis/agent-workforce:agents/drucker/state/pr_reminder_state.py`
- Module: state/pr_reminder_state.py
- Description: SQLite state store for PR reminder tracking. Manages reminder
- scheduling, snooze state, and action history for pull requests
- that need reviewer attention.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import sqlite3
- import threading
- from datetime import datetime, timezone

### Source: `jmac-cornelis/agent-workforce:agents/drucker/state/report_store.py`
- Module: state/drucker_report_store.py
- Description: Persistence helpers for Drucker hygiene reports.
- Stores durable JSON + Markdown artifacts for Jira hygiene analysis.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import sys
- from datetime import datetime

### Source: `jmac-cornelis/agent-workforce:agents/drucker/tools.py`
- Module: tools/drucker_tools.py
- Description: Drucker hygiene tools for agent use.
- Wraps the Drucker hygiene workflow as agent-callable tools.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from typing import Optional
- from tools.base import BaseTool, ToolResult, tool
- Logging config - follows jira_utils.py pattern
- No authoritative source facts were available.

## Existing Target Context
- Existing repo doc: `agents/drucker/docs/as-built.md`
  - <!-- Generated by Documentation Agent — do not edit between markers -->
  - title: "As-Built: Drucker Engineering Hygiene Agent"
  - date: "2026-04-06"
  - status: "draft"
  - Drucker Engineering Hygiene Agent — Design Reference
  - 1. Module Overview
  - The Drucker Engineering Hygiene Agent is a deterministic-first automation system that monitors Jira ticket quality and GitHub pull request lifecycle health across the Cornelis Networks engineering organization. Named after management theorist Peter Drucker, the agent identifies workflow drift, missing metadata, stale work, and routing mistakes in both Jira and GitHub, then produces actionable hygiene reports with review-gated remediation proposals. Drucker operates in dry-run mode by default, ensuring all mutation operations are previewed before execution. It exposes a REST API (port 8201), integrates with the Shannon Teams bot for interactive commands, and runs scheduled polling jobs for continuous hygiene monitoring. The agent is the most feature-rich implemented agent in the workforce, combining Jira ticket validation, GitHub PR staleness detection, PR reminder DMs via Teams, natural language query translation, and a learning subsystem that observes ticket-intake patterns to suggest metadata for new issues.
  - 2. What Changed
  - Drucker was a Jira-only hygiene agent with three core workflows: full project hygiene scans, single-ticket intake validation, and recent-ticket intake reports.
  - GitHub PR hygiene was a planned feature but not implemented.

## Publication Targets
- `repo_markdown` -> `agents/drucker/docs/as-built.md` (update)

## Source References
- `agents/drucker/`
- `jmac-cornelis/agent-workforce:agents/drucker/config/polling.yaml`
- `jmac-cornelis/agent-workforce:agents/drucker/README.md`
- `jmac-cornelis/agent-workforce:agents/drucker/cli.py`
- `jmac-cornelis/agent-workforce:agents/drucker/cards.py`
- `jmac-cornelis/agent-workforce:agents/drucker/api.py`
- `jmac-cornelis/agent-workforce:agents/drucker/agent.py`
- `jmac-cornelis/agent-workforce:agents/drucker/config/monitor.yaml`
- `jmac-cornelis/agent-workforce:agents/drucker/config/pr_reminders.yaml`
- `jmac-cornelis/agent-workforce:agents/drucker/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/drucker/docs/as-built.md`
- `jmac-cornelis/agent-workforce:agents/drucker/docs/config.md`
- `jmac-cornelis/agent-workforce:agents/drucker/docs/state.md`
- `jmac-cornelis/agent-workforce:agents/drucker/jira_reporting.py`
- `jmac-cornelis/agent-workforce:agents/drucker/models.py`
- `jmac-cornelis/agent-workforce:agents/drucker/docs/docs.md`
- `jmac-cornelis/agent-workforce:agents/drucker/pr_reminders.py`
- `jmac-cornelis/agent-workforce:agents/drucker/state/activity_counter.py`
- `jmac-cornelis/agent-workforce:agents/drucker/nl_query.py`
- `jmac-cornelis/agent-workforce:agents/drucker/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/drucker/state/learning_store.py`
- `jmac-cornelis/agent-workforce:agents/drucker/state/monitor_state.py`
- `jmac-cornelis/agent-workforce:agents/drucker/state/pr_reminder_state.py`
- `jmac-cornelis/agent-workforce:agents/drucker/state/report_store.py`
- `jmac-cornelis/agent-workforce:agents/drucker/tools.py`
