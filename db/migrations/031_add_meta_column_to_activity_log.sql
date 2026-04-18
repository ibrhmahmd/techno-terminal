-- Migration 031: Add meta column to student_activity_log
-- Created: 2026-04-18
-- Purpose: Add missing meta column that the application model expects

-- Add meta column to student_activity_log table
ALTER TABLE student_activity_log ADD COLUMN IF NOT EXISTS meta JSONB;

-- Create index for meta JSONB queries
CREATE INDEX IF NOT EXISTS idx_activity_log_meta ON student_activity_log USING GIN(meta);
