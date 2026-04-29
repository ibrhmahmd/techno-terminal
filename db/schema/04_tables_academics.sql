-- =============================================================================
-- ACADEMICS TABLES
-- Courses, groups, sessions, and academic organization
-- Dependencies: employees (02_tables_core.sql)
-- =============================================================================

DROP TABLE IF EXISTS group_course_history CASCADE;
DROP TABLE IF EXISTS group_levels CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS groups CASCADE;
DROP TABLE IF EXISTS academic_years CASCADE;
DROP TABLE IF EXISTS academic_categories CASCADE;
DROP TABLE IF EXISTS courses CASCADE;

-- =============================================================================
-- ACADEMIC_CATEGORIES
-- Categories for organizing courses
-- =============================================================================
CREATE TABLE academic_categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE academic_categories IS 'Categories for organizing academic courses';

-- =============================================================================
-- ACADEMIC_YEARS
-- Academic year definitions for session organization
-- =============================================================================
CREATE TABLE academic_years (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_academic_year_dates CHECK (start_date < end_date)
);

COMMENT ON TABLE academic_years IS 'Academic year definitions for organizing sessions';
COMMENT ON COLUMN academic_years.name IS 'E.g., 2025-2026 Academic Year';

-- =============================================================================
-- COURSES
-- Course definitions and curriculum
-- =============================================================================
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT CHECK (
        category IN ('software', 'hardware', 'steam', 'other')
    ),
    price_per_level DECIMAL(10, 2) CHECK (price_per_level > 0),
    sessions_per_level INTEGER DEFAULT 12 CHECK (sessions_per_level > 0),
    description TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE courses IS 'Course definitions and curriculum structure';
COMMENT ON COLUMN courses.sessions_per_level IS 'Number of sessions per course level (default: 12)';
COMMENT ON COLUMN courses.price_per_level IS 'Standard price for one level of this course';

-- =============================================================================
-- GROUPS
-- Course groups (classes) with scheduling
-- =============================================================================
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name TEXT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    instructor_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    level_number INTEGER DEFAULT 1 CHECK (level_number > 0),
    default_day TEXT,
    default_time_start TIME,
    default_time_end TIME,
    max_capacity INTEGER CHECK (max_capacity > 0),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'completed', 'archived')),
    started_at DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    
    CHECK (
        default_time_start IS NULL
        OR default_time_end IS NULL
        OR default_time_start < default_time_end
    )
);

COMMENT ON TABLE groups IS 'Course groups (classes) with scheduling information';
COMMENT ON COLUMN groups.default_day IS 'Weekly meeting day (e.g., Saturday, Sunday)';
COMMENT ON COLUMN groups.default_time_start IS 'Default session start time';
COMMENT ON COLUMN groups.default_time_end IS 'Default session end time';
COMMENT ON COLUMN groups.level_number IS 'Current level number for this group';

-- =============================================================================
-- SESSIONS
-- Individual class sessions
-- =============================================================================
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE RESTRICT,
    group_level_id INTEGER REFERENCES group_levels(id) ON DELETE SET NULL,
    level_number INTEGER NOT NULL,
    session_number INTEGER NOT NULL,
    session_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    actual_instructor_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    is_substitute BOOLEAN DEFAULT FALSE,
    is_extra_session BOOLEAN DEFAULT FALSE,
    notes TEXT,
    status TEXT DEFAULT 'scheduled' CHECK (
        status IN ('scheduled', 'completed', 'cancelled')
    ),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (
        start_time IS NULL
        OR end_time IS NULL
        OR start_time < end_time
    )
);

COMMENT ON TABLE sessions IS 'Individual class sessions for groups';
COMMENT ON COLUMN sessions.session_number IS 'Sequential number within the level';
COMMENT ON COLUMN sessions.is_substitute IS 'True if instructor is substituting';
COMMENT ON COLUMN sessions.is_extra_session IS 'True if session is outside normal schedule';
COMMENT ON COLUMN sessions.group_level_id IS 'Link to specific group level record';

-- =============================================================================
-- GROUP_LEVELS
-- Track group progression through course levels
-- =============================================================================
CREATE TABLE group_levels (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    level_number INTEGER NOT NULL,
    sessions_planned INTEGER DEFAULT 5 NOT NULL,
    sessions_completed INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    effective_from DATE DEFAULT CURRENT_DATE,
    effective_until DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (group_id, level_number),
    CHECK (effective_from <= effective_until OR effective_until IS NULL)
);

COMMENT ON TABLE group_levels IS 'Tracks group progression through course levels';
COMMENT ON COLUMN group_levels.sessions_planned IS 'Number of sessions planned for this level';
COMMENT ON COLUMN group_levels.sessions_completed IS 'Number of sessions actually completed';
COMMENT ON COLUMN group_levels.effective_from IS 'Date this level became active';
COMMENT ON COLUMN group_levels.effective_until IS 'Date this level was completed/cancelled';

-- =============================================================================
-- GROUP_COURSE_HISTORY
-- Track course assignments to groups over time
-- =============================================================================
CREATE TABLE group_course_history (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE group_course_history IS 'Historical record of course assignments to groups';
