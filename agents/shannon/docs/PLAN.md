# Shannon Communications Agent Plan

## Summary

Shannon is the communications service agent — the single Microsoft Teams bot that serves as the human interface for all 15 domain agents in the Cornelis Networks Agent Workforce. Named after Claude Shannon, the father of information theory.

One deployment, 15+ channels. Shannon receives messages from all agent channels, routes commands to the correct agent API, manages conversation threads and state, handles approval workflows with timeouts and escalation, posts activity notifications and error alerts, and tracks every interaction for audit.

Shannon is not a dumb proxy. It owns:
- Command parsing, routing, and response rendering
- Approval lifecycle management (request, post card, track response, timeout, escalate)
- Conversation threading and deduplication
- Rate limiting and error handling
- Audit logging of all human-agent interactions

Shannon has its own operational channel (`#agent-shannon`) where operators monitor bot health, message throughput, routing errors, and issue meta-commands.

> **Full technical specification:** [docs/reference/TEAMS_BOT_FRAMEWORK.md](../docs/reference/TEAMS_BOT_FRAMEWORK.md)

## Product definition

### Goal
- Provide a single, unified Teams bot interface for all 15 domain agents.
- Route standard and custom commands from Teams channels to the correct agent API.
- Render agent responses as Adaptive Cards for consistent, interactive formatting.
- Manage approval workflows end-to-end: request, post card, track response, timeout, escalate.
- Handle input requests from agents that need structured human input to proceed.
- Log every interaction with user identity, agent identity, action, timestamp, and correlation ID.
- Expose a Bot API that all 15 agents call to push notifications, request approvals, and request input.

### Non-goals for v1
- Shannon does not own domain logic — it routes to agents that do.
- Shannon does not replace agent REST APIs — it complements them with a human-friendly Teams interface.
- Shannon does not perform LLM-based reasoning for command interpretation in v1 (free-text queries are forwarded to agents).
- Shannon does not manage agent deployment, scaling, or lifecycle.

### V1 shape
- `shannon-bot`: single service handling Teams webhooks, command routing, card rendering, approval workflows, and the Bot API.
- Agent Registry: YAML configuration mapping channels to agents, loaded at startup with hot-reload.
- PostgreSQL: conversation state, approval records, audit log.
- Redis: rate limiting, session cache, message deduplication.

## Triggering model
- Shannon runs as an always-on service.
- Inbound triggers: Teams webhook events (user messages, card actions, form submissions).
- Inbound triggers: Agent API calls (notifications, approval requests, input requests, alerts).
- Shannon does not poll — it reacts to webhooks and API calls.

## Architecture

### Components

| Component | Responsibility |
|-----------|---------------|
| **WebhookReceiver** | Receives incoming messages and card actions from Microsoft Teams. Validates JWT signatures, enforces rate limits. |
| **CommandRouter** | Parses commands, resolves channel-to-agent mapping via the Agent Registry, routes to the correct agent API endpoint. |
| **CardRenderer** | Renders Adaptive Cards for activity notifications, decisions, approvals, errors, stats, and all standard command responses. |
| **ThreadManager** | Manages conversation threading — top-level vs threaded replies, conversation state tracking, deduplication. |
| **MessagePoster** | Posts messages and Adaptive Cards to Teams channels via the Microsoft Graph API / Bot Framework SDK. |
| **ApprovalEngine** | Manages approval lifecycle — request receipt, card posting, response tracking, timeout detection, escalation, expiry notification. |
| **AgentRegistry** | Maintains registry of all agents — channel_id, api_base_url, approval_types, custom_commands. YAML config with hot-reload. |
| **AuditLogger** | Logs all interactions with user_id, agent_id, action, timestamp, correlation_id to PostgreSQL. |

### Execution topology
- Shannon runs as a single Docker container on `cn-ai-01` within the agent platform's Docker Compose stack.
- Nginx reverse-proxies the webhook endpoint for TLS termination (`Internet -> Nginx (TLS) -> shannon-bot:8200`).
- The Bot API is accessible on the internal network only (no TLS required for agent-to-bot calls).
- PostgreSQL and Redis are co-located on `cn-ai-01`.

## Interfaces

### Inputs

| Source | Mechanism | Description |
|--------|-----------|-------------|
| Microsoft Teams | Incoming webhooks | User messages, card action submissions (approve/reject), form submissions |
| All 15 domain agents | Bot API (`POST /v1/bot/*`) | Notifications, approval requests, input requests, error alerts |

### Outputs

| Target | Mechanism | Description |
|--------|-----------|-------------|
| Microsoft Teams | Outgoing messages | Adaptive Cards, threaded replies, approval cards, error alerts |
| All 15 domain agents | Routed API calls | Standard commands forwarded to agent `/v1/status/*` endpoints, custom commands to agent-specific endpoints, approval/input responses to agent callback endpoints |
| PostgreSQL | Direct writes | Conversation state, approval records, audit log |

## API

Shannon exposes two API surfaces:

