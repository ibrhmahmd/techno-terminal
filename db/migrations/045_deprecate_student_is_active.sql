-- =============================================================================
-- MIGRATION 045: Deprecate student.is_active column
-- Complete removal - no backward compatibility
-- =============================================================================

-- =============================================================================
-- PHASE 1: DATA MIGRATION
-- Align status field with is_active before removing column
-- =============================================================================

-- Students with is_active=TRUE but status != 'active' get promoted to 'active'
UPDATE students 
SET status = 'active' 
WHERE is_active = TRUE AND status != 'active';

-- Students with is_active=FALSE but status = 'active' get demoted to 'inactive'
UPDATE students 
SET status = 'inactive' 
WHERE is_active = FALSE AND status = 'active';

-- =============================================================================
-- PHASE 2: DROP VIEWS THAT REFERENCE is_active (CASCADE to handle dependencies)
-- =============================================================================

-- Drop views that SELECT * from students (includes is_active)
DROP VIEW IF EXISTS v_students CASCADE;
DROP VIEW IF EXISTS v_siblings CASCADE;
DROP VIEW IF EXISTS active_students CASCADE;
DROP VIEW IF EXISTS deleted_students CASCADE;

-- =============================================================================
-- PHASE 3: DROP INDEX ON is_active
-- =============================================================================

DROP INDEX IF EXISTS idx_students_active;

-- =============================================================================
-- PHASE 4: REMOVE is_active COLUMN
-- =============================================================================

ALTER TABLE students DROP COLUMN IF EXISTS is_active;

-- =============================================================================
-- PHASE 5: RECREATE VIEWS WITHOUT is_active
-- =============================================================================

CREATE OR REPLACE VIEW v_students AS
SELECT s.id,
    s.full_name,
    s.date_of_birth,
    EXTRACT(YEAR FROM AGE(s.date_of_birth))::INTEGER AS age,
    s.gender,
    s.phone AS student_phone,
    s.notes,
    s.status,
    s.created_at,
    s.updated_at,
    s.metadata,
    p.full_name AS primary_parent_name,
    p.phone_primary AS primary_parent_phone,
    p.email AS primary_parent_email
FROM students s
    LEFT JOIN student_parents sp ON s.id = sp.student_id AND sp.is_primary = TRUE
    LEFT JOIN parents p ON sp.parent_id = p.id
WHERE s.deleted_at IS NULL;

COMMENT ON VIEW v_students IS 'Student information with primary parent details (excludes deleted)';

-- Recreate active_students view (excludes soft-deleted)
CREATE OR REPLACE VIEW active_students AS
SELECT * FROM students WHERE deleted_at IS NULL;

COMMENT ON VIEW active_students IS 'View of non-deleted students';

-- Recreate deleted_students view (only soft-deleted)
CREATE OR REPLACE VIEW deleted_students AS
SELECT * FROM students WHERE deleted_at IS NOT NULL;

COMMENT ON VIEW deleted_students IS 'View of soft-deleted students (for recovery/admin)';

-- Recreate v_siblings view (sibling relationships)
CREATE OR REPLACE VIEW v_siblings AS
SELECT
    sp1.student_id AS student_id,
    s1.full_name AS student_name,
    sp2.student_id AS sibling_id,
    s2.full_name AS sibling_name,
    p.id AS parent_id,
    p.full_name AS parent_name
FROM student_parents sp1
    JOIN student_parents sp2 ON sp1.parent_id = sp2.parent_id AND sp1.student_id != sp2.student_id
    JOIN students s1 ON sp1.student_id = s1.id
    JOIN students s2 ON sp2.student_id = s2.id
    JOIN parents p ON sp1.parent_id = p.id
WHERE s1.deleted_at IS NULL AND s2.deleted_at IS NULL;

COMMENT ON VIEW v_siblings IS 'Sibling relationships (students sharing a parent)';

-- =============================================================================
-- PHASE 6: ADD STATUS INDEX (optional, for performance)
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_students_status ON students(status) WHERE status = 'active';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Verify is_active column is removed
SELECT 'is_active column removed: ' || 
    CASE WHEN COUNT(*) = 0 THEN 'YES' ELSE 'NO - still exists!' END AS verification
FROM information_schema.columns 
WHERE table_name = 'students' AND column_name = 'is_active';

-- Show status distribution after migration
SELECT status, COUNT(*) as count
FROM students 
WHERE deleted_at IS NULL 
GROUP BY status;
