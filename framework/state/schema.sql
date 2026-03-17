-- ==========================================================================
-- State backend schema for agent persistence, audit, and token tracking.
-- PostgreSQL — separate from the event bus schema (framework/events/schema.sql).
--
-- Author: Cornelis Networks
-- ==========================================================================

-- ==========================================================================
-- Agent key-value state
-- ==========================================================================

CREATE TABLE IF NOT EXISTS agent_state (
    agent_id    VARCHAR(100)    NOT NULL,
    key         VARCHAR(500)    NOT NULL,
    value       TEXT,
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (agent_id, key)
);

CREATE INDEX IF NOT EXISTS idx_agent_state_updated
    ON agent_state(updated_at);

-- ==========================================================================
-- Agent sessions
-- ==========================================================================

CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id  VARCHAR(100)    PRIMARY KEY,
    agent_id    VARCHAR(100)    NOT NULL,
    metadata    JSONB           DEFAULT '{}',
    data        JSONB           DEFAULT '{}',
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_agent
    ON agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated
    ON agent_sessions(updated_at);

-- ==========================================================================
-- Audit log — actions
-- ==========================================================================

CREATE TABLE IF NOT EXISTS audit_actions (
    id              BIGSERIAL       PRIMARY KEY,
    action_id       UUID            UNIQUE NOT NULL,
    agent_id        VARCHAR(100)    NOT NULL,
    action          VARCHAR(255)    NOT NULL,
    details         JSONB           DEFAULT '{}',
    correlation_id  UUID,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_agent
    ON audit_actions(agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_correlation
    ON audit_actions(correlation_id);
CREATE INDEX IF NOT EXISTS idx_audit_created
    ON audit_actions(created_at);

-- ==========================================================================
-- Audit log — decisions (full decision tree)
-- ==========================================================================

CREATE TABLE IF NOT EXISTS audit_decisions (
    id                      BIGSERIAL       PRIMARY KEY,
    decision_id             UUID            UNIQUE NOT NULL,
    agent_id                VARCHAR(100)    NOT NULL,
    decision_type           VARCHAR(255)    NOT NULL,
    inputs                  JSONB           NOT NULL,
    candidates              JSONB           NOT NULL,
    selected                VARCHAR(500)    NOT NULL,
    rationale               TEXT            NOT NULL,
    rules_evaluated         JSONB           DEFAULT '[]',
    alternatives_rejected   JSONB           DEFAULT '[]',
    source_data_links       JSONB           DEFAULT '[]',
    correlation_id          UUID,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decisions_agent
    ON audit_decisions(agent_id);
CREATE INDEX IF NOT EXISTS idx_decisions_type
    ON audit_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_decisions_created
    ON audit_decisions(created_at);
CREATE INDEX IF NOT EXISTS idx_decisions_correlation
    ON audit_decisions(correlation_id);

-- ==========================================================================
-- Audit log — rejections (blocked / overridden actions)
-- ==========================================================================

CREATE TABLE IF NOT EXISTS audit_rejections (
    id              BIGSERIAL       PRIMARY KEY,
    rejection_id    UUID            UNIQUE NOT NULL,
    agent_id        VARCHAR(100)    NOT NULL,
    action          VARCHAR(255)    NOT NULL,
    blocked_by      VARCHAR(500)    NOT NULL,
    alternative     VARCHAR(500),
    correlation_id  UUID,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rejections_agent
    ON audit_rejections(agent_id);
CREATE INDEX IF NOT EXISTS idx_rejections_created
    ON audit_rejections(created_at);

-- ==========================================================================
-- Token usage tracking
-- ==========================================================================

CREATE TABLE IF NOT EXISTS token_usage (
    id              BIGSERIAL       PRIMARY KEY,
    agent_id        VARCHAR(100)    NOT NULL,
    operation       VARCHAR(255)    NOT NULL,
    input_tokens    INT             NOT NULL DEFAULT 0,
    output_tokens   INT             NOT NULL DEFAULT 0,
    model           VARCHAR(100),
    latency_ms      FLOAT,
    cost_usd        FLOAT           NOT NULL DEFAULT 0,
    is_deterministic BOOLEAN        NOT NULL DEFAULT FALSE,
    correlation_id  UUID,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tokens_agent
    ON token_usage(agent_id);
CREATE INDEX IF NOT EXISTS idx_tokens_created
    ON token_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_tokens_agent_date
    ON token_usage(agent_id, created_at);
