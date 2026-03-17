#!/usr/bin/env python3
"""
Publish the Teams Bot Framework spec to Confluence as a legacy editor page.
Converts the Markdown to Confluence storage format XHTML and creates the page
as a child of the AI Agent Workforce page (ID: 656572464).
"""
import sys
sys.path.insert(0, '/Users/johnmacdonald/code/other/jira')
from confluence_utils import connect_to_confluence
import html


def build_body():
    """Build the full Confluence storage format XHTML body."""
    parts = []

    # Back link
    parts.append(
        '<p><ac:link><ri:page ri:content-title="AI Agent Workforce" />'
        '<ac:plain-text-link-body><![CDATA[Back to AI Agent Workforce]]>'
        '</ac:plain-text-link-body></ac:link></p>'
    )

    # Table of Contents macro
    parts.append(
        '<ac:structured-macro ac:name="toc">'
        '<ac:parameter ac:name="maxLevel">2</ac:parameter>'
        '</ac:structured-macro>'
    )

    # Info panel
    parts.append(
        '<ac:structured-macro ac:name="info">'
        '<ac:rich-text-body><p>This document specifies the generic Microsoft Teams Bot Framework '
        'that serves as the unified human interface for all 15 AI agents in the Cornelis Networks '
        'Agent Workforce.</p></ac:rich-text-body></ac:structured-macro>'
    )

    parts.append('<hr />')

    # ==================== Section 1: Overview ====================
    parts.append('<h2>1. Overview</h2>')

    parts.append('<h3>What This Is</h3>')
    parts.append(
        '<p>The Teams Bot Framework is a single, generic bot service that provides the human '
        'interface for all 15 AI agents in the Cornelis Networks Agent Workforce. Each agent has '
        'a dedicated Teams channel (<code>#agent-{name}</code>) within the &quot;Agent Workforce&quot; '
        'team. The bot receives messages from all 15 channels, routes them to the correct agent API, '
        'and posts responses back.</p>'
    )

    parts.append('<h3>One Bot, One Deployment, 15 Channels</h3>')
    parts.append(
        '<p>There is exactly one bot service deployed. It is not 15 separate bots. The bot determines '
        'which agent to interact with based on the channel where the message was posted. Channel-to-agent '
        'mapping is maintained in the Agent Registry.</p>'
    )

    # Channel-Agent-Zone table
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Channel</th><th>Agent</th><th>Zone</th></tr>'
    )
    channel_rows = [
        ('#agent-josephine', 'Josephine -- Build and Package', 'Execution Spine'),
        ('#agent-ada', 'Ada -- Test Planner', 'Execution Spine'),
        ('#agent-curie', 'Curie -- Test Generator', 'Execution Spine'),
        ('#agent-faraday', 'Faraday -- Test Executor', 'Execution Spine'),
        ('#agent-tesla', 'Tesla -- Environment Manager', 'Execution Spine'),
        ('#agent-hedy', 'Hedy -- Release Manager', 'Execution Spine'),
        ('#agent-linus', 'Linus -- Code Review', 'Execution Spine'),
        ('#agent-babbage', 'Babbage -- Version Manager', 'Intelligence and Knowledge'),
        ('#agent-linnaeus', 'Linnaeus -- Traceability', 'Intelligence and Knowledge'),
        ('#agent-herodotus', 'Herodotus -- Knowledge Capture', 'Intelligence and Knowledge'),
        ('#agent-hypatia', 'Hypatia -- Documentation', 'Intelligence and Knowledge'),
        ('#agent-nightingale', 'Nightingale -- Bug Investigation', 'Intelligence and Knowledge'),
        ('#agent-drucker', 'Drucker -- Jira Coordinator', 'Intelligence and Knowledge'),
        ('#agent-gantt', 'Gantt -- Project Planner', 'Planning and Delivery'),
        ('#agent-brooks', 'Brooks -- Delivery Manager', 'Planning and Delivery'),
    ]
    for ch, agent, zone in channel_rows:
        parts.append(f'<tr><td><code>{html.escape(ch)}</code></td><td>{html.escape(agent)}</td><td>{html.escape(zone)}</td></tr>')
    parts.append('</tbody></table>')

    parts.append('<h3>Design Principles</h3>')
    parts.append('<ul>')
    parts.append('<li><strong>Generic framework</strong> -- The bot code is agent-agnostic. All agent-specific behavior comes from configuration in the Agent Registry, not from code branches.</li>')
    parts.append('<li><strong>Configuration over code</strong> -- Adding a new agent means adding a registry entry, not modifying bot source code.</li>')
    parts.append('<li><strong>Adaptive Cards for structure</strong> -- All bot output uses Microsoft Adaptive Cards for consistent, interactive formatting.</li>')
    parts.append('<li><strong>Stateless routing, stateful conversations</strong> -- The bot itself is stateless for routing decisions. Conversation state (threads, pending approvals) is persisted in PostgreSQL.</li>')
    parts.append('<li><strong>Agents push, humans pull</strong> -- Agents proactively push notifications to their channels. Humans pull status on demand via commands.</li>')
    parts.append('</ul>')

    parts.append('<hr />')

    # ==================== Section 2: Architecture ====================
    parts.append('<h2>2. Architecture</h2>')

    parts.append('<h3>Message Flow</h3>')
    parts.append(
        '<p>The following sequence diagram shows the end-to-end flow when a user posts a command in an agent channel:</p>'
    )
    parts.append(
        '<ac:structured-macro ac:name="note">'
        '<ac:rich-text-body><p>This section contains Mermaid sequence and component diagrams in the source Markdown file. '
        'See the source file <code>docs/reference/TEAMS_BOT_FRAMEWORK.md</code> for the full diagrams.</p>'
        '</ac:rich-text-body></ac:structured-macro>'
    )
    parts.append(
        '<p>The message flow is: User posts command in Teams channel &rarr; Teams webhook &rarr; '
        'Bot Webhook Receiver &rarr; Redis rate limit check &rarr; Command Router parses command &rarr; '
        'Agent Registry lookup by channel_id &rarr; Agent API call &rarr; Card Renderer formats response &rarr; '
        'Reply posted to channel &rarr; Audit log written to PostgreSQL.</p>'
    )

    parts.append('<h3>Component Diagram</h3>')
    parts.append(
        '<p>The bot service consists of: Webhook Receiver, Message Poster, Command Router, Card Renderer, '
        'Thread Manager, and Approval Workflow Engine. It connects to the Agent Registry (15 agent configs), '
        'all 15 Agent APIs, PostgreSQL (conversation state, audit log, approval records), and Redis '
        '(rate limiting, session cache).</p>'
    )

    parts.append('<hr />')

    # ==================== Section 3: Agent Registry ====================
    parts.append('<h2>3. Agent Registry</h2>')

    parts.append('<h3>Registration Model</h3>')
    parts.append(
        '<p>Agents are registered via a YAML configuration file loaded at bot startup. The bot watches '
        'the file for changes and hot-reloads without restart. An optional REST endpoint allows runtime '
        'registration for development and testing.</p>'
    )
    parts.append('<p>Configuration file path: <code>/etc/teams-bot/agent-registry.yaml</code></p>')

    parts.append('<h3>Registry Schema</h3>')
    parts.append('<p>Each agent entry contains:</p>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Field</th><th>Type</th><th>Required</th><th>Description</th></tr>'
        '<tr><td><code>agent_id</code></td><td>string</td><td>Yes</td><td>Unique identifier. Lowercase, no spaces. Example: <code>josephine</code></td></tr>'
        '<tr><td><code>display_name</code></td><td>string</td><td>Yes</td><td>Human-readable name shown in cards. Example: <code>Josephine</code></td></tr>'
        '<tr><td><code>role</code></td><td>string</td><td>Yes</td><td>Short role description. Example: <code>Build and Package</code></td></tr>'
        '<tr><td><code>channel_id</code></td><td>string</td><td>Yes</td><td>Teams channel ID (from Teams admin). Maps inbound messages to this agent.</td></tr>'
        '<tr><td><code>api_base_url</code></td><td>string</td><td>Yes</td><td>Base URL for the agent\'s REST API. Example: <code>http://cn-ai-01:8101</code></td></tr>'
        '<tr><td><code>icon_url</code></td><td>string</td><td>No</td><td>URL to agent avatar image for card headers.</td></tr>'
        '<tr><td><code>description</code></td><td>string</td><td>Yes</td><td>One-line description of what the agent does.</td></tr>'
        '<tr><td><code>zone</code></td><td>string</td><td>Yes</td><td>Operational zone: <code>execution_spine</code>, <code>intelligence_knowledge</code>, or <code>planning_delivery</code></td></tr>'
        '<tr><td><code>approval_types</code></td><td>list[string]</td><td>No</td><td>Types of approvals this agent can request. Empty list if none.</td></tr>'
        '<tr><td><code>custom_commands</code></td><td>list[object]</td><td>No</td><td>Agent-specific commands beyond the 6 standard commands.</td></tr>'
        '<tr><td><code>health_endpoint</code></td><td>string</td><td>No</td><td>Override health check path. Default: <code>/v1/health</code></td></tr>'
        '<tr><td><code>timeout_seconds</code></td><td>integer</td><td>No</td><td>API call timeout. Default: <code>30</code></td></tr>'
        '</tbody></table>'
    )

    parts.append('<h3>Custom Command Schema</h3>')
    parts.append('<p>Each entry in <code>custom_commands</code>:</p>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Field</th><th>Type</th><th>Description</th></tr>'
        '<tr><td><code>command</code></td><td>string</td><td>Command string including leading slash. Example: <code>/build</code></td></tr>'
        '<tr><td><code>description</code></td><td>string</td><td>Help text shown in <code>/help</code> output.</td></tr>'
        '<tr><td><code>api_method</code></td><td>string</td><td>HTTP method: <code>GET</code> or <code>POST</code></td></tr>'
        '<tr><td><code>api_path</code></td><td>string</td><td>Agent API path to call. Example: <code>/v1/build-jobs</code></td></tr>'
        '<tr><td><code>parameters</code></td><td>list[object]</td><td>Expected parameters with name, type, required flag.</td></tr>'
        '</tbody></table>'
    )

    parts.append('<h3>Example Registry Entry</h3>')

    registry_yaml = r'''agents:
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
    timeout_seconds: 60'''

    parts.append(_code_macro('yaml', registry_yaml))

    parts.append('<hr />')

    # ==================== Section 4: Message Types ====================
    parts.append('<h2>4. Message Types</h2>')

    parts.append('<h3>Outbound Messages (Bot to Channel)</h3>')

    # 4.1 Activity Notification
    parts.append('<h4>4.1 Activity Notification</h4>')
    parts.append('<p>Posted when an agent completes a significant action. Top-level message in the channel.</p>')
    parts.append(_code_macro('json', _activity_notification_json()))

    # 4.2 Decision Notification
    parts.append('<h4>4.2 Decision Notification</h4>')
    parts.append('<p>Posted when an agent makes a non-trivial decision. Includes rationale for transparency.</p>')
    parts.append(_code_macro('json', _decision_notification_json()))

    # 4.3 Approval Request
    parts.append('<h4>4.3 Approval Request</h4>')
    parts.append('<p>Posted when an agent needs human authorization for an irreversible action. Includes context and approve/reject buttons.</p>')
    parts.append(_code_macro('json', _approval_request_json()))

    # 4.4 Input Request
    parts.append('<h4>4.4 Input Request</h4>')
    parts.append('<p>Posted when an agent needs structured information from a human to proceed.</p>')
    parts.append(_code_macro('json', _input_request_json()))

    # 4.5 Error Alert
    parts.append('<h4>4.5 Error Alert</h4>')
    parts.append('<p>Posted when an agent encounters a failure or anomaly that requires human attention.</p>')
    parts.append(_code_macro('json', _error_alert_json()))

    parts.append('<p>Severity mapping:</p>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Severity</th><th>Badge Text</th><th>Color</th><th>Style</th></tr>'
        '<tr><td><code>critical</code></td><td><code>CRITICAL</code></td><td>Attention (red)</td><td><code>attention</code></td></tr>'
        '<tr><td><code>error</code></td><td><code>ERROR</code></td><td>Warning (yellow)</td><td><code>warning</code></td></tr>'
        '<tr><td><code>warning</code></td><td><code>WARNING</code></td><td>Accent (blue)</td><td><code>accent</code></td></tr>'
        '<tr><td><code>info</code></td><td><code>INFO</code></td><td>Default</td><td><code>default</code></td></tr>'
        '</tbody></table>'
    )

    # 4.6 Command Response
    parts.append('<h4>4.6 Command Response</h4>')
    parts.append('<p>Generic formatted response to any standard command. Structure varies by command; see Section 5 for per-command layouts.</p>')

    # Inbound Messages
    parts.append('<h3>Inbound Messages (User to Bot)</h3>')

    parts.append('<h4>Standard Commands</h4>')
    parts.append('<p>Messages beginning with <code>/</code> are parsed as commands. The bot recognizes the 6 standard commands (available in every channel) plus any <code>custom_commands</code> defined in the agent\'s registry entry.</p>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Command</th><th>Pattern</th><th>Description</th></tr>'
        '<tr><td><code>/token-status</code></td><td>Exact match</td><td>Token usage summary</td></tr>'
        '<tr><td><code>/decision-tree</code></td><td>Exact match</td><td>Recent decisions with rationale</td></tr>'
        '<tr><td><code>/why {decision-id}</code></td><td><code>/why</code> + space + ID</td><td>Deep dive into specific decision</td></tr>'
        '<tr><td><code>/stats</code></td><td>Exact match</td><td>Operational statistics</td></tr>'
        '<tr><td><code>/work-today</code></td><td>Exact match</td><td>Today\'s work summary</td></tr>'
        '<tr><td><code>/busy</code></td><td>Exact match</td><td>Current load status</td></tr>'
        '<tr><td><code>/help</code></td><td>Exact match</td><td>List available commands for this agent</td></tr>'
        '</tbody></table>'
    )

    parts.append('<h4>Approval Responses</h4>')
    parts.append('<p><code>Action.Submit</code> payloads from Adaptive Card button clicks. The bot identifies these by the <code>action</code> field in the submitted data:</p>')
    parts.append(_code_macro('json', '''{
  "action": "approval_response",
  "approval_id": "APR-2024-001",
  "decision": "approved",
  "agent_id": "hedy",
  "approval_comment": "Looks good. Test coverage is sufficient."
}'''))

    parts.append('<h4>Input Responses</h4>')
    parts.append('<p><code>Action.Submit</code> payloads from input request form submissions:</p>')
    parts.append(_code_macro('json', '''{
  "action": "input_response",
  "request_id": "INP-2024-042",
  "agent_id": "nightingale",
  "field_1": "The crash occurs only on dual-rail configurations",
  "field_2": "hardware_specific"
}'''))

    parts.append('<h4>Free-Text Queries</h4>')
    parts.append('<p>Any message that does not start with <code>/</code> and is not a card submission is treated as a free-text query. The bot forwards it to the agent\'s <code>/v1/query</code> endpoint.</p>')
    parts.append('<p>Example: A user posts <code>status of build BLD-1234</code> in <code>#agent-josephine</code>. The bot sends:</p>')
    parts.append(_code_macro('http', '''POST http://cn-ai-01:8101/v1/query
Content-Type: application/json

{
  "query": "status of build BLD-1234",
  "user_id": "john.macdonald@cornelisnetworks.com",
  "channel_id": "19:abc123def456@thread.tacv2",
  "thread_id": null
}'''))

    parts.append('<hr />')

    # ==================== Section 5: Standard Commands ====================
    parts.append('<h2>5. Standard Commands</h2>')
    parts.append('<p>All 15 agents expose the same 6 standard commands via their REST APIs. The bot routes each command to the corresponding agent endpoint and renders the response as an Adaptive Card.</p>')

    # 5.1 /token-status
    parts.append('<h3>5.1 /token-status</h3>')
    parts.append('<p><strong>Purpose:</strong> Show token usage -- today, cumulative, cost, and efficiency ratio.</p>')
    parts.append('<p><strong>Routing:</strong></p>')
    parts.append(_code_macro('', 'GET {api_base_url}/v1/status/tokens'))
    parts.append('<p><strong>Example Request:</strong></p>')
    parts.append('<p>User posts <code>/token-status</code> in <code>#agent-josephine</code>.</p>')
    parts.append(_code_macro('http', 'GET http://cn-ai-01:8101/v1/status/tokens'))
    parts.append('<p><strong>Example Response (from agent API):</strong></p>')
    parts.append(_code_macro('json', '''{
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
}'''))
    parts.append('<p><strong>Adaptive Card Layout:</strong> Rendered using the Token Status Card template (Section 6.7). Shows usage bars for today and cumulative, cost figures, and efficiency ratio.</p>')

    # 5.2 /decision-tree
    parts.append('<h3>5.2 /decision-tree</h3>')
    parts.append('<p><strong>Purpose:</strong> Show recent decisions with inputs, candidates, outcomes, and rationale.</p>')
    parts.append('<p><strong>Routing:</strong></p>')
    parts.append(_code_macro('', 'GET {api_base_url}/v1/status/decisions'))
    parts.append('<p><strong>Example Request:</strong></p>')
    parts.append('<p>User posts <code>/decision-tree</code> in <code>#agent-hedy</code>.</p>')
    parts.append(_code_macro('http', 'GET http://cn-ai-02:8106/v1/status/decisions'))
    parts.append('<p><strong>Example Response:</strong></p>')
    parts.append(_code_macro('json', '''{
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
}'''))
    parts.append('<p><strong>Adaptive Card Layout:</strong> Rendered using the Decision Card template (Section 6.2). Each decision is a collapsible section showing title, outcome, and rationale.</p>')

    # 5.3 /why {decision-id}
    parts.append('<h3>5.3 /why {decision-id}</h3>')
    parts.append('<p><strong>Purpose:</strong> Deep dive into a specific decision\'s full reasoning chain.</p>')
    parts.append('<p><strong>Routing:</strong></p>')
    parts.append(_code_macro('', 'GET {api_base_url}/v1/status/decisions/{decision_id}'))
    parts.append('<p><strong>Example Request:</strong></p>')
    parts.append('<p>User posts <code>/why DEC-hedy-20250315-001</code> in <code>#agent-hedy</code>.</p>')
    parts.append(_code_macro('http', 'GET http://cn-ai-02:8106/v1/status/decisions/DEC-hedy-20250315-001'))
    parts.append('<p><strong>Example Response:</strong></p>')
    parts.append(_code_macro('json', '''{
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
}'''))
    parts.append('<p><strong>Adaptive Card Layout:</strong> Full decision detail card with expandable sections for inputs, alternatives, rationale, and follow-up actions.</p>')

    # 5.4 /stats
    parts.append('<h3>5.4 /stats</h3>')
    parts.append('<p><strong>Purpose:</strong> Operational statistics -- uptime, success/failure rates, latency, queue depth, error trends.</p>')
    parts.append('<p><strong>Routing:</strong></p>')
    parts.append(_code_macro('', 'GET {api_base_url}/v1/status/stats'))
    parts.append('<p><strong>Example Request:</strong></p>')
    parts.append('<p>User posts <code>/stats</code> in <code>#agent-josephine</code>.</p>')
    parts.append(_code_macro('http', 'GET http://cn-ai-01:8101/v1/status/stats'))
    parts.append('<p><strong>Example Response:</strong></p>')
    parts.append(_code_macro('json', '''{
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
}'''))
    parts.append('<p><strong>Adaptive Card Layout:</strong> Rendered using the Stats Card template (Section 6.6). Metrics table with color-coded success rate and trend indicators.</p>')

    # 5.5 /work-today
    parts.append('<h3>5.5 /work-today</h3>')
    parts.append('<p><strong>Purpose:</strong> Summary of today\'s work -- jobs processed, outcomes, notable events.</p>')
    parts.append('<p><strong>Routing:</strong></p>')
    parts.append(_code_macro('', 'GET {api_base_url}/v1/status/work-summary'))
    parts.append('<p><strong>Example Request:</strong></p>')
    parts.append('<p>User posts <code>/work-today</code> in <code>#agent-faraday</code>.</p>')
    parts.append(_code_macro('http', 'GET http://cn-ai-02:8104/v1/status/work-summary'))
    parts.append('<p><strong>Example Response:</strong></p>')
    parts.append(_code_macro('json', '''{
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
}'''))
    parts.append('<p><strong>Adaptive Card Layout:</strong> Rendered using the Work Summary Card template (Section 6.8). Chronological list of work items with status badges.</p>')

    # 5.6 /busy
    parts.append('<h3>5.6 /busy</h3>')
    parts.append('<p><strong>Purpose:</strong> Current load status -- is the agent idle, working, busy, or overloaded?</p>')
    parts.append('<p><strong>Routing:</strong></p>')
    parts.append(_code_macro('', 'GET {api_base_url}/v1/status/load'))
    parts.append('<p><strong>Example Request:</strong></p>')
    parts.append('<p>User posts <code>/busy</code> in <code>#agent-tesla</code>.</p>')
    parts.append(_code_macro('http', 'GET http://cn-ai-02:8105/v1/status/load'))
    parts.append('<p><strong>Example Response:</strong></p>')
    parts.append(_code_macro('json', '''{
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
}'''))
    parts.append('<p><strong>Adaptive Card Layout:</strong> Compact card with load indicator (color-coded), utilization bar, and current work list.</p>')
    parts.append('<p>Load status color mapping:</p>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Status</th><th>Color</th><th>Threshold</th></tr>'
        '<tr><td><code>idle</code></td><td>Good (green)</td><td>0% utilization</td></tr>'
        '<tr><td><code>working</code></td><td>Default</td><td>1-50% utilization</td></tr>'
        '<tr><td><code>busy</code></td><td>Warning (yellow)</td><td>51-85% utilization</td></tr>'
        '<tr><td><code>overloaded</code></td><td>Attention (red)</td><td>&gt;85% utilization</td></tr>'
        '</tbody></table>'
    )

    parts.append('<hr />')

    # ==================== Section 6: Adaptive Card Templates ====================
    parts.append('<h2>6. Adaptive Card Templates</h2>')
    parts.append('<p>All bot output uses reusable Adaptive Card templates. Templates are parameterized with <code>${variable}</code> placeholders that the Card Renderer fills from agent API responses.</p>')

    # 6.1 Activity Card
    parts.append('<h3>6.1 Activity Card</h3>')
    parts.append('<p>Used for: Activity notifications (agent completed an action).</p>')
    parts.append(_code_macro('json', _activity_card_template_json()))

    # 6.2 Decision Card
    parts.append('<h3>6.2 Decision Card</h3>')
    parts.append('<p>Used for: Decision notifications and <code>/decision-tree</code> responses. Supports expandable sections via <code>Action.ShowCard</code>.</p>')
    parts.append(_code_macro('json', _decision_card_template_json()))

    # 6.3 Approval Card
    parts.append('<h3>6.3 Approval Card</h3>')
    parts.append('<p>Used for: Approval requests. See Section 4.3 for the full JSON. Key design points:</p>')
    parts.append('<ul>')
    parts.append('<li>Warning-styled header container for visual urgency</li>')
    parts.append('<li>Evidence summary in an emphasis container</li>')
    parts.append('<li>Comment field (required for rejections, optional for approvals)</li>')
    parts.append('<li>Approve (positive style) and Reject (destructive style) buttons</li>')
    parts.append('<li>Expiry time displayed prominently</li>')
    parts.append('<li>Approval ID for audit trail</li>')
    parts.append('</ul>')

    # 6.4 Input Request Card
    parts.append('<h3>6.4 Input Request Card</h3>')
    parts.append('<p>Used for: Structured input requests. See Section 4.4 for the full JSON. Key design points:</p>')
    parts.append('<ul>')
    parts.append('<li>Dynamic form fields generated from the agent\'s input schema</li>')
    parts.append('<li>Supported input types: <code>Input.Text</code>, <code>Input.ChoiceSet</code>, <code>Input.Number</code>, <code>Input.Date</code>, <code>Input.Toggle</code></li>')
    parts.append('<li>Submit and Skip buttons</li>')
    parts.append('<li>Deadline displayed for time-sensitive requests</li>')
    parts.append('</ul>')

    # 6.5 Error Alert Card
    parts.append('<h3>6.5 Error Alert Card</h3>')
    parts.append('<p>Used for: Error and anomaly alerts. See Section 4.5 for the full JSON. Key design points:</p>')
    parts.append('<ul>')
    parts.append('<li>Severity-colored header (critical=red, error=yellow, warning=blue, info=default)</li>')
    parts.append('<li>Error code and correlation ID for debugging</li>')
    parts.append('<li>Suggested actions section</li>')
    parts.append('<li>Link to Grafana dashboard for the agent (if configured)</li>')
    parts.append('</ul>')

    # 6.6 Stats Card
    parts.append('<h3>6.6 Stats Card</h3>')
    parts.append('<p>Used for: <code>/stats</code> command responses.</p>')
    parts.append(_code_macro('json', _stats_card_template_json()))

    # 6.7 Token Status Card
    parts.append('<h3>6.7 Token Status Card</h3>')
    parts.append('<p>Used for: <code>/token-status</code> command responses.</p>')
    parts.append(_code_macro('json', _token_status_card_template_json()))

    # 6.8 Work Summary Card
    parts.append('<h3>6.8 Work Summary Card</h3>')
    parts.append('<p>Used for: <code>/work-today</code> command responses.</p>')
    parts.append(_code_macro('json', _work_summary_card_template_json()))

    parts.append('<hr />')

    # ==================== Section 7: Command Routing ====================
    parts.append('<h2>7. Command Routing</h2>')

    parts.append('<h3>Channel-to-Agent Resolution</h3>')
    parts.append('<p>When the bot receives a message, it resolves the agent using this lookup chain:</p>')
    parts.append('<ol>')
    parts.append('<li>Extract <code>channel_id</code> from the Teams activity payload.</li>')
    parts.append('<li>Look up <code>channel_id</code> in the Agent Registry.</li>')
    parts.append('<li>If found, use the corresponding <code>agent_id</code> and <code>api_base_url</code>.</li>')
    parts.append('<li>If not found, reply with an error: &quot;This channel is not configured for any agent.&quot;</li>')
    parts.append('</ol>')
    parts.append('<p>The lookup is cached in Redis with a TTL of 300 seconds. Registry changes invalidate the cache.</p>')

    parts.append('<h3>Standard Command to API Endpoint Mapping</h3>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Command</th><th>HTTP Method</th><th>Agent API Endpoint</th><th>Notes</th></tr>'
        '<tr><td><code>/token-status</code></td><td>GET</td><td><code>/v1/status/tokens</code></td><td>No parameters</td></tr>'
        '<tr><td><code>/decision-tree</code></td><td>GET</td><td><code>/v1/status/decisions</code></td><td>Optional <code>?limit=N</code> (default 10)</td></tr>'
        '<tr><td><code>/why {id}</code></td><td>GET</td><td><code>/v1/status/decisions/{id}</code></td><td><code>{id}</code> extracted from message text</td></tr>'
        '<tr><td><code>/stats</code></td><td>GET</td><td><code>/v1/status/stats</code></td><td>Optional <code>?period=last_24h</code> (default)</td></tr>'
        '<tr><td><code>/work-today</code></td><td>GET</td><td><code>/v1/status/work-summary</code></td><td>No parameters</td></tr>'
        '<tr><td><code>/busy</code></td><td>GET</td><td><code>/v1/status/load</code></td><td>No parameters</td></tr>'
        '<tr><td><code>/help</code></td><td>N/A</td><td>Handled locally by bot</td><td>Returns standard + custom commands from registry</td></tr>'
        '</tbody></table>'
    )

    parts.append('<h3>Custom Command Routing</h3>')
    parts.append('<p>For commands defined in the agent\'s <code>custom_commands</code> registry entry:</p>')
    parts.append('<ol>')
    parts.append('<li>Parse the command name from the message.</li>')
    parts.append('<li>Match against <code>custom_commands[].command</code> for the resolved agent.</li>')
    parts.append('<li>Extract parameters from the message text (positional or named).</li>')
    parts.append('<li>Call <code>{api_base_url}{api_path}</code> with the specified <code>api_method</code>.</li>')
    parts.append('<li>Render the response using the appropriate card template.</li>')
    parts.append('</ol>')

    parts.append('<h3>Free-Text Query Handling</h3>')
    parts.append('<p>Messages that do not match any command pattern are forwarded as free-text queries:</p>')
    parts.append(_code_macro('', '''POST {api_base_url}/v1/query
Content-Type: application/json

{
  "query": "<user message text>",
  "user_id": "<teams user principal name>",
  "channel_id": "<teams channel id>",
  "thread_id": "<teams thread id or null>"
}'''))
    parts.append('<p>The agent processes the query and returns a structured response. The bot renders it as a text block or Adaptive Card depending on the response <code>content_type</code> field.</p>')

    parts.append('<h3>Error Handling</h3>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Scenario</th><th>Bot Behavior</th></tr>'
        '<tr><td>Agent API unreachable</td><td>Reply: &quot;Agent {name} is currently unreachable. Last healthy: {timestamp}. Check #ops-alerts.&quot;</td></tr>'
        '<tr><td>Agent API timeout (exceeds <code>timeout_seconds</code>)</td><td>Reply: &quot;Agent {name} did not respond within {timeout}s. The request may still be processing. Try <code>/busy</code> to check load.&quot;</td></tr>'
        '<tr><td>Agent API returns 4xx</td><td>Reply: &quot;Agent {name} returned an error: {status_code} -- {error_message}&quot;</td></tr>'
        '<tr><td>Agent API returns 5xx</td><td>Reply: &quot;Agent {name} encountered an internal error. Correlation ID: {id}. This has been logged.&quot;</td></tr>'
        '<tr><td>Unknown command</td><td>Reply: &quot;Unknown command: {command}. Type <code>/help</code> to see available commands.&quot;</td></tr>'
        '<tr><td>Rate limited</td><td>Reply: &quot;Rate limit exceeded for this channel. Please wait {retry_after}s.&quot;</td></tr>'
        '</tbody></table>'
    )
    parts.append('<p>All errors are logged to PostgreSQL with correlation_id, agent_id, error_code, and timestamp.</p>')

    parts.append('<hr />')

    # ==================== Section 8: Approval Workflow ====================
    parts.append('<h2>8. Approval Workflow</h2>')

    parts.append('<h3>Flow Overview</h3>')
    parts.append(
        '<ac:structured-macro ac:name="note">'
        '<ac:rich-text-body><p>This section contains Mermaid sequence diagrams in the source Markdown file. '
        'See <code>docs/reference/TEAMS_BOT_FRAMEWORK.md</code> for the full diagrams.</p>'
        '</ac:rich-text-body></ac:structured-macro>'
    )
    parts.append(
        '<p>The approval flow is: Agent calls <code>POST /v1/bot/request-approval</code> &rarr; '
        'Bot inserts approval_request (status=pending) in PostgreSQL &rarr; Bot posts Approval Card to channel &rarr; '
        'User clicks Approve/Reject &rarr; Bot verifies user authority &rarr; Bot updates approval_request &rarr; '
        'Bot notifies agent via <code>POST {api_base_url}/v1/approvals/{id}/respond</code> &rarr; '
        'Bot posts confirmation (threaded reply) &rarr; Audit log written.</p>'
    )

    parts.append('<h3>Approval Types by Agent</h3>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Agent</th><th>Approval Type</th><th>Description</th><th>Typical Approvers</th></tr>'
        '<tr><td><strong>Hedy</strong></td><td><code>release_promotion</code></td><td>Promote a build from one release stage to the next (sit to qa, qa to release)</td><td>Release Approvers</td></tr>'
        '<tr><td><strong>Linus</strong></td><td><code>review_policy_override</code></td><td>Override a review policy finding that the agent flagged as blocking</td><td>Engineers, Tech Leads</td></tr>'
        '<tr><td><strong>Linnaeus</strong></td><td><code>traceability_exception</code></td><td>Allow a release or build to proceed despite a traceability gap</td><td>Project Leads</td></tr>'
        '<tr><td><strong>Hypatia</strong></td><td><code>external_doc_publish</code></td><td>Publish documentation to an external-facing target</td><td>Documentation Owners, Engineering Managers</td></tr>'
        '</tbody></table>'
    )

    parts.append('<h3>Approval Request Payload</h3>')
    parts.append('<p>Agents call the bot\'s approval API with this payload:</p>')
    parts.append(_code_macro('json', '''{
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
}'''))

    parts.append('<h3>Approval Database Schema</h3>')
    parts.append(_code_macro('sql', '''CREATE TABLE approval_requests (
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
CREATE INDEX idx_approval_timeout ON approval_requests (timeout_at) WHERE status = 'pending';'''))

    parts.append('<h3>Timeout Handling</h3>')
    parts.append('<p>A background scheduler runs every 5 minutes and checks for expired approvals:</p>')
    parts.append('<ol>')
    parts.append('<li>Query: <code>SELECT * FROM approval_requests WHERE status = \'pending\' AND timeout_at &lt; NOW()</code></li>')
    parts.append('<li>For each expired approval:<ul>')
    parts.append('<li>If <code>escalation_config</code> is set and escalation has not yet occurred: Update status to <code>escalated</code>, re-post the approval card with an <code>ESCALATED</code> banner, @mention the escalation targets.</li>')
    parts.append('<li>If escalation already occurred or no escalation config: Update status to <code>expired</code>, post expiry notification to the channel, notify the agent via <code>POST {api_base_url}/v1/approvals/{id}/expired</code>.</li>')
    parts.append('</ul></li>')
    parts.append('</ol>')

    parts.append('<h3>Escalation Behavior</h3>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Time Elapsed</th><th>Action</th></tr>'
        '<tr><td>0h</td><td>Approval card posted to channel</td></tr>'
        '<tr><td><code>escalate_after_hours</code></td><td>Re-post with ESCALATED banner, @mention escalation targets</td></tr>'
        '<tr><td><code>timeout_hours</code></td><td>Mark expired, notify agent, post expiry notice</td></tr>'
        '</tbody></table>'
    )

    parts.append('<hr />')

    # ==================== Section 9: Thread Management ====================
    parts.append('<h2>9. Thread Management</h2>')

    parts.append('<h3>Threading Rules</h3>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Message Type</th><th>Threading Behavior</th></tr>'
        '<tr><td>Activity notification</td><td>Top-level message in channel</td></tr>'
        '<tr><td>Decision notification</td><td>Top-level message in channel</td></tr>'
        '<tr><td>Approval request</td><td>Top-level message in channel</td></tr>'
        '<tr><td>Approval response confirmation</td><td>Threaded reply to the approval request message</td></tr>'
        '<tr><td>Error alert</td><td>Top-level message in channel</td></tr>'
        '<tr><td>Command response</td><td>Threaded reply to the user\'s command message</td></tr>'
        '<tr><td>Free-text query response</td><td>Threaded reply to the user\'s query message</td></tr>'
        '<tr><td>Input request</td><td>Top-level message in channel</td></tr>'
        '<tr><td>Input response confirmation</td><td>Threaded reply to the input request message</td></tr>'
        '<tr><td>Escalation re-post</td><td>Threaded reply to the original approval message</td></tr>'
        '</tbody></table>'
    )

    parts.append('<h3>Conversation State Tracking</h3>')
    parts.append('<p>The bot tracks conversation state in PostgreSQL to maintain thread context and enable follow-up interactions.</p>')
    parts.append(_code_macro('sql', '''CREATE TABLE conversation_state (
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
CREATE INDEX idx_conv_agent ON conversation_state (agent_id);'''))

    parts.append('<h3>Message Deduplication</h3>')
    parts.append('<p>The bot deduplicates messages using a combination of:</p>')
    parts.append('<ol>')
    parts.append('<li><strong>Teams activity ID</strong> -- Each Teams message has a unique activity ID. The bot stores processed activity IDs in Redis with a 1-hour TTL.</li>')
    parts.append('<li><strong>Idempotency keys for outbound messages</strong> -- When agents call the bot\'s notification API, they include an <code>idempotency_key</code>. The bot checks Redis before posting. Duplicate keys within 1 hour are silently dropped.</li>')
    parts.append('<li><strong>Approval response deduplication</strong> -- Once an approval is responded to (approved/rejected), subsequent button clicks on the same card return a message: &quot;This approval has already been processed.&quot;</li>')
    parts.append('</ol>')
    parts.append(_code_macro('sql', '''CREATE TABLE processed_messages (
    activity_id   TEXT PRIMARY KEY,
    channel_id    TEXT NOT NULL,
    processed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Cleanup: DELETE FROM processed_messages WHERE processed_at < NOW() - INTERVAL '24 hours';'''))

    parts.append('<hr />')

    # ==================== Section 10: Teams App Manifest ====================
    parts.append('<h2>10. Teams App Manifest</h2>')

    parts.append('<h3>App Registration</h3>')
    parts.append('<p>The bot is registered as a single Azure AD application with a Bot Framework registration. It uses the Bot Framework SDK for Python to handle Teams webhook events.</p>')

    parts.append('<h3>Manifest Configuration</h3>')
    parts.append(_code_macro('json', '''{
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
}'''))

    parts.append('<h3>Required Permissions</h3>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Permission</th><th>Scope</th><th>Purpose</th></tr>'
        '<tr><td><code>ChannelMessage.Read.Group</code></td><td>Team</td><td>Read messages in agent channels</td></tr>'
        '<tr><td><code>ChannelMessage.Send</code></td><td>Team</td><td>Post responses and notifications</td></tr>'
        '<tr><td><code>TeamMember.Read.Group</code></td><td>Team</td><td>Verify user identity for approvals</td></tr>'
        '<tr><td><code>Files.Read.Group</code></td><td>Team</td><td>Not required (supportsFiles=false)</td></tr>'
        '</tbody></table>'
    )

    parts.append('<h3>Adaptive Card Schema Version</h3>')
    parts.append('<p>All cards use Adaptive Card schema version <strong>1.5</strong>, which is supported by Teams desktop, web, and mobile clients. This version supports <code>Action.ShowCard</code> for expandable sections, <code>Action.Submit</code> for button interactions, and all input types used in the templates.</p>')

    parts.append('<hr />')

    # ==================== Section 11: API Contract ====================
    parts.append('<h2>11. API Contract</h2>')
    parts.append('<p>The bot exposes a REST API that agents call to push notifications, request approvals, and request input. This is the agent-to-bot interface.</p>')
    parts.append('<p><strong>Base URL:</strong> <code>http://cn-ai-01:8200/v1/bot</code></p>')

    # 11.1
    parts.append('<h3>11.1 POST /v1/bot/notify</h3>')
    parts.append('<p>Agent sends a notification to its Teams channel.</p>')
    parts.append('<p><strong>Request:</strong></p>')
    parts.append(_code_macro('http', '''POST /v1/bot/notify
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
}'''))
    parts.append('<p><strong>Response:</strong></p>')
    parts.append(_code_macro('json', '''{
  "status": "sent",
  "message_id": "msg-20250315-xyz789",
  "channel_id": "19:abc123def456@thread.tacv2",
  "timestamp": "2025-03-15T14:30:00Z"
}'''))
    parts.append('<p><strong>Notification types:</strong> <code>activity</code>, <code>decision</code>, <code>error</code></p>')

    # 11.2
    parts.append('<h3>11.2 POST /v1/bot/request-approval</h3>')
    parts.append('<p>Agent requests human approval via an Adaptive Card.</p>')
    parts.append('<p><strong>Request:</strong></p>')
    parts.append(_code_macro('http', '''POST /v1/bot/request-approval
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
}'''))
    parts.append('<p><strong>Response:</strong></p>')
    parts.append(_code_macro('json', '''{
  "approval_id": "APR-20250315-001",
  "status": "pending",
  "message_id": "msg-20250315-apr001",
  "channel_id": "19:xyz789ghi012@thread.tacv2",
  "timeout_at": "2025-03-16T14:30:00Z",
  "timestamp": "2025-03-15T14:30:00Z"
}'''))

    # 11.3
    parts.append('<h3>11.3 POST /v1/bot/request-input</h3>')
    parts.append('<p>Agent requests structured input from a human.</p>')
    parts.append('<p><strong>Request:</strong></p>')
    parts.append(_code_macro('http', '''POST /v1/bot/request-input
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
}'''))
    parts.append('<p><strong>Response:</strong></p>')
    parts.append(_code_macro('json', '''{
  "request_id": "INP-20250315-042",
  "status": "pending",
  "message_id": "msg-20250315-inp042",
  "channel_id": "19:nightingale-channel@thread.tacv2",
  "deadline": "2025-03-16T12:00:00Z",
  "timestamp": "2025-03-15T14:30:00Z"
}'''))

    # 11.4
    parts.append('<h3>11.4 POST /v1/bot/alert</h3>')
    parts.append('<p>Agent sends an error alert to its channel.</p>')
    parts.append('<p><strong>Request:</strong></p>')
    parts.append(_code_macro('http', '''POST /v1/bot/alert
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
  "suggested_actions": "1. Check bld-host-01 SSH connectivity.\\n2. Verify Docker daemon is running.\\n3. If unrecoverable, drain worker and reassign jobs."
}'''))
    parts.append('<p><strong>Response:</strong></p>')
    parts.append(_code_macro('json', '''{
  "status": "sent",
  "message_id": "msg-20250315-alert001",
  "channel_id": "19:abc123def456@thread.tacv2",
  "timestamp": "2025-03-15T14:30:00Z"
}'''))

    # 11.5
    parts.append('<h3>11.5 GET /v1/bot/approvals/{id}</h3>')
    parts.append('<p>Check the status of a pending approval.</p>')
    parts.append('<p><strong>Request:</strong></p>')
    parts.append(_code_macro('http', '''GET /v1/bot/approvals/APR-20250315-001
Authorization: Bearer <agent_service_token>'''))
    parts.append('<p><strong>Response:</strong></p>')
    parts.append(_code_macro('json', '''{
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
}'''))

    parts.append('<hr />')

    # ==================== Section 12: Security ====================
    parts.append('<h2>12. Security</h2>')

    parts.append('<h3>Bot Authentication with Teams</h3>')
    parts.append('<p>The bot authenticates with Microsoft Teams using Azure AD app registration:</p>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Component</th><th>Value</th></tr>'
        '<tr><td>Azure AD App ID</td><td>Registered in Cornelis Networks Azure AD tenant</td></tr>'
        '<tr><td>App Secret</td><td>Stored in Docker secrets, rotated quarterly</td></tr>'
        '<tr><td>Bot Framework Registration</td><td>Azure Bot Service registration linked to the App ID</td></tr>'
        '<tr><td>Webhook Validation</td><td>Bot Framework SDK validates inbound webhook signatures using the app secret</td></tr>'
        '<tr><td>Token Endpoint</td><td><code>https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token</code></td></tr>'
        '</tbody></table>'
    )
    parts.append('<p>The bot validates every inbound webhook request by verifying the JWT bearer token in the <code>Authorization</code> header against Microsoft\'s public signing keys. Requests with invalid or missing tokens are rejected with HTTP 401.</p>')

    parts.append('<h3>Agent-to-Bot Authentication</h3>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Mechanism</th><th>Details</th></tr>'
        '<tr><td>Auth Method</td><td>Bearer token (JWT) issued per agent service principal</td></tr>'
        '<tr><td>Token Issuer</td><td>Internal token service or Azure AD app-to-app auth</td></tr>'
        '<tr><td>Token Lifetime</td><td>1 hour, auto-refreshed by agent SDK</td></tr>'
        '<tr><td>API Key Fallback</td><td>Static API key per agent for development environments only</td></tr>'
        '<tr><td>Header</td><td><code>Authorization: Bearer &lt;token&gt;</code></td></tr>'
        '</tbody></table>'
    )
    parts.append('<p>Each agent has a unique service principal. The bot validates the token and extracts the <code>agent_id</code> claim. The <code>agent_id</code> in the token must match the <code>agent_id</code> in the request body.</p>')

    parts.append('<h3>User Identity Verification</h3>')
    parts.append('<p>For approval and input responses, the bot verifies the user\'s identity:</p>')
    parts.append('<ol>')
    parts.append('<li>Extract the user\'s Azure AD object ID and UPN from the Teams activity payload.</li>')
    parts.append('<li>Verify the user is a member of the &quot;Agent Workforce&quot; team.</li>')
    parts.append('<li>For approvals, optionally verify the user has the required role (e.g., &quot;Release Approver&quot;) via Azure AD group membership.</li>')
    parts.append('<li>Record the verified user identity in the approval/input response record.</li>')
    parts.append('</ol>')

    parts.append('<h3>Audit Trail</h3>')
    parts.append('<p>Every interaction is logged to the <code>audit_log</code> table:</p>')
    parts.append(_code_macro('sql', '''CREATE TABLE audit_log (
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
CREATE INDEX idx_audit_correlation ON audit_log (correlation_id);'''))

    parts.append('<p>Logged actions include:</p>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Action</th><th>Description</th></tr>'
        '<tr><td><code>command_received</code></td><td>User issued a standard or custom command</td></tr>'
        '<tr><td><code>command_response_sent</code></td><td>Bot posted a command response</td></tr>'
        '<tr><td><code>query_received</code></td><td>User posted a free-text query</td></tr>'
        '<tr><td><code>query_response_sent</code></td><td>Bot posted a query response</td></tr>'
        '<tr><td><code>approval_requested</code></td><td>Agent requested an approval</td></tr>'
        '<tr><td><code>approval_approved</code></td><td>User approved a request</td></tr>'
        '<tr><td><code>approval_rejected</code></td><td>User rejected a request</td></tr>'
        '<tr><td><code>approval_expired</code></td><td>Approval timed out</td></tr>'
        '<tr><td><code>approval_escalated</code></td><td>Approval escalated to additional approvers</td></tr>'
        '<tr><td><code>input_requested</code></td><td>Agent requested human input</td></tr>'
        '<tr><td><code>input_received</code></td><td>User submitted input</td></tr>'
        '<tr><td><code>notification_sent</code></td><td>Agent sent a notification</td></tr>'
        '<tr><td><code>alert_sent</code></td><td>Agent sent an error alert</td></tr>'
        '<tr><td><code>error</code></td><td>Bot encountered an error processing a request</td></tr>'
        '</tbody></table>'
    )

    parts.append('<h3>Rate Limiting</h3>')
    parts.append('<p>Rate limits are enforced per channel using Redis sliding window counters:</p>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Scope</th><th>Limit</th><th>Window</th></tr>'
        '<tr><td>Inbound commands per channel</td><td>30</td><td>1 minute</td></tr>'
        '<tr><td>Inbound commands per user per channel</td><td>10</td><td>1 minute</td></tr>'
        '<tr><td>Agent notifications per channel</td><td>60</td><td>1 minute</td></tr>'
        '<tr><td>Agent approval requests per channel</td><td>10</td><td>1 hour</td></tr>'
        '</tbody></table>'
    )
    parts.append('<p>When a rate limit is exceeded, the bot returns a message indicating the limit and retry-after time. Agent API calls receive HTTP 429 with a <code>Retry-After</code> header.</p>')

    parts.append('<hr />')

    # ==================== Section 13: Deployment ====================
    parts.append('<h2>13. Deployment</h2>')

    parts.append('<h3>Docker Container</h3>')
    parts.append('<p>The bot runs as a single Docker container within the agent platform\'s Docker Compose stack on <code>cn-ai-01</code>.</p>')
    parts.append(_code_macro('yaml', '''# docker-compose.teams-bot.yaml
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
        tag: "teams-bot"'''))

    parts.append('<h3>Environment Variables</h3>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Variable</th><th>Required</th><th>Description</th></tr>'
        '<tr><td><code>AZURE_BOT_APP_ID</code></td><td>Yes</td><td>Azure AD application ID for the bot</td></tr>'
        '<tr><td><code>AZURE_BOT_APP_SECRET</code></td><td>Yes</td><td>Azure AD application secret</td></tr>'
        '<tr><td><code>AZURE_TENANT_ID</code></td><td>Yes</td><td>Azure AD tenant ID</td></tr>'
        '<tr><td><code>DATABASE_URL</code></td><td>Yes</td><td>PostgreSQL connection string</td></tr>'
        '<tr><td><code>REDIS_URL</code></td><td>Yes</td><td>Redis connection string</td></tr>'
        '<tr><td><code>AGENT_REGISTRY_PATH</code></td><td>Yes</td><td>Path to agent registry YAML file</td></tr>'
        '<tr><td><code>LOG_LEVEL</code></td><td>No</td><td>Logging level (default: <code>INFO</code>)</td></tr>'
        '<tr><td><code>BOT_PORT</code></td><td>No</td><td>HTTP port (default: <code>8200</code>)</td></tr>'
        '<tr><td><code>HEALTH_CHECK_INTERVAL</code></td><td>No</td><td>Agent health check interval in seconds (default: <code>30</code>)</td></tr>'
        '<tr><td><code>APPROVAL_CHECK_INTERVAL</code></td><td>No</td><td>Approval timeout check interval in seconds (default: <code>300</code>)</td></tr>'
        '</tbody></table>'
    )

    parts.append('<h3>Dependencies</h3>')
    parts.append(
        '<table data-layout="default"><tbody>'
        '<tr><th>Dependency</th><th>Version</th><th>Purpose</th></tr>'
        '<tr><td><code>botbuilder-core</code></td><td>&gt;=4.14</td><td>Microsoft Bot Framework SDK for Python</td></tr>'
        '<tr><td><code>botbuilder-integration-aiohttp</code></td><td>&gt;=4.14</td><td>AIOHTTP integration for Bot Framework</td></tr>'
        '<tr><td><code>fastapi</code></td><td>&gt;=0.100</td><td>REST API framework for agent-to-bot endpoints</td></tr>'
        '<tr><td><code>uvicorn</code></td><td>&gt;=0.23</td><td>ASGI server</td></tr>'
        '<tr><td><code>asyncpg</code></td><td>&gt;=0.28</td><td>Async PostgreSQL driver</td></tr>'
        '<tr><td><code>redis[hiredis]</code></td><td>&gt;=5.0</td><td>Redis client with hiredis parser</td></tr>'
        '<tr><td><code>pyyaml</code></td><td>&gt;=6.0</td><td>YAML parsing for agent registry</td></tr>'
        '<tr><td><code>pydantic</code></td><td>&gt;=2.0</td><td>Request/response validation</td></tr>'
        '<tr><td><code>structlog</code></td><td>&gt;=23.0</td><td>Structured logging</td></tr>'
        '</tbody></table>'
    )

    parts.append('<h3>Health Check Endpoint</h3>')
    parts.append(_code_macro('', 'GET /v1/bot/health'))
    parts.append('<p><strong>Response (healthy):</strong></p>')
    parts.append(_code_macro('json', '''{
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
}'''))
    parts.append('<p>The health endpoint is used by Docker health checks and by the Prometheus scraper for monitoring.</p>')

    parts.append('<h3>Host Placement</h3>')
    parts.append('<p>The bot runs on <code>cn-ai-01</code> alongside PostgreSQL, Redis, and Nginx. Nginx reverse-proxies the bot\'s webhook endpoint for TLS termination:</p>')
    parts.append(_code_macro('', 'Internet -> Nginx (TLS) -> teams-bot:8200'))
    parts.append('<p>The bot\'s agent-to-bot API is accessible only on the internal network (no TLS required for agent-to-bot calls within the Docker network).</p>')

    parts.append('<hr />')

    # ==================== Section 14: Implementation Phases ====================
    parts.append('<h2>14. Implementation Phases</h2>')

    # Phase 1
    parts.append('<h3>Phase 1: Basic Bot + Standard Commands + Activity Notifications</h3>')
    parts.append('<p><strong>Scope:</strong></p>')
    parts.append('<ul>')
    parts.append('<li>Bot Framework SDK integration with Teams</li>')
    parts.append('<li>Webhook receiver and message parser</li>')
    parts.append('<li>Agent Registry (YAML config, hot-reload)</li>')
    parts.append('<li>Channel-to-agent routing</li>')
    parts.append('<li>All 6 standard commands routed to agent APIs</li>')
    parts.append('<li>Activity notification posting (agent-to-bot <code>/v1/bot/notify</code>)</li>')
    parts.append('<li>Basic Adaptive Card templates (Activity, Stats, Token Status, Work Summary)</li>')
    parts.append('<li>PostgreSQL audit logging</li>')
    parts.append('<li>Redis rate limiting</li>')
    parts.append('<li>Health check endpoint</li>')
    parts.append('<li>Docker deployment</li>')
    parts.append('</ul>')
    parts.append('<p><strong>Deliverables:</strong></p>')
    parts.append('<ul>')
    parts.append('<li>Users can post <code>/stats</code>, <code>/token-status</code>, <code>/decision-tree</code>, <code>/why {id}</code>, <code>/work-today</code>, <code>/busy</code> in any agent channel and get formatted responses.</li>')
    parts.append('<li>Agents can push activity notifications to their channels.</li>')
    parts.append('<li>All interactions are logged.</li>')
    parts.append('</ul>')
    parts.append('<p><strong>Dependencies:</strong> Agent APIs must implement the 6 standard status endpoints.</p>')

    # Phase 2
    parts.append('<h3>Phase 2: Approval Workflow + Adaptive Cards</h3>')
    parts.append('<p><strong>Scope:</strong></p>')
    parts.append('<ul>')
    parts.append('<li>Approval request API (<code>/v1/bot/request-approval</code>)</li>')
    parts.append('<li>Approval Adaptive Card with Approve/Reject buttons</li>')
    parts.append('<li>Approval response handling (button click processing)</li>')
    parts.append('<li>Approval status tracking in PostgreSQL</li>')
    parts.append('<li>Approval timeout and escalation scheduler</li>')
    parts.append('<li>Decision notification cards</li>')
    parts.append('<li>Error alert cards and API (<code>/v1/bot/alert</code>)</li>')
    parts.append('<li>Approval status query API (<code>/v1/bot/approvals/{id}</code>)</li>')
    parts.append('<li>User identity verification for approvals</li>')
    parts.append('</ul>')
    parts.append('<p><strong>Deliverables:</strong></p>')
    parts.append('<ul>')
    parts.append('<li>Hedy, Linus, Linnaeus, and Hypatia can request human approvals.</li>')
    parts.append('<li>Users can approve/reject via Adaptive Card buttons.</li>')
    parts.append('<li>Timeouts trigger escalation.</li>')
    parts.append('<li>All approval actions are audited with user identity.</li>')
    parts.append('</ul>')
    parts.append('<p><strong>Dependencies:</strong> Phase 1 complete. Agents must implement <code>/v1/approvals/{id}/respond</code> endpoint.</p>')

    # Phase 3
    parts.append('<h3>Phase 3: Input Requests + Free-Text Queries</h3>')
    parts.append('<p><strong>Scope:</strong></p>')
    parts.append('<ul>')
    parts.append('<li>Input request API (<code>/v1/bot/request-input</code>)</li>')
    parts.append('<li>Dynamic form generation from field schemas</li>')
    parts.append('<li>Input response handling (form submission processing)</li>')
    parts.append('<li>Free-text query forwarding to agent <code>/v1/query</code> endpoint</li>')
    parts.append('<li>Thread management for conversations</li>')
    parts.append('<li>Conversation state tracking in PostgreSQL</li>')
    parts.append('<li>Message deduplication</li>')
    parts.append('</ul>')
    parts.append('<p><strong>Deliverables:</strong></p>')
    parts.append('<ul>')
    parts.append('<li>Agents can request structured input from humans.</li>')
    parts.append('<li>Users can ask free-text questions in agent channels.</li>')
    parts.append('<li>Conversations are properly threaded.</li>')
    parts.append('</ul>')
    parts.append('<p><strong>Dependencies:</strong> Phase 2 complete. Agents must implement <code>/v1/query</code> endpoint.</p>')

    # Phase 4
    parts.append('<h3>Phase 4: Custom Agent Commands + Advanced Cards</h3>')
    parts.append('<p><strong>Scope:</strong></p>')
    parts.append('<ul>')
    parts.append('<li>Custom command routing from registry <code>custom_commands</code></li>')
    parts.append('<li>Parameter extraction and validation for custom commands</li>')
    parts.append('<li>Agent-specific card templates (if needed beyond standard templates)</li>')
    parts.append('<li><code>/help</code> command with per-agent command listing</li>')
    parts.append('<li>Card template hot-reload</li>')
    parts.append('<li>Performance optimization (connection pooling, response caching)</li>')
    parts.append('<li>Grafana dashboard for bot metrics</li>')
    parts.append('</ul>')
    parts.append('<p><strong>Deliverables:</strong></p>')
    parts.append('<ul>')
    parts.append('<li>Agent-specific commands (e.g., <code>/build</code>, <code>/release-status</code>) work in their channels.</li>')
    parts.append('<li><code>/help</code> shows all available commands for the current channel\'s agent.</li>')
    parts.append('<li>Bot performance is monitored via Grafana.</li>')
    parts.append('</ul>')
    parts.append('<p><strong>Dependencies:</strong> Phase 3 complete. Agents define their custom commands in the registry.</p>')

    parts.append('<hr />')

    # ==================== Section 15: Diagrams ====================
    parts.append('<h2>15. Diagrams</h2>')
    parts.append(
        '<ac:structured-macro ac:name="note">'
        '<ac:rich-text-body><p>This section contains Mermaid diagrams for the overall architecture, '
        'standard command flow, approval workflow, and input request workflow. Mermaid diagrams cannot '
        'be rendered natively in Confluence. See the source Markdown file at '
        '<code>docs/reference/TEAMS_BOT_FRAMEWORK.md</code> for the full diagram definitions.</p>'
        '</ac:rich-text-body></ac:structured-macro>'
    )

    parts.append('<h3>Overall Architecture</h3>')
    parts.append('<p>Shows all 15 agent channels in Microsoft Teams connecting via webhook to Nginx (TLS) on cn-ai-01, '
                 'which forwards to the Teams Bot Service. The bot connects to the Agent Registry, PostgreSQL, Redis, '
                 'and routes commands to all 15 Agent APIs across cn-ai-01/02/03. Agents push notifications and approval '
                 'requests back to the bot.</p>')

    parts.append('<h3>Standard Command Flow</h3>')
    parts.append('<p>Sequence: User posts <code>/stats</code> in <code>#agent-josephine</code> &rarr; Teams webhook &rarr; '
                 'Nginx TLS termination &rarr; Bot validates JWT &rarr; Redis rate limit check &rarr; Parse command &rarr; '
                 'Registry lookup &rarr; Agent API call &rarr; Render Adaptive Card &rarr; Reply (threaded) &rarr; Audit log.</p>')

    parts.append('<h3>Approval Workflow</h3>')
    parts.append('<p>Sequence: Agent calls <code>POST /v1/bot/request-approval</code> &rarr; Bot inserts pending approval &rarr; '
                 'Posts Approval Card &rarr; User clicks Approve/Reject &rarr; Bot verifies identity/role &rarr; Updates DB &rarr; '
                 'Notifies agent &rarr; Posts confirmation. Timeout scheduler handles escalation (re-post with ESCALATED banner) '
                 'and expiry (mark expired, notify agent).</p>')

    parts.append('<h3>Input Request Workflow</h3>')
    parts.append('<p>Sequence: Agent calls <code>POST /v1/bot/request-input</code> &rarr; Bot inserts pending request &rarr; '
                 'Generates form card from field schema &rarr; Posts to channel &rarr; User fills form and submits &rarr; '
                 'Bot validates required fields &rarr; Updates DB &rarr; Forwards to agent &rarr; Posts confirmation. '
                 'User can also click &quot;Skip / Cannot Provide&quot; and the agent proceeds with available info.</p>')

    # Footer
    parts.append('<hr />')
    parts.append('<p><em>Teams Bot Framework Specification -- Cornelis Networks AI Agent Workforce</em></p>')

    return ''.join(parts)


