-- =============================================================================
-- COMPETITIONS TABLES
-- Competition management and team participation
-- Dependencies: groups (04_tables_academics.sql), employees (02_tables_core.sql),
--               students (03_tables_crm.sql), payments (06_tables_finance.sql)
-- =============================================================================

DROP TABLE IF EXISTS group_competition_participation CASCADE;
DROP TABLE IF EXISTS team_members CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS competition_categories CASCADE;
DROP TABLE IF EXISTS competitions CASCADE;

-- =============================================================================
-- COMPETITIONS
-- Competition definitions
-- =============================================================================
CREATE TABLE competitions (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    edition TEXT,
    edition_year INTEGER,
    competition_date DATE,
    location TEXT,
    fee_per_student DECIMAL(10, 2) CHECK (fee_per_student >= 0),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

COMMENT ON TABLE competitions IS 'Competition definitions and details';
COMMENT ON COLUMN competitions.edition IS 'Competition edition name/identifier';
COMMENT ON COLUMN competitions.edition_year IS 'Year of the competition edition';
COMMENT ON COLUMN competitions.fee_per_student IS 'Registration fee per participating student';
COMMENT ON COLUMN competitions.deleted_at IS 'Soft delete timestamp';

-- =============================================================================
-- COMPETITION_CATEGORIES
-- Categories within a competition
-- =============================================================================
CREATE TABLE competition_categories (
    id SERIAL PRIMARY KEY,
    competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    category_name TEXT NOT NULL,
    age_range_min INTEGER,
    age_range_max INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE competition_categories IS 'Categories within a competition (age groups, skill levels)';
COMMENT ON COLUMN competition_categories.age_range_min IS 'Minimum age for this category';
COMMENT ON COLUMN competition_categories.age_range_max IS 'Maximum age for this category';

-- =============================================================================
-- TEAMS
-- Competition teams
-- =============================================================================
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES competition_categories(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    team_name TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    coach_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

COMMENT ON TABLE teams IS 'Competition teams linked to categories and optionally to groups';
COMMENT ON COLUMN teams.category IS 'Team category (normalized)';
COMMENT ON COLUMN teams.subcategory IS 'Team subcategory (normalized)';
COMMENT ON COLUMN teams.deleted_at IS 'Soft delete timestamp';

-- =============================================================================
-- TEAM_MEMBERS
-- Students assigned to competition teams
-- =============================================================================
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    member_share DECIMAL(10, 2) CHECK (member_share >= 0),
    fee_paid BOOLEAN DEFAULT FALSE,
    payment_id INTEGER REFERENCES payments(id) ON DELETE SET NULL,
    joined_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE(team_id, student_id)
);

COMMENT ON TABLE team_members IS 'Students assigned to competition teams';
COMMENT ON COLUMN team_members.member_share IS 'Snapshotted enrollment fee share at registration';
COMMENT ON COLUMN team_members.fee_paid IS 'Whether the competition fee has been paid';
COMMENT ON COLUMN team_members.payment_id IS 'Link to payment record if fee was paid';

-- =============================================================================
-- GROUP_COMPETITION_PARTICIPATION
-- Group-level competition participation tracking
-- =============================================================================
CREATE TABLE group_competition_participation (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    enrolled_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    enrolled_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    UNIQUE(group_id, team_id, competition_id)
);

COMMENT ON TABLE group_competition_participation IS 'Group-level competition participation tracking';
COMMENT ON COLUMN group_competition_participation.is_active IS 'Whether this participation is currently active';
