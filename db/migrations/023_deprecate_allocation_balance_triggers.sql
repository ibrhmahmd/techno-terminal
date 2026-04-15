-- Migration 023: Deprecate allocation-based balance triggers
-- Purpose: In payments-only finance mode, balance calculations no longer rely on payment_allocations.
-- Keep legacy tables for compatibility, but disable runtime trigger dependency.

DROP TRIGGER IF EXISTS trg_update_balance_on_payment ON payments;
DROP TRIGGER IF EXISTS trg_update_balance_on_enrollment ON enrollments;

DROP FUNCTION IF EXISTS update_student_balance();
DROP FUNCTION IF EXISTS update_balance_on_enrollment_change();
