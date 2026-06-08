-- =============================================================================
-- CRM TABLES (SYNCED FROM LIVE DB)
-- =============================================================================

DROP TABLE IF EXISTS student_activity_log CASCADE;
DROP TABLE IF EXISTS student_parents CASCADE;
DROP TABLE IF EXISTS students CASCADE;

CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    date_of_birth DATE,
    gender TEXT,
    phone TEXT,
    notes TEXT,
    created_by INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    status STUDENT_STATUS NOT NULL DEFAULT 'active'::student_status,
    waiting_since TIMESTAMP,
    waiting_priority INTEGER,
    waiting_notes TEXT,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER,
    CONSTRAINT students_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT students_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT students_gender_check CHECK ((gender = ANY (ARRAY['male'::text, 'female'::text])))
);

CREATE TABLE student_parents (
    student_id INTEGER NOT NULL,
    parent_id INTEGER NOT NULL,
    relationship TEXT,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT student_parents_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE CASCADE,
    CONSTRAINT student_parents_student_id_fkey FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE student_activity_log (
    id BIGSERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_subtype VARCHAR(50),
    reference_type VARCHAR(50),
    reference_id INTEGER,
    description TEXT NOT NULL,
    metadata JSONB,
    performed_by INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    meta JSONB,
    CONSTRAINT student_activity_log_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT student_activity_log_student_id_fkey FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);
