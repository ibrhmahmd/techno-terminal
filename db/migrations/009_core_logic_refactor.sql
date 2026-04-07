-- db/migrations/009_core_logic_refactor.sql
-- ──────────────────────────────────────────────────
-- Phase 3: Core Logic Architecture Changes.

-- 1. Financial Decoupling
ALTER TABLE receipts DROP COLUMN parent_id;
ALTER TABLE receipts ADD COLUMN payer_name TEXT;

-- 2. Notes Expansion
ALTER TABLE groups ADD COLUMN notes TEXT;
ALTER TABLE courses ADD COLUMN notes TEXT;

-- 3. Session Multi-status
ALTER TABLE sessions ADD COLUMN status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled'));
