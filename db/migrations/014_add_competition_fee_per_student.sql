-- Migration: 014_add_competition_fee_per_student
-- Purpose: Add missing fee_per_student column to competitions table
-- Created: 2026-04-07

-- Add the missing column with default 0.0
ALTER TABLE competitions 
ADD COLUMN IF NOT EXISTS fee_per_student NUMERIC(10, 2) DEFAULT 0.0;

-- Update existing rows to have 0.0 as default
UPDATE competitions 
SET fee_per_student = 0.0 
WHERE fee_per_student IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN competitions.fee_per_student IS 'Entry fee per student for this competition';
