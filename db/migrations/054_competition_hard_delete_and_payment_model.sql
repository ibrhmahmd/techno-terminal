-- Migration 054: Competition Hard Delete & Enrollment-Style Payment Model
-- Date: 2026-05-17
-- Purpose: Replace soft-delete with hard delete for competitions/teams,
--          add project tracking to teams, migrate team_members to amount_due/amount_paid,
--          add team_member_id to payments, drop GroupCompetitionParticipation.

-- Phase 1: Drop group_competition_participation table
DROP TABLE IF EXISTS group_competition_participation CASCADE;

-- Phase 2: Add project tracking columns to teams
ALTER TABLE teams ADD COLUMN IF NOT EXISTS project_name VARCHAR(500);
ALTER TABLE teams ADD COLUMN IF NOT EXISTS project_description TEXT;

-- Phase 3: Migrate team_members to enrollment-style fee model
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS amount_due DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS amount_paid DECIMAL(10,2) DEFAULT 0.00;

-- Migrate existing data: member_share -> amount_due
UPDATE team_members SET amount_due = member_share WHERE amount_due = 0;

-- If fee_paid, set amount_paid = amount_due (assume fully paid)
UPDATE team_members SET amount_paid = amount_due WHERE fee_paid = TRUE AND amount_paid = 0;

-- Drop old columns
ALTER TABLE team_members DROP COLUMN IF EXISTS member_share;
ALTER TABLE team_members DROP COLUMN IF EXISTS fee_paid;
ALTER TABLE team_members DROP COLUMN IF EXISTS payment_id;

-- Phase 4: Add team_member_id to payments table (like enrollment_id)
ALTER TABLE payments ADD COLUMN IF NOT EXISTS team_member_id INTEGER REFERENCES team_members(id);

-- Phase 5: Remove soft delete from competitions
ALTER TABLE competitions DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE competitions DROP COLUMN IF EXISTS deleted_by;

-- Phase 6: Remove soft delete from teams
ALTER TABLE teams DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE teams DROP COLUMN IF EXISTS deleted_by;
