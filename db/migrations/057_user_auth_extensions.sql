-- 057: User auth extensions — audit log table + invite columns
-- Adds: audit_logs table (event audit trail)
-- Adds: invite_token, invite_expires_at columns to users table

BEGIN;

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_created ON audit_logs (user_id, created_at DESC);
CREATE INDEX idx_audit_logs_event_created ON audit_logs (event_type, created_at DESC);

-- Add invite columns to users table
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS invite_token TEXT UNIQUE,
    ADD COLUMN IF NOT EXISTS invite_expires_at TIMESTAMPTZ;

COMMIT;
