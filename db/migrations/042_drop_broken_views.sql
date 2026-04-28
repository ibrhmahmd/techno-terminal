-- Migration 042: Drop Confirmed-Broken Views
-- Created: 2026-04-27
-- Purpose: Remove views that reference tables dropped in migration 028
--          (student_balances, payment_allocations). These views fail at query
--          time and have zero application code references.
--
-- Views dropped:
--   1. v_student_financial_summary  — depends on student_balances (dropped mig 028)
--   2. v_payment_allocations_detailed — depends on payment_allocations (dropped mig 028)
--
-- Prerequisite: Migration 041 must be applied first (fixes v_unpaid_enrollments
--               which also depended on payment_allocations).

-- ── 1. Drop v_student_financial_summary ──────────────────────────────────────
-- Originally created in migration 020.
-- Joined on student_balances (materialized table dropped in migration 028).
-- Replacement: query v_enrollment_balance directly for per-enrollment balance.
DROP VIEW IF EXISTS v_student_financial_summary CASCADE;

-- ── 2. Drop v_payment_allocations_detailed ───────────────────────────────────
-- Originally created in migration 016 alongside payment_allocations table.
-- Migration 028 attempted to drop it but may not have been applied.
-- Zero references in application code.
DROP VIEW IF EXISTS v_payment_allocations_detailed CASCADE;

COMMENT ON SCHEMA public IS
'Removed v_student_financial_summary and v_payment_allocations_detailed in migration 042. '
'Both depended on tables dropped in migration 028 (student_balances, payment_allocations).';

-- ── Verification ─────────────────────────────────────────────────────────────
-- SELECT viewname FROM pg_views WHERE schemaname = 'public'
--   AND viewname IN ('v_student_financial_summary', 'v_payment_allocations_detailed');
-- Expected: 0 rows
