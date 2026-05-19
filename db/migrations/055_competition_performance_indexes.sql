-- Migration 055: Competition Module Performance Indexes
-- Date: 2026-05-19
-- Purpose: Add missing indexes to eliminate full table scans on competition module queries.
--          Identified in audit-report.md Section 7 (Missing Indexes).

-- teams table indexes
CREATE INDEX IF NOT EXISTS idx_teams_competition_id ON teams(competition_id);
CREATE INDEX IF NOT EXISTS idx_teams_category ON teams(category);
CREATE INDEX IF NOT EXISTS idx_teams_coach_id ON teams(coach_id);

-- team_members table indexes
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_student_id ON team_members(student_id);
CREATE INDEX IF NOT EXISTS idx_team_members_amount_paid ON team_members(amount_paid);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_team_members_team_student ON team_members(team_id, student_id);
CREATE INDEX IF NOT EXISTS idx_teams_competition_category ON teams(competition_id, category);