def _code_macro(language, code):
    """Build a Confluence code macro."""
    lang_param = f'<ac:parameter ac:name="language">{html.escape(language)}</ac:parameter>' if language else ''
    return (
        f'<ac:structured-macro ac:name="code">'
        f'{lang_param}'
        f'<ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body>'
        f'</ac:structured-macro>'
    )


# ==================== Adaptive Card JSON helpers ====================
# These return the raw JSON strings for the large card templates

def _activity_notification_json():
    return '''{
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
}'''


def _decision_notification_json():
    return '''{
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
            { "type": "Image", "url": "${agent_icon_url}", "size": "Small", "style": "Person" }
          ]
        },
        {
          "type": "Column",
          "width": "stretch",
          "items": [
            { "type": "TextBlock", "text": "Decision: ${decision_title}", "weight": "Bolder", "size": "Medium", "color": "Accent" },
            { "type": "TextBlock", "text": "${agent_display_name} | ${timestamp}", "isSubtle": true, "spacing": "None", "size": "Small" }
          ]
        }
      ]
    },
    { "type": "TextBlock", "text": "**Outcome:** ${chosen_action}", "wrap": true },
    { "type": "TextBlock", "text": "**Rationale:** ${rationale}", "wrap": true },
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
          "data": { "action": "view_decision", "decision_id": "${decision_id}", "agent_id": "${agent_id}" }
        }
      ]
    }
  ]
}'''


