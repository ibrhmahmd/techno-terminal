-- =============================================================================
-- Migration 011: Phase 3 — Schema Updates and Receipt Enhancements
-- =============================================================================
-- Purpose:
--   Modifies the receipts table to use payer_name instead of parent_id.
--   Adds notes to groups and courses.
--   Adds status to academic sessions.
--
-- Apply:
--   psql "$DATABASE_URL" -f db/migrations/011_phase3_schema_updates.sql
-- =============================================================================

BEGIN;

-- 1. Modify receipts
ALTER TABLE receipts DROP COLUMN IF EXISTS parent_id;
ALTER TABLE receipts ADD COLUMN IF NOT EXISTS payer_name TEXT;

-- 2. Add notes
ALTER TABLE groups ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS notes TEXT;

-- 3. Add session status
ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'scheduled'
    CHECK (status IN ('scheduled', 'completed', 'cancelled'));

COMMIT;