### Bot API (agents call Shannon)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/bot/notify` | POST | Agent posts activity notification to its channel |
| `/v1/bot/request-approval` | POST | Agent requests human approval (posts Adaptive Card with approve/reject buttons) |
| `/v1/bot/request-input` | POST | Agent requests human input (posts form card with dynamic fields) |
| `/v1/bot/alert` | POST | Agent posts error alert to its channel |
| `/v1/bot/approvals/{id}` | GET | Check approval status |
| `/v1/bot/health` | GET | Bot health check — uptime, agent connectivity, pending approvals |

### Status API (Shannon reports on itself)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/status/tokens` | GET | Shannon's own token usage (minimal — mostly deterministic) |
| `/v1/status/stats` | GET | Messages routed, approvals processed, errors, uptime, throughput |
| `/v1/status/load` | GET | Current message queue depth, active conversations, rate limit headroom |
| `/v1/status/decisions` | GET | Shannon's own routing and escalation decisions |
| `/v1/status/work-summary` | GET | Today's message volume, approvals processed, errors handled |

## Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `approval.requested` | Consumed | Agent requests human approval via Bot API |
| `approval.completed` | Emitted | Human responded to approval (approved or rejected) |
| `approval.timeout` | Emitted | Approval not received within deadline — triggers escalation or expiry |
| `approval.escalated` | Emitted | Approval escalated to additional approvers after initial timeout |
| `message.routed` | Emitted | Command successfully routed to agent API |
| `message.failed` | Emitted | Command routing failed (agent unreachable, timeout, error) |
| `input.requested` | Consumed | Agent requests structured human input via Bot API |
| `input.received` | Emitted | Human submitted input response |

## Standard Commands

Shannon responds to the 6 standard commands about itself in `#agent-shannon`:

| Command | What It Returns |
|---------|----------------|
| `/token-status` | Shannon's token usage (minimal — >95% deterministic) |
| `/decision-tree` | Recent routing and escalation decisions |
| `/why {decision-id}` | Deep dive into a specific routing or escalation decision |
| `/stats` | Messages routed, approvals processed, errors, uptime, throughput |
| `/work-today` | Today's message volume, approvals handled, notable errors |
| `/busy` | Current load: message queue depth, active conversations, status |

Additionally, Shannon routes all standard commands posted in any agent channel to the appropriate domain agent. When a user posts `/stats` in `#agent-josephine`, Shannon routes it to Josephine's `/v1/status/stats` endpoint and renders the response as an Adaptive Card.

All commands also work via Shannon's REST API (e.g., `GET /v1/status/tokens`, `GET /v1/status/stats`).

## Decision Logging & Audit Trail

Every action Shannon takes is logged with full context. For decisions (routing, escalation, timeout handling), the complete decision tree is recorded — what options were considered, what data was evaluated, and why the chosen path was selected.

| Log Type | What Is Captured | Example |
|----------|-----------------|---------|
| **Action log** | Every webhook received, command routed, card posted, approval processed. Timestamped with correlation_id and agent_id. | `action=route_command, command=/stats, channel=#agent-josephine, agent_id=josephine, correlation_id=abc-123` |
| **Decision log** | Routing decisions, escalation decisions, timeout handling. Inputs evaluated, rules applied, outcome selected. | `decision=escalate_approval, approval_id=APR-001, elapsed_hours=12, escalation_targets=[@release-leads], reason="exceeded escalate_after_hours threshold"` |
| **Rejection log** | When a message is rejected — rate limited, unknown channel, malformed command. | `decision=reject_message, channel=#unknown, reason="channel not registered in agent registry"` |

All logs are stored in PostgreSQL (audit table) and streamed to Grafana/Loki. Decision logs are queryable by correlation_id, agent_id, decision type, and time range.

## Tool Use & Token Efficiency

Shannon is almost entirely deterministic — command parsing, channel-to-agent routing, card rendering, approval state management, and audit logging are all code paths that consume zero tokens. LLM calls are reserved only for free-text query interpretation (Phase 3), and even then the query is forwarded to the domain agent's `/v1/query` endpoint for actual reasoning.

| Principle | Implementation |
|-----------|---------------|
| **Deterministic first** | Command parsing, routing, card rendering, approval lifecycle, rate limiting, deduplication — all deterministic code. No tokens spent. |
| **LLM only for ambiguity** | Free-text queries that don't match a command pattern are the only path that may involve LLM interpretation. Target: >95% deterministic. |
| **Custom tooling** | Adaptive Card templates are parameterized and reusable. Agent Registry eliminates per-agent code branches. |
| **Token-aware execution** | Any LLM call logs input tokens, output tokens, model used, and cost. Shannon selects the smallest capable model. |
| **Caching** | Agent registry lookups cached in Redis (300s TTL). Rate limit counters in Redis sliding windows. |

### Token Tracking

All token usage is logged to PostgreSQL and accumulates per agent, per day, per operation type.

| Metric | Tracked | Queryable By |
|--------|---------|-------------|
| **Per-call tokens** | input_tokens, output_tokens, model, latency_ms, cost_usd | correlation_id, agent_id, timestamp |
| **Cumulative totals** | total_input_tokens, total_output_tokens, total_cost_usd | agent_id, date range, operation type |
| **Efficiency ratio** | deterministic_actions / total_actions (target: >95%) | agent_id, date range |

