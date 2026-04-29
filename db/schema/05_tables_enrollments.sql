-- =============================================================================
-- ENROLLMENTS TABLES
-- Student enrollments and attendance tracking
-- Dependencies: students (03_tables_crm.sql), groups (04_tables_academics.sql),
--               sessions (04_tables_academics.sql), users (02_tables_core.sql)
-- =============================================================================

DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS enrollment_level_history CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;

-- =============================================================================
-- ENROLLMENTS
-- Student enrollment in groups
-- =============================================================================
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE RESTRICT,
    level_number INTEGER NOT NULL,
    enrolled_at DATE,
    amount_due DECIMAL(10, 2) CHECK (amount_due >= 0),
    discount_applied DECIMAL(10, 2) DEFAULT 0 CHECK (discount_applied >= 0),
    status TEXT DEFAULT 'active' CHECK (
        status IN ('active', 'completed', 'transferred', 'dropped')
    ),
    transferred_from INTEGER REFERENCES enrollments(id) ON DELETE SET NULL,
    notes TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

COMMENT ON TABLE enrollments IS 'Student enrollment records in course groups';
COMMENT ON COLUMN enrollments.level_number IS 'Level number at time of enrollment';
COMMENT ON COLUMN enrollments.amount_due IS 'Total amount due for this enrollment';
COMMENT ON COLUMN enrollments.discount_applied IS 'Discount amount applied to this enrollment';
COMMENT ON COLUMN enrollments.transferred_from IS 'Previous enrollment ID if this is a transfer';
COMMENT ON COLUMN enrollments.deleted_at IS 'Soft delete timestamp for enrollment cancellation';
COMMENT ON COLUMN enrollments.status IS 'active, completed, transferred, or dropped';

-- Unique constraint: only one active enrollment per student per group
CREATE UNIQUE INDEX idx_enrollments_active_unique ON enrollments(student_id, group_id)
WHERE status = 'active';

-- =============================================================================
-- ENROLLMENT_LEVEL_HISTORY
-- Track student progression through levels within an enrollment
-- =============================================================================
CREATE TABLE enrollment_level_history (
    id SERIAL PRIMARY KEY,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    group_level_id INTEGER REFERENCES group_levels(id) ON DELETE SET NULL,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    level_number INTEGER NOT NULL,
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    sessions_attended INTEGER DEFAULT 0,
    sessions_missed INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE enrollment_level_history IS 'Tracks student progression through levels within an enrollment';
COMMENT ON COLUMN enrollment_level_history.group_level_id IS 'Link to the group level record';
COMMENT ON COLUMN enrollment_level_history.sessions_attended IS 'Count of sessions attended at this level';
COMMENT ON COLUMN enrollment_level_history.sessions_missed IS 'Count of sessions missed at this level';

-- =============================================================================
-- ATTENDANCE
-- Session attendance records
-- =============================================================================
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE RESTRICT,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK (
        status IN ('present', 'absent', 'cancelled')
    ),
    marked_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    marked_at TIMESTAMPTZ,
    notes TEXT,
    UNIQUE(student_id, session_id)
);

COMMENT ON TABLE attendance IS 'Student attendance records for each session';
COMMENT ON COLUMN attendance.status IS 'present, absent, or cancelled';
COMMENT ON COLUMN attendance.marked_by IS 'User ID who recorded the attendance';
COMMENT ON COLUMN attendance.marked_at IS 'Timestamp when attendance was recorded';
