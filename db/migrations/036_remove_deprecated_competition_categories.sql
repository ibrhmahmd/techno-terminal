-- Migration 036: Remove Deprecated Competition Categories
-- Created: 2026-04-21
-- Purpose: Drop deprecated competition_categories table and related FKs after 3-table migration

-- ── Pre-Migration Verification ───────────────────────────────────────────────
-- Verify competition_categories table is empty or can be safely dropped
-- SELECT COUNT(*) as remaining_categories FROM competition_categories;
-- Expected: 0 (all migrated to teams.category in migration 035)

-- ── Remove Foreign Key Constraints ───────────────────────────────────────────
-- Drop FK from group_competition_participation to competition_categories
ALTER TABLE group_competition_participation 
DROP CONSTRAINT IF EXISTS fk_group_competition_participation_category_id;

-- ── Drop Deprecated Columns ───────────────────────────────────────────────────
-- Remove category_id from group_competition_participation (replaced by teams.category)
ALTER TABLE group_competition_participation 
DROP COLUMN IF EXISTS category_id;

-- ── Drop Deprecated Table ─────────────────────────────────────────────────────
-- Drop competition_categories table (replaced by citext category on teams)
DROP TABLE IF EXISTS competition_categories CASCADE;

-- ── Drop Related Sequences ───────────────────────────────────────────────────
DROP SEQUENCE IF EXISTS competition_categories_id_seq CASCADE;

-- ── Update Comments ───────────────────────────────────────────────────────────
COMMENT ON TABLE group_competition_participation IS 
'Tracks group participation in competitions via teams. Category stored on team record.';

-- ── Verification Query (run manually to confirm) ─────────────────────────────
-- \dt competition_categories  -- Should return "Did not find any relation"
-- \d group_competition_participation  -- Should not show category_id column
