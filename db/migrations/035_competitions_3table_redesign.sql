-- Migration 035: Competitions Module 3-Table Redesign
-- Created: 2026-04-21
-- Purpose: Redesign competitions to 3-table structure with citext categories

-- ── Enable citext Extension ─────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS citext;

-- ── Competitions Table Updates ───────────────────────────────────────────────
-- Add soft delete columns
ALTER TABLE competitions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
ALTER TABLE competitions ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) DEFAULT NULL;

-- Add edition_year column
ALTER TABLE competitions ADD COLUMN IF NOT EXISTS edition_year INTEGER;

-- Migrate edition string to edition_year
UPDATE competitions
SET edition_year = CAST(SUBSTRING(edition FROM '[0-9]+') AS INTEGER)
WHERE edition ~ '[0-9]+' AND edition_year IS NULL;

-- Set default for any remaining NULL edition_year from competition_date
UPDATE competitions
SET edition_year = EXTRACT(YEAR FROM COALESCE(competition_date, NOW()))
WHERE edition_year IS NULL;

-- Make edition_year NOT NULL
ALTER TABLE competitions ALTER COLUMN edition_year SET NOT NULL;

-- Add unique constraint on name + edition_year (prevent duplicate editions)
ALTER TABLE competitions 
ADD CONSTRAINT uq_competitions_name_edition_year 
UNIQUE (name, edition_year);

-- Create index on edition_year for filtering
CREATE INDEX IF NOT EXISTS idx_competitions_edition_year ON competitions(edition_year);
CREATE INDEX IF NOT EXISTS idx_competitions_deleted_at ON competitions(deleted_at) WHERE deleted_at IS NOT NULL;

-- ── Teams Table Restructure ───────────────────────────────────────────────────
-- Add new columns for 3-table design
ALTER TABLE teams ADD COLUMN IF NOT EXISTS competition_id INTEGER REFERENCES competitions(id);
ALTER TABLE teams ADD COLUMN IF NOT EXISTS category CITEXT;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS subcategory CITEXT;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS fee NUMERIC(10, 2);
ALTER TABLE teams ADD COLUMN IF NOT EXISTS placement_rank INTEGER;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS placement_label VARCHAR(100);
ALTER TABLE teams ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) DEFAULT NULL;

-- Migrate data from old structure (category_id -> competition_id + category)
UPDATE teams t
SET competition_id = c.competition_id,
    category = c.category_name::citext,
    subcategory = NULL,
    fee = comp.fee_per_student
FROM competition_categories c
JOIN competitions comp ON c.competition_id = comp.id
WHERE t.category_id = c.id;

-- Make competition_id and category NOT NULL after migration
ALTER TABLE teams ALTER COLUMN competition_id SET NOT NULL;
ALTER TABLE teams ALTER COLUMN category SET NOT NULL;

-- Create indexes on new columns
CREATE INDEX IF NOT EXISTS idx_teams_competition_id ON teams(competition_id);
CREATE INDEX IF NOT EXISTS idx_teams_category ON teams(category);
CREATE INDEX IF NOT EXISTS idx_teams_subcategory ON teams(subcategory);
CREATE INDEX IF NOT EXISTS idx_teams_deleted_at ON teams(deleted_at) WHERE deleted_at IS NOT NULL;

-- Create composite index for competition + category queries
CREATE INDEX IF NOT EXISTS idx_teams_competition_category ON teams(competition_id, category);

-- ── Create Trim Trigger Function ─────────────────────────────────────────────
CREATE OR REPLACE FUNCTION normalize_team_fields()
RETURNS TRIGGER AS $$
BEGIN
    NEW.category := TRIM(NEW.category);
    NEW.subcategory := TRIM(NEW.subcategory);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on teams table
DROP TRIGGER IF EXISTS normalize_team_fields_trigger ON teams;
CREATE TRIGGER normalize_team_fields_trigger
    BEFORE INSERT OR UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION normalize_team_fields();

-- ── Views for Active Records ──────────────────────────────────────────────────
CREATE OR REPLACE VIEW active_competitions AS
SELECT * FROM competitions WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_teams AS
SELECT * FROM teams WHERE deleted_at IS NULL;

-- ── Comments ───────────────────────────────────────────────────────────────────
COMMENT ON COLUMN competitions.edition_year IS 'The year of this competition edition (e.g., 2026). Each year is a separate competition row.';
COMMENT ON COLUMN competitions.deleted_at IS 'Soft delete timestamp. NULL = active. Set = logically deleted.';
COMMENT ON COLUMN teams.competition_id IS 'Direct reference to competition (replaces category_id FK chain)';
COMMENT ON COLUMN teams.category IS 'Category name as citext (case-insensitive). Examples: Software Leader, Robotics, AI Challenge';
COMMENT ON COLUMN teams.subcategory IS 'Optional subcategory as citext. Examples: Junior, Senior, Advanced';
COMMENT ON COLUMN teams.fee IS 'Academy-set fee for this specific team (not inherited from category)';
COMMENT ON COLUMN teams.placement_rank IS 'Final placement: 1=1st place, 2=2nd place, 3=3rd place, etc. NULL until competition ends';
COMMENT ON COLUMN teams.placement_label IS 'Placement description: Gold, Silver, Bronze, or 3rd Place, Honorable Mention, etc.';
COMMENT ON COLUMN teams.deleted_at IS 'Soft delete timestamp. NULL = active. Set = logically deleted.';

-- ── Rollback Procedure ────────────────────────────────────────────────────────
-- To rollback this migration:
-- 1. Drop new columns from teams (after migrating data back)
-- 2. Drop new columns from competitions
-- 3. Drop trigger and function
-- 4. Drop extension (if not used elsewhere)
-- 5. Drop views
