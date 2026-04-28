-- Migration 044: Drop Orphan Table — generated_receipts
-- Created: 2026-04-27
-- Purpose: Remove generated_receipts table which was created in migration 018
--          alongside receipt_templates. receipt_templates IS actively used
--          (receipt_generation_service.py). generated_receipts (storing rendered
--          receipt HTML/text content) was never integrated into any application
--          module and has zero code references.
--
-- Evidence of non-use:
--   - Zero matches for "generated_receipts" in entire app/ directory
--   - receipt_generation_service.py uses receipt_templates only
--   - No API endpoint references the table

-- ── Drop indexes first (auto-dropped with table, listed for audit) ────────────
-- idx_generated_receipts_receipt
-- idx_generated_receipts_format
-- idx_generated_receipts_generated_at

-- ── Drop table ────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS generated_receipts CASCADE;

COMMENT ON TABLE receipt_templates IS
'Active receipt template store. generated_receipts (rendered output cache) was '
'removed in migration 044 — it had zero application references.';

-- ── Verification ─────────────────────────────────────────────────────────────
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public' AND table_name = 'generated_receipts';
-- Expected: 0 rows returned

-- ── Rollback ─────────────────────────────────────────────────────────────────
-- Restore from migration 018_add_receipt_enhancements.sql:
-- CREATE TABLE IF NOT EXISTS generated_receipts (
--     id SERIAL PRIMARY KEY,
--     receipt_id INTEGER NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
--     template_used VARCHAR(50) NOT NULL,
--     content_format VARCHAR(20) NOT NULL DEFAULT 'text',
--     content TEXT NOT NULL,
--     file_path VARCHAR(500),
--     file_size INTEGER,
--     checksum VARCHAR(64),
--     generated_at TIMESTAMPTZ DEFAULT NOW(),
--     generated_by INTEGER REFERENCES users(id),
--     expires_at TIMESTAMPTZ
-- );