def _approval_request_json():
    return '''{
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "Container",
      "style": "warning",
      "items": [
        { "type": "TextBlock", "text": "APPROVAL REQUIRED", "weight": "Bolder", "size": "Medium", "color": "Warning" }
      ]
    },
    {
      "type": "ColumnSet",
      "columns": [
        { "type": "Column", "width": "auto", "items": [{ "type": "Image", "url": "${agent_icon_url}", "size": "Small", "style": "Person" }] },
        {
          "type": "Column", "width": "stretch",
          "items": [
            { "type": "TextBlock", "text": "${agent_display_name} requests approval", "weight": "Bolder" },
            { "type": "TextBlock", "text": "${timestamp} | Expires: ${expiry_time}", "isSubtle": true, "spacing": "None", "size": "Small" }
          ]
        }
      ]
    },
    { "type": "TextBlock", "text": "**${approval_title}**", "wrap": true, "size": "Medium" },
    { "type": "TextBlock", "text": "${approval_description}", "wrap": true },
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
      "type": "Container", "style": "emphasis",
      "items": [
        { "type": "TextBlock", "text": "**Evidence Summary**", "weight": "Bolder" },
        { "type": "TextBlock", "text": "${evidence_summary}", "wrap": true }
      ]
    },
    { "type": "Input.Text", "id": "approval_comment", "placeholder": "Optional comment (required if rejecting)", "isMultiline": true },
    {
      "type": "ActionSet",
      "actions": [
        { "type": "Action.Submit", "title": "Approve", "style": "positive", "data": { "action": "approval_response", "approval_id": "${approval_id}", "decision": "approved", "agent_id": "${agent_id}" } },
        { "type": "Action.Submit", "title": "Reject", "style": "destructive", "data": { "action": "approval_response", "approval_id": "${approval_id}", "decision": "rejected", "agent_id": "${agent_id}" } }
      ]
    }
  ]
}'''


