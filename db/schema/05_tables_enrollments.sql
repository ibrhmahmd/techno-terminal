-- =============================================================================
-- ENROLLMENTS TABLES (SYNCED FROM LIVE DB)
-- =============================================================================

DROP TABLE IF EXISTS enrollment_level_history CASCADE;
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;

CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    level_number INTEGER NOT NULL,
    enrolled_at DATE,
    amount_due NUMERIC,
    discount_applied NUMERIC DEFAULT 0,
    status TEXT DEFAULT 'active'::text,
    transferred_from INTEGER,
    notes TEXT,
    created_by INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT enrollments_amount_due_check CHECK ((amount_due >= (0)::numeric)),
    CONSTRAINT enrollments_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT enrollments_discount_applied_check CHECK ((discount_applied >= (0)::numeric)),
    CONSTRAINT enrollments_group_id_fkey FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE RESTRICT,
    CONSTRAINT enrollments_status_check CHECK ((status = ANY (ARRAY['active'::text, 'completed'::text, 'transferred'::text, 'dropped'::text]))),
    CONSTRAINT enrollments_student_id_fkey FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE RESTRICT,
    CONSTRAINT enrollments_transferred_from_fkey FOREIGN KEY (transferred_from) REFERENCES enrollments(id) ON DELETE SET NULL
);

CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    enrollment_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    marked_by INTEGER,
    marked_at TIMESTAMPTZ,
    CONSTRAINT attendance_enrollment_id_fkey FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE RESTRICT,
    CONSTRAINT attendance_marked_by_fkey FOREIGN KEY (marked_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT attendance_session_id_fkey FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE RESTRICT,
    CONSTRAINT attendance_status_check CHECK ((status = ANY (ARRAY['present'::text, 'absent'::text, 'cancelled'::text]))),
    CONSTRAINT attendance_student_id_fkey FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE RESTRICT,
    CONSTRAINT attendance_student_id_session_id_key UNIQUE (student_id, session_id)
);

CREATE TABLE enrollment_level_history (
    id SERIAL PRIMARY KEY,
    enrollment_id INTEGER NOT NULL,
    group_level_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    level_entered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level_completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'active'::text,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT enrollment_level_history_enrollment_id_fkey FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE,
    CONSTRAINT enrollment_level_history_group_level_id_fkey FOREIGN KEY (group_level_id) REFERENCES group_levels(id) ON DELETE RESTRICT,
    CONSTRAINT enrollment_level_history_status_check CHECK ((status = ANY (ARRAY['active'::text, 'completed'::text, 'dropped'::text]))),
    CONSTRAINT enrollment_level_history_student_id_fkey FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE RESTRICT
);
