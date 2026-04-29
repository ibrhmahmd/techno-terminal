-- =============================================================================
-- ENUMERATED TYPES
-- Custom ENUM types used across the database
-- =============================================================================

-- Student status for enrollment workflow
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'student_status') THEN
        CREATE TYPE student_status AS ENUM ('active', 'waiting', 'inactive');
    END IF;
END
$$;

COMMENT ON TYPE student_status IS 'Student enrollment status: active, waiting (queue), or inactive';