def _input_request_json():
    return '''{
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "ColumnSet",
      "columns": [
        { "type": "Column", "width": "auto", "items": [{ "type": "Image", "url": "${agent_icon_url}", "size": "Small", "style": "Person" }] },
        { "type": "Column", "width": "stretch", "items": [{ "type": "TextBlock", "text": "${agent_display_name} needs your input", "weight": "Bolder", "size": "Medium" }] }
      ]
    },
    { "type": "TextBlock", "text": "${input_request_description}", "wrap": true },
    {
      "type": "FactSet",
      "facts": [
        { "title": "Request ID", "value": "${request_id}" },
        { "title": "Context", "value": "${context_summary}" },
        { "title": "Deadline", "value": "${deadline}" }
      ]
    },
    { "type": "Input.Text", "id": "field_1", "label": "${field_1_label}", "placeholder": "${field_1_placeholder}", "isRequired": true },
    {
      "type": "Input.ChoiceSet", "id": "field_2", "label": "${field_2_label}",
      "choices": [
        { "title": "${choice_1}", "value": "${choice_1_value}" },
        { "title": "${choice_2}", "value": "${choice_2_value}" }
      ]
    },
    {
      "type": "ActionSet",
      "actions": [
        { "type": "Action.Submit", "title": "Submit", "style": "positive", "data": { "action": "input_response", "request_id": "${request_id}", "agent_id": "${agent_id}" } },
        { "type": "Action.Submit", "title": "Skip / Cannot Provide", "data": { "action": "input_response", "request_id": "${request_id}", "agent_id": "${agent_id}", "skipped": true } }
      ]
    }
  ]
}'''


