-- =============================================================================
-- CORE TABLES
-- Foundation tables: parents, employees, users
-- Dependencies: None (these are the base tables)
-- =============================================================================

-- Drop statements for idempotent execution (reverse dependency order)
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS parents CASCADE;

-- =============================================================================
-- PARENTS
-- Parent/guardian information for students
-- =============================================================================
CREATE TABLE parents (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    phone_primary TEXT,
    phone_secondary TEXT,
    email TEXT,
    relation TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE parents IS 'Parent/guardian information for students';
COMMENT ON COLUMN parents.phone_primary IS 'Primary contact phone number';
COMMENT ON COLUMN parents.relation IS 'Relationship to student (e.g., father, mother, guardian)';

-- =============================================================================
-- EMPLOYEES
-- Staff and instructor records
-- =============================================================================
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    national_id TEXT NOT NULL,
    university TEXT NOT NULL,
    major TEXT NOT NULL,
    is_graduate BOOLEAN NOT NULL DEFAULT FALSE,
    job_title TEXT,
    employment_type TEXT NOT NULL CHECK (
        employment_type IN ('full_time', 'part_time', 'contract')
    ),
    monthly_salary DECIMAL(10, 2),
    contract_percentage DECIMAL(5, 2),
    is_active BOOLEAN DEFAULT TRUE,
    hired_at DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    CONSTRAINT employees_contract_pct_check CHECK (
        (
            employment_type != 'contract'
            AND contract_percentage IS NULL
        )
        OR (employment_type = 'contract')
    ),
    CONSTRAINT uq_employees_national_id UNIQUE (national_id),
    CONSTRAINT uq_employees_phone UNIQUE (phone),
    CONSTRAINT uq_employees_email UNIQUE (email),
    CONSTRAINT uq_employees_user_id UNIQUE (user_id)
);

COMMENT ON TABLE employees IS 'Staff and instructor records';
COMMENT ON COLUMN employees.national_id IS 'National ID number (unique identifier)';
COMMENT ON COLUMN employees.employment_type IS 'Employment classification: full_time, part_time, or contract';
COMMENT ON COLUMN employees.user_id IS 'Link to users table for employee login access';

-- =============================================================================
-- USERS
-- Application users linked to Supabase Auth
-- =============================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    supabase_uid TEXT UNIQUE NOT NULL,
    employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    role TEXT NOT NULL CHECK (
        role IN ('admin', 'instructor', 'system_admin')
    ),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE users IS 'Application users linked to Supabase Auth via supabase_uid';
COMMENT ON COLUMN users.supabase_uid IS 'Supabase Auth user UUID (required for authentication)';
COMMENT ON COLUMN users.role IS 'User role for authorization: admin, instructor, or system_admin';
COMMENT ON COLUMN users.employee_id IS 'Link to employees table if user is staff';
