-- ============================================================================
-- Migration: Add Group Lifecycle Tables
-- Date: 2026-04-04
-- Description: Creates tables for immutable group level snapshots, course
--              history, enrollment level history, and group competition
--              participation. Also adds group_level_id to sessions.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Add soft delete columns to teams table (no dependencies)
-- ----------------------------------------------------------------------------
ALTER TABLE teams
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- ----------------------------------------------------------------------------
-- 2. Create group_levels table first (no dependencies on new tables)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS group_levels (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    level_number INTEGER NOT NULL,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    instructor_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    sessions_planned INTEGER NOT NULL DEFAULT 5,
    price_override DECIMAL(10, 2),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    effective_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to TIMESTAMPTZ,
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, level_number)
);

-- ----------------------------------------------------------------------------
-- 3. Now add group_level_id to sessions (depends on group_levels)
-- ----------------------------------------------------------------------------
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS group_level_id INTEGER REFERENCES group_levels(id) ON DELETE SET NULL;

-- ----------------------------------------------------------------------------
-- 4. Create group_course_history table (no dependencies on other new tables)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS group_course_history (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMPTZ,
    assigned_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    removed_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 5. Create enrollment_level_history table (depends on group_levels)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enrollment_level_history (
    id SERIAL PRIMARY KEY,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    group_level_id INTEGER NOT NULL REFERENCES group_levels(id) ON DELETE RESTRICT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    level_entered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level_completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'dropped')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 6. Create group_competition_participation table (no dependencies on other new tables)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS group_competition_participation (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES competition_categories(id) ON DELETE SET NULL,
    entered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    final_placement INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, team_id, competition_id)
);

-- ----------------------------------------------------------------------------
-- 7. Create indexes for performance
-- ----------------------------------------------------------------------------
-- Group levels indexes
CREATE INDEX IF NOT EXISTS idx_group_levels_group ON group_levels(group_id);
CREATE INDEX IF NOT EXISTS idx_group_levels_status ON group_levels(status);
CREATE INDEX IF NOT EXISTS idx_group_levels_effective ON group_levels(effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_group_levels_group_number ON group_levels(group_id, level_number);

-- Group course history indexes
CREATE INDEX IF NOT EXISTS idx_group_course_history_group ON group_course_history(group_id);
CREATE INDEX IF NOT EXISTS idx_group_course_history_course ON group_course_history(course_id);
CREATE INDEX IF NOT EXISTS idx_group_course_history_assigned ON group_course_history(assigned_at);

-- Enrollment level history indexes
CREATE INDEX IF NOT EXISTS idx_enrollment_level_history_enrollment ON enrollment_level_history(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_level_history_level ON enrollment_level_history(group_level_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_level_history_student ON enrollment_level_history(student_id);

-- Competition participation indexes
CREATE INDEX IF NOT EXISTS idx_group_competition_participation_group ON group_competition_participation(group_id);
CREATE INDEX IF NOT EXISTS idx_group_competition_participation_team ON group_competition_participation(team_id);
CREATE INDEX IF NOT EXISTS idx_group_competition_participation_competition ON group_competition_participation(competition_id);
CREATE INDEX IF NOT EXISTS idx_group_competition_participation_active ON group_competition_participation(is_active)
WHERE is_active = TRUE;

-- Sessions new column index
CREATE INDEX IF NOT EXISTS idx_sessions_group_level ON sessions(group_level_id);

-- Teams soft delete index
CREATE INDEX IF NOT EXISTS idx_teams_deleted ON teams(is_deleted)
WHERE is_deleted = TRUE;

-- ----------------------------------------------------------------------------
-- 8. Add audit triggers for new tables
-- ----------------------------------------------------------------------------
CREATE TRIGGER  trg_group_levels_updated_at
BEFORE UPDATE ON group_levels
FOR EACH ROW EXECUTE FUNCTION tf_set_updated_at();

CREATE TRIGGER trg_enrollment_level_history_updated_at
BEFORE UPDATE ON enrollment_level_history
FOR EACH ROW EXECUTE FUNCTION tf_set_updated_at();

CREATE TRIGGER trg_group_competition_participation_updated_at
BEFORE UPDATE ON group_competition_participation
FOR EACH ROW EXECUTE FUNCTION tf_set_updated_at();

-- ============================================================================
-- Migration Complete
-- ============================================================================