def _error_alert_json():
    return '''{
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
            { "type": "Column", "width": "auto", "items": [{ "type": "TextBlock", "text": "${severity_badge}", "weight": "Bolder", "color": "${severity_color}", "size": "Large" }] },
            {
              "type": "Column", "width": "stretch",
              "items": [
                { "type": "TextBlock", "text": "${error_title}", "weight": "Bolder", "size": "Medium" },
                { "type": "TextBlock", "text": "${agent_display_name} | ${timestamp}", "isSubtle": true, "spacing": "None", "size": "Small" }
              ]
            }
          ]
        }
      ]
    },
    { "type": "TextBlock", "text": "${error_description}", "wrap": true },
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
      "type": "Container", "style": "emphasis",
      "items": [
        { "type": "TextBlock", "text": "**Suggested Actions**", "weight": "Bolder" },
        { "type": "TextBlock", "text": "${suggested_actions}", "wrap": true }
      ]
    }
  ]
}'''


def _activity_card_template_json():
    return '''{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "ColumnSet",
      "columns": [
        { "type": "Column", "width": "auto", "items": [{ "type": "Image", "url": "${agent_icon_url}", "size": "Small", "style": "Person" }] },
        {
          "type": "Column", "width": "stretch",
          "items": [
            { "type": "TextBlock", "text": "${agent_display_name} -- ${agent_role}", "weight": "Bolder", "size": "Medium" },
            { "type": "TextBlock", "text": "${timestamp}", "isSubtle": true, "spacing": "None", "size": "Small" }
          ]
        }
      ]
    },
    { "type": "TextBlock", "text": "${activity_summary}", "wrap": true, "size": "Default" },
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
}'''


