-- =============================================================================
-- CRM TABLES
-- Student management and relationships
-- Dependencies: parents (02_tables_core.sql), users (02_tables_core.sql)
-- =============================================================================

DROP TABLE IF EXISTS student_activity_log CASCADE;
DROP TABLE IF EXISTS student_parents CASCADE;
DROP TABLE IF EXISTS students CASCADE;

-- =============================================================================
-- STUDENTS
-- Student records with soft-delete and status tracking
-- =============================================================================
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    date_of_birth DATE,
    gender TEXT CHECK (gender IN ('male', 'female')),
    phone TEXT,
    notes TEXT,
    status student_status DEFAULT 'waiting',
    status_history JSONB DEFAULT '[]',
    waiting_since TIMESTAMP,
    waiting_priority INTEGER,
    waiting_notes TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    CONSTRAINT uq_students_phone UNIQUE (phone)
);

COMMENT ON TABLE students IS 'Student records with soft-delete and status tracking';
COMMENT ON COLUMN students.status IS 'Current enrollment status: active, waiting, or inactive';
COMMENT ON COLUMN students.waiting_since IS 'Timestamp when student was added to waiting list';
COMMENT ON COLUMN students.waiting_priority IS 'Priority level in waiting queue (lower = higher priority)';
COMMENT ON COLUMN students.deleted_at IS 'Soft delete timestamp. NULL = active record';
COMMENT ON COLUMN students.deleted_by IS 'User ID who performed the soft delete';
COMMENT ON COLUMN students.metadata IS 'JSONB for flexible additional student data';

-- =============================================================================
-- STUDENT_PARENTS
-- Many-to-many junction: students ↔ parents
-- =============================================================================
CREATE TABLE student_parents (
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    parent_id INTEGER NOT NULL REFERENCES parents(id) ON DELETE CASCADE,
    relationship TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, parent_id)
);

COMMENT ON TABLE student_parents IS 'Many-to-many relationship between students and parents';
COMMENT ON COLUMN student_parents.relationship IS 'Relationship type (father, mother, guardian, etc.)';
COMMENT ON COLUMN student_parents.is_primary IS 'Designates the primary contact parent';

-- =============================================================================
-- STUDENT_ACTIVITY_LOG
-- Unified student activity timeline
-- Replaces: student_status_history, student_enrollment_history, student_competition_history
-- =============================================================================
CREATE TABLE student_activity_log (
    id BIGSERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_subtype VARCHAR(50),
    reference_type VARCHAR(50),
    reference_id INTEGER,
    description TEXT NOT NULL,
    metadata JSONB,
    meta JSONB,
    performed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE student_activity_log IS 'Unified student activity timeline. Replaces separate history tables (removed in migration 043).';
COMMENT ON COLUMN student_activity_log.activity_type IS 'Category: enrollment, payment, attendance, competition, status_change, etc.';
COMMENT ON COLUMN student_activity_log.activity_subtype IS 'Specific action within category';
COMMENT ON COLUMN student_activity_log.reference_type IS 'Table name for related entity (enrollments, payments, etc.)';
COMMENT ON COLUMN student_activity_log.reference_id IS 'ID of related entity';
COMMENT ON COLUMN student_activity_log.meta IS 'Alias column for metadata compatibility';
