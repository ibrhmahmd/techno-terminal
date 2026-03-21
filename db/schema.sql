-- Techno Kids — PostgreSQL Schema v3.3
-- 15 tables, 5 views, 23 indexes
-- v3.3: users — Supabase auth (supabase_uid), roles admin/instructor/system_admin; seed via app (see db/README.md)
-- CHANGES FROM v3.2:
--   [T1]  Changed `sessions.group_id` ON DELETE CASCADE to RESTRICT
--   [T2]  Changed `payments.receipt_id` ON DELETE CASCADE to RESTRICT
--   [T3]  Removed `total_amount` from receipts (derived from payments)
--   [T4]  Changed `CHECK (amount > 0)` to `!= 0` to allow refunds
--   [T5]  Added `transaction_type` to payments ('charge', 'payment', 'refund')
--   [T6]  Made `attendance.enrollment_id` NOT NULL
--   [T7]  Replaced `students.guardian_id` with `student_guardians` junction table
--
-- Tables ordered by dependency (referenced tables first).
-- =============================================================================
-- Drop all (for re-runs)
DROP TABLE IF EXISTS team_members CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS competition_categories CASCADE;
DROP TABLE IF EXISTS competitions CASCADE;
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS receipts CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS groups CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS student_guardians CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS guardians CASCADE;
CREATE TABLE guardians (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    phone_primary TEXT,
    phone_secondary TEXT,
    email TEXT,
    relation TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    job_title TEXT,
    employment_type TEXT CHECK (employment_type IN ('part_time', 'contract')),
    monthly_salary DECIMAL(10, 2),
    contract_percentage DECIMAL(5, 2) DEFAULT 25.00,
    is_active BOOLEAN DEFAULT TRUE,
    hired_at DATE,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    supabase_uid TEXT UNIQUE NOT NULL,
    employee_id INTEGER REFERENCES employees(id) ON DELETE
    SET NULL,
        role TEXT NOT NULL CHECK (
            role IN ('admin', 'instructor', 'system_admin')
        ),
        is_active BOOLEAN DEFAULT TRUE,
        last_login TIMESTAMPTZ,
        created_at TIMESTAMPTZ
);
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    date_of_birth DATE,
    gender TEXT CHECK (gender IN ('male', 'female')),
    phone TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id) ON DELETE
    SET NULL,
        created_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ,
        metadata JSONB DEFAULT '{}'
);
CREATE TABLE student_guardians (
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    guardian_id INTEGER NOT NULL REFERENCES guardians(id) ON DELETE CASCADE,
    relationship TEXT,
    -- 'father', 'mother', etc.
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ,
    PRIMARY KEY (student_id, guardian_id)
);
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT CHECK (
        category IN ('software', 'hardware', 'steam', 'other')
    ),
    price_per_level DECIMAL(10, 2) CHECK (price_per_level > 0),
    sessions_per_level INTEGER DEFAULT 5 CHECK (sessions_per_level > 0),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name TEXT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    instructor_id INTEGER REFERENCES employees(id) ON DELETE
    SET NULL,
        level_number INTEGER DEFAULT 1 CHECK (level_number > 0),
        default_day TEXT,
        default_time_start TIME,
        default_time_end TIME,
        max_capacity INTEGER CHECK (max_capacity > 0),
        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
        started_at DATE,
        created_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ,
        metadata JSONB DEFAULT '{}',
        CHECK (
            default_time_start IS NULL
            OR default_time_end IS NULL
            OR default_time_start < default_time_end
        )
);
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE RESTRICT,
    level_number INTEGER NOT NULL,
    session_number INTEGER NOT NULL,
    session_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    actual_instructor_id INTEGER REFERENCES employees(id) ON DELETE
    SET NULL,
        is_substitute BOOLEAN DEFAULT FALSE,
        is_extra_session BOOLEAN DEFAULT FALSE,
        notes TEXT,
        created_at TIMESTAMPTZ,
        CHECK (
            start_time IS NULL
            OR end_time IS NULL
            OR start_time < end_time
        )
);
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
    transferred_from INTEGER REFERENCES enrollments(id) ON DELETE
    SET NULL,
        notes TEXT,
        created_by INTEGER REFERENCES users(id) ON DELETE
    SET NULL,
        created_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ,
        metadata JSONB DEFAULT '{}'
);
CREATE UNIQUE INDEX idx_enrollments_active_unique ON enrollments(student_id, group_id)
WHERE status = 'active';
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE RESTRICT,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK (
        status IN ('present', 'absent', 'late', 'excused')
    ),
    marked_by INTEGER REFERENCES users(id) ON DELETE
    SET NULL,
        marked_at TIMESTAMPTZ,
        UNIQUE(student_id, session_id)
);
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    guardian_id INTEGER REFERENCES guardians(id) ON DELETE
    SET NULL,
        payment_method TEXT CHECK (
            payment_method IN ('cash', 'card', 'transfer', 'online')
        ),
        received_by INTEGER REFERENCES users(id) ON DELETE
    SET NULL,
        receipt_number TEXT UNIQUE,
        notes TEXT,
        paid_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ
);
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER NOT NULL REFERENCES receipts(id) ON DELETE RESTRICT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE
    SET NULL,
        amount DECIMAL(10, 2) NOT NULL CHECK (amount != 0),
        transaction_type TEXT NOT NULL CHECK (
            transaction_type IN ('charge', 'payment', 'refund')
        ),
        payment_type TEXT CHECK (
            payment_type IN ('course_level', 'competition', 'other')
        ),
        discount_amount DECIMAL(10, 2) DEFAULT 0 CHECK (discount_amount >= 0),
        notes TEXT,
        created_at TIMESTAMPTZ,
        metadata JSONB DEFAULT '{}'
);
CREATE TABLE competitions (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    edition TEXT,
    competition_date DATE,
    location TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ
);
CREATE TABLE competition_categories (
    id SERIAL PRIMARY KEY,
    competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    category_name TEXT NOT NULL,
    notes TEXT
);
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES competition_categories(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE
    SET NULL,
        team_name TEXT NOT NULL,
        coach_id INTEGER REFERENCES employees(id) ON DELETE
    SET NULL,
        enrollment_fee_per_student DECIMAL(10, 2) CHECK (enrollment_fee_per_student > 0),
        created_at TIMESTAMPTZ,
        metadata JSONB DEFAULT '{}'
);
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    fee_paid BOOLEAN DEFAULT FALSE,
    payment_id INTEGER REFERENCES payments(id) ON DELETE
    SET NULL,
        UNIQUE(team_id, student_id)
);
-- Indexes
CREATE INDEX idx_guardians_phone ON guardians(phone_primary)
WHERE phone_primary IS NOT NULL;
CREATE INDEX idx_student_guardians_student ON student_guardians(student_id);
CREATE INDEX idx_student_guardians_guardian ON student_guardians(guardian_id);
CREATE INDEX idx_students_active ON students(is_active)
WHERE is_active = TRUE;
CREATE INDEX idx_students_name ON students(full_name);
CREATE INDEX idx_groups_course ON groups(course_id);
CREATE INDEX idx_groups_instructor ON groups(instructor_id);
CREATE INDEX idx_groups_active ON groups(status)
WHERE status = 'active';
CREATE INDEX idx_sessions_group ON sessions(group_id);
CREATE INDEX idx_sessions_group_level ON sessions(group_id, level_number);
CREATE INDEX idx_sessions_date ON sessions(session_date);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_group ON enrollments(group_id);
CREATE INDEX idx_enrollments_active ON enrollments(status)
WHERE status = 'active';
CREATE INDEX idx_attendance_student ON attendance(student_id);
CREATE INDEX idx_attendance_session ON attendance(session_id);
CREATE INDEX idx_attendance_enrollment ON attendance(enrollment_id);
CREATE INDEX idx_payments_student ON payments(student_id);
CREATE INDEX idx_payments_enrollment ON payments(enrollment_id);
CREATE INDEX idx_payments_receipt ON payments(receipt_id);
CREATE INDEX idx_comp_categories_comp ON competition_categories(competition_id);
CREATE INDEX idx_teams_category ON teams(category_id);
CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_student ON team_members(student_id);
CREATE UNIQUE INDEX idx_users_supabase_uid ON users(supabase_uid);
-- Views
CREATE OR REPLACE VIEW v_students AS
SELECT s.id,
    s.full_name,
    s.date_of_birth,
    EXTRACT(
        YEAR
        FROM AGE(s.date_of_birth)
    )::INTEGER AS age,
    s.gender,
    s.phone AS student_phone,
    s.notes,
    s.is_active,
    s.created_at,
    s.updated_at,
    s.metadata,
    g.full_name AS primary_guardian_name,
    g.phone_primary AS primary_guardian_phone