def _decision_card_template_json():
    return '''{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    { "type": "TextBlock", "text": "Decision Log -- ${agent_display_name}", "weight": "Bolder", "size": "Large" },
    { "type": "TextBlock", "text": "${total_decisions_today} decisions today | ${total_decisions_cumulative} total", "isSubtle": true, "size": "Small" },
    {
      "type": "Container", "separator": true,
      "items": [
        {
          "type": "ColumnSet",
          "columns": [
            { "type": "Column", "width": "auto", "items": [{ "type": "TextBlock", "text": "${outcome_badge}", "weight": "Bolder", "color": "${outcome_color}" }] },
            {
              "type": "Column", "width": "stretch",
              "items": [
                { "type": "TextBlock", "text": "${decision_title}", "weight": "Bolder", "wrap": true },
                { "type": "TextBlock", "text": "${decision_id} | ${timestamp}", "isSubtle": true, "size": "Small" }
              ]
            }
          ]
        },
        { "type": "TextBlock", "text": "${rationale}", "wrap": true, "isSubtle": true }
      ]
    }
  ],
  "actions": [
    {
      "type": "Action.ShowCard", "title": "Expand Details",
      "card": {
        "type": "AdaptiveCard",
        "body": [
          { "type": "TextBlock", "text": "**Inputs Evaluated:** ${input_count}", "wrap": true },
          { "type": "TextBlock", "text": "**Alternatives Considered:** ${alternative_count}", "wrap": true },
          { "type": "TextBlock", "text": "**Confidence:** ${confidence_level}", "wrap": true }
        ]
      }
    },
    {
      "type": "Action.Submit", "title": "Full Decision Tree",
      "data": { "action": "command", "command": "/why", "args": "${decision_id}", "agent_id": "${agent_id}" }
    }
  ]
}'''