## Teams Channel Interface

Shannon IS the Teams channel interface. It is the single bot service that manages all 15 agent channels plus its own operational channel.

Shannon's own ops channel is `#agent-shannon`, where operators:
- Monitor bot health, message throughput, and routing errors
- Issue standard commands (`/stats`, `/busy`, `/work-today`) to check Shannon's own operational status
- Receive error alerts when Shannon encounters issues (agent unreachable, webhook failures, database connectivity)
- Review escalation and timeout decisions

For all other channels (`#agent-josephine`, `#agent-ada`, etc.), Shannon acts as the message broker — receiving user commands, routing them to the correct agent, and posting formatted responses back.

## Phased roadmap

### Phase 1. Basic bot + standard command routing + activity notifications

- Bot Framework SDK integration with Microsoft Teams
- Webhook receiver and message parser with JWT validation
- Agent Registry (YAML config, hot-reload)
- Channel-to-agent routing for all 6 standard commands
- Activity notification posting via Bot API (`/v1/bot/notify`)
- Basic Adaptive Card templates (Activity, Stats, Token Status, Work Summary)
- PostgreSQL audit logging
- Redis rate limiting
- Health check endpoint
- Docker deployment on `cn-ai-01`

Exit criteria:
- Users can post `/stats`, `/token-status`, `/decision-tree`, `/why {id}`, `/work-today`, `/busy` in any agent channel and get formatted Adaptive Card responses
- Agents can push activity notifications to their channels via the Bot API
- All interactions are logged with user identity and correlation ID

### Phase 2. Approval workflow + Adaptive Cards

- Approval request API (`/v1/bot/request-approval`)
- Approval Adaptive Card with Approve/Reject buttons and evidence summary
- Approval response handling (button click processing, user identity verification)
- Approval status tracking in PostgreSQL
- Approval timeout detection and escalation scheduler
- Decision notification cards
- Error alert cards and API (`/v1/bot/alert`)
- Approval status query API (`/v1/bot/approvals/{id}`)

Exit criteria:
- Hedy, Linus, Linnaeus, and Hypatia can request human approvals via the Bot API
- Users can approve/reject via Adaptive Card buttons with identity verification
- Timeouts trigger escalation with @mentions
- All approval actions are audited with user identity

### Phase 3. Input requests + free-text queries

- Input request API (`/v1/bot/request-input`)
- Dynamic form generation from agent-provided field schemas
- Input response handling (form submission processing)
- Free-text query forwarding to agent `/v1/query` endpoint
- Thread management for multi-turn conversations
- Conversation state tracking in PostgreSQL
- Message deduplication (activity ID + idempotency keys)

Exit criteria:
- Agents can request structured input from humans via form cards
- Users can ask free-text questions in agent channels
- Conversations are properly threaded
- Duplicate messages are silently dropped

### Phase 4. Custom agent commands + advanced cards

- Custom command routing from Agent Registry `custom_commands` entries
- Parameter extraction and validation for custom commands
- `/help` command with per-agent command listing
- Card template hot-reload
- Performance optimization (connection pooling, response caching)
- Grafana dashboard for Shannon metrics (throughput, latency, error rates, approval SLA)

Exit criteria:
- Agent-specific commands (e.g., `/build`, `/release-status`) work in their channels
- `/help` shows all available commands for the current channel's agent
- Shannon performance is monitored via Grafana

> **Full technical specification:** [docs/reference/TEAMS_BOT_FRAMEWORK.md](../docs/reference/TEAMS_BOT_FRAMEWORK.md)

## Test and acceptance plan

### Command routing
- Standard command in each of the 15 agent channels routes to the correct agent API endpoint
- Unknown command returns helpful error with `/help` suggestion
- Command in unregistered channel returns clear error

### Approval workflow
- Approval request creates pending record, posts card, tracks response
- Approve and reject button clicks update record and notify agent
- Timeout triggers escalation at configured threshold
- Expired approval notifies agent and posts expiry notice
- Duplicate button clicks on resolved approval return "already processed"

### Threading and deduplication
- Command responses are threaded replies to the user's message
- Activity notifications are top-level messages
- Approval confirmations are threaded replies to the approval card
- Duplicate webhook deliveries are silently dropped

### Error handling
- Agent unreachable returns clear error with last-healthy timestamp
- Agent timeout returns error with suggestion to check `/busy`
- Rate limit exceeded returns retry-after time
- Malformed requests return structured error responses

### Security
- Invalid JWT signatures are rejected with HTTP 401
- Agent-to-bot calls require valid service principal token
- Approval responses verify user identity and team membership
- All interactions are audit-logged

## Assumptions
- Shannon is internal-only — the bot serves the "Agent Workforce" team in Microsoft Teams.
- All 15 domain agents implement the 6 standard status endpoints (`/v1/status/*`).
- PostgreSQL and Redis are available on `cn-ai-01` as shared infrastructure.
- Azure AD app registration and Bot Framework registration are provisioned by IT.
- Shannon is deployed as part of Phase 0 (Platform Foundation) since all agents depend on the Teams interface.
