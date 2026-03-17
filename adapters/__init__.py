"""
adapters — External system integration interfaces.

Each sub-package exposes an ABC interface and a skeleton concrete implementation
for one external system consumed by the AI Agent Workforce.

Sub-packages:
    github      — GitHub REST API (PRs, status checks, inline comments, webhooks)
    teams       — Microsoft Teams / Graph API (messages, adaptive cards, transcripts)
    fuze        — Fuze build/test CLI wrapper (builds, artifacts, test execution)
    environment — Test environment manager (ATF resource files, HIL/mock racks)

NOTE: The Jira adapter already exists in this repository:
    - jira_utils.py  (top-level utility module)
    - core/          (structured Jira client and helpers)
Do NOT recreate it here. Import from those locations directly.
"""
