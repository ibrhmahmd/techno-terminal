-- Add ON DELETE SET NULL to FK constraints on users(id) that were
-- created by migrations without an ON DELETE action (defaults to RESTRICT).
-- competitions.deleted_by and teams.deleted_by columns were never added —
-- migration 035 used IF NOT EXISTS and they didn't exist yet.

ALTER TABLE student_activity_log
  DROP CONSTRAINT IF EXISTS student_activity_log_performed_by_fkey,
  ADD CONSTRAINT student_activity_log_performed_by_fkey
    FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE students
  DROP CONSTRAINT IF EXISTS students_deleted_by_fkey,
  ADD CONSTRAINT students_deleted_by_fkey
    FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE payments
  DROP CONSTRAINT IF EXISTS payments_deleted_by_fkey,
  ADD CONSTRAINT payments_deleted_by_fkey
    FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;
