-- Migration 028: Drop Deprecated Tables and Views
-- Created: 2026-04-15
-- Purpose: Remove materialized tables and views superseded by v_enrollment_balance
--          Cleans up payment_allocations, student_balances, enrollment_balance_history, student_credits

-- Drop dependent views first
DROP VIEW IF EXISTS v_payment_allocations_detailed CASCADE;

-- Drop deprecated tables (foreign keys already have CASCADE from migration 027)
DROP TABLE IF EXISTS payment_allocations CASCADE;
DROP TABLE IF EXISTS student_credits CASCADE;
DROP TABLE IF EXISTS enrollment_balance_history CASCADE;
DROP TABLE IF EXISTS student_balances CASCADE;

-- Update comments on remaining tables
COMMENT ON TABLE payments IS 'Source of truth for all financial transactions. Enrollment balance computed via v_enrollment_balance view.';
COMMENT ON VIEW v_enrollment_balance IS 'Real-time enrollment balance with payment_status (not_paid/partially_paid/paid) and amount_remaining.';
