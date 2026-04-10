-- Migration: 021_fix_attendance_status_constraint
-- Purpose: Update attendance status check constraint to include 'cancelled'
-- Created: 2026-04-08
-- Issue: Database constraint only allowed ('present', 'absent') but code uses ('present', 'absent', 'cancelled')

-- First, update any rows with invalid status to 'absent'
UPDATE attendance 
SET status = 'absent' 
WHERE status NOT IN ('present', 'absent', 'cancelled');

-- Drop the existing constraint if it exists
ALTER TABLE attendance DROP CONSTRAINT IF EXISTS attendance_status_check;

-- Add the corrected constraint
ALTER TABLE attendance ADD CONSTRAINT attendance_status_check 
    CHECK (status IN ('present', 'absent', 'cancelled'));
