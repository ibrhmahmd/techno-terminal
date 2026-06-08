-- Migration 069: Fix Student Activity Log Cascade Delete
-- Created: 2026-06-08
-- Purpose: Add ON DELETE CASCADE to student_activity_log's student_id foreign key constraint
--          to allow permanent deletion of students.

ALTER TABLE student_activity_log
    DROP CONSTRAINT IF EXISTS student_activity_log_student_id_fkey,
    ADD CONSTRAINT student_activity_log_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;
