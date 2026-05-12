-- Migration 050: Remove teams.fee column
-- Fees are now per-student via TeamMember.member_share
-- The team-level fee column is no longer needed

DROP VIEW IF EXISTS active_teams;
ALTER TABLE teams DROP COLUMN IF EXISTS fee;
CREATE VIEW active_teams AS
SELECT id, category_id, group_id, team_name, coach_id, category, subcategory,
       placement_rank, placement_label, notes, competition_id, created_at,
       metadata, deleted_at, deleted_by
FROM teams
WHERE deleted_at IS NULL;
