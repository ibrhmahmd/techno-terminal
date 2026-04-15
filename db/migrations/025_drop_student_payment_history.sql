-- Migration 025: Drop student_payment_history table and dependent objects
-- Created: 2026-04-15
-- Purpose: Remove redundant student_payment_history table (data is in payments table)

-- Drop dependent views first
DROP VIEW IF EXISTS v_student_payment_history CASCADE;

-- Drop table and all constraints/indexes
DROP TABLE IF EXISTS student_payment_history CASCADE;

-- Verify cleanup
-- Note: Indexes and foreign keys are automatically dropped with the table
