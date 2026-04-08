-- Migration: 020_fix_groups_status_constraint
-- Purpose: Update groups status check constraint to match constants.py
-- Created: 2026-04-08
-- Issue: Database only allowed ('active', 'completed', 'cancelled') but code uses ('active', 'inactive', 'completed', 'archived')

-- First, update any rows with invalid status to 'active'
UPDATE groups 
SET status = 'active' 
WHERE status NOT IN ('active', 'inactive', 'completed', 'archived');

-- Drop the existing constraint
ALTER TABLE groups DROP CONSTRAINT IF EXISTS groups_status_check;

-- Add the corrected constraint
ALTER TABLE groups ADD CONSTRAINT groups_status_check 
    CHECK (status IN ('active', 'inactive', 'completed', 'archived'));
