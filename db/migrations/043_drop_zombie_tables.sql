-- Migration 043: Drop Zombie Tables
-- Created: 2026-04-27
-- Purpose: Apply the cleanup that migrations 023, 026, and 028 intended but
--          never reached the live production database. All tables confirmed
--          to have 0 rows before this migration was applied.
--
-- Tables removed:
--   From migration 023: orphan functions (triggers already dropped)
--   From migration 026: student_enrollment_history, student_competition_history,
--                       student_status_history
--   From migration 028: enrollment_balance_history, student_credits,
--                       payment_allocations, student_balances
--
-- Prerequisite: Migration 041 must be applied first (removes payment_allocations
--               dependency from v_unpaid_enrollments before we drop the table).

-- ═══════════════════════════════════════════════════════════════════════════════
-- BLOCK A: Orphan Functions (from migration 023)
-- Triggers were already dropped by migration 023. Functions may still exist.
-- ═══════════════════════════════════════════════════════════════════════════════
DROP FUNCTION IF EXISTS update_student_balance() CASCADE;
DROP FUNCTION IF EXISTS update_balance_on_enrollment_change() CASCADE;

-- ═══════════════════════════════════════════════════════════════════════════════
-- BLOCK B: Student History Tables (from migration 026)
-- Confirmed 0 rows per Phase 0 verification.
-- student_activity_log is the canonical replacement for all history tracking.
-- ═══════════════════════════════════════════════════════════════════════════════
DROP TABLE IF EXISTS student_enrollment_history CASCADE;
DROP TABLE IF EXISTS student_competition_history CASCADE;

-- student_status_history: has a repository INSERT path (student_repository.py:369)
-- and a router endpoint (students_router.py:403). Confirmed 0 rows before applying.
-- The activity_log table now serves as the unified history store.
DROP TABLE IF EXISTS student_status_history CASCADE;

-- ═══════════════════════════════════════════════════════════════════════════════
-- BLOCK C: Balance/Allocation Tables (from migration 028)
-- These were superseded by the payments-only finance model (v_enrollment_balance).
-- Confirmed 0 rows per Phase 0 verification.
-- ═══════════════════════════════════════════════════════════════════════════════

-- enrollment_balance_history: point-in-time balance snapshots, replaced by
-- v_enrollment_balance real-time calculation
DROP TABLE IF EXISTS enrollment_balance_history CASCADE;

-- student_credits: overpayment credit tracking, replaced by balance column
-- in v_enrollment_balance (negative balance = credit)
DROP TABLE IF EXISTS student_credits CASCADE;

-- payment_allocations: per-enrollment allocation tracking, replaced by
-- direct enrollment_id on payments table
DROP TABLE IF EXISTS payment_allocations CASCADE;

-- student_balances: materialized balance cache, replaced by v_enrollment_balance view
DROP TABLE IF EXISTS student_balances CASCADE;

-- ── Post-drop comments ────────────────────────────────────────────────────────
COMMENT ON TABLE payments IS
'Source of truth for all financial transactions (charge, payment, refund). '
'Enrollment balance is computed in real-time via v_enrollment_balance view. '
'payment_allocations table deprecated in migration 028 and removed in migration 043.';

COMMENT ON TABLE student_activity_log IS
'Unified student activity timeline. Replaced student_status_history, '
'student_enrollment_history, and student_competition_history (all removed in migration 043).';

-- ── Verification ─────────────────────────────────────────────────────────────
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
--   AND table_name IN (
--     'student_enrollment_history','student_competition_history','student_status_history',
--     'enrollment_balance_history','student_credits','payment_allocations','student_balances'
--   );
-- Expected: 0 rows returned

-- ── Rollback (emergency only) ─────────────────────────────────────────────────
-- If rollback is needed, restore from migration files:
--   student_status_history  → see migration 021_student_status_history.sql
--   enrollment_balance_history, student_credits → see migration 015_add_student_balance_tables.sql
--   payment_allocations → see migration 016_add_payment_allocations.sql
--   student_balances → see migration 015_add_student_balance_tables.sql