FROM students s
    LEFT JOIN student_guardians sg ON s.id = sg.student_id
    AND sg.is_primary = TRUE
    LEFT JOIN guardians g ON sg.guardian_id = g.id;
CREATE OR REPLACE VIEW v_enrollment_balance AS
SELECT e.id AS enrollment_id,
    e.student_id,
    e.group_id,
    e.level_number,
    e.amount_due,
    e.discount_applied,
    (e.amount_due - e.discount_applied) AS net_due,
    COALESCE(
        SUM(p.amount) FILTER (
            WHERE p.transaction_type IN ('payment', 'charge')
        ),
        0
    ) - COALESCE(
        SUM(p.amount) FILTER (
            WHERE p.transaction_type = 'refund'
        ),
        0
    ) AS total_paid,
    (e.amount_due - e.discount_applied) - (
        COALESCE(
            SUM(p.amount) FILTER (
                WHERE p.transaction_type IN ('payment', 'charge')
            ),
            0
        ) - COALESCE(
            SUM(p.amount) FILTER (
                WHERE p.transaction_type = 'refund'
            ),
            0
        )
    ) AS balance
FROM enrollments e
    LEFT JOIN payments p ON p.enrollment_id = e.id
GROUP BY e.id;
CREATE OR REPLACE VIEW v_enrollment_attendance AS
SELECT a.enrollment_id,
    COUNT(*) FILTER (
        WHERE a.status IN ('present', 'late')
    ) AS sessions_attended,
    COUNT(*) FILTER (
        WHERE a.status = 'absent'
    ) AS sessions_missed
