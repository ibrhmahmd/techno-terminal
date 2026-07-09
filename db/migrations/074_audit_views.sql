-- =============================================================================
-- Migration 074 — Balance Integrity Audit Views
-- Spec: specs/036-balance-integrity-audit/spec.md
-- Date: 2026-07-09
--
-- Creates 10 read-only audit views for detecting suspicious/false student
-- balances and enrollments. Use via Supabase SQL Editor or API.
--
-- Usage:
--   SELECT * FROM v_audit_summary;                    -- health check
--   SELECT * FROM v_audit_duplicate_enrollments;      -- ERROR tier
--   SELECT * FROM v_audit_overpaid_enrollments;       -- WARNING tier
--   SELECT * FROM v_audit_zero_charge_enrollments     -- INFO tier
--     WHERE enrolled_at >= '2026-07-01';              -- filter migration artifacts
--
-- Severity tiers:
--   ERROR   (D, H) — direct financial risk, investigate immediately
--   WARNING (B, C, F, I) — financial discrepancy, review within week
--   INFO    (A, E, G) — data hygiene, review and document
-- =============================================================================

-- =============================================================================
-- SCENARIO A 🔵 INFO — Zero-Charge Active Enrollments
-- Active enrollments where amount_due is NULL or 0
-- =============================================================================
CREATE OR REPLACE VIEW v_audit_zero_charge_enrollments AS
SELECT
    e.id           AS enrollment_id,
    s.full_name    AS student_name,
    s.phone        AS student_phone,
    g.name         AS group_name,
    c.name         AS course_name,
    e.level_number,
    e.enrolled_at,
    e.amount_due,
    e.discount_applied,
    e.notes,
    e.created_at
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
WHERE e.status = 'active'
  AND (e.amount_due IS NULL OR e.amount_due = 0)
  AND s.deleted_at IS NULL
ORDER BY e.enrolled_at DESC;

COMMENT ON VIEW v_audit_zero_charge_enrollments IS
'INFO: Active enrollments with amount_due = NULL or 0. May be intentional (scholarship) or a data-entry omission. Filter by enrolled_at to exclude known migration artifacts.';

-- =============================================================================
-- SCENARIO B 🟡 WARNING — Overpaid Enrollments (Credit Balances)
-- Net payments exceed net_due — duplicate payment or credit not returned
-- =============================================================================
CREATE OR REPLACE VIEW v_audit_overpaid_enrollments AS
SELECT
    e.id                                             AS enrollment_id,
    s.full_name                                      AS student_name,
    s.phone,
    g.name                                           AS group_name,
    c.name                                           AS course_name,
    e.level_number,
    e.status                                         AS enrollment_status,
    e.amount_due,
    COALESCE(e.discount_applied, 0)                  AS discount_applied,
    (e.amount_due - COALESCE(e.discount_applied, 0)) AS net_due,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
                                                     AS total_paid,
    (
        COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
      - (e.amount_due - COALESCE(e.discount_applied, 0))
    )                                                AS overpaid_by
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
WHERE s.deleted_at IS NULL
GROUP BY e.id, s.full_name, s.phone, g.name, c.name,
         e.level_number, e.status, e.amount_due, e.discount_applied
HAVING (
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
  - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
) > (e.amount_due - COALESCE(e.discount_applied, 0))
ORDER BY overpaid_by DESC;

COMMENT ON VIEW v_audit_overpaid_enrollments IS
'WARNING: Enrollments where total_paid > net_due. Possible duplicate payment or credit owed back. overpaid_by column shows exact excess amount in EGP.';

-- =============================================================================
-- SCENARIO C 🟡 WARNING — Orphaned Payments (No Enrollment Link)
-- course_level payments with no enrollment_id — money unattributable
-- =============================================================================
CREATE OR REPLACE VIEW v_audit_orphaned_payments AS
SELECT
    p.id               AS payment_id,
    r.receipt_number,
    s.full_name        AS student_name,
    s.phone,
    p.amount,
    p.transaction_type,
    p.payment_type,
    p.notes            AS payment_notes,
    r.paid_at,
    r.payment_method,
    p.created_at
FROM payments p
JOIN students s ON s.id = p.student_id
JOIN receipts r ON r.id = p.receipt_id
WHERE p.enrollment_id IS NULL
  AND p.payment_type = 'course_level'
  AND p.deleted_at IS NULL
  AND s.deleted_at IS NULL
