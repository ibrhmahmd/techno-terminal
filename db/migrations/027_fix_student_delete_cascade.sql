-- Migration 027: Fix Student Delete Cascade
-- Created: 2026-04-15
-- Purpose: Add ON DELETE CASCADE to student_balances and related tables
--          to allow student deletion when balance records exist.

-- Fix student_balances foreign key
ALTER TABLE student_balances
    DROP CONSTRAINT IF EXISTS student_balances_student_id_fkey,
    ADD CONSTRAINT student_balances_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

-- Fix enrollment_balance_history foreign key
ALTER TABLE enrollment_balance_history
    DROP CONSTRAINT IF EXISTS enrollment_balance_history_student_id_fkey,
    ADD CONSTRAINT enrollment_balance_history_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

-- Fix student_credits foreign key  
ALTER TABLE student_credits
    DROP CONSTRAINT IF EXISTS student_credits_student_id_fkey,
    ADD CONSTRAINT student_credits_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

COMMENT ON TABLE student_balances IS
'Materialized student balance totals. Records cascade-deleted when student is removed.';
