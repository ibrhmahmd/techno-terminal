-- =============================================================================
-- Migration 085: drop audit scenario H, "Active Payments for Soft-Deleted Students" (#275)
--
-- Deleting a student keeps their payments live on purpose (#175: the cash was received),
-- so the check flagged every deleted student's payments. The scenario codes do not shift:
-- A-G and I remain, H is retired. v_audit_summary is recreated without its H row (it feeds the
-- Logfire audit gauges). Safe to re-run. Apply to staging first, then production.
-- Rollback: re-create v_audit_ghost_payments and the H row from migration 074.
-- =============================================================================

BEGIN;

CREATE OR REPLACE VIEW v_audit_summary AS
SELECT 'A' AS code, 'INFO'    AS severity, 'Zero-Charge Active Enrollments'            AS label,
       COUNT(*) AS anomaly_count
FROM enrollments e JOIN students s ON s.id = e.student_id
WHERE e.status = 'active' AND (e.amount_due IS NULL OR e.amount_due = 0) AND s.deleted_at IS NULL

UNION ALL

SELECT 'B', 'WARNING', 'Overpaid Enrollments (Credit Balances)', COUNT(*) FROM (
    SELECT e.id FROM enrollments e JOIN students s ON s.id = e.student_id
    LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
    WHERE s.deleted_at IS NULL
    GROUP BY e.id, e.amount_due, e.discount_applied
    HAVING (
        COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
    ) > (e.amount_due - COALESCE(e.discount_applied, 0))
) sub

UNION ALL

SELECT 'C', 'WARNING', 'Orphaned Payments (No Enrollment Link)', COUNT(*) FROM payments p
JOIN students s ON s.id = p.student_id
WHERE p.enrollment_id IS NULL AND p.payment_type = 'course_level'
  AND p.deleted_at IS NULL AND s.deleted_at IS NULL

UNION ALL

SELECT 'D', 'ERROR', 'Duplicate Active Enrollments', COUNT(*) FROM (
    SELECT student_id, group_id FROM enrollments WHERE status = 'active'
    GROUP BY student_id, group_id HAVING COUNT(*) > 1
) sub

UNION ALL

SELECT 'E', 'INFO', 'Active Enrollments on Dead Groups', COUNT(*) FROM enrollments e
JOIN students s ON s.id = e.student_id JOIN groups g ON g.id = e.group_id
WHERE e.status = 'active' AND g.status IN ('inactive','completed','archived') AND s.deleted_at IS NULL

UNION ALL

SELECT 'F', 'WARNING', 'Dropped/Transferred with Unrefunded Balance', COUNT(*) FROM (
    SELECT e.id FROM enrollments e JOIN students s ON s.id = e.student_id
    LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
    WHERE e.status IN ('dropped','transferred') AND s.deleted_at IS NULL
    GROUP BY e.id
    HAVING (
        COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
    ) > 0
) sub

UNION ALL

SELECT 'G', 'INFO', 'Level Mismatch (No group_levels Row)', COUNT(*) FROM enrollments e
JOIN students s ON s.id = e.student_id
WHERE s.deleted_at IS NULL
  AND NOT EXISTS (SELECT 1 FROM group_levels gl
    WHERE gl.group_id = e.group_id AND gl.level_number = e.level_number)

UNION ALL

SELECT 'I', 'WARNING', 'Full or Over-Discounts (>= 100%)', COUNT(*) FROM enrollments e
JOIN students s ON s.id = e.student_id
WHERE s.deleted_at IS NULL
  AND e.discount_applied IS NOT NULL AND e.discount_applied >= e.amount_due

ORDER BY code;

COMMENT ON VIEW v_audit_summary IS
'Balance integrity audit summary. Run SELECT * FROM v_audit_summary to get anomaly counts for all 8 scenarios (A-G, I). Drill into v_audit_<scenario> for detail rows. ERROR = immediate action; WARNING = review this week; INFO = document and clean.';

DROP VIEW IF EXISTS v_audit_ghost_payments;

COMMIT;
