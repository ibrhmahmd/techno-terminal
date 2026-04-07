-- Sprint 3 (D4): backfill audit timestamps, defaults, and updated_at triggers.
-- Safe to run on existing DBs; idempotent-ish (DROP TRIGGER IF EXISTS before create).
--
-- ── If you see: SQLSTATE 25P02 "current transaction is aborted" ─────────────
-- Something earlier in *this* BEGIN block failed (or you re-ran commands after a
-- failure without clearing the session). PostgreSQL ignores all further commands
-- until the transaction ends. Do **not** keep pasting the rest of the file.
--
-- Fix: run  ROLLBACK;  in the same SQL session (or close the tab / open a new
-- connection in the Supabase SQL editor). Then run this **entire** file from the top.
-- Partial re-runs after a failure will keep hitting 25P02 until you ROLLBACK.

BEGIN;

-- ── Backfill NULL timestamps ───────────────────────────────────────────────
UPDATE parents SET
    created_at = COALESCE(created_at, NOW()),
    updated_at = COALESCE(updated_at, created_at, NOW());

UPDATE employees SET
    created_at = COALESCE(created_at, NOW()),
    updated_at = COALESCE(updated_at, created_at, NOW());

UPDATE students SET
    created_at = COALESCE(created_at, NOW()),
    updated_at = COALESCE(updated_at, created_at, NOW());

UPDATE student_parents SET
    created_at = COALESCE(created_at, NOW());

UPDATE courses SET
    created_at = COALESCE(created_at, NOW()),
    updated_at = COALESCE(updated_at, created_at, NOW());

UPDATE groups SET
    created_at = COALESCE(created_at, NOW()),
    updated_at = COALESCE(updated_at, created_at, NOW());

-- Legacy DBs: CourseSession ORM used TEXT for created_at — COALESCE(tz, now()) fails until typed.
DO $sess$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns c
        WHERE c.table_schema = 'public'
          AND c.table_name = 'sessions'
          AND c.column_name = 'created_at'
          AND c.data_type IN ('character varying', 'text', 'character')
    ) THEN
        ALTER TABLE public.sessions
            ALTER COLUMN created_at TYPE timestamptz
            USING (
                CASE
                    WHEN created_at IS NULL OR btrim(created_at::text) = '' THEN NULL
                    ELSE btrim(created_at::text)::timestamptz
                END
            );
    END IF;
END
$sess$;

-- Legacy ORM: session_date as TEXT — normalize to DATE for schema alignment / comparisons.
DO $sd$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns c
        WHERE c.table_schema = 'public'
          AND c.table_name = 'sessions'
          AND c.column_name = 'session_date'
          AND c.data_type IN ('character varying', 'text', 'character')
    ) THEN
        ALTER TABLE public.sessions
            ALTER COLUMN session_date TYPE date
            USING (
                CASE
                    WHEN session_date IS NULL OR btrim(session_date::text) = '' THEN NULL
                    ELSE btrim(session_date::text)::date
                END
            );
    END IF;
END
$sd$;

UPDATE sessions SET
    created_at = COALESCE(created_at, NOW());

UPDATE enrollments SET
    created_at = COALESCE(
        created_at::timestamptz,
        enrolled_at::timestamptz,
        NOW()
    ),
    updated_at = COALESCE(
        updated_at::timestamptz,
        created_at::timestamptz,
        enrolled_at::timestamptz,
        NOW()
    );

UPDATE users SET
    created_at = COALESCE(created_at, NOW());

UPDATE receipts SET
    created_at = COALESCE(created_at, paid_at, NOW());

UPDATE payments SET
    created_at = COALESCE(created_at, NOW());

UPDATE competitions SET
    created_at = COALESCE(created_at, NOW());

UPDATE teams SET
    created_at = COALESCE(created_at, NOW());

-- ── INSERT defaults (ORM may still set explicitly) ──────────────────────────
ALTER TABLE parents ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE parents ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE employees ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE employees ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE students ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE students ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE student_parents ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE courses ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE courses ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE groups ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE groups ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE sessions ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE enrollments ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE enrollments ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE users ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE receipts ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE payments ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE competitions ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE teams ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

-- ── Touch updated_at on row updates ─────────────────────────────────────────
CREATE OR REPLACE FUNCTION tf_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_parents_updated_at ON parents;
CREATE TRIGGER trg_parents_updated_at
    BEFORE UPDATE ON parents
    FOR EACH ROW EXECUTE PROCEDURE tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_employees_updated_at ON employees;
CREATE TRIGGER trg_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW EXECUTE PROCEDURE tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_students_updated_at ON students;
CREATE TRIGGER trg_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE PROCEDURE tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_courses_updated_at ON courses;
CREATE TRIGGER trg_courses_updated_at
    BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE PROCEDURE tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_groups_updated_at ON groups;
CREATE TRIGGER trg_groups_updated_at
    BEFORE UPDATE ON groups
    FOR EACH ROW EXECUTE PROCEDURE tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_enrollments_updated_at ON enrollments;
CREATE TRIGGER trg_enrollments_updated_at
    BEFORE UPDATE ON enrollments
    FOR EACH ROW EXECUTE PROCEDURE tf_set_updated_at();

COMMIT;
