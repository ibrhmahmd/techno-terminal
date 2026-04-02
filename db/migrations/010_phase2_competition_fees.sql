-- =============================================================================
-- Migration 010: Phase 2 — Competition Fees Architecture
-- =============================================================================
-- Purpose:
--   Moves the fee definition from teams.enrollment_fee_per_student to a proper
--   source-of-truth on competitions.fee_per_student, and adds a historical
--   snapshot column team_members.member_share so that payment receipts remain
--   accurate even if the competition's fee is later edited.
--
-- Safe to re-run? YES — all statements use IF NOT EXISTS / IF EXISTS guards.
-- Destructive?    NO  — no columns or data are dropped.
--
-- Apply:
--   psql "$DATABASE_URL" -f db/migrations/010_phase2_competition_fees.sql
-- =============================================================================

BEGIN;

-- ── 1. Add fee_per_student to competitions ───────────────────────────────────
-- This is the canonical, admin-editable fee for a given competition event.
-- Existing rows default to 0.00 (no fee) — update them manually as needed.
ALTER TABLE competitions
    ADD COLUMN IF NOT EXISTS fee_per_student NUMERIC(10, 2) NOT NULL DEFAULT 0.00;

COMMENT ON COLUMN competitions.fee_per_student IS
    'Base fee charged to every student registered under any team in this competition. '
    'Changes here do NOT retroactively affect team_members.member_share.';


-- ── 2. Add member_share to team_members ──────────────────────────────────────
-- Snapshotted at the moment a student is added to a team. Preserves the fee
-- that was in force at registration time, independent of later edits to
-- competitions.fee_per_student.
ALTER TABLE team_members
    ADD COLUMN IF NOT EXISTS member_share NUMERIC(10, 2) NOT NULL DEFAULT 0.00;

COMMENT ON COLUMN team_members.member_share IS
    'Snapshot of competitions.fee_per_student captured when this student was '
    'added to the team. Used as the authoritative amount for receipt generation.';


-- ── 3. Backfill existing rows from the legacy teams column ───────────────────
-- For any team member already in the database, seed member_share from the team's
-- old enrollment_fee_per_student if it was set and member_share is still 0.
UPDATE team_members tm
SET    member_share = t.enrollment_fee_per_student
FROM   teams t
WHERE  tm.team_id               = t.id
AND    t.enrollment_fee_per_student IS NOT NULL
AND    t.enrollment_fee_per_student  > 0
AND    tm.member_share           = 0.00;


-- ── NOTE: teams.enrollment_fee_per_student ───────────────────────────────────
-- The old column is intentionally LEFT IN PLACE to avoid data loss.
-- It is no longer read by the application (removed from SQLModel).
-- A future cleanup migration may DROP it once the backfill is verified.

COMMIT;
