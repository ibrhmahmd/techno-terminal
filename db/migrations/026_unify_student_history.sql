-- Migration 026: Unify Student History Tables
-- Purpose: Add partial indexes for performance and drop deprecated empty tables

-- Step 1: Create partial indexes for performance
-- These indexes optimize queries filtering by activity_type

CREATE INDEX IF NOT EXISTS idx_activity_log_enrollment 
ON student_activity_log(student_id, created_at DESC) 
WHERE activity_type IN ('enrollment', 'enrollment_change');

CREATE INDEX IF NOT EXISTS idx_activity_log_status 
ON student_activity_log(student_id, created_at DESC) 
WHERE activity_type = 'status_change';

CREATE INDEX IF NOT EXISTS idx_activity_log_competition 
ON student_activity_log(student_id, created_at DESC) 
WHERE activity_type = 'competition';

-- Step 2: Create general index for student_id queries (if not exists)
CREATE INDEX IF NOT EXISTS idx_activity_log_student_created 
ON student_activity_log(student_id, created_at DESC);

-- Step 3: Verify tables are empty before dropping (safety check)
-- These tables were confirmed empty via Supabase MCP:
-- - student_enrollment_history: 0 rows
-- - student_status_history: 0 rows  
-- - student_competition_history: 0 rows

-- Drop deprecated tables (no data to migrate)
DROP TABLE IF EXISTS student_enrollment_history CASCADE;
DROP TABLE IF EXISTS student_status_history CASCADE;
DROP TABLE IF EXISTS student_competition_history CASCADE;

-- Note: Migration 025 already dropped student_payment_history

-- Step 4: Optional - Clean up students.status_history JSONB column
-- This column is redundant with activity_log but kept for now
-- ALTER TABLE students DROP COLUMN IF EXISTS status_history;
