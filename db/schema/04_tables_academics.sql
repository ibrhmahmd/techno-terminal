-- =============================================================================
-- ACADEMICS TABLES (SYNCED FROM LIVE DB)
-- =============================================================================

DROP TABLE IF EXISTS group_course_history CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS group_levels CASCADE;
DROP TABLE IF EXISTS groups CASCADE;
DROP TABLE IF EXISTS courses CASCADE;

CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    price_per_level NUMERIC,
    sessions_per_level INTEGER DEFAULT 5,
    description TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT courses_category_check CHECK ((category = ANY (ARRAY['software'::text, 'hardware'::text, 'steam'::text, 'other'::text]))),
    CONSTRAINT courses_name_key UNIQUE (name),
    CONSTRAINT courses_price_per_level_check CHECK ((price_per_level > (0)::numeric)),
    CONSTRAINT courses_sessions_per_level_check CHECK ((sessions_per_level > 0))
);

CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name TEXT,
    course_id INTEGER NOT NULL,
    instructor_id INTEGER,
    level_number INTEGER DEFAULT 1,
    default_day TEXT,
    default_time_start TIME WITHOUT TIME ZONE,
    default_time_end TIME WITHOUT TIME ZONE,
    max_capacity INTEGER,
    status TEXT DEFAULT 'active'::text,
    started_at DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT groups_check CHECK (((default_time_start IS NULL) OR (default_time_end IS NULL) OR (default_time_start < default_time_end))),
    CONSTRAINT groups_course_id_fkey FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
    CONSTRAINT groups_instructor_id_fkey FOREIGN KEY (instructor_id) REFERENCES employees(id) ON DELETE SET NULL,
    CONSTRAINT groups_level_number_check CHECK ((level_number > 0)),
    CONSTRAINT groups_max_capacity_check CHECK ((max_capacity > 0)),
    CONSTRAINT groups_status_check CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text, 'completed'::text, 'archived'::text])))
);

CREATE TABLE group_levels (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL,
    level_number INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    instructor_id INTEGER,
    sessions_planned INTEGER NOT NULL DEFAULT 5,
    price_override NUMERIC,
    status TEXT DEFAULT 'active'::text,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to TIMESTAMPTZ,
    created_by_user_id INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT group_levels_course_id_fkey FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
    CONSTRAINT group_levels_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT group_levels_group_id_fkey FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
    CONSTRAINT group_levels_group_id_level_number_key UNIQUE (group_id, level_number),
    CONSTRAINT group_levels_instructor_id_fkey FOREIGN KEY (instructor_id) REFERENCES employees(id) ON DELETE SET NULL,
    CONSTRAINT group_levels_status_check CHECK ((status = ANY (ARRAY['active'::text, 'completed'::text, 'cancelled'::text])))
);

CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL,
    group_level_id INTEGER,
    level_number INTEGER NOT NULL,
    session_number INTEGER NOT NULL,
    session_date DATE NOT NULL,
    start_time TIME WITHOUT TIME ZONE,
    end_time TIME WITHOUT TIME ZONE,
    actual_instructor_id INTEGER,
    is_substitute BOOLEAN DEFAULT false,
    is_extra_session BOOLEAN DEFAULT false,
    notes TEXT,
    status TEXT DEFAULT 'scheduled'::text,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT sessions_actual_instructor_id_fkey FOREIGN KEY (actual_instructor_id) REFERENCES employees(id) ON DELETE SET NULL,
    CONSTRAINT sessions_check CHECK (((start_time IS NULL) OR (end_time IS NULL) OR (start_time < end_time))),
    CONSTRAINT sessions_group_id_fkey FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE RESTRICT,
    CONSTRAINT sessions_group_level_id_fkey FOREIGN KEY (group_level_id) REFERENCES group_levels(id) ON DELETE SET NULL,
    CONSTRAINT sessions_status_check CHECK ((status = ANY (ARRAY['scheduled'::text, 'completed'::text, 'cancelled'::text])))
);

CREATE TABLE group_course_history (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMPTZ,
    assigned_by_user_id INTEGER,
    removed_by_user_id INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT group_course_history_assigned_by_user_id_fkey FOREIGN KEY (assigned_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT group_course_history_course_id_fkey FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
    CONSTRAINT group_course_history_group_id_fkey FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
    CONSTRAINT group_course_history_removed_by_user_id_fkey FOREIGN KEY (removed_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);
