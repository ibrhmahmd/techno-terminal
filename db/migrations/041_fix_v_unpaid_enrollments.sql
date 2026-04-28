-- Migration 041: Fix v_unpaid_enrollments — Remove payment_allocations Dependency
-- Created: 2026-04-27
-- Purpose: Recreate v_unpaid_enrollments using v_enrollment_balance (payments-only finance model)
--          The original definition (migration 020) joined on payment_allocations which was
--          deprecated in migration 028 and should have been dropped. This fix removes that
--          dependency entirely, using the canonical v_enrollment_balance view instead.
--
-- BEFORE APPLYING: Confirm v_unpaid_enrollments current definition:
--   SELECT definition FROM pg_views WHERE viewname = 'v_unpaid_enrollments';

-- ── Drop old view ─────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS v_unpaid_enrollments;

-- ── Recreate using v_enrollment_balance (no payment_allocations dependency) ──
CREATE OR REPLACE VIEW v_unpaid_enrollments AS
SELECT
    e.id                                                   AS enrollment_id,
    e.student_id,
    s.full_name                                            AS student_name,
    s.phone                                                AS student_phone,
    e.group_id,
    g.name                                                 AS group_name,
    c.name                                                 AS course_name,
    e.level_number,
    e.amount_due,
    e.discount_applied,
    (e.amount_due - COALESCE(e.discount_applied, 0))       AS net_due,
    COALESCE(vb.total_paid, 0)                             AS total_paid,
    -- Amount remaining: never goes negative
    GREATEST(
        (e.amount_due - COALESCE(e.discount_applied, 0)) - COALESCE(vb.total_paid, 0),
        0
    )                                                      AS remaining_balance,
    -- Signed balance: positive = debt, negative = credit/overpayment
    COALESCE(
        vb.balance,
        (e.amount_due - COALESCE(e.discount_applied, 0))
    )                                                      AS balance,
    -- Payment status from canonical view
    COALESCE(vb.payment_status, 'not_paid')                AS payment_status,
    e.status                                               AS enrollment_status,
    e.enrolled_at,
    e.notes
FROM enrollments e
JOIN     students s ON s.id = e.student_id
JOIN     groups   g ON g.id = e.group_id
LEFT JOIN courses c ON c.id = g.course_id
LEFT JOIN v_enrollment_balance vb ON vb.enrollment_id = e.id
-- Only active enrollments with an outstanding balance
WHERE e.status = 'active'
  AND GREATEST(
        (e.amount_due - COALESCE(e.discount_applied, 0)) - COALESCE(vb.total_paid, 0),
        0
      ) > 0
ORDER BY remaining_balance DESC;

COMMENT ON VIEW v_unpaid_enrollments IS
'Active enrollments with outstanding balance. Rebuilt in migration 041 to use '
'v_enrollment_balance (payments-only model). No longer depends on payment_allocations.';

-- ── Rollback ──────────────────────────────────────────────────────────────────
-- To rollback, restore from migration 020 definition (requires payment_allocations to exist)