FROM attendance a
GROUP BY a.enrollment_id;
CREATE OR REPLACE VIEW v_siblings AS
SELECT sg1.student_id AS student_id,
    s1.full_name AS student_name,
    sg2.student_id AS sibling_id,
    s2.full_name AS sibling_name,
    sg1.guardian_id
FROM student_guardians sg1
    JOIN student_guardians sg2 ON sg1.guardian_id = sg2.guardian_id
    AND sg1.student_id < sg2.student_id
    JOIN students s1 ON sg1.student_id = s1.id
    JOIN students s2 ON sg2.student_id = s2.id
WHERE s1.is_active = TRUE
    AND s2.is_active = TRUE;
CREATE OR REPLACE VIEW v_group_session_count AS
SELECT group_id,
    level_number,
    COUNT(*) FILTER (
        WHERE is_extra_session = FALSE
    ) AS regular_sessions,
    COUNT(*) FILTER (
        WHERE is_extra_session = TRUE
    ) AS extra_sessions,
    COUNT(*) AS total_sessions
FROM sessions
GROUP BY group_id,
    level_number;
-- Seed (optional local employee row). Login users are created in Supabase and mapped via app/db/seed.py.
INSERT INTO employees (
        full_name,
        job_title,
        employment_type,
        created_at
    )
VALUES (
        'Admin',
        'admin',
        'part_time',
        NOW()
    );