ORDER BY r.paid_at DESC;

COMMENT ON VIEW v_audit_orphaned_payments IS
'WARNING: Non-deleted course_level payments with no enrollment_id. Money was collected but cannot be attributed to any enrollment.';

-- =============================================================================
-- SCENARIO D 🔴 ERROR — Duplicate Active Enrollments
-- Same (student_id, group_id) pair has >1 active enrollment row
-- =============================================================================
CREATE OR REPLACE VIEW v_audit_duplicate_enrollments AS
SELECT
    s.id               AS student_id,
    s.full_name        AS student_name,
    s.phone,
    g.id               AS group_id,
    g.name             AS group_name,
    c.name             AS course_name,
    COUNT(e.id)        AS active_enrollment_count,
    STRING_AGG(e.id::text, ', ' ORDER BY e.id) AS enrollment_ids,
    MIN(e.enrolled_at) AS first_enrolled,
    MAX(e.enrolled_at) AS last_enrolled,
    SUM(e.amount_due)  AS total_amount_due_across_duplicates
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
WHERE e.status = 'active'
  AND s.deleted_at IS NULL
GROUP BY s.id, s.full_name, s.phone, g.id, g.name, c.name
HAVING COUNT(e.id) > 1
ORDER BY active_enrollment_count DESC;

COMMENT ON VIEW v_audit_duplicate_enrollments IS
'ERROR: Student-group pairs with >1 active enrollment. Likely a pre-index bulk-import artifact. Each duplicate represents a potential double-charge.';

-- =============================================================================
-- SCENARIO E 🔵 INFO — Active Enrollments on Inactive/Archived Groups
-- Enrollment is active but parent group is no longer active
-- =============================================================================
CREATE OR REPLACE VIEW v_audit_dead_group_enrollments AS
SELECT
    e.id           AS enrollment_id,
    s.full_name    AS student_name,
    s.phone,
    g.id           AS group_id,
    g.name         AS group_name,
    g.status       AS group_status,
    c.name         AS course_name,
    e.level_number,
    e.enrolled_at,
    e.amount_due,
    COALESCE(e.discount_applied, 0) AS discount_applied,
    e.notes
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
WHERE e.status = 'active'
  AND g.status IN ('inactive','completed','archived')
  AND s.deleted_at IS NULL
ORDER BY g.status, g.name;

COMMENT ON VIEW v_audit_dead_group_enrollments IS
'INFO: Active enrollments in groups that are no longer active. Likely cleanup lag — enrollment should have been transitioned when group ended.';

-- =============================================================================
-- SCENARIO F 🟡 WARNING — Dropped/Transferred with Unrefunded Balance
-- Student left but money was never refunded or carried forward
-- =============================================================================
CREATE OR REPLACE VIEW v_audit_unrefunded_exits AS
SELECT
    e.id                                             AS enrollment_id,
    s.full_name                                      AS student_name,
    s.phone,
    g.name                                           AS group_name,
    c.name                                           AS course_name,
    e.level_number,
    e.status                                         AS enrollment_status,
    e.amount_due,
    COALESCE(e.discount_applied, 0)                  AS discount_applied,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
                                                     AS net_collected,
    e.transferred_from,
    e.notes
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
WHERE e.status IN ('dropped','transferred')
  AND s.deleted_at IS NULL
GROUP BY e.id, s.full_name, s.phone, g.name, c.name
HAVING (
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
  - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
) > 0
ORDER BY net_collected DESC;

COMMENT ON VIEW v_audit_unrefunded_exits IS
'WARNING: Dropped/transferred enrollments with net-positive payments and no offsetting refund. net_collected = money owed back to student or forward to new enrollment.';

-- =============================================================================
-- SCENARIO G 🔵 INFO — Level Mismatch (No Matching group_levels Row)
-- Enrollment references a (group_id, level_number) with no group_levels entry
-- Note: Report 4 (Round Cost) emits data_quality_warning when this has results
-- =============================================================================
CREATE OR REPLACE VIEW v_audit_level_mismatch AS
SELECT
    e.id           AS enrollment_id,
    s.full_name    AS student_name,
    s.phone,
    g.id           AS group_id,
    g.name         AS group_name,
    c.name         AS course_name,
    e.level_number AS enrollment_level,
    e.status       AS enrollment_status,
    e.amount_due,
    e.enrolled_at,
    e.notes
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
WHERE s.deleted_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM group_levels gl
      WHERE gl.group_id    = e.group_id
        AND gl.level_number = e.level_number
  )
