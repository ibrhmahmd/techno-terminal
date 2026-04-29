-- =============================================================================
-- ADDITIONAL CONSTRAINTS
-- Complex constraints and exclusions added after table creation
-- =============================================================================

-- =============================================================================
-- EXCLUSION CONSTRAINTS (if using btree_gist extension)
-- =============================================================================

-- Prevent overlapping active enrollments for same student in same group
-- Note: This requires the btree_gist extension
-- 
-- CREATE EXTENSION IF NOT EXISTS btree_gist;
-- ALTER TABLE enrollments
--     ADD CONSTRAINT no_overlapping_enrollments
--     EXCLUDE USING gist (
--         student_id WITH =,
--         group_id WITH =,
--         status WITH =
--     ) WHERE (status = 'active');

-- =============================================================================
-- COMPLEX CHECK CONSTRAINTS
-- =============================================================================

-- Ensure enrollment dates are reasonable (not in future, not too old)
-- ALTER TABLE enrollments
--     ADD CONSTRAINT chk_enrollment_date_reasonable
--     CHECK (enrolled_at IS NULL OR (enrolled_at >= '2020-01-01' AND enrolled_at <= CURRENT_DATE + INTERVAL '1 day'));

-- Ensure payment dates match receipt dates
-- ALTER TABLE payments
--     ADD CONSTRAINT chk_payment_created_with_receipt
--     CHECK (
--         created_at >= (SELECT MIN(created_at) FROM receipts WHERE receipts.id = payments.receipt_id)
--     );

-- =============================================================================
-- FOREIGN KEY ADDITIONS (if not in table definitions)
-- =============================================================================

-- These are already defined in table creation, but listed here for reference:
-- - enrollments.student_id → students.id
-- - enrollments.group_id → groups.id
-- - payments.receipt_id → receipts.id
-- - payments.student_id → students.id
-- - etc.

-- =============================================================================
-- INDEX CONSTRAINTS (Partial Unique Indexes)
-- =============================================================================

-- Only one active enrollment per student per group (already in 05_tables_enrollments.sql)
-- CREATE UNIQUE INDEX idx_enrollments_active_unique ON enrollments(student_id, group_id) WHERE status = 'active';

-- Only one default receipt template
-- CREATE UNIQUE INDEX idx_receipt_templates_default_unique ON receipt_templates(is_default) WHERE is_default = TRUE;

-- =============================================================================
-- NOTES
-- =============================================================================
-- 
-- Most constraints are defined inline in table creation statements.
-- This file is reserved for:
-- 1. Complex constraints that reference other tables
-- 2. Exclusion constraints requiring extensions
-- 3. Constraints added after initial schema deployment
-- 4. Temporary constraint relaxations during migrations
--
