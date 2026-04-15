-- db/migrations/022_student_indexes.sql
CREATE INDEX IF NOT EXISTS idx_students_status   ON students(status);
CREATE INDEX IF NOT EXISTS idx_students_dob      ON students(date_of_birth);
CREATE INDEX IF NOT EXISTS idx_students_active   ON students(is_active);
COMMENT ON COLUMN students.is_active IS 'Deprecated: use status column instead';
