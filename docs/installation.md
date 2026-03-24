# Installation Guide

Manual installation instructions for the Cornelis Agent Workforce. For a faster setup using OpenCode, see the [Quick Start in the README](../README.md#quick-start).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Clone and Install](#clone-and-install)
- [Configure Environment](#configure-environment)
  - [Required Credentials](#required-credentials)
  - [Optional Credentials](#optional-credentials)
  - [Multiple Environment Files](#multiple-environment-files)
- [Global CLI Install (pipx)](#global-cli-install-pipx)
- [LLM Provider Options](#llm-provider-options)
- [Verify Installation](#verify-installation)
- [Shannon Teams Bot Setup](#shannon-teams-bot-setup)

---

## Prerequisites

- Python 3.9 or higher
- Access to Cornelis Networks Jira instance
- Jira API token ([generate one here](https://id.atlassian.com/manage-profile/security/api-tokens))
- Access to Cornelis internal LLM (or external LLM API key) — *only required for agentic workflows*

---

## Clone and Install

```bash
# 1. Clone the repository
git clone <repository-url>
cd agent-workforce

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
```

---

## Configure Environment

Edit `.env` with your credentials. The file is organized by section — only fill in what you need.

### Required Credentials

These are needed for **all** functionality (utilities, agents, and workflows):

```bash
# Jira API
JIRA_EMAIL=your.email@cornelisnetworks.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_URL=https://cornelisnetworks.atlassian.net
```

### Optional Credentials

Fill in these sections based on what you plan to use:

**For agentic workflows** (`pm_agent --workflow ...`), configure at least one LLM provider:

```bash
# Cornelis internal LLM (preferred)
CORNELIS_LLM_BASE_URL=http://internal-llm.cornelis.com/v1
CORNELIS_LLM_API_KEY=your_internal_key
CORNELIS_LLM_MODEL=cornelis-default

# OR external providers
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

**For Confluence utilities** (`confluence-utils`):

```bash
# Uses the same JIRA_EMAIL and JIRA_API_TOKEN — Confluence Cloud shares Atlassian auth
CONFLUENCE_URL=https://cornelisnetworks.atlassian.net/wiki
```

**For Shannon Teams bot**:

```bash
SHANNON_TEAMS_POST_MODE=workflows
SHANNON_TEAMS_OUTGOING_WEBHOOK_SECRET=your_webhook_secret
SHANNON_TEAMS_WORKFLOWS_WEBHOOK_URL=https://prod-XX.westus.logic.azure.com:443/workflows/...
SHANNON_HOST=0.0.0.0
SHANNON_PORT=8200
```

**For web search tools** (used by some agent workflows):

```bash
BRAVE_SEARCH_API_KEY=your_brave_key
# OR
TAVILY_API_KEY=your_tavily_key
```

### Multiple Environment Files

You can maintain separate configs for production vs. sandbox:

```bash
python3 jira_utils.py --list --env .env_prod
python3 jira_utils.py --list --env .env_sandbox
pm_agent --env .env_sandbox --workflow feature-plan --project STLSB --feature "Redfish RDE"
```

---

## Global CLI Install (pipx)

To make `jira-utils`, `drawio-utils`, `excel-utils`, and `confluence-utils` available as commands in **any** directory (without activating a venv), use [pipx](https://pipx.pypa.io/):

```bash
# Install pipx (macOS)
brew install pipx
pipx ensurepath

# Editable install from the repo
pipx install /path/to/this/repo --editable

# Verify
jira-utils -h
drawio-utils -h
excel-utils -h
confluence-utils -h
```

To include agent pipeline extras:

```bash
pipx install /path/to/this/repo --editable --pip-args='.[agents]'
```

---

## LLM Provider Options

| Provider | Use Case | Configuration |
|----------|----------|---------------|
| `cornelis` | Default, internal LLM | `CORNELIS_LLM_BASE_URL`, `CORNELIS_LLM_API_KEY`, `CORNELIS_LLM_MODEL` |
| `openai` | GPT-4, GPT-4o | `OPENAI_API_KEY` |
| `anthropic` | Claude models | `ANTHROPIC_API_KEY` |

Set `LLM_PROVIDER` in `.env` to choose the default:

```bash
LLM_PROVIDER=cornelis   # or openai, anthropic
```

---

## Verify Installation

```bash
# Check standalone utilities work
jira-utils -h           # or: python3 jira_utils.py -h
excel-utils -h          # or: python3 excel_utils.py -h
confluence-utils -h     # or: python3 confluence_utils.py -h

# Check Jira connection
python3 jira_utils.py --list

# Check agentic workflows (requires LLM config)
python3 pm_agent.py --help
```

---

## Shannon Teams Bot Setup

Shannon requires additional setup for Microsoft Teams integration. See the dedicated guide:

**[docs/shannon-teams-setup.md](shannon-teams-setup.md)**

This covers:
- Teams Outgoing Webhook configuration
- Power Automate Workflows incoming webhook for zero-cost outbound
- ngrok setup for local development
- Agent registry channel routing
- Production deployment options
