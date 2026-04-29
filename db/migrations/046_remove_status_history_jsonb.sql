-- =============================================================================
-- MIGRATION 046: Remove status_history JSONB column
-- The student_activity_log table is now the authoritative source for status history
-- =============================================================================

-- =============================================================================
-- PHASE 1: DROP VIEWS THAT REFERENCE status_history (CASCADE to handle dependencies)
-- =============================================================================

-- Drop views that SELECT * from students (includes status_history)
DROP VIEW IF EXISTS active_students CASCADE;
DROP VIEW IF EXISTS deleted_students CASCADE;

-- =============================================================================
-- PHASE 2: REMOVE status_history COLUMN
-- =============================================================================

-- Remove status_history JSONB column (redundant with student_activity_log)
ALTER TABLE students DROP COLUMN IF EXISTS status_history;

-- =============================================================================
-- PHASE 3: RECREATE VIEWS WITHOUT status_history
-- =============================================================================

-- Recreate active_students view (excludes soft-deleted)
CREATE OR REPLACE VIEW active_students AS
SELECT * FROM students WHERE deleted_at IS NULL;

COMMENT ON VIEW active_students IS 'View of non-deleted students';

-- Recreate deleted_students view (only soft-deleted)
CREATE OR REPLACE VIEW deleted_students AS
SELECT * FROM students WHERE deleted_at IS NOT NULL;

COMMENT ON VIEW deleted_students IS 'View of soft-deleted students (for recovery/admin)';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Verify column is removed
SELECT 'status_history column removed: ' || 
    CASE WHEN COUNT(*) = 0 THEN 'YES' ELSE 'NO - still exists!' END AS verification
FROM information_schema.columns 
WHERE table_name = 'students' AND column_name = 'status_history';
