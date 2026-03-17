-- Event bus schema for agent-to-agent communication.
-- PostgreSQL pg_notify + LISTEN/NOTIFY with polling fallback.

-- ==========================================================================
-- Event store (append-only, immutable)
-- ==========================================================================

CREATE TABLE IF NOT EXISTS events (
    id              BIGSERIAL       PRIMARY KEY,
    event_id        UUID            UNIQUE NOT NULL,
    event_type      VARCHAR(255)    NOT NULL,
    producer        VARCHAR(100)    NOT NULL,
    occurred_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    correlation_id  UUID            NOT NULL,
    subject_id      VARCHAR(255),
    payload         JSONB           NOT NULL DEFAULT '{}',
    schema_version  VARCHAR(10)     NOT NULL DEFAULT '1.0',
    idempotency_key VARCHAR(255),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_type        ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_subject     ON events(subject_id);
CREATE INDEX IF NOT EXISTS idx_events_correlation ON events(correlation_id);
CREATE INDEX IF NOT EXISTS idx_events_occurred    ON events(occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_created     ON events(created_at);

-- ==========================================================================
-- Consumer offsets — each consumer tracks its position in the event stream
-- ==========================================================================

CREATE TABLE IF NOT EXISTS consumer_offsets (
    consumer_id   VARCHAR(100)  PRIMARY KEY,
    last_event_id BIGINT        NOT NULL DEFAULT 0,
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ==========================================================================
-- Dead letter queue — events that failed processing after max retries
-- ==========================================================================

CREATE TABLE IF NOT EXISTS dead_letter_events (
    id            BIGSERIAL     PRIMARY KEY,
    event_id      UUID          NOT NULL REFERENCES events(event_id),
    consumer_id   VARCHAR(100)  NOT NULL,
    error_message TEXT,
    retry_count   INT           NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    last_retry_at TIMESTAMPTZ,
    UNIQUE (event_id, consumer_id)
);

CREATE INDEX IF NOT EXISTS idx_dle_consumer ON dead_letter_events(consumer_id);
CREATE INDEX IF NOT EXISTS idx_dle_created  ON dead_letter_events(created_at);

-- ==========================================================================
-- pg_notify trigger — fires on every INSERT into events
-- ==========================================================================

CREATE OR REPLACE FUNCTION notify_event() RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(NEW.event_type, NEW.event_id::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS event_notify_trigger ON events;
CREATE TRIGGER event_notify_trigger
    AFTER INSERT ON events
    FOR EACH ROW EXECUTE FUNCTION notify_event();
