-- Migration 032: Add Soft Delete Support to Students and Payments
-- Created: 2026-04-19
-- Purpose: Enable logical deletion with restore capability for students and payments

-- ── Students Table ───────────────────────────────────────────────────────────
ALTER TABLE students ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
ALTER TABLE students ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) DEFAULT NULL;

-- Partial index: Only non-deleted students (keeps queries fast)
CREATE INDEX IF NOT EXISTS idx_students_active ON students(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_students_deleted ON students(deleted_at) WHERE deleted_at IS NOT NULL;

-- ── Payments Table ───────────────────────────────────────────────────────────
ALTER TABLE payments ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) DEFAULT NULL;

-- Partial indexes for payments
CREATE INDEX IF NOT EXISTS idx_payments_active ON payments(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_payments_deleted ON payments(deleted_at) WHERE deleted_at IS NOT NULL;

-- ── Views for Active-Only Queries ───────────────────────────────────────────
CREATE OR REPLACE VIEW active_students AS
SELECT * FROM students WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_payments AS
SELECT * FROM payments WHERE deleted_at IS NULL;

-- Soft-deleted records view (for admin recovery interface)
CREATE OR REPLACE VIEW deleted_students AS
SELECT * FROM students WHERE deleted_at IS NOT NULL;

CREATE OR REPLACE VIEW deleted_payments AS
SELECT * FROM payments WHERE deleted_at IS NOT NULL;

-- ── Add Comment Documentation ───────────────────────────────────────────────
COMMENT ON COLUMN students.deleted_at IS 
    'Soft delete timestamp. NULL = active record. Set = logically deleted but recoverable.';
COMMENT ON COLUMN students.deleted_by IS 
    'User ID who performed the soft delete.';
COMMENT ON COLUMN payments.deleted_at IS 
    'Soft delete timestamp. NULL = active record. Set = logically deleted but recoverable.';
COMMENT ON COLUMN payments.deleted_by IS 
    'User ID who performed the soft delete (usually via student cascade).';

-- ── Rollback Procedure ───────────────────────────────────────────────────────
-- To rollback this migration, execute:
-- DROP VIEW IF EXISTS active_students;
-- DROP VIEW IF EXISTS active_payments;
-- DROP VIEW IF EXISTS deleted_students;
-- DROP VIEW IF EXISTS deleted_payments;
-- DROP INDEX IF EXISTS idx_students_active;
-- DROP INDEX IF EXISTS idx_students_deleted;
-- DROP INDEX IF EXISTS idx_payments_active;
-- DROP INDEX IF EXISTS idx_payments_deleted;
-- ALTER TABLE students DROP COLUMN IF EXISTS deleted_at;
-- ALTER TABLE students DROP COLUMN IF EXISTS deleted_by;
-- ALTER TABLE payments DROP COLUMN IF EXISTS deleted_at;
-- ALTER TABLE payments DROP COLUMN IF EXISTS deleted_by;
