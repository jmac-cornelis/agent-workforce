# Teams Bot Framework Specification

[Back to AI Agent Workforce](README.md)

> **This is the technical specification for [Shannon](../../agents/SHANNON_COMMUNICATIONS_AGENT_PLAN.md), the communications service agent.** Shannon is the single Teams bot that serves as the unified human interface for all 16 AI agents in the Cornelis Networks Agent Workforce. Named after Claude Shannon, father of information theory.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Agent Registry](#3-agent-registry)
4. [Message Types](#4-message-types)
5. [Standard Commands](#5-standard-commands)
6. [Adaptive Card Templates](#6-adaptive-card-templates)
7. [Command Routing](#7-command-routing)
8. [Approval Workflow](#8-approval-workflow)
9. [Thread Management](#9-thread-management)
10. [Teams App Manifest](#10-teams-app-manifest)
11. [API Contract](#11-api-contract)
12. [Security](#12-security)
13. [Deployment](#13-deployment)
14. [Implementation Phases](#14-implementation-phases)
15. [Diagrams](#15-diagrams)

---

## 1. Overview

### What This Is

The Teams Bot Framework is a single, generic bot service that provides the human interface for all 15 AI agents in the Cornelis Networks Agent Workforce. Each agent has a dedicated Teams channel (`#agent-{name}`) within the "Agent Workforce" team. The bot receives messages from all 15 channels, routes them to the correct agent API, and posts responses back.

### One Bot, One Deployment, 15 Channels

There is exactly one bot service deployed. It is not 15 separate bots. The bot determines which agent to interact with based on the channel where the message was posted. Channel-to-agent mapping is maintained in the Agent Registry.

| Channel | Agent | Zone |
|---------|-------|------|
| `#agent-josephine` | Josephine -- Build and Package | Execution Spine |
| `#agent-ada` | Ada -- Test Planner | Execution Spine |
| `#agent-curie` | Curie -- Test Generator | Execution Spine |
| `#agent-faraday` | Faraday -- Test Executor | Execution Spine |
| `#agent-tesla` | Tesla -- Environment Manager | Execution Spine |
| `#agent-hedy` | Hedy -- Release Manager | Execution Spine |
| `#agent-linus` | Linus -- Code Review | Execution Spine |
| `#agent-babbage` | Babbage -- Version Manager | Intelligence and Knowledge |
| `#agent-linnaeus` | Linnaeus -- Traceability | Intelligence and Knowledge |
| `#agent-herodotus` | Herodotus -- Knowledge Capture | Intelligence and Knowledge |
| `#agent-hemingway` | Hemingway -- Documentation | Intelligence and Knowledge |
| `#agent-nightingale` | Nightingale -- Bug Investigation | Intelligence and Knowledge |
| `#agent-drucker` | Drucker -- Jira Coordinator | Intelligence and Knowledge |
| `#agent-gantt` | Gantt -- Project Planner | Planning and Delivery |
| `#agent-brooks` | Brooks -- Delivery Manager | Planning and Delivery |

### Design Principles

- **Generic framework** -- The bot code is agent-agnostic. All agent-specific behavior comes from configuration in the Agent Registry, not from code branches.
- **Configuration over code** -- Adding a new agent means adding a registry entry, not modifying bot source code.
- **Adaptive Cards for structure** -- All bot output uses Microsoft Adaptive Cards for consistent, interactive formatting.
- **Stateless routing, stateful conversations** -- The bot itself is stateless for routing decisions. Conversation state (threads, pending approvals) is persisted in PostgreSQL.
- **Agents push, humans pull** -- Agents proactively push notifications to their channels. Humans pull status on demand via commands.

---

## 2. Architecture

### Message Flow

The following sequence diagram shows the end-to-end flow when a user posts a command in an agent channel:

```mermaid
sequenceDiagram
    participant U as User
    participant T as Microsoft Teams
    participant W as Bot Webhook Receiver
    participant R as Command Router
    participant AR as Agent Registry
    participant A as Agent API (e.g. Josephine)
    participant CR as Card Renderer
    participant DB as PostgreSQL
    participant RD as Redis

    U->>T: Posts "/stats" in #agent-josephine
    T->>W: HTTP POST webhook (activity payload)
    W->>RD: Check rate limit (channel_id)
    RD-->>W: Allowed
    W->>R: Parse message, extract command
    R->>AR: Lookup agent by channel_id
    AR-->>R: agent_id=josephine, api_base_url=http://cn-ai-01:8101
    R->>A: GET http://cn-ai-01:8101/v1/status/stats
    A-->>R: JSON response (stats payload)
    R->>CR: Render stats Adaptive Card
    CR-->>R: Adaptive Card JSON
    R->>T: POST reply to channel (Adaptive Card)
    T-->>U: Bot posts formatted stats card
    R->>DB: INSERT audit_log (user_id, agent_id, command, timestamp)
```

### Component Diagram

```mermaid
graph TB
    subgraph teams["Microsoft Teams"]
        CH1["#agent-josephine"]
        CH2["#agent-ada"]
        CH3["#agent-curie"]
        CHN["... 12 more channels"]
    end

    subgraph bot["Teams Bot Service"]
        WH[Webhook Receiver]
        MP[Message Poster]
        CR[Command Router]
        CARD[Card Renderer]
        TM[Thread Manager]
        AW[Approval Workflow Engine]
    end

    subgraph registry["Agent Registry"]
        CFG[Agent Configs<br/>15 entries]
    end

    subgraph agents["Agent APIs"]
        J_API["Josephine API<br/>cn-ai-01:8101"]
        A_API["Ada API<br/>cn-ai-01:8102"]
        C_API["Curie API<br/>cn-ai-02:8103"]
        MORE["... 12 more agents"]
    end

    subgraph data["Data Stores"]
        PG[(PostgreSQL<br/>conversation state<br/>audit log<br/>approval records)]
        RD[(Redis<br/>rate limiting<br/>session cache)]
    end

    CH1 & CH2 & CH3 & CHN -->|webhook| WH
    WH --> CR
    CR --> CFG
    CR --> J_API & A_API & C_API & MORE
    J_API & A_API & C_API & MORE -->|notify/approve| WH
    CR --> CARD
    CARD --> MP
    MP --> CH1 & CH2 & CH3 & CHN
    CR --> TM
    TM --> PG
    AW --> PG
    WH --> RD
```

---

## 3. Agent Registry

### Registration Model

Agents are registered via a YAML configuration file loaded at bot startup. The bot watches the file for changes and hot-reloads without restart. An optional REST endpoint allows runtime registration for development and testing.

Configuration file path: `/etc/teams-bot/agent-registry.yaml`

### Registry Schema

Each agent entry contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_id` | string | Yes | Unique identifier. Lowercase, no spaces. Example: `josephine` |
| `display_name` | string | Yes | Human-readable name shown in cards. Example: `Josephine` |
| `role` | string | Yes | Short role description. Example: `Build and Package` |
| `channel_id` | string | Yes | Teams channel ID (from Teams admin). Maps inbound messages to this agent. |
| `api_base_url` | string | Yes | Base URL for the agent's REST API. Example: `http://cn-ai-01:8101` |
| `icon_url` | string | No | URL to agent avatar image for card headers. |
| `description` | string | Yes | One-line description of what the agent does. |
| `zone` | string | Yes | Operational zone: `execution_spine`, `intelligence_knowledge`, or `planning_delivery` |
| `approval_types` | list[string] | No | Types of approvals this agent can request. Empty list if none. |
| `custom_commands` | list[object] | No | Agent-specific commands beyond the 6 standard commands. |
| `health_endpoint` | string | No | Override health check path. Default: `/v1/health` |
| `timeout_seconds` | integer | No | API call timeout. Default: `30` |

### Custom Command Schema

Each entry in `custom_commands`:

| Field | Type | Description |
|-------|------|-------------|
| `command` | string | Command string including leading slash. Example: `/build` |
| `description` | string | Help text shown in `/help` output. |
| `api_method` | string | HTTP method: `GET` or `POST` |
| `api_path` | string | Agent API path to call. Example: `/v1/build-jobs` |
| `parameters` | list[object] | Expected parameters with name, type, required flag. |

### Example Registry Entry

```yaml
agents:
  - agent_id: josephine
    display_name: Josephine
    role: Build and Package
    channel_id: "19:abc123def456@thread.tacv2"
    api_base_url: http://cn-ai-01:8101
    icon_url: https://internal.cornelisnetworks.com/icons/josephine.png
    description: >
      Build orchestration, compilation management, and artifact production
      across all Cornelis repositories.
    zone: execution_spine
    approval_types: []
    custom_commands:
      - command: /build
        description: Submit a new build job
        api_method: POST
        api_path: /v1/build-jobs
        parameters:
          - name: repo
            type: string
            required: true
          - name: ref
            type: string
            required: true
          - name: targets
            type: string
            required: false
      - command: /build-status
        description: Check status of a build job
        api_method: GET
        api_path: /v1/build-jobs/{id}
        parameters:
          - name: id
            type: string
            required: true
    health_endpoint: /v1/health
    timeout_seconds: 30

  - agent_id: hedy
    display_name: Hedy
    role: Release Manager
    channel_id: "19:xyz789ghi012@thread.tacv2"
    api_base_url: http://cn-ai-02:8106
    icon_url: https://internal.cornelisnetworks.com/icons/hedy.png
    description: >
      Orchestrates release decisions using the Fuze release model with
      stage promotion and human approval gates.
    zone: execution_spine
    approval_types:
      - release_promotion
    custom_commands:
      - command: /release-status
        description: Check release readiness for a build
        api_method: GET
        api_path: /v1/releases/{build_id}/status
        parameters:
          - name: build_id
            type: string
            required: true
    timeout_seconds: 60
```

---

## 4. Message Types

### Outbound Messages (Bot to Channel)

#### 4.1 Activity Notification

Posted when an agent completes a significant action. Top-level message in the channel.

```json
{
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "ColumnSet",
      "columns": [
        {
          "type": "Column",
          "width": "auto",
          "items": [
            {
              "type": "Image",
              "url": "${agent_icon_url}",
              "size": "Small",
              "style": "Person"
            }
          ]
        },
        {
          "type": "Column",
          "width": "stretch",
          "items": [
            {
              "type": "TextBlock",
              "text": "${agent_display_name}",
              "weight": "Bolder",
              "size": "Medium"
            },
            {
              "type": "TextBlock",
              "text": "${timestamp}",
              "isSubtle": true,
              "spacing": "None",
              "size": "Small"
            }
          ]
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "${activity_summary}",
      "wrap": true
    },
    {
      "type": "FactSet",
      "facts": [
        { "title": "Action", "value": "${action_type}" },
        { "title": "Subject", "value": "${subject_id}" },
        { "title": "Result", "value": "${result_status}" },
        { "title": "Duration", "value": "${duration}" }
      ]
    }
  ]
}
```

#### 4.2 Decision Notification

Posted when an agent makes a non-trivial decision. Includes rationale for transparency.

```json
{
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "ColumnSet",
      "columns": [
        {
          "type": "Column",
          "width": "auto",
          "items": [
            {
              "type": "Image",
              "url": "${agent_icon_url}",
              "size": "Small",
              "style": "Person"
            }
          ]
        },
        {
          "type": "Column",
          "width": "stretch",
          "items": [
            {
              "type": "TextBlock",
              "text": "Decision: ${decision_title}",
              "weight": "Bolder",
              "size": "Medium",
              "color": "Accent"
            },
            {
              "type": "TextBlock",
              "text": "${agent_display_name} | ${timestamp}",
              "isSubtle": true,
              "spacing": "None",
              "size": "Small"
            }
          ]
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "**Outcome:** ${chosen_action}",
      "wrap": true
    },
    {
      "type": "TextBlock",
      "text": "**Rationale:** ${rationale}",
      "wrap": true
    },
    {
      "type": "FactSet",
      "facts": [
        { "title": "Decision ID", "value": "${decision_id}" },
        { "title": "Inputs Evaluated", "value": "${input_count}" },
        { "title": "Alternatives Considered", "value": "${alternative_count}" },
        { "title": "Confidence", "value": "${confidence_level}" }
      ]
    },
    {
      "type": "ActionSet",
      "actions": [
        {
          "type": "Action.Submit",
          "title": "View Full Decision Tree",
          "data": {
            "action": "view_decision",
            "decision_id": "${decision_id}",
            "agent_id": "${agent_id}"
          }
        }
      ]
    }
  ]
}
```

#### 4.3 Approval Request

Posted when an agent needs human authorization for an irreversible action. Includes context and approve/reject buttons.

```json
{
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "Container",
      "style": "warning",
      "items": [
        {
          "type": "TextBlock",
          "text": "APPROVAL REQUIRED",
          "weight": "Bolder",
          "size": "Medium",
          "color": "Warning"
        }
      ]
    },
    {
      "type": "ColumnSet",
      "columns": [
        {
          "type": "Column",
          "width": "auto",
          "items": [
            {
              "type": "Image",
              "url": "${agent_icon_url}",
              "size": "Small",
              "style": "Person"
            }
          ]
        },
        {
          "type": "Column",
          "width": "stretch",
          "items": [
            {
              "type": "TextBlock",
              "text": "${agent_display_name} requests approval",
              "weight": "Bolder"
            },
            {
              "type": "TextBlock",
              "text": "${timestamp} | Expires: ${expiry_time}",
              "isSubtle": true,
              "spacing": "None",
              "size": "Small"
            }
          ]
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "**${approval_title}**",
      "wrap": true,
      "size": "Medium"
    },
    {
      "type": "TextBlock",
      "text": "${approval_description}",
      "wrap": true
    },
    {
      "type": "FactSet",
      "facts": [
        { "title": "Approval ID", "value": "${approval_id}" },
        { "title": "Type", "value": "${approval_type}" },
        { "title": "Subject", "value": "${subject_id}" },
        { "title": "Risk Level", "value": "${risk_level}" }
      ]
    },
    {
      "type": "Container",
      "style": "emphasis",
      "items": [
        {
          "type": "TextBlock",
          "text": "**Evidence Summary**",
          "weight": "Bolder"
        },
        {
          "type": "TextBlock",
          "text": "${evidence_summary}",
          "wrap": true
        }
      ]
    },
    {
      "type": "Input.Text",
      "id": "approval_comment",
      "placeholder": "Optional comment (required if rejecting)",
      "isMultiline": true
    },
    {
      "type": "ActionSet",
      "actions": [
        {
          "type": "Action.Submit",
          "title": "Approve",
          "style": "positive",
          "data": {
            "action": "approval_response",
            "approval_id": "${approval_id}",
            "decision": "approved",
            "agent_id": "${agent_id}"
          }
        },
        {
          "type": "Action.Submit",
          "title": "Reject",
          "style": "destructive",
          "data": {
            "action": "approval_response",
            "approval_id": "${approval_id}",
            "decision": "rejected",
            "agent_id": "${agent_id}"
          }
        }
      ]
    }
  ]
}
```

#### 4.4 Input Request

Posted when an agent needs structured information from a human to proceed.

```json
{
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "ColumnSet",
      "columns": [
        {
          "type": "Column",
          "width": "auto",
          "items": [
            {
              "type": "Image",
              "url": "${agent_icon_url}",
              "size": "Small",
              "style": "Person"
            }
          ]
        },
        {
          "type": "Column",
          "width": "stretch",
          "items": [
            {
              "type": "TextBlock",
              "text": "${agent_display_name} needs your input",
              "weight": "Bolder",
              "size": "Medium"
            }
          ]
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "${input_request_description}",
      "wrap": true
    },
    {
      "type": "FactSet",
      "facts": [
        { "title": "Request ID", "value": "${request_id}" },
        { "title": "Context", "value": "${context_summary}" },
        { "title": "Deadline", "value": "${deadline}" }
      ]
    },
    {
      "type": "Input.Text",
      "id": "field_1",
      "label": "${field_1_label}",
      "placeholder": "${field_1_placeholder}",
      "isRequired": true
    },
    {
      "type": "Input.ChoiceSet",
      "id": "field_2",
      "label": "${field_2_label}",
      "choices": [
        { "title": "${choice_1}", "value": "${choice_1_value}" },
        { "title": "${choice_2}", "value": "${choice_2_value}" }
      ]
    },
    {
      "type": "ActionSet",
      "actions": [
        {
          "type": "Action.Submit",
          "title": "Submit",
          "style": "positive",
          "data": {
            "action": "input_response",
            "request_id": "${request_id}",
            "agent_id": "${agent_id}"
          }
        },
        {
          "type": "Action.Submit",
          "title": "Skip / Cannot Provide",
          "data": {
            "action": "input_response",
            "request_id": "${request_id}",
            "agent_id": "${agent_id}",
            "skipped": true
          }
        }
      ]
    }
  ]
}
```

#### 4.5 Error Alert

Posted when an agent encounters a failure or anomaly that requires human attention.

```json
{
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "Container",
      "style": "${severity_style}",
      "items": [
        {
          "type": "ColumnSet",
          "columns": [
            {
              "type": "Column",
              "width": "auto",
              "items": [
                {
                  "type": "TextBlock",
                  "text": "${severity_badge}",
                  "weight": "Bolder",
                  "color": "${severity_color}",
                  "size": "Large"
                }
              ]
            },
            {
              "type": "Column",
              "width": "stretch",
              "items": [
                {
                  "type": "TextBlock",
                  "text": "${error_title}",
                  "weight": "Bolder",
                  "size": "Medium"
                },
                {
                  "type": "TextBlock",
                  "text": "${agent_display_name} | ${timestamp}",
                  "isSubtle": true,
                  "spacing": "None",
                  "size": "Small"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "${error_description}",
      "wrap": true
    },
    {
      "type": "FactSet",
      "facts": [
        { "title": "Error Code", "value": "${error_code}" },
        { "title": "Component", "value": "${component}" },
        { "title": "Correlation ID", "value": "${correlation_id}" },
        { "title": "Severity", "value": "${severity}" }
      ]
    },
    {
      "type": "Container",
      "style": "emphasis",
      "items": [
        {
          "type": "TextBlock",
          "text": "**Suggested Actions**",
          "weight": "Bolder"
        },
        {
          "type": "TextBlock",
          "text": "${suggested_actions}",
          "wrap": true
        }
      ]
    }
  ]
}
```

Severity mapping:

| Severity | Badge Text | Color | Style |
|----------|-----------|-------|-------|
| `critical` | `CRITICAL` | Attention (red) | `attention` |
| `error` | `ERROR` | Warning (yellow) | `warning` |
| `warning` | `WARNING` | Accent (blue) | `accent` |
| `info` | `INFO` | Default | `default` |

#### 4.6 Command Response

Generic formatted response to any standard command. Structure varies by command; see Section 5 for per-command layouts.

### Inbound Messages (User to Bot)

#### Standard Commands

Messages beginning with `/` are parsed as commands. The bot recognizes the 6 standard commands (available in every channel) plus any `custom_commands` defined in the agent's registry entry.

| Command | Pattern | Description |
|---------|---------|-------------|
| `/token-status` | Exact match | Token usage summary |
| `/decision-tree` | Exact match | Recent decisions with rationale |
| `/why {decision-id}` | `/why` + space + ID | Deep dive into specific decision |
| `/stats` | Exact match | Operational statistics |
| `/work-today` | Exact match | Today's work summary |
| `/busy` | Exact match | Current load status |
| `/help` | Exact match | List available commands for this agent |

#### Approval Responses

`Action.Submit` payloads from Adaptive Card button clicks. The bot identifies these by the `action` field in the submitted data:

```json
{
  "action": "approval_response",
  "approval_id": "APR-2024-001",
  "decision": "approved",
  "agent_id": "hedy",
  "approval_comment": "Looks good. Test coverage is sufficient."
}
```

#### Input Responses

`Action.Submit` payloads from input request form submissions:

```json
{
  "action": "input_response",
  "request_id": "INP-2024-042",
  "agent_id": "nightingale",
  "field_1": "The crash occurs only on dual-rail configurations",
  "field_2": "hardware_specific"
}
```

#### Free-Text Queries

Any message that does not start with `/` and is not a card submission is treated as a free-text query. The bot forwards it to the agent's `/v1/query` endpoint.

Example: A user posts `status of build BLD-1234` in `#agent-josephine`. The bot sends:

```http
POST http://cn-ai-01:8101/v1/query
Content-Type: application/json

{
  "query": "status of build BLD-1234",
  "user_id": "john.macdonald@cornelisnetworks.com",
  "channel_id": "19:abc123def456@thread.tacv2",
  "thread_id": null
}
```

---

## 5. Standard Commands

All 15 agents expose the same 6 standard commands via their REST APIs. The bot routes each command to the corresponding agent endpoint and renders the response as an Adaptive Card.

### 5.1 `/token-status`

**Purpose:** Show token usage -- today, cumulative, cost, and efficiency ratio.

**Routing:**

```
GET {api_base_url}/v1/status/tokens
```

**Example Request:**

User posts `/token-status` in `#agent-josephine`.

```http
GET http://cn-ai-01:8101/v1/status/tokens
```

**Example Response (from agent API):**

```json
{
  "agent_id": "josephine",
  "period": "2025-03-15",
  "tokens_today": {
    "input": 12450,
    "output": 3200,
    "total": 15650
  },
  "tokens_cumulative": {
    "input": 1245000,
    "output": 320000,
    "total": 1565000
  },
  "cost_today_usd": 0.47,
  "cost_cumulative_usd": 46.95,
  "efficiency_ratio": 0.87,
  "deterministic_action_pct": 83.2,
  "model": "gpt-4o"
}
```

**Adaptive Card Layout:** Rendered using the Token Status Card template (Section 6.7). Shows usage bars for today and cumulative, cost figures, and efficiency ratio.

### 5.2 `/decision-tree`

**Purpose:** Show recent decisions with inputs, candidates, outcomes, and rationale.

**Routing:**

```
GET {api_base_url}/v1/status/decisions
```

**Example Request:**

User posts `/decision-tree` in `#agent-hedy`.

```http
GET http://cn-ai-02:8106/v1/status/decisions
```

**Example Response:**

```json
{
  "agent_id": "hedy",
  "decisions": [
    {
      "decision_id": "DEC-hedy-20250315-001",
      "timestamp": "2025-03-15T10:23:00Z",
      "title": "Release readiness evaluation for BLD-4521",
      "outcome": "blocked",
      "rationale": "HIL test coverage below 80% threshold for release stage",
      "inputs_evaluated": 5,
      "alternatives_considered": 2,
      "confidence": "high"
    },
    {
      "decision_id": "DEC-hedy-20250315-002",
      "timestamp": "2025-03-15T11:45:00Z",
      "title": "Promote BLD-4519 from sit to qa",
      "outcome": "promoted",
      "rationale": "All sit-stage gates passed. Test coverage 94%. No blocking issues.",
      "inputs_evaluated": 7,
      "alternatives_considered": 1,
      "confidence": "high"
    }
  ],
  "total_decisions_today": 2,
  "total_decisions_cumulative": 347
}
```

**Adaptive Card Layout:** Rendered using the Decision Card template (Section 6.2). Each decision is a collapsible section showing title, outcome, and rationale.

### 5.3 `/why {decision-id}`

**Purpose:** Deep dive into a specific decision's full reasoning chain.

**Routing:**

```
GET {api_base_url}/v1/status/decisions/{decision_id}
```

**Example Request:**

User posts `/why DEC-hedy-20250315-001` in `#agent-hedy`.

```http
GET http://cn-ai-02:8106/v1/status/decisions/DEC-hedy-20250315-001
```

**Example Response:**

```json
{
  "decision_id": "DEC-hedy-20250315-001",
  "agent_id": "hedy",
  "timestamp": "2025-03-15T10:23:00Z",
  "title": "Release readiness evaluation for BLD-4521",
  "outcome": "blocked",
  "confidence": "high",
  "inputs": [
    {
      "source": "josephine",
      "type": "build_record",
      "subject_id": "BLD-4521",
      "summary": "Build succeeded. 14 packages produced."
    },
    {
      "source": "babbage",
      "type": "version_mapping",
      "subject_id": "BLD-4521",
      "summary": "Mapped to external version 12.0.3.1"
    },
    {
      "source": "faraday",
      "type": "test_execution_summary",
      "subject_id": "BLD-4521",
      "summary": "HIL coverage: 72%. Unit coverage: 98%. 3 test failures."
    },
    {
      "source": "linnaeus",
      "type": "traceability_summary",
      "subject_id": "BLD-4521",
      "summary": "2 Jira issues linked. 1 requirement gap detected."
    },
    {
      "source": "policy",
      "type": "release_policy",
      "subject_id": "release_stage_qa",
      "summary": "Requires HIL coverage >= 80%, zero P1 test failures."
    }
  ],
  "alternatives": [
    {
      "option": "Promote to qa with waiver",
      "rejected_reason": "HIL coverage gap is 8 points below threshold. Policy does not allow waiver for gaps > 5 points."
    },
    {
      "option": "Block and request additional HIL testing",
      "selected": true,
      "reason": "Standard policy response. Faraday can schedule targeted HIL runs for the 3 failing test areas."
    }
  ],
  "rationale": "HIL test coverage for BLD-4521 is 72%, which is 8 points below the 80% threshold required for qa stage promotion. The 3 test failures are in fabric initialization paths that are HIL-only. Policy does not permit waiver for coverage gaps exceeding 5 points. Blocking and requesting targeted HIL testing is the correct action.",
  "follow_up_actions": [
    "Requested Faraday to schedule targeted HIL test run for fabric initialization paths",
    "Notified Ada to update test plan for BLD-4521 with expanded HIL scope"
  ]
}
```

**Adaptive Card Layout:** Full decision detail card with expandable sections for inputs, alternatives, rationale, and follow-up actions.

### 5.4 `/stats`

**Purpose:** Operational statistics -- uptime, success/failure rates, latency, queue depth, error trends.

**Routing:**

```
GET {api_base_url}/v1/status/stats
```

**Example Request:**

User posts `/stats` in `#agent-josephine`.

```http
GET http://cn-ai-01:8101/v1/status/stats
```

**Example Response:**

```json
{
  "agent_id": "josephine",
  "uptime_hours": 720.5,
  "uptime_pct": 99.93,
  "period": "last_24h",
  "jobs_processed": 47,
  "jobs_succeeded": 44,
  "jobs_failed": 2,
  "jobs_cancelled": 1,
  "success_rate_pct": 93.6,
  "avg_latency_seconds": 342,
  "p95_latency_seconds": 890,
  "queue_depth": 3,
  "active_jobs": 1,
  "error_trend": "stable",
  "top_errors": [
    {
      "code": "BUILD_DEPENDENCY_MISSING",
      "count": 2,
      "last_seen": "2025-03-15T09:12:00Z"
    }
  ]
}
```

**Adaptive Card Layout:** Rendered using the Stats Card template (Section 6.6). Metrics table with color-coded success rate and trend indicators.

### 5.5 `/work-today`

**Purpose:** Summary of today's work -- jobs processed, outcomes, notable events.

**Routing:**

```
GET {api_base_url}/v1/status/work-summary
```

**Example Request:**

User posts `/work-today` in `#agent-faraday`.

```http
GET http://cn-ai-02:8104/v1/status/work-summary
```

**Example Response:**

```json
{
  "agent_id": "faraday",
  "date": "2025-03-15",
  "summary": "Executed 12 test cycles across 3 environments. 11 passed, 1 failed with 3 test case failures in fabric init.",
  "items": [
    {
      "type": "test_execution",
      "subject_id": "TEX-20250315-001",
      "description": "PR validation for PR-892: 45 tests, all passed",
      "status": "passed",
      "timestamp": "2025-03-15T08:15:00Z"
    },
    {
      "type": "test_execution",
      "subject_id": "TEX-20250315-012",
      "description": "HIL regression for BLD-4521: 120 tests, 3 failures",
      "status": "failed",
      "timestamp": "2025-03-15T14:30:00Z"
    }
  ],
  "totals": {
    "processed": 12,
    "passed": 11,
    "failed": 1,
    "environments_used": 3
  }
}
```

**Adaptive Card Layout:** Rendered using the Work Summary Card template (Section 6.8). Chronological list of work items with status badges.

### 5.6 `/busy`

**Purpose:** Current load status -- is the agent idle, working, busy, or overloaded?

**Routing:**

```
GET {api_base_url}/v1/status/load
```

**Example Request:**

User posts `/busy` in `#agent-tesla`.

```http
GET http://cn-ai-02:8105/v1/status/load
```

**Example Response:**

```json
{
  "agent_id": "tesla",
  "status": "busy",
  "active_tasks": 4,
  "queue_depth": 2,
  "capacity": 6,
  "utilization_pct": 66.7,
  "current_work": [
    {
      "task_id": "ENV-20250315-003",
      "description": "Provisioning HIL environment for BLD-4521 regression",
      "started_at": "2025-03-15T14:00:00Z",
      "estimated_remaining_minutes": 15
    },
    {
      "task_id": "ENV-20250315-004",
      "description": "Health check on mock-env-02",
      "started_at": "2025-03-15T14:10:00Z",
      "estimated_remaining_minutes": 5
    }
  ]
}
```

**Adaptive Card Layout:** Compact card with load indicator (color-coded), utilization bar, and current work list.

Load status color mapping:

| Status | Color | Threshold |
|--------|-------|-----------|
| `idle` | Good (green) | 0% utilization |
| `working` | Default | 1-50% utilization |
| `busy` | Warning (yellow) | 51-85% utilization |
| `overloaded` | Attention (red) | >85% utilization |

---

## 6. Adaptive Card Templates

All bot output uses reusable Adaptive Card templates. Templates are parameterized with `${variable}` placeholders that the Card Renderer fills from agent API responses.

### 6.1 Activity Card

Used for: Activity notifications (agent completed an action).

```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "ColumnSet",
      "columns": [
        {
          "type": "Column",
          "width": "auto",
          "items": [
            {
              "type": "Image",
              "url": "${agent_icon_url}",
              "size": "Small",
              "style": "Person"
            }
          ]
        },
        {
          "type": "Column",
          "width": "stretch",
          "items": [
            {
              "type": "TextBlock",
              "text": "${agent_display_name} -- ${agent_role}",
              "weight": "Bolder",
              "size": "Medium"
            },
            {
              "type": "TextBlock",
              "text": "${timestamp}",
              "isSubtle": true,
              "spacing": "None",
              "size": "Small"
            }
          ]
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "${activity_summary}",
      "wrap": true,
      "size": "Default"
    },
    {
      "type": "FactSet",
      "facts": [
        { "title": "Action", "value": "${action_type}" },
        { "title": "Subject", "value": "${subject_id}" },
        { "title": "Result", "value": "${result_status}" },
        { "title": "Duration", "value": "${duration}" },
        { "title": "Correlation ID", "value": "${correlation_id}" }
      ]
    }
  ]
}
```

### 6.2 Decision Card

Used for: Decision notifications and `/decision-tree` responses. Supports expandable sections via `Action.ShowCard`.

```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "TextBlock",
      "text": "Decision Log -- ${agent_display_name}",
      "weight": "Bolder",
      "size": "Large"
    },
    {
      "type": "TextBlock",
      "text": "${total_decisions_today} decisions today | ${total_decisions_cumulative} total",
      "isSubtle": true,
      "size": "Small"
    },
    {
      "type": "Container",
      "separator": true,
      "items": [
        {
          "type": "ColumnSet",
          "columns": [
            {
              "type": "Column",
              "width": "auto",
              "items": [
                {
                  "type": "TextBlock",
                  "text": "${outcome_badge}",
                  "weight": "Bolder",
                  "color": "${outcome_color}"
                }
              ]
            },
            {
              "type": "Column",
              "width": "stretch",
              "items": [
                {
                  "type": "TextBlock",
                  "text": "${decision_title}",
                  "weight": "Bolder",
                  "wrap": true
                },
                {
                  "type": "TextBlock",
                  "text": "${decision_id} | ${timestamp}",
                  "isSubtle": true,
                  "size": "Small"
                }
              ]
            }
          ]
        },
        {
          "type": "TextBlock",
          "text": "${rationale}",
          "wrap": true,
          "isSubtle": true
        }
      ]
    }
  ],
  "actions": [
    {
      "type": "Action.ShowCard",
      "title": "Expand Details",
      "card": {
        "type": "AdaptiveCard",
        "body": [
          {
            "type": "TextBlock",
            "text": "**Inputs Evaluated:** ${input_count}",
            "wrap": true
          },
          {
            "type": "TextBlock",
            "text": "**Alternatives Considered:** ${alternative_count}",
            "wrap": true
          },
          {
            "type": "TextBlock",
            "text": "**Confidence:** ${confidence_level}",
            "wrap": true
          }
        ]
      }
    },
    {
      "type": "Action.Submit",
      "title": "Full Decision Tree",
      "data": {
        "action": "command",
        "command": "/why",
        "args": "${decision_id}",
        "agent_id": "${agent_id}"
      }
    }
  ]
}
```

### 6.3 Approval Card

Used for: Approval requests. See Section 4.3 for the full JSON. Key design points:

- Warning-styled header container for visual urgency
- Evidence summary in an emphasis container
- Comment field (required for rejections, optional for approvals)
- Approve (positive style) and Reject (destructive style) buttons
- Expiry time displayed prominently
- Approval ID for audit trail

### 6.4 Input Request Card

Used for: Structured input requests. See Section 4.4 for the full JSON. Key design points:

- Dynamic form fields generated from the agent's input schema
- Supported input types: `Input.Text`, `Input.ChoiceSet`, `Input.Number`, `Input.Date`, `Input.Toggle`
- Submit and Skip buttons
- Deadline displayed for time-sensitive requests

### 6.5 Error Alert Card

Used for: Error and anomaly alerts. See Section 4.5 for the full JSON. Key design points:

- Severity-colored header (critical=red, error=yellow, warning=blue, info=default)
- Error code and correlation ID for debugging
- Suggested actions section
- Link to Grafana dashboard for the agent (if configured)

### 6.6 Stats Card

Used for: `/stats` command responses.

```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "TextBlock",
      "text": "Operational Statistics -- ${agent_display_name}",
      "weight": "Bolder",
      "size": "Large"
    },
    {
      "type": "ColumnSet",
      "columns": [
        {
          "type": "Column",
          "width": "1",
          "items": [
            {
              "type": "TextBlock",
              "text": "Uptime",
              "weight": "Bolder",
              "horizontalAlignment": "Center"
            },
            {
              "type": "TextBlock",
              "text": "${uptime_pct}%",
              "size": "ExtraLarge",
              "horizontalAlignment": "Center",
              "color": "${uptime_color}"
            }
          ]
        },
        {
          "type": "Column",
          "width": "1",
          "items": [
            {
              "type": "TextBlock",
              "text": "Success Rate",
              "weight": "Bolder",
              "horizontalAlignment": "Center"
            },
            {
              "type": "TextBlock",
              "text": "${success_rate_pct}%",
              "size": "ExtraLarge",
              "horizontalAlignment": "Center",
              "color": "${success_color}"
            }
          ]
        },
        {
          "type": "Column",
          "width": "1",
          "items": [
            {
              "type": "TextBlock",
              "text": "Queue",
              "weight": "Bolder",
              "horizontalAlignment": "Center"
            },
            {
              "type": "TextBlock",
              "text": "${queue_depth}",
              "size": "ExtraLarge",
              "horizontalAlignment": "Center"
            }
          ]
        }
      ]
    },
    {
      "type": "FactSet",
      "separator": true,
      "facts": [
        { "title": "Period", "value": "${period}" },
        { "title": "Jobs Processed", "value": "${jobs_processed}" },
        { "title": "Jobs Succeeded", "value": "${jobs_succeeded}" },
        { "title": "Jobs Failed", "value": "${jobs_failed}" },
        { "title": "Avg Latency", "value": "${avg_latency_seconds}s" },
        { "title": "P95 Latency", "value": "${p95_latency_seconds}s" },
        { "title": "Active Jobs", "value": "${active_jobs}" },
        { "title": "Error Trend", "value": "${error_trend}" }
      ]
    },
    {
      "type": "TextBlock",
      "text": "**Top Errors**",
      "weight": "Bolder",
      "separator": true
    },
    {
      "type": "FactSet",
      "facts": [
        { "title": "${error_code_1}", "value": "${error_count_1}x (last: ${error_last_1})" }
      ]
    }
  ]
}
```

### 6.7 Token Status Card

Used for: `/token-status` command responses.

```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "TextBlock",
      "text": "Token Usage -- ${agent_display_name}",
      "weight": "Bolder",
      "size": "Large"
    },
    {
      "type": "TextBlock",
      "text": "Model: ${model} | Efficiency: ${efficiency_ratio}",
      "isSubtle": true,
      "size": "Small"
    },
    {
      "type": "TextBlock",
      "text": "**Today (${period})**",
      "weight": "Bolder",
      "separator": true
    },
    {
      "type": "ColumnSet",
      "columns": [
        {
          "type": "Column",
          "width": "1",
          "items": [
            { "type": "TextBlock", "text": "Input", "size": "Small", "isSubtle": true },
            { "type": "TextBlock", "text": "${tokens_today_input}", "weight": "Bolder" }
          ]
        },
        {
          "type": "Column",
          "width": "1",
          "items": [
            { "type": "TextBlock", "text": "Output", "size": "Small", "isSubtle": true },
            { "type": "TextBlock", "text": "${tokens_today_output}", "weight": "Bolder" }
          ]
        },
        {
          "type": "Column",
          "width": "1",
          "items": [
            { "type": "TextBlock", "text": "Cost", "size": "Small", "isSubtle": true },
            { "type": "TextBlock", "text": "$${cost_today_usd}", "weight": "Bolder" }
          ]
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "**Cumulative**",
      "weight": "Bolder",
      "separator": true
    },
    {
      "type": "ColumnSet",
      "columns": [
        {
          "type": "Column",
          "width": "1",
          "items": [
            { "type": "TextBlock", "text": "Input", "size": "Small", "isSubtle": true },
            { "type": "TextBlock", "text": "${tokens_cumulative_input}", "weight": "Bolder" }
          ]
        },
        {
          "type": "Column",
          "width": "1",
          "items": [
            { "type": "TextBlock", "text": "Output", "size": "Small", "isSubtle": true },
            { "type": "TextBlock", "text": "${tokens_cumulative_output}", "weight": "Bolder" }
          ]
        },
        {
          "type": "Column",
          "width": "1",
          "items": [
            { "type": "TextBlock", "text": "Cost", "size": "Small", "isSubtle": true },
            { "type": "TextBlock", "text": "$${cost_cumulative_usd}", "weight": "Bolder" }
          ]
        }
      ]
    },
    {
      "type": "FactSet",
      "separator": true,
      "facts": [
        { "title": "Deterministic Actions", "value": "${deterministic_action_pct}%" },
        { "title": "Target", "value": ">80%" }
      ]
    }
  ]
}
```

### 6.8 Work Summary Card

Used for: `/work-today` command responses.

```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "TextBlock",
      "text": "Work Summary -- ${agent_display_name}",
      "weight": "Bolder",
      "size": "Large"
    },
    {
      "type": "TextBlock",
      "text": "${date}",
      "isSubtle": true,
      "size": "Small"
    },
    {
      "type": "TextBlock",
      "text": "${summary}",
      "wrap": true,
      "separator": true
    },
    {
      "type": "ColumnSet",
      "separator": true,
      "columns": [
        {
          "type": "Column",
          "width": "1",
          "items": [
            { "type": "TextBlock", "text": "Processed", "size": "Small", "isSubtle": true, "horizontalAlignment": "Center" },
            { "type": "TextBlock", "text": "${totals_processed}", "size": "ExtraLarge", "horizontalAlignment": "Center", "weight": "Bolder" }
          ]
        },
        {
          "type": "Column",
          "width": "1",
          "items": [
            { "type": "TextBlock", "text": "Passed", "size": "Small", "isSubtle": true, "horizontalAlignment": "Center" },
            { "type": "TextBlock", "text": "${totals_passed}", "size": "ExtraLarge", "horizontalAlignment": "Center", "color": "Good" }
          ]
        },
        {
          "type": "Column",
          "width": "1",
          "items": [
            { "type": "TextBlock", "text": "Failed", "size": "Small", "isSubtle": true, "horizontalAlignment": "Center" },
            { "type": "TextBlock", "text": "${totals_failed}", "size": "ExtraLarge", "horizontalAlignment": "Center", "color": "Attention" }
          ]
        }
      ]
    },
    {
      "type": "Container",
      "separator": true,
      "items": [
        {
          "type": "TextBlock",
          "text": "**Work Items**",
          "weight": "Bolder"
        },
        {
          "type": "ColumnSet",
          "columns": [
            {
              "type": "Column",
              "width": "auto",
              "items": [
                {
                  "type": "TextBlock",
                  "text": "${item_status_badge}",
                  "color": "${item_status_color}",
                  "weight": "Bolder"
                }
              ]
            },
            {
              "type": "Column",
              "width": "stretch",
              "items": [
                {
                  "type": "TextBlock",
                  "text": "${item_description}",
                  "wrap": true
                },
                {
                  "type": "TextBlock",
                  "text": "${item_subject_id} | ${item_timestamp}",
                  "isSubtle": true,
                  "size": "Small"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 7. Command Routing

### Channel-to-Agent Resolution

When the bot receives a message, it resolves the agent using this lookup chain:

1. Extract `channel_id` from the Teams activity payload.
2. Look up `channel_id` in the Agent Registry.
3. If found, use the corresponding `agent_id` and `api_base_url`.
4. If not found, reply with an error: "This channel is not configured for any agent."

The lookup is cached in Redis with a TTL of 300 seconds. Registry changes invalidate the cache.

### Standard Command to API Endpoint Mapping

| Command | HTTP Method | Agent API Endpoint | Notes |
|---------|-------------|-------------------|-------|
| `/token-status` | GET | `/v1/status/tokens` | No parameters |
| `/decision-tree` | GET | `/v1/status/decisions` | Optional `?limit=N` (default 10) |
| `/why {id}` | GET | `/v1/status/decisions/{id}` | `{id}` extracted from message text |
| `/stats` | GET | `/v1/status/stats` | Optional `?period=last_24h` (default) |
| `/work-today` | GET | `/v1/status/work-summary` | No parameters |
| `/busy` | GET | `/v1/status/load` | No parameters |
| `/help` | N/A | Handled locally by bot | Returns standard + custom commands from registry |

### Custom Command Routing

For commands defined in the agent's `custom_commands` registry entry:

1. Parse the command name from the message.
2. Match against `custom_commands[].command` for the resolved agent.
3. Extract parameters from the message text (positional or named).
4. Call `{api_base_url}{api_path}` with the specified `api_method`.
5. Render the response using the appropriate card template.

### Free-Text Query Handling

Messages that do not match any command pattern are forwarded as free-text queries:

```
POST {api_base_url}/v1/query
Content-Type: application/json

{
  "query": "<user message text>",
  "user_id": "<teams user principal name>",
  "channel_id": "<teams channel id>",
  "thread_id": "<teams thread id or null>"
}
```

The agent processes the query and returns a structured response. The bot renders it as a text block or Adaptive Card depending on the response `content_type` field.

### Error Handling

| Scenario | Bot Behavior |
|----------|-------------|
| Agent API unreachable | Reply: "Agent {name} is currently unreachable. Last healthy: {timestamp}. Check #ops-alerts." |
| Agent API timeout (exceeds `timeout_seconds`) | Reply: "Agent {name} did not respond within {timeout}s. The request may still be processing. Try `/busy` to check load." |
| Agent API returns 4xx | Reply: "Agent {name} returned an error: {status_code} -- {error_message}" |
| Agent API returns 5xx | Reply: "Agent {name} encountered an internal error. Correlation ID: {id}. This has been logged." |
| Unknown command | Reply: "Unknown command: {command}. Type `/help` to see available commands." |
| Rate limited | Reply: "Rate limit exceeded for this channel. Please wait {retry_after}s." |

All errors are logged to PostgreSQL with correlation_id, agent_id, error_code, and timestamp.

---

## 8. Approval Workflow

### Flow Overview

```mermaid
sequenceDiagram
    participant A as Agent (e.g. Hedy)
    participant BOT as Teams Bot
    participant DB as PostgreSQL
    participant T as Teams Channel
    participant U as Human Approver
    participant RD as Redis

    A->>BOT: POST /v1/bot/request-approval (approval payload)
    BOT->>DB: INSERT approval_request (status=pending)
    BOT->>T: Post Approval Card to #agent-hedy
    T-->>U: User sees approval card
    U->>T: Clicks "Approve" with comment
    T->>BOT: Action.Submit payload
    BOT->>BOT: Verify user has approval authority
    BOT->>DB: UPDATE approval_request (status=approved, approver, comment)
    BOT->>A: POST {api_base_url}/v1/approvals/{id}/respond
    A-->>BOT: Acknowledgment
    BOT->>T: Post confirmation card (threaded reply)
    BOT->>DB: INSERT audit_log
```

### Approval Types by Agent

| Agent | Approval Type | Description | Typical Approvers |
|-------|--------------|-------------|-------------------|
| **Hedy** | `release_promotion` | Promote a build from one release stage to the next (sit to qa, qa to release) | Release Approvers |
| **Linus** | `review_policy_override` | Override a review policy finding that the agent flagged as blocking | Engineers, Tech Leads |
| **Linnaeus** | `traceability_exception` | Allow a release or build to proceed despite a traceability gap | Project Leads |
| **Hemingway** | `external_doc_publish` | Publish documentation to an external-facing target | Documentation Owners, Engineering Managers |

### Approval Request Payload

Agents call the bot's approval API with this payload:

```json
{
  "agent_id": "hedy",
  "approval_type": "release_promotion",
  "title": "Promote BLD-4519 from qa to release",
  "description": "All qa-stage gates passed. Requesting promotion to release stage.",
  "subject_id": "BLD-4519",
  "risk_level": "high",
  "evidence": {
    "build_id": "BLD-4519",
    "version": "12.0.3.0",
    "test_coverage_pct": 94,
    "test_failures": 0,
    "traceability_gaps": 0,
    "policy_checks_passed": true
  },
  "evidence_summary": "Build BLD-4519 (v12.0.3.0) passed all qa gates. 94% test coverage, zero failures, zero traceability gaps. All policy checks passed.",
  "timeout_hours": 24,
  "escalation_config": {
    "escalate_after_hours": 12,
    "escalation_targets": ["@release-leads"]
  }
}
```

### Approval Database Schema

```sql
CREATE TABLE approval_requests (
    approval_id       TEXT PRIMARY KEY,
    agent_id          TEXT NOT NULL,
    approval_type     TEXT NOT NULL,
    title             TEXT NOT NULL,
    description       TEXT,
    subject_id        TEXT,
    risk_level        TEXT CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    evidence          JSONB,
    evidence_summary  TEXT,
    status            TEXT NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending', 'approved', 'rejected', 'expired', 'escalated')),
    requested_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    timeout_at        TIMESTAMPTZ NOT NULL,
    responded_at      TIMESTAMPTZ,
    approver_id       TEXT,
    approver_name     TEXT,
    approver_comment  TEXT,
    teams_message_id  TEXT,
    teams_channel_id  TEXT,
    escalation_config JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_approval_status ON approval_requests (status);
CREATE INDEX idx_approval_agent ON approval_requests (agent_id);
CREATE INDEX idx_approval_timeout ON approval_requests (timeout_at) WHERE status = 'pending';
```

### Timeout Handling

A background scheduler runs every 5 minutes and checks for expired approvals:

1. Query: `SELECT * FROM approval_requests WHERE status = 'pending' AND timeout_at < NOW()`
2. For each expired approval:
   - If `escalation_config` is set and escalation has not yet occurred:
     - Update status to `escalated`
     - Re-post the approval card with an `ESCALATED` banner
     - @mention the escalation targets
   - If escalation already occurred or no escalation config:
     - Update status to `expired`
     - Post expiry notification to the channel
     - Notify the agent via `POST {api_base_url}/v1/approvals/{id}/expired`

### Escalation Behavior

| Time Elapsed | Action |
|-------------|--------|
| 0h | Approval card posted to channel |
| `escalate_after_hours` | Re-post with ESCALATED banner, @mention escalation targets |
| `timeout_hours` | Mark expired, notify agent, post expiry notice |

---

## 9. Thread Management

### Threading Rules

| Message Type | Threading Behavior |
|-------------|-------------------|
| Activity notification | Top-level message in channel |
| Decision notification | Top-level message in channel |
| Approval request | Top-level message in channel |
| Approval response confirmation | Threaded reply to the approval request message |
| Error alert | Top-level message in channel |
| Command response | Threaded reply to the user's command message |
| Free-text query response | Threaded reply to the user's query message |
| Input request | Top-level message in channel |
| Input response confirmation | Threaded reply to the input request message |
| Escalation re-post | Threaded reply to the original approval message |

### Conversation State Tracking

The bot tracks conversation state in PostgreSQL to maintain thread context and enable follow-up interactions.

```sql
CREATE TABLE conversation_state (
    conversation_id   TEXT PRIMARY KEY,
    channel_id        TEXT NOT NULL,
    agent_id          TEXT NOT NULL,
    thread_id         TEXT,
    message_type      TEXT NOT NULL,
    root_message_id   TEXT NOT NULL,
    context           JSONB,
    status            TEXT NOT NULL DEFAULT 'active',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at        TIMESTAMPTZ
);

CREATE INDEX idx_conv_channel ON conversation_state (channel_id);
CREATE INDEX idx_conv_thread ON conversation_state (thread_id);
CREATE INDEX idx_conv_agent ON conversation_state (agent_id);
```

### Message Deduplication

The bot deduplicates messages using a combination of:

1. **Teams activity ID** -- Each Teams message has a unique activity ID. The bot stores processed activity IDs in Redis with a 1-hour TTL.
2. **Idempotency keys for outbound messages** -- When agents call the bot's notification API, they include an `idempotency_key`. The bot checks Redis before posting. Duplicate keys within 1 hour are silently dropped.
3. **Approval response deduplication** -- Once an approval is responded to (approved/rejected), subsequent button clicks on the same card return a message: "This approval has already been processed."

```sql
CREATE TABLE processed_messages (
    activity_id   TEXT PRIMARY KEY,
    channel_id    TEXT NOT NULL,
    processed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Cleanup: DELETE FROM processed_messages WHERE processed_at < NOW() - INTERVAL '24 hours'
```

---

## 10. Teams App Manifest

### App Registration

The bot is registered as a single Azure AD application with a Bot Framework registration. It uses the Bot Framework SDK for Python to handle Teams webhook events.

### Manifest Configuration

```json
{
  "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "cn-agent-workforce-bot",
  "developer": {
    "name": "Cornelis Networks",
    "websiteUrl": "https://www.cornelisnetworks.com",
    "privacyUrl": "https://www.cornelisnetworks.com/privacy",
    "termsOfUseUrl": "https://www.cornelisnetworks.com/terms"
  },
  "name": {
    "short": "Agent Workforce",
    "full": "Cornelis Networks AI Agent Workforce Bot"
  },
  "description": {
    "short": "Human interface for 15 AI engineering agents",
    "full": "The Agent Workforce bot provides a unified Teams interface for interacting with all 15 AI agents in the Cornelis Networks Agent Workforce. Each agent has a dedicated channel. Use standard commands to query status, review decisions, and respond to approval requests."
  },
  "icons": {
    "color": "color-icon-192x192.png",
    "outline": "outline-icon-32x32.png"
  },
  "accentColor": "#0078D4",
  "bots": [
    {
      "botId": "${AZURE_BOT_APP_ID}",
      "scopes": ["team"],
      "supportsFiles": false,
      "isNotificationOnly": false,
      "commandLists": [
        {
          "scopes": ["team"],
          "commands": [
            { "title": "token-status", "description": "Token usage summary" },
            { "title": "decision-tree", "description": "Recent decisions with rationale" },
            { "title": "why", "description": "Deep dive into a specific decision" },
            { "title": "stats", "description": "Operational statistics" },
            { "title": "work-today", "description": "Today's work summary" },
            { "title": "busy", "description": "Current load status" },
            { "title": "help", "description": "List available commands" }
          ]
        }
      ]
    }
  ],
  "permissions": [
    "identity",
    "messageTeamMembers"
  ],
  "validDomains": [
    "internal.cornelisnetworks.com"
  ]
}
```

### Required Permissions

| Permission | Scope | Purpose |
|-----------|-------|---------|
| `ChannelMessage.Read.Group` | Team | Read messages in agent channels |
| `ChannelMessage.Send` | Team | Post responses and notifications |
| `TeamMember.Read.Group` | Team | Verify user identity for approvals |
| `Files.Read.Group` | Team | Not required (supportsFiles=false) |

### Adaptive Card Schema Version

All cards use Adaptive Card schema version **1.5**, which is supported by Teams desktop, web, and mobile clients. This version supports `Action.ShowCard` for expandable sections, `Action.Submit` for button interactions, and all input types used in the templates.

---

## 11. API Contract

The bot exposes a REST API that agents call to push notifications, request approvals, and request input. This is the agent-to-bot interface.

**Base URL:** `http://cn-ai-01:8200/v1/bot`

### 11.1 POST /v1/bot/notify

Agent sends a notification to its Teams channel.

**Request:**

```http
POST /v1/bot/notify
Content-Type: application/json
Authorization: Bearer <agent_service_token>
X-Idempotency-Key: <unique_key>

{
  "agent_id": "josephine",
  "notification_type": "activity",
  "title": "Build BLD-4522 completed successfully",
  "summary": "Built 14 packages from cornelis/opa-psm in 342 seconds.",
  "details": {
    "action_type": "build_complete",
    "subject_id": "BLD-4522",
    "result_status": "success",
    "duration": "5m 42s",
    "correlation_id": "evt-20250315-abc123"
  },
  "thread_id": null
}
```

**Response:**

```json
{
  "status": "sent",
  "message_id": "msg-20250315-xyz789",
  "channel_id": "19:abc123def456@thread.tacv2",
  "timestamp": "2025-03-15T14:30:00Z"
}
```

**Notification types:** `activity`, `decision`, `error`

### 11.2 POST /v1/bot/request-approval

Agent requests human approval via an Adaptive Card.

**Request:**

```http
POST /v1/bot/request-approval
Content-Type: application/json
Authorization: Bearer <agent_service_token>
X-Idempotency-Key: <unique_key>

{
  "agent_id": "hedy",
  "approval_type": "release_promotion",
  "title": "Promote BLD-4519 from qa to release",
  "description": "All qa-stage gates passed. Requesting promotion to release stage.",
  "subject_id": "BLD-4519",
  "risk_level": "high",
  "evidence": {
    "build_id": "BLD-4519",
    "version": "12.0.3.0",
    "test_coverage_pct": 94,
    "test_failures": 0,
    "traceability_gaps": 0
  },
  "evidence_summary": "Build BLD-4519 (v12.0.3.0) passed all qa gates. 94% test coverage, zero failures, zero traceability gaps.",
  "timeout_hours": 24,
  "escalation_config": {
    "escalate_after_hours": 12,
    "escalation_targets": ["@release-leads"]
  }
}
```

**Response:**

```json
{
  "approval_id": "APR-20250315-001",
  "status": "pending",
  "message_id": "msg-20250315-apr001",
  "channel_id": "19:xyz789ghi012@thread.tacv2",
  "timeout_at": "2025-03-16T14:30:00Z",
  "timestamp": "2025-03-15T14:30:00Z"
}
```

### 11.3 POST /v1/bot/request-input

Agent requests structured input from a human.

**Request:**

```http
POST /v1/bot/request-input
Content-Type: application/json
Authorization: Bearer <agent_service_token>
X-Idempotency-Key: <unique_key>

{
  "agent_id": "nightingale",
  "title": "Additional context needed for BUG-2341",
  "description": "Nightingale is investigating BUG-2341 (fabric link flap under load). The reproduction attempt needs additional environment details.",
  "context_summary": "Bug reported on dual-rail HFI configuration. Initial reproduction on single-rail did not trigger the issue.",
  "fields": [
    {
      "id": "rail_config",
      "label": "Rail Configuration",
      "type": "choice",
      "required": true,
      "choices": [
        { "title": "Single Rail", "value": "single" },
        { "title": "Dual Rail", "value": "dual" },
        { "title": "Unknown", "value": "unknown" }
      ]
    },
    {
      "id": "firmware_version",
      "label": "HFI Firmware Version",
      "type": "text",
      "required": true,
      "placeholder": "e.g., 1.27.0"
    },
    {
      "id": "additional_notes",
      "label": "Additional Notes",
      "type": "text",
      "required": false,
      "multiline": true,
      "placeholder": "Any other relevant details"
    }
  ],
  "deadline": "2025-03-16T12:00:00Z"
}
```

**Response:**

```json
{
  "request_id": "INP-20250315-042",
  "status": "pending",
  "message_id": "msg-20250315-inp042",
  "channel_id": "19:nightingale-channel@thread.tacv2",
  "deadline": "2025-03-16T12:00:00Z",
  "timestamp": "2025-03-15T14:30:00Z"
}
```

### 11.4 POST /v1/bot/alert

Agent sends an error alert to its channel.

**Request:**

```http
POST /v1/bot/alert
Content-Type: application/json
Authorization: Bearer <agent_service_token>
X-Idempotency-Key: <unique_key>

{
  "agent_id": "josephine",
  "severity": "error",
  "title": "Build worker bld-host-01 unresponsive",
  "description": "Heartbeat from bld-host-01 not received for 10 minutes. 2 queued jobs may be affected.",
  "error_code": "WORKER_HEARTBEAT_TIMEOUT",
  "component": "josephine-worker",
  "correlation_id": "evt-20250315-def456",
  "suggested_actions": "1. Check bld-host-01 SSH connectivity.\n2. Verify Docker daemon is running.\n3. If unrecoverable, drain worker and reassign jobs."
}
```

**Response:**

```json
{
  "status": "sent",
  "message_id": "msg-20250315-alert001",
  "channel_id": "19:abc123def456@thread.tacv2",
  "timestamp": "2025-03-15T14:30:00Z"
}
```

### 11.5 GET /v1/bot/approvals/{id}

Check the status of a pending approval.

**Request:**

```http
GET /v1/bot/approvals/APR-20250315-001
Authorization: Bearer <agent_service_token>
```

**Response:**

```json
{
  "approval_id": "APR-20250315-001",
  "agent_id": "hedy",
  "approval_type": "release_promotion",
  "status": "approved",
  "requested_at": "2025-03-15T14:30:00Z",
  "responded_at": "2025-03-15T15:12:00Z",
  "approver_id": "john.macdonald@cornelisnetworks.com",
  "approver_name": "John MacDonald",
  "approver_comment": "Coverage looks good. Approved for release.",
  "timeout_at": "2025-03-16T14:30:00Z"
}
```

---

## 12. Security

### Bot Authentication with Teams

The bot authenticates with Microsoft Teams using Azure AD app registration:

| Component | Value |
|-----------|-------|
| Azure AD App ID | Registered in Cornelis Networks Azure AD tenant |
| App Secret | Stored in Docker secrets, rotated quarterly |
| Bot Framework Registration | Azure Bot Service registration linked to the App ID |
| Webhook Validation | Bot Framework SDK validates inbound webhook signatures using the app secret |
| Token Endpoint | `https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token` |

The bot validates every inbound webhook request by verifying the JWT bearer token in the `Authorization` header against Microsoft's public signing keys. Requests with invalid or missing tokens are rejected with HTTP 401.

### Agent-to-Bot Authentication

Agents authenticate to the bot's REST API using service principal tokens:

| Mechanism | Details |
|-----------|---------|
| Auth Method | Bearer token (JWT) issued per agent service principal |
| Token Issuer | Internal token service or Azure AD app-to-app auth |
| Token Lifetime | 1 hour, auto-refreshed by agent SDK |
| API Key Fallback | Static API key per agent for development environments only |
| Header | `Authorization: Bearer <token>` |

Each agent has a unique service principal. The bot validates the token and extracts the `agent_id` claim. The `agent_id` in the token must match the `agent_id` in the request body.

### User Identity Verification

For approval and input responses, the bot verifies the user's identity:

1. Extract the user's Azure AD object ID and UPN from the Teams activity payload.
2. Verify the user is a member of the "Agent Workforce" team.
3. For approvals, optionally verify the user has the required role (e.g., "Release Approver") via Azure AD group membership.
4. Record the verified user identity in the approval/input response record.

### Audit Trail

Every interaction is logged to the `audit_log` table:

```sql
CREATE TABLE audit_log (
    log_id          TEXT PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id         TEXT,
    user_name       TEXT,
    agent_id        TEXT NOT NULL,
    channel_id      TEXT NOT NULL,
    action          TEXT NOT NULL,
    action_detail   JSONB,
    message_id      TEXT,
    thread_id       TEXT,
    correlation_id  TEXT,
    ip_address      TEXT,
    user_agent      TEXT
);

CREATE INDEX idx_audit_agent ON audit_log (agent_id, timestamp);
CREATE INDEX idx_audit_user ON audit_log (user_id, timestamp);
CREATE INDEX idx_audit_action ON audit_log (action, timestamp);
CREATE INDEX idx_audit_correlation ON audit_log (correlation_id);
```

Logged actions include:

| Action | Description |
|--------|-------------|
| `command_received` | User issued a standard or custom command |
| `command_response_sent` | Bot posted a command response |
| `query_received` | User posted a free-text query |
| `query_response_sent` | Bot posted a query response |
| `approval_requested` | Agent requested an approval |
| `approval_approved` | User approved a request |
| `approval_rejected` | User rejected a request |
| `approval_expired` | Approval timed out |
| `approval_escalated` | Approval escalated to additional approvers |
| `input_requested` | Agent requested human input |
| `input_received` | User submitted input |
| `notification_sent` | Agent sent a notification |
| `alert_sent` | Agent sent an error alert |
| `error` | Bot encountered an error processing a request |

### Rate Limiting

Rate limits are enforced per channel using Redis sliding window counters:

| Scope | Limit | Window |
|-------|-------|--------|
| Inbound commands per channel | 30 | 1 minute |
| Inbound commands per user per channel | 10 | 1 minute |
| Agent notifications per channel | 60 | 1 minute |
| Agent approval requests per channel | 10 | 1 hour |

When a rate limit is exceeded, the bot returns a message indicating the limit and retry-after time. Agent API calls receive HTTP 429 with a `Retry-After` header.

---

## 13. Deployment

### Docker Container

The bot runs as a single Docker container within the agent platform's Docker Compose stack on `cn-ai-01`.

```yaml
# docker-compose.teams-bot.yaml
version: "3.8"

services:
  teams-bot:
    image: cornelis/teams-bot:${BOT_VERSION:-latest}
    container_name: teams-bot
    restart: unless-stopped
    network_mode: host
    ports:
      - "8200:8200"
    environment:
      - BOT_APP_ID=${AZURE_BOT_APP_ID}
      - BOT_APP_SECRET=${AZURE_BOT_APP_SECRET}
      - BOT_TENANT_ID=${AZURE_TENANT_ID}
      - DATABASE_URL=postgresql://teams_bot:${DB_PASSWORD}@localhost:5432/agent_workforce
      - REDIS_URL=redis://localhost:6379/1
      - AGENT_REGISTRY_PATH=/etc/teams-bot/agent-registry.yaml
      - LOG_LEVEL=INFO
      - BOT_PORT=8200
      - HEALTH_CHECK_INTERVAL=30
      - APPROVAL_CHECK_INTERVAL=300
    volumes:
      - ./config/agent-registry.yaml:/etc/teams-bot/agent-registry.yaml:ro
      - ./config/card-templates:/etc/teams-bot/card-templates:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8200/v1/bot/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"
        tag: "teams-bot"
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_BOT_APP_ID` | Yes | Azure AD application ID for the bot |
| `AZURE_BOT_APP_SECRET` | Yes | Azure AD application secret |
| `AZURE_TENANT_ID` | Yes | Azure AD tenant ID |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `AGENT_REGISTRY_PATH` | Yes | Path to agent registry YAML file |
| `LOG_LEVEL` | No | Logging level (default: `INFO`) |
| `BOT_PORT` | No | HTTP port (default: `8200`) |
| `HEALTH_CHECK_INTERVAL` | No | Agent health check interval in seconds (default: `30`) |
| `APPROVAL_CHECK_INTERVAL` | No | Approval timeout check interval in seconds (default: `300`) |

### Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `botbuilder-core` | >=4.14 | Microsoft Bot Framework SDK for Python |
| `botbuilder-integration-aiohttp` | >=4.14 | AIOHTTP integration for Bot Framework |
| `fastapi` | >=0.100 | REST API framework for agent-to-bot endpoints |
| `uvicorn` | >=0.23 | ASGI server |
| `asyncpg` | >=0.28 | Async PostgreSQL driver |
| `redis[hiredis]` | >=5.0 | Redis client with hiredis parser |
| `pyyaml` | >=6.0 | YAML parsing for agent registry |
| `pydantic` | >=2.0 | Request/response validation |
| `structlog` | >=23.0 | Structured logging |

### Health Check Endpoint

```
GET /v1/bot/health
```

**Response (healthy):**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "agents_registered": 15,
  "agents_healthy": 14,
  "agents_unhealthy": ["tesla"],
  "database": "connected",
  "redis": "connected",
  "teams_webhook": "active",
  "pending_approvals": 2,
  "last_message_processed": "2025-03-15T14:30:00Z"
}
```

The health endpoint is used by Docker health checks and by the Prometheus scraper for monitoring.

### Host Placement

The bot runs on `cn-ai-01` alongside PostgreSQL, Redis, and Nginx. Nginx reverse-proxies the bot's webhook endpoint for TLS termination:

```
Internet -> Nginx (TLS) -> teams-bot:8200
```

The bot's agent-to-bot API is accessible only on the internal network (no TLS required for agent-to-bot calls within the Docker network).

---

## 14. Implementation Phases

### Phase 1: Basic Bot + Standard Commands + Activity Notifications

**Scope:**

- Bot Framework SDK integration with Teams
- Webhook receiver and message parser
- Agent Registry (YAML config, hot-reload)
- Channel-to-agent routing
- All 6 standard commands routed to agent APIs
- Activity notification posting (agent-to-bot `/v1/bot/notify`)
- Basic Adaptive Card templates (Activity, Stats, Token Status, Work Summary)
- PostgreSQL audit logging
- Redis rate limiting
- Health check endpoint
- Docker deployment

**Deliverables:**

- Users can post `/stats`, `/token-status`, `/decision-tree`, `/why {id}`, `/work-today`, `/busy` in any agent channel and get formatted responses.
- Agents can push activity notifications to their channels.
- All interactions are logged.

**Dependencies:** Agent APIs must implement the 6 standard status endpoints.

### Phase 2: Approval Workflow + Adaptive Cards

**Scope:**

- Approval request API (`/v1/bot/request-approval`)
- Approval Adaptive Card with Approve/Reject buttons
- Approval response handling (button click processing)
- Approval status tracking in PostgreSQL
- Approval timeout and escalation scheduler
- Decision notification cards
- Error alert cards and API (`/v1/bot/alert`)
- Approval status query API (`/v1/bot/approvals/{id}`)
- User identity verification for approvals

**Deliverables:**

- Hedy, Linus, Linnaeus, and Hemingway can request human approvals.
- Users can approve/reject via Adaptive Card buttons.
- Timeouts trigger escalation.
- All approval actions are audited with user identity.

**Dependencies:** Phase 1 complete. Agents must implement `/v1/approvals/{id}/respond` endpoint.

### Phase 3: Input Requests + Free-Text Queries

**Scope:**

- Input request API (`/v1/bot/request-input`)
- Dynamic form generation from field schemas
- Input response handling (form submission processing)
- Free-text query forwarding to agent `/v1/query` endpoint
- Thread management for conversations
- Conversation state tracking in PostgreSQL
- Message deduplication

**Deliverables:**

- Agents can request structured input from humans.
- Users can ask free-text questions in agent channels.
- Conversations are properly threaded.

**Dependencies:** Phase 2 complete. Agents must implement `/v1/query` endpoint.

### Phase 4: Custom Agent Commands + Advanced Cards

**Scope:**

- Custom command routing from registry `custom_commands`
- Parameter extraction and validation for custom commands
- Agent-specific card templates (if needed beyond standard templates)
- `/help` command with per-agent command listing
- Card template hot-reload
- Performance optimization (connection pooling, response caching)
- Grafana dashboard for bot metrics

**Deliverables:**

- Agent-specific commands (e.g., `/build`, `/release-status`) work in their channels.
- `/help` shows all available commands for the current channel's agent.
- Bot performance is monitored via Grafana.

**Dependencies:** Phase 3 complete. Agents define their custom commands in the registry.

---

## 15. Diagrams

### Overall Architecture

```mermaid
graph TB
    subgraph teams["Microsoft Teams"]
        direction TB
        TEAM["Agent Workforce Team"]
        CH_J["#agent-josephine"]
        CH_A["#agent-ada"]
        CH_C["#agent-curie"]
        CH_F["#agent-faraday"]
        CH_T["#agent-tesla"]
        CH_H["#agent-hedy"]
        CH_L["#agent-linus"]
        CH_B["#agent-babbage"]
        CH_LN["#agent-linnaeus"]
        CH_HE["#agent-herodotus"]
        CH_HY["#agent-hemingway"]
        CH_N["#agent-nightingale"]
        CH_D["#agent-drucker"]
        CH_G["#agent-gantt"]
        CH_BR["#agent-brooks"]
    end

    subgraph cn_ai_01["cn-ai-01"]
        NX["Nginx (TLS)"]
        BOT["Teams Bot Service"]
        PG[(PostgreSQL)]
        RD[(Redis)]
        REG["Agent Registry"]
    end

    subgraph cn_ai_hosts["cn-ai-01 / cn-ai-02 / cn-ai-03"]
        J["Josephine API"]
        A["Ada API"]
        C["Curie API"]
        F["Faraday API"]
        T["Tesla API"]
        HE["Hedy API"]
        LI["Linus API"]
        BA["Babbage API"]
        LN["Linnaeus API"]
        HR["Herodotus API"]
        HY["Hemingway API"]
        NI["Nightingale API"]
        DR["Drucker API"]
        GA["Gantt API"]
        BR["Brooks API"]
    end

    TEAM --> CH_J & CH_A & CH_C & CH_F & CH_T & CH_H & CH_L & CH_B & CH_LN & CH_HE & CH_HY & CH_N & CH_D & CH_G & CH_BR
    CH_J & CH_A & CH_C & CH_F & CH_T & CH_H & CH_L & CH_B & CH_LN & CH_HE & CH_HY & CH_N & CH_D & CH_G & CH_BR -->|webhook| NX
    NX --> BOT
    BOT --> REG
    BOT --> PG
    BOT --> RD
    BOT -->|route commands| J & A & C & F & T & HE & LI & BA & LN & HR & HY & NI & DR & GA & BR
    J & A & C & F & T & HE & LI & BA & LN & HR & HY & NI & DR & GA & BR -->|notify/approve| BOT
```

### Standard Command Flow

```mermaid
sequenceDiagram
    participant U as User
    participant T as Teams
    participant NX as Nginx
    participant BOT as Teams Bot
    participant RD as Redis
    participant REG as Agent Registry
    participant API as Agent API
    participant PG as PostgreSQL

    U->>T: /stats in #agent-josephine
    T->>NX: POST /api/messages (webhook)
    NX->>BOT: Forward (TLS terminated)
    BOT->>BOT: Validate JWT signature
    BOT->>RD: Check rate limit
    RD-->>BOT: OK
    BOT->>BOT: Parse command: /stats
    BOT->>REG: Lookup channel_id
    REG-->>BOT: agent_id=josephine, url=http://cn-ai-01:8101
    BOT->>API: GET http://cn-ai-01:8101/v1/status/stats
    API-->>BOT: JSON stats response
    BOT->>BOT: Render Stats Adaptive Card
    BOT->>T: Reply with Adaptive Card (threaded)
    T-->>U: Formatted stats card
    BOT->>PG: INSERT audit_log
```

### Approval Workflow

```mermaid
sequenceDiagram
    participant A as Hedy (Agent)
    participant BOT as Teams Bot
    participant PG as PostgreSQL
    participant T as Teams
    participant U as Release Approver
    participant SCH as Timeout Scheduler

    Note over A: Build BLD-4519 passes qa gates
    A->>BOT: POST /v1/bot/request-approval
    BOT->>PG: INSERT approval_request (pending)
    BOT->>T: Post Approval Card to #agent-hedy
    T-->>U: Approval card with Approve/Reject buttons
    BOT->>PG: INSERT audit_log (approval_requested)

    alt Approved within timeout
        U->>T: Clicks "Approve" + comment
        T->>BOT: Action.Submit payload
        BOT->>BOT: Verify user identity and role
        BOT->>PG: UPDATE approval_request (approved)
        BOT->>A: POST /v1/approvals/{id}/respond (approved)
        A-->>BOT: ACK
        BOT->>T: Post confirmation (threaded reply)
        BOT->>PG: INSERT audit_log (approval_approved)
    else Escalation triggered
        SCH->>PG: Query pending approvals past escalation time
        PG-->>SCH: APR-20250315-001 (12h elapsed)
        SCH->>PG: UPDATE approval_request (escalated)
        SCH->>T: Re-post with ESCALATED banner, @mention release-leads
        SCH->>PG: INSERT audit_log (approval_escalated)
    else Timeout expired
        SCH->>PG: Query pending approvals past timeout
        PG-->>SCH: APR-20250315-001 (24h elapsed)
        SCH->>PG: UPDATE approval_request (expired)
        SCH->>A: POST /v1/approvals/{id}/expired
        SCH->>T: Post expiry notice (threaded reply)
        SCH->>PG: INSERT audit_log (approval_expired)
    end
```

### Input Request Workflow

```mermaid
sequenceDiagram
    participant A as Nightingale (Agent)
    participant BOT as Teams Bot
    participant PG as PostgreSQL
    participant T as Teams
    participant U as Engineer

    Note over A: Investigating BUG-2341, needs environment details
    A->>BOT: POST /v1/bot/request-input
    BOT->>PG: INSERT input_request (pending)
    BOT->>BOT: Generate form card from field schema
    BOT->>T: Post Input Request Card to #agent-nightingale
    T-->>U: Form card with fields and Submit button
    BOT->>PG: INSERT audit_log (input_requested)

    alt User submits input
        U->>T: Fills form, clicks "Submit"
        T->>BOT: Action.Submit payload with field values
        BOT->>BOT: Validate required fields
        BOT->>PG: UPDATE input_request (received)
        BOT->>A: POST /v1/input/{id}/respond (field values)
        A-->>BOT: ACK
        BOT->>T: Post confirmation (threaded reply)
        BOT->>PG: INSERT audit_log (input_received)
    else User skips
        U->>T: Clicks "Skip / Cannot Provide"
        T->>BOT: Action.Submit payload with skipped=true
        BOT->>PG: UPDATE input_request (skipped)
        BOT->>A: POST /v1/input/{id}/respond (skipped)
        A-->>BOT: ACK (agent proceeds with available info)
        BOT->>T: Post skip confirmation (threaded reply)
    end
```

---

*Teams Bot Framework Specification -- Cornelis Networks AI Agent Workforce*
