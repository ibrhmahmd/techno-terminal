-- =============================================================================
-- CORE TABLES (SYNCED FROM LIVE DB)
-- =============================================================================

DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS parents CASCADE;

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

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    national_id TEXT NOT NULL,
    university TEXT NOT NULL,
    major TEXT NOT NULL,
    is_graduate BOOLEAN NOT NULL DEFAULT false,
    job_title TEXT,
    employment_type TEXT NOT NULL,
    monthly_salary NUMERIC,
    contract_percentage NUMERIC,
    is_active BOOLEAN DEFAULT true,
    hired_at DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    user_id INTEGER,
    CONSTRAINT employees_contract_pct_check CHECK ((((employment_type <> 'contract'::text) AND (contract_percentage IS NULL)) OR (employment_type = 'contract'::text))),
    CONSTRAINT employees_employment_type_check CHECK ((employment_type = ANY (ARRAY['full_time'::text, 'part_time'::text, 'contract'::text]))),
    CONSTRAINT uq_employees_email UNIQUE (email),
    CONSTRAINT uq_employees_national_id UNIQUE (national_id),
    CONSTRAINT uq_employees_phone UNIQUE (phone),
    CONSTRAINT uq_employees_user_id UNIQUE (user_id)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    supabase_uid TEXT,
    employee_id INTEGER,
    role TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    invite_token TEXT,
    invite_expires_at TIMESTAMPTZ,
    CONSTRAINT users_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL,
    CONSTRAINT users_invite_token_key UNIQUE (invite_token),
    CONSTRAINT users_role_check CHECK ((role = ANY (ARRAY['admin'::text, 'instructor'::text, 'system_admin'::text]))),
    CONSTRAINT users_supabase_uid_key UNIQUE (supabase_uid),
    CONSTRAINT users_username_key UNIQUE (username)
);

ALTER TABLE employees ADD CONSTRAINT fk_employees_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
