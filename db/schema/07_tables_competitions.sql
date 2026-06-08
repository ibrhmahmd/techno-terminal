-- =============================================================================
-- COMPETITIONS TABLES (SYNCED FROM LIVE DB)
-- =============================================================================

DROP TABLE IF EXISTS team_members CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS competitions CASCADE;

CREATE TABLE competitions (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    edition TEXT,
    competition_date DATE,
    location TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    fee_per_student NUMERIC DEFAULT 0.0,
    edition_year INTEGER NOT NULL,
    CONSTRAINT uq_competitions_name_edition_year UNIQUE (name, edition_year)
);

CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    category_id INTEGER,
    group_id INTEGER,
    team_name TEXT NOT NULL,
    coach_id INTEGER,
    enrollment_fee_per_student NUMERIC,
    is_deleted BOOLEAN DEFAULT false,
    deleted_by_user_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    competition_id INTEGER NOT NULL,
    category CITEXT NOT NULL,
    subcategory CITEXT,
    placement_rank INTEGER,
    placement_label VARCHAR(100),
    notes TEXT,
    project_name VARCHAR(500),
    project_description TEXT,
    CONSTRAINT teams_coach_id_fkey FOREIGN KEY (coach_id) REFERENCES employees(id) ON DELETE SET NULL,
    CONSTRAINT teams_competition_id_fkey FOREIGN KEY (competition_id) REFERENCES competitions(id),
    CONSTRAINT teams_deleted_by_user_id_fkey FOREIGN KEY (deleted_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT teams_enrollment_fee_per_student_check CHECK ((enrollment_fee_per_student > (0)::numeric)),
    CONSTRAINT teams_group_id_fkey FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL
);

CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    amount_due NUMERIC DEFAULT 0.00,
    amount_paid NUMERIC DEFAULT 0.00,
    CONSTRAINT team_members_student_id_fkey FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE RESTRICT,
    CONSTRAINT team_members_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    CONSTRAINT team_members_team_id_student_id_key UNIQUE (team_id, student_id)
);

ALTER TABLE payments ADD CONSTRAINT payments_team_member_id_fkey FOREIGN KEY (team_member_id) REFERENCES team_members(id);
