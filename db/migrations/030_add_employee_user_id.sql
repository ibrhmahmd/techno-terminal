-- Migration: Add user_id column to employees table
-- Created: 2024-01-20
-- Purpose: Link employees to user accounts for authentication

BEGIN;

-- Add user_id column to employees table
ALTER TABLE employees
    ADD COLUMN user_id INTEGER NULL;

-- Add unique constraint (one user per employee max)
ALTER TABLE employees
    ADD CONSTRAINT uq_employees_user_id UNIQUE (user_id);

-- Add foreign key constraint to users table
ALTER TABLE employees
    ADD CONSTRAINT fk_employees_user_id
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE SET NULL;

COMMIT;