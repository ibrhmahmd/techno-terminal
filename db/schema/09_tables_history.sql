-- =============================================================================
-- HISTORY TABLES (SYNCED FROM LIVE DB)
-- =============================================================================

DROP TABLE IF EXISTS audit_logs CASCADE;

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    event_type TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