ORDER BY e.enrolled_at DESC;

COMMENT ON VIEW v_audit_level_mismatch IS
'INFO: Enrollments whose (group_id, level_number) has no corresponding group_levels row. Cannot be attributed in Round Cost or analytics. Triggers data_quality_warning in Report 4.';

-- =============================================================================
-- SCENARIO H 🔴 ERROR — Active Payments for Soft-Deleted Students
-- Non-deleted payments referencing soft-deleted students
-- =============================================================================
CREATE OR REPLACE VIEW v_audit_ghost_payments AS
SELECT
    p.id              AS payment_id,
    p.student_id,
    s.full_name       AS deleted_student_name,
    s.deleted_at      AS student_deleted_at,
    p.amount,
    p.transaction_type,
    p.enrollment_id,
    r.receipt_number,
    r.paid_at,
    p.created_at
FROM payments p
JOIN students s ON s.id = p.student_id
JOIN receipts r ON r.id = p.receipt_id
WHERE p.deleted_at IS NULL
  AND s.deleted_at IS NOT NULL
ORDER BY s.deleted_at DESC;

COMMENT ON VIEW v_audit_ghost_payments IS
'ERROR: Active (non-soft-deleted) payments for soft-deleted students. Ghost money — distorts revenue totals. Should be soft-deleted together with the student record.';

-- =============================================================================
-- SCENARIO I 🟡 WARNING — Full or Over-Discounts (≥ 100% of amount_due)
-- discount_applied >= amount_due — charge effectively zeroed or negated
-- =============================================================================
CREATE OR REPLACE VIEW v_audit_overdiscounted_enrollments AS
SELECT
    e.id                                                        AS enrollment_id,
    s.full_name                                                 AS student_name,
    s.phone,
    g.name                                                      AS group_name,
    c.name                                                      AS course_name,
    e.level_number,
    e.status                                                    AS enrollment_status,
    e.amount_due,
    e.discount_applied,
    ROUND(e.discount_applied / NULLIF(e.amount_due, 0) * 100, 1) AS discount_pct,
    (e.amount_due - COALESCE(e.discount_applied, 0))            AS net_due,
    e.notes,
    e.enrolled_at
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
WHERE s.deleted_at IS NULL
  AND e.discount_applied IS NOT NULL
  AND e.discount_applied >= e.amount_due
ORDER BY discount_pct DESC NULLS LAST;

COMMENT ON VIEW v_audit_overdiscounted_enrollments IS
'WARNING: Enrollments where discount_applied >= amount_due (net_due = 0 or negative). Likely a data-entry error. Could also be a legitimate full scholarship — document if intentional.';

-- =============================================================================
-- SUMMARY VIEW — v_audit_summary
-- Run this first. Any non-zero count tells you where to look.
-- Returns: code, severity, label, anomaly_count for all 9 scenarios
-- =============================================================================
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

SELECT 'H', 'ERROR', 'Active Payments for Soft-Deleted Students', COUNT(*) FROM payments p
JOIN students s ON s.id = p.student_id
WHERE p.deleted_at IS NULL AND s.deleted_at IS NOT NULL

UNION ALL

SELECT 'I', 'WARNING', 'Full or Over-Discounts (>= 100%)', COUNT(*) FROM enrollments e
JOIN students s ON s.id = e.student_id
WHERE s.deleted_at IS NULL
  AND e.discount_applied IS NOT NULL AND e.discount_applied >= e.amount_due

ORDER BY code;

COMMENT ON VIEW v_audit_summary IS
'Balance integrity audit summary. Run SELECT * FROM v_audit_summary to get anomaly counts for all 9 scenarios. Drill into v_audit_<scenario> for detail rows. ERROR = immediate action; WARNING = review this week; INFO = document and clean.';

-- =============================================================================
-- VERIFICATION
-- =============================================================================
SELECT 'Migration 074 applied successfully — 10 audit views created' AS status,
       (SELECT COUNT(*) FROM pg_views WHERE schemaname = 'public' AND viewname LIKE 'v_audit%') AS audit_view_count;
