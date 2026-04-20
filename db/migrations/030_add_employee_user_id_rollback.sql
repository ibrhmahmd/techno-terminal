-- Rollback: Remove user_id column from employees table
-- Run this to revert the 006 migration

BEGIN;

-- Remove foreign key constraint
ALTER TABLE employees
    DROP CONSTRAINT IF EXISTS fk_employees_user_id;

-- Remove unique constraint
ALTER TABLE employees
    DROP CONSTRAINT IF EXISTS uq_employees_user_id;

-- Remove user_id column
ALTER TABLE employees
    DROP COLUMN IF EXISTS user_id;

COMMIT;