def _stats_card_template_json():
    return '''{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    { "type": "TextBlock", "text": "Operational Statistics -- ${agent_display_name}", "weight": "Bolder", "size": "Large" },
    {
      "type": "ColumnSet",
      "columns": [
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Uptime", "weight": "Bolder", "horizontalAlignment": "Center" },
          { "type": "TextBlock", "text": "${uptime_pct}%", "size": "ExtraLarge", "horizontalAlignment": "Center", "color": "${uptime_color}" }
        ]},
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Success Rate", "weight": "Bolder", "horizontalAlignment": "Center" },
          { "type": "TextBlock", "text": "${success_rate_pct}%", "size": "ExtraLarge", "horizontalAlignment": "Center", "color": "${success_color}" }
        ]},
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Queue", "weight": "Bolder", "horizontalAlignment": "Center" },
          { "type": "TextBlock", "text": "${queue_depth}", "size": "ExtraLarge", "horizontalAlignment": "Center" }
        ]}
      ]
    },
    {
      "type": "FactSet", "separator": true,
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
    { "type": "TextBlock", "text": "**Top Errors**", "weight": "Bolder", "separator": true },
    { "type": "FactSet", "facts": [{ "title": "${error_code_1}", "value": "${error_count_1}x (last: ${error_last_1})" }] }
  ]
}'''


