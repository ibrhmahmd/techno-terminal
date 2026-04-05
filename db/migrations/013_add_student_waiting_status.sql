-- Migration: Add student waiting status
-- Created: 2026-04-05

-- Step 1: Create enum type for student status
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'student_status') THEN
        CREATE TYPE student_status AS ENUM ('active', 'waiting', 'inactive');
    END IF;
END $$;

-- Step 2: Add new status column with default value
ALTER TABLE students
ADD COLUMN IF NOT EXISTS status student_status DEFAULT 'active';

-- Step 3: Migrate existing data - is_active = true -> 'active', is_active = false -> 'inactive'
UPDATE students
SET status = CASE
    WHEN is_active = true THEN 'active'::student_status
    ELSE 'inactive'::student_status
END
WHERE status IS NULL;

-- Step 4: Add index on status for efficient filtering
CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);

-- Step 5: Add index for waiting list queries (status = waiting)
CREATE INDEX IF NOT EXISTS idx_students_waiting ON students(status) WHERE status = 'waiting';

-- Step 6: Make status non-nullable after migration
ALTER TABLE students
ALTER COLUMN status SET NOT NULL;

-- Step 7: Add audit tracking JSONB fields
ALTER TABLE students
ADD COLUMN IF NOT EXISTS status_history JSONB DEFAULT '[]'::jsonb;

-- Step 8: Add waiting list metadata fields
ALTER TABLE students
ADD COLUMN IF NOT EXISTS waiting_since TIMESTAMP DEFAULT NULL;
ALTER TABLE students
ADD COLUMN IF NOT EXISTS waiting_priority INTEGER DEFAULT NULL;
ALTER TABLE students
ADD COLUMN IF NOT EXISTS waiting_notes TEXT DEFAULT NULL;

-- Step 9: Create trigger for automatic waiting_since timestamp
CREATE OR REPLACE FUNCTION update_waiting_since()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'waiting' AND OLD.status != 'waiting' THEN
        NEW.waiting_since = NOW();
    ELSIF NEW.status != 'waiting' AND OLD.status = 'waiting' THEN
        NEW.waiting_since = NULL;
        NEW.waiting_priority = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_waiting_since ON students;
CREATE TRIGGER trg_update_waiting_since
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION update_waiting_since();

-- Rollback script (for reference):
-- DROP TRIGGER IF EXISTS trg_update_waiting_since ON students;
-- DROP FUNCTION IF EXISTS update_waiting_since();
-- ALTER TABLE students DROP COLUMN IF EXISTS status;
-- ALTER TABLE students DROP COLUMN IF EXISTS status_history;
-- ALTER TABLE students DROP COLUMN IF EXISTS waiting_since;
-- ALTER TABLE students DROP COLUMN IF EXISTS waiting_priority;
-- ALTER TABLE students DROP COLUMN IF EXISTS waiting_notes;
-- DROP TYPE IF EXISTS student_status;