def _token_status_card_template_json():
    return '''{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    { "type": "TextBlock", "text": "Token Usage -- ${agent_display_name}", "weight": "Bolder", "size": "Large" },
    { "type": "TextBlock", "text": "Model: ${model} | Efficiency: ${efficiency_ratio}", "isSubtle": true, "size": "Small" },
    { "type": "TextBlock", "text": "**Today (${period})**", "weight": "Bolder", "separator": true },
    {
      "type": "ColumnSet",
      "columns": [
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Input", "size": "Small", "isSubtle": true },
          { "type": "TextBlock", "text": "${tokens_today_input}", "weight": "Bolder" }
        ]},
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Output", "size": "Small", "isSubtle": true },
          { "type": "TextBlock", "text": "${tokens_today_output}", "weight": "Bolder" }
        ]},
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Cost", "size": "Small", "isSubtle": true },
          { "type": "TextBlock", "text": "$${cost_today_usd}", "weight": "Bolder" }
        ]}
      ]
    },
    { "type": "TextBlock", "text": "**Cumulative**", "weight": "Bolder", "separator": true },
    {
      "type": "ColumnSet",
      "columns": [
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Input", "size": "Small", "isSubtle": true },
          { "type": "TextBlock", "text": "${tokens_cumulative_input}", "weight": "Bolder" }
        ]},
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Output", "size": "Small", "isSubtle": true },
          { "type": "TextBlock", "text": "${tokens_cumulative_output}", "weight": "Bolder" }
        ]},
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Cost", "size": "Small", "isSubtle": true },
          { "type": "TextBlock", "text": "$${cost_cumulative_usd}", "weight": "Bolder" }
        ]}
      ]
    },
    {
      "type": "FactSet", "separator": true,
      "facts": [
        { "title": "Deterministic Actions", "value": "${deterministic_action_pct}%" },
        { "title": "Target", "value": ">80%" }
      ]
    }
  ]
}'''


def _work_summary_card_template_json():
    return '''{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    { "type": "TextBlock", "text": "Work Summary -- ${agent_display_name}", "weight": "Bolder", "size": "Large" },
    { "type": "TextBlock", "text": "${date}", "isSubtle": true, "size": "Small" },
    { "type": "TextBlock", "text": "${summary}", "wrap": true, "separator": true },
    {
      "type": "ColumnSet", "separator": true,
      "columns": [
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Processed", "size": "Small", "isSubtle": true, "horizontalAlignment": "Center" },
          { "type": "TextBlock", "text": "${totals_processed}", "size": "ExtraLarge", "horizontalAlignment": "Center", "weight": "Bolder" }
        ]},
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Passed", "size": "Small", "isSubtle": true, "horizontalAlignment": "Center" },
          { "type": "TextBlock", "text": "${totals_passed}", "size": "ExtraLarge", "horizontalAlignment": "Center", "color": "Good" }
        ]},
        { "type": "Column", "width": "1", "items": [
          { "type": "TextBlock", "text": "Failed", "size": "Small", "isSubtle": true, "horizontalAlignment": "Center" },
          { "type": "TextBlock", "text": "${totals_failed}", "size": "ExtraLarge", "horizontalAlignment": "Center", "color": "Attention" }
        ]}
      ]
    },
    {
      "type": "Container", "separator": true,
      "items": [
        { "type": "TextBlock", "text": "**Work Items**", "weight": "Bolder" },
        {
          "type": "ColumnSet",
          "columns": [
            { "type": "Column", "width": "auto", "items": [{ "type": "TextBlock", "text": "${item_status_badge}", "color": "${item_status_color}", "weight": "Bolder" }] },
            {
              "type": "Column", "width": "stretch",
              "items": [
                { "type": "TextBlock", "text": "${item_description}", "wrap": true },
                { "type": "TextBlock", "text": "${item_subject_id} | ${item_timestamp}", "isSubtle": true, "size": "Small" }
              ]
            }
          ]
        }
      ]
    }
  ]
}'''


def _find_existing_page(c, title, space_key):
    """Find an existing page by title in the given space."""
    resp = c.session.get(f'{c.base_url}/rest/api/content', params={
        'title': title,
        'spaceKey': space_key,
        'expand': 'version'
    })
    if resp.status_code >= 400:
        return None
    data = resp.json()
    results = data.get('results', [])
    return results[0] if results else None


def main():
    print("Building Confluence storage format body...")
    body_html = build_body()
    print(f"Body size: {len(body_html)} characters")

    print("Connecting to Confluence...")
    c = connect_to_confluence()

    space_key = '~712020daf767ace9e14880b27724add0de7116'
    page_title = 'Teams Bot Framework'

    # Check if page already exists
    existing = _find_existing_page(c, page_title, space_key)

    if existing:
        # Update existing page
        page_id = existing['id']
        current_version = existing.get('version', {}).get('number', 1)
        print(f"Found existing page: ID={page_id}, version={current_version}. Updating...")

        update_payload = {
            'type': 'page',
            'title': page_title,
            'space': {'key': space_key},
            'ancestors': [{'id': '656572464'}],
            'body': {'storage': {'value': body_html, 'representation': 'storage'}},
            'version': {'number': current_version + 1}
        }
        resp = c.session.put(f'{c.base_url}/rest/api/content/{page_id}', json=update_payload)

        if resp.status_code >= 400:
            print(f"ERROR updating: {resp.status_code}")
            print(resp.text)
            sys.exit(1)

        result = resp.json()
        print(f"Page updated: ID={page_id}, Title={result['title']}, Version={result.get('version', {}).get('number')}")
    else:
        # Create new page
        print("Creating page via v1 API...")
        create_payload = {
            'type': 'page',
            'title': page_title,
            'space': {'key': space_key},
            'ancestors': [{'id': '656572464'}],
            'body': {'storage': {'value': body_html, 'representation': 'storage'}}
        }
        resp = c.session.post(f'{c.base_url}/rest/api/content', json=create_payload)

        if resp.status_code >= 400:
            print(f"ERROR: {resp.status_code}")
            print(resp.text)
            sys.exit(1)

        result = resp.json()
        page_id = result['id']
        print(f"Page created: ID={page_id}, Title={result['title']}")

    page_link = result.get('_links', {}).get('webui', '')
    if page_link and not page_link.startswith('http'):
        page_link = f"{c.base_url.replace('/wiki', '')}{page_link}" if page_link.startswith('/') else page_link

    # Set legacy editor properties
    print("Setting legacy editor properties...")
    prop_value = {
        "titleLayoutAlignment": "LEFT",
        "subtitle": "",
        "subtitleEnabled": False,
        "titlePropertyBylineEnabled": False,
        "titlePropertyEmojiEnabled": False,
        "headerImageLayout": "ABOVE",
        "headerImageStylingEnabled": False
    }
    for prop_key in ['page-title-property-draft', 'page-title-property-published']:
        # Get current property version if it exists
        get_resp = c.session.get(f'{c.base_url}/rest/api/content/{page_id}/property/{prop_key}')
        if get_resp.status_code == 200:
            current = get_resp.json()
            ver = current.get('version', {}).get('number', 1)
            prop_resp = c.session.put(
                f'{c.base_url}/rest/api/content/{page_id}/property/{prop_key}',
                json={'key': prop_key, 'value': prop_value, 'version': {'number': ver + 1, 'minorEdit': True}}
            )
        else:
            prop_resp = c.session.post(
                f'{c.base_url}/rest/api/content/{page_id}/property',
                json={'key': prop_key, 'value': prop_value}
            )
        if prop_resp.status_code >= 400:
            print(f"WARNING: Failed to set property {prop_key}: {prop_resp.status_code} - {prop_resp.text[:200]}")
        else:
            print(f"Set property: {prop_key}")

    print("\nDone!")
    print(f"Page URL: {page_link}")


if __name__ == '__main__':
    main()
