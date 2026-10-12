-- Reporting views read by the audit module (ADR-0011/0012): integrity checks, finance and BI.
-- Folded in from migrations 074_audit_views.sql, 075_finance_views.sql and 076_bi_report_views.sql
-- so a database built from schema.sql matches production (#113).


-- ---- from db/migrations/074_audit_views.sql ----
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

-- ---- from db/migrations/075_finance_views.sql ----
-- =============================================================================
-- Migration 075 — Finance Monitoring Views
-- Date: 2026-07-09
--
-- Creates 12 finance views + 1 summary view for proactive financial monitoring.
-- These complement the 9 audit views from 074 (which detect anomalies).
-- These views answer "where is money flowing" — revenue, costs, AR, risk.
--
-- Usage:
--   SELECT * FROM v_finance_summary;                    -- single-row KPI snapshot
--   SELECT * FROM v_finance_outstanding_balances;       -- accounts receivable
--   SELECT * FROM v_finance_monthly_revenue;            -- revenue trend
--   SELECT * FROM v_finance_high_risk_balances;         -- AR aging (>30 days unpaid)
--   SELECT * FROM v_finance_contract_instructor_costs;  -- payroll per round
--
-- Categories:
--   Revenue & Collection  : v_finance_monthly_revenue, v_finance_revenue_by_course,
--                           v_finance_outstanding_balances, v_finance_collection_rate_by_group,
--                           v_finance_payment_method_breakdown
--   Payroll & Cost        : v_finance_contract_instructor_costs,
--                           v_finance_part_time_group_allocation,
--                           v_finance_total_payroll_vs_revenue
--   Discounts & Risk      : v_finance_discount_impact, v_finance_high_risk_balances
--   Group Health          : v_finance_group_revenue_summary,
--                           v_finance_waiting_list_revenue_potential
--   Summary               : v_finance_summary
-- =============================================================================


-- =============================================================================
-- CATEGORY 1 — REVENUE & COLLECTION
-- =============================================================================

-- -----------------------------------------------------------------------------
-- v_finance_monthly_revenue
-- Core KPI: how much money arrived each month, net of refunds
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_monthly_revenue AS
SELECT
    date_trunc('month', r.paid_at)::date                                      AS month,
    COUNT(DISTINCT r.id)                                                       AS receipt_count,
    COUNT(p.id)                                                                AS payment_line_count,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'),  0) AS gross_collected,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'),   0) AS total_refunded,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'charge'),   0) AS total_charged,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'),  0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
                                                                               AS net_revenue
FROM payments p
JOIN receipts r ON r.id = p.receipt_id
WHERE p.deleted_at IS NULL
GROUP BY date_trunc('month', r.paid_at)
ORDER BY month;

COMMENT ON VIEW v_finance_monthly_revenue IS
'Monthly revenue summary. gross_collected = all payment-type rows; net_revenue = payments minus refunds. Use for trend analysis and reporting.';


-- -----------------------------------------------------------------------------
-- v_finance_revenue_by_course
-- Strategic: which courses generate the most revenue and have best collection rates
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_revenue_by_course AS
SELECT
    c.id                                                                       AS course_id,
    c.name                                                                     AS course_name,
    COUNT(DISTINCT e.id)                                                       AS enrollment_count,
    SUM(e.amount_due)                                                          AS total_billed,
    COALESCE(SUM(e.discount_applied), 0)                                       AS total_discounts,
    SUM(e.amount_due) - COALESCE(SUM(e.discount_applied), 0)                  AS net_billed,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'),  0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
                                                                               AS net_collected,
    (SUM(e.amount_due) - COALESCE(SUM(e.discount_applied), 0))
      - (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'),  0)
         - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0))
                                                                               AS outstanding,
    ROUND(
        (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'),  0)
         - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0))
        / NULLIF(SUM(e.amount_due) - COALESCE(SUM(e.discount_applied), 0), 0) * 100, 1
    )                                                                          AS collection_rate_pct
FROM enrollments e
JOIN groups   g  ON g.id = e.group_id
JOIN courses  c  ON c.id = g.course_id
JOIN students s  ON s.id = e.student_id
LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
WHERE s.deleted_at IS NULL
GROUP BY c.id, c.name
ORDER BY net_collected DESC;

COMMENT ON VIEW v_finance_revenue_by_course IS
'Revenue breakdown per course: billed, discounts, collected, outstanding, and collection rate %. Useful for identifying top-earning and under-collecting courses.';


-- -----------------------------------------------------------------------------
-- v_finance_outstanding_balances
-- Accounts Receivable: every active enrollment where student still owes money
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_outstanding_balances AS
SELECT
    s.id                                                                       AS student_id,
    s.full_name                                                                AS student_name,
    s.phone,
    e.id                                                                       AS enrollment_id,
    g.name                                                                     AS group_name,
    c.name                                                                     AS course_name,
    e.level_number,
    e.status                                                                   AS enrollment_status,
    e.amount_due,
    COALESCE(e.discount_applied, 0)                                            AS discount_applied,
    e.amount_due - COALESCE(e.discount_applied, 0)                            AS net_due,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
                                                                               AS total_paid,
    (e.amount_due - COALESCE(e.discount_applied, 0))
      - (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
         - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0))
                                                                               AS balance_owed,
    e.enrolled_at,
    CURRENT_DATE - e.enrolled_at::date                                         AS days_since_enrollment
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
WHERE s.deleted_at IS NULL
  AND e.status = 'active'
GROUP BY s.id, s.full_name, s.phone,
         e.id, g.name, c.name, e.level_number, e.status,
         e.amount_due, e.discount_applied, e.enrolled_at
HAVING (
    (e.amount_due - COALESCE(e.discount_applied, 0))
    - (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
       - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0))
) > 0
ORDER BY balance_owed DESC;

COMMENT ON VIEW v_finance_outstanding_balances IS
'Accounts Receivable: active enrollments with a positive balance_owed. Complements v_audit_overpaid_enrollments (the underpaid side). Sort by balance_owed DESC for collections priority.';


-- -----------------------------------------------------------------------------
-- v_finance_collection_rate_by_group
-- Operational: which groups have poor payment follow-through
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_collection_rate_by_group AS
SELECT
    g.id                                                                       AS group_id,
    g.name                                                                     AS group_name,
    c.name                                                                     AS course_name,
    g.status                                                                   AS group_status,
    COUNT(DISTINCT e.id)                                                       AS active_enrollments,
    COALESCE(SUM(e.amount_due - COALESCE(e.discount_applied, 0)), 0)          AS total_net_due,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
                                                                               AS total_collected,
    COALESCE(SUM(e.amount_due - COALESCE(e.discount_applied, 0)), 0)
      - (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
         - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0))
                                                                               AS total_outstanding,
    ROUND(
        (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
         - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0))
        / NULLIF(SUM(e.amount_due - COALESCE(e.discount_applied, 0)), 0) * 100, 1
    )                                                                          AS collection_rate_pct
FROM groups g
JOIN courses  c  ON c.id = g.course_id
JOIN enrollments e ON e.group_id = g.id AND e.status = 'active'
JOIN students s   ON s.id = e.student_id AND s.deleted_at IS NULL
LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
GROUP BY g.id, g.name, c.name, g.status
ORDER BY collection_rate_pct ASC NULLS LAST;

COMMENT ON VIEW v_finance_collection_rate_by_group IS
'Per-group collection rate. Low collection_rate_pct groups need payment follow-up. Sort ASC to see worst-performing groups first.';


-- -----------------------------------------------------------------------------
-- v_finance_payment_method_breakdown
-- Operational: cash vs card vs bank transfer, per month
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_payment_method_breakdown AS
SELECT
    date_trunc('month', r.paid_at)::date                                       AS month,
    r.payment_method,
    COUNT(DISTINCT r.id)                                                        AS receipt_count,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'), 0)   AS amount_collected
FROM payments p
JOIN receipts r ON r.id = p.receipt_id
WHERE p.deleted_at IS NULL
GROUP BY date_trunc('month', r.paid_at), r.payment_method
ORDER BY month DESC, amount_collected DESC;

COMMENT ON VIEW v_finance_payment_method_breakdown IS
'Monthly payment method distribution: cash, card, bank transfer, etc. Useful for understanding preferred collection channels.';


-- =============================================================================
-- CATEGORY 2 — PAYROLL & COST
-- =============================================================================

-- -----------------------------------------------------------------------------
-- v_finance_contract_instructor_costs
-- Payroll: formalizes Report 4 (Round Cost) as a permanent, queryable view
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_contract_instructor_costs AS
WITH level_revenue AS (
    SELECT
        gl.id                                                                  AS group_level_id,
        gl.group_id,
        gl.level_number,
        COALESCE(gl.instructor_id, g.instructor_id)                           AS instructor_id,
        gl.status                                                              AS level_status,
        gl.effective_from,
        gl.effective_to,
        COALESCE(SUM(p.amount), 0)                                             AS revenue_collected
    FROM group_levels gl
    JOIN groups g ON g.id = gl.group_id
    LEFT JOIN enrollments e ON e.group_id = gl.group_id
                            AND e.level_number = gl.level_number
    LEFT JOIN payments    p ON p.enrollment_id = e.id
                            AND p.deleted_at IS NULL
                            AND p.transaction_type = 'payment'
    GROUP BY gl.id, gl.group_id, gl.level_number,
             COALESCE(gl.instructor_id, g.instructor_id),
             gl.status, gl.effective_from, gl.effective_to
)
SELECT
    lr.group_level_id,
    c.name                                                                     AS course_name,
    g.name                                                                     AS group_name,
    lr.level_number,
    lr.level_status,
    lr.effective_from,
    lr.effective_to,
    emp.full_name                                                              AS instructor_name,
    emp.contract_percentage,
    lr.revenue_collected,
    ROUND(lr.revenue_collected * emp.contract_percentage / 100, 2)            AS instructor_cost,
    lr.revenue_collected
      - ROUND(lr.revenue_collected * emp.contract_percentage / 100, 2)        AS net_after_instructor
FROM level_revenue lr
JOIN groups    g   ON g.id  = lr.group_id
JOIN courses   c   ON c.id  = g.course_id
JOIN employees emp ON emp.id = lr.instructor_id
WHERE emp.employment_type = 'contract'
ORDER BY lr.effective_from DESC NULLS LAST, lr.group_level_id;

COMMENT ON VIEW v_finance_contract_instructor_costs IS
'Contract instructor payroll per round. instructor_cost = revenue_collected * contract_percentage / 100. Formalizes Report 4 (Round Cost) as a permanent view. Part-time instructors excluded (fixed salary — separate report).';


-- -----------------------------------------------------------------------------
-- v_finance_part_time_group_allocation
-- Payroll: which groups each part-time instructor teaches (salary allocation setup)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_part_time_group_allocation AS
SELECT
    emp.id                                                                     AS employee_id,
    emp.full_name                                                              AS instructor_name,
    emp.monthly_salary,
    g.id                                                                       AS group_id,
    g.name                                                                     AS group_name,
    c.name                                                                     AS course_name,
    gl.level_number,
    gl.status                                                                  AS level_status,
    gl.sessions_planned,
    gl.effective_from,
    gl.effective_to,
    COUNT(DISTINCT e.id)                                                       AS enrolled_students,
    COALESCE(
        SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'), 0
    )                                                                          AS round_revenue
FROM group_levels gl
JOIN groups     g   ON g.id   = gl.group_id
JOIN courses    c   ON c.id   = g.course_id
JOIN employees  emp ON emp.id = gl.instructor_id
LEFT JOIN enrollments e ON e.group_id = gl.group_id
                        AND e.level_number = gl.level_number
LEFT JOIN payments    p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
WHERE emp.employment_type = 'part_time'
GROUP BY emp.id, emp.full_name, emp.monthly_salary,
         g.id, g.name, c.name, gl.level_number, gl.status,
         gl.sessions_planned, gl.effective_from, gl.effective_to
ORDER BY emp.full_name, gl.effective_from DESC NULLS LAST;

COMMENT ON VIEW v_finance_part_time_group_allocation IS
'Part-time instructor group assignments with round revenue. Use this as the foundation for monthly salary allocation (salary / groups_taught). Pairs with future part-time cost report.';


-- -----------------------------------------------------------------------------
-- v_finance_total_payroll_vs_revenue
-- Profitability: estimated monthly profit = revenue minus all known costs
-- Note: part-time salaries approximated as fixed monthly cost
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_total_payroll_vs_revenue AS
WITH months AS (
    -- generate months covered by actual payment data
    SELECT DISTINCT date_trunc('month', r.paid_at)::date AS month
    FROM payments p
    JOIN receipts r ON r.id = p.receipt_id
    WHERE p.deleted_at IS NULL
),
monthly_revenue AS (
    SELECT
        date_trunc('month', r.paid_at)::date                                   AS month,
        COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'),  0)
          - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
                                                                               AS net_revenue
    FROM payments p
    JOIN receipts r ON r.id = p.receipt_id
    WHERE p.deleted_at IS NULL
    GROUP BY date_trunc('month', r.paid_at)
),
monthly_contract_cost AS (
    SELECT
        date_trunc('month', COALESCE(gl.effective_from, NOW()))::date          AS month,
        SUM(
            COALESCE(lr.revenue, 0) * emp.contract_percentage / 100
        )                                                                      AS contract_cost
    FROM group_levels gl
    JOIN employees emp ON emp.id = gl.instructor_id AND emp.employment_type = 'contract'
    LEFT JOIN LATERAL (
        SELECT COALESCE(SUM(p.amount), 0) AS revenue
        FROM enrollments e
        LEFT JOIN payments p ON p.enrollment_id = e.id
                             AND p.deleted_at IS NULL
                             AND p.transaction_type = 'payment'
        WHERE e.group_id = gl.group_id AND e.level_number = gl.level_number
    ) lr ON true
    GROUP BY date_trunc('month', COALESCE(gl.effective_from, NOW()))
),
fixed_monthly_cost AS (
    -- full-time + part-time monthly salaries (fixed cost, same every month)
    SELECT COALESCE(SUM(monthly_salary), 0) AS fixed_cost
    FROM employees
    WHERE employment_type IN ('full_time', 'part_time')
      AND monthly_salary IS NOT NULL
)
SELECT
    m.month,
    COALESCE(mr.net_revenue,   0)                                              AS net_revenue,
    COALESCE(cc.contract_cost, 0)                                              AS contract_instructor_cost,
    (SELECT fixed_cost FROM fixed_monthly_cost)                                AS fixed_staff_cost,
    COALESCE(cc.contract_cost, 0) + (SELECT fixed_cost FROM fixed_monthly_cost)
                                                                               AS total_known_cost,
    COALESCE(mr.net_revenue, 0)
      - COALESCE(cc.contract_cost, 0)
      - (SELECT fixed_cost FROM fixed_monthly_cost)                            AS estimated_profit
FROM months m
LEFT JOIN monthly_revenue      mr ON mr.month = m.month
LEFT JOIN monthly_contract_cost cc ON cc.month = m.month
ORDER BY m.month;

COMMENT ON VIEW v_finance_total_payroll_vs_revenue IS
'Monthly profitability estimate. net_revenue minus contract instructor costs minus fixed staff salaries. estimated_profit is a floor estimate — excludes operational costs beyond payroll.';


-- =============================================================================
-- CATEGORY 3 — DISCOUNTS & FINANCIAL RISK
-- =============================================================================

-- -----------------------------------------------------------------------------
-- v_finance_discount_impact
-- Strategic: how much revenue is lost to discounts, by month and course
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_discount_impact AS
SELECT
    date_trunc('month', e.enrolled_at)::date                                   AS month,
    c.name                                                                     AS course_name,
    COUNT(e.id)                                                                AS total_enrollments,
    COUNT(e.id) FILTER (WHERE e.discount_applied > 0)                         AS discounted_enrollments,
    SUM(e.amount_due)                                                          AS gross_billed,
    COALESCE(SUM(e.discount_applied), 0)                                       AS total_discount_given,
    ROUND(
        COALESCE(SUM(e.discount_applied), 0)
        / NULLIF(SUM(e.amount_due), 0) * 100, 1
    )                                                                          AS discount_rate_pct,
    SUM(e.amount_due) - COALESCE(SUM(e.discount_applied), 0)                  AS net_after_discount
FROM enrollments e
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
JOIN students s ON s.id = e.student_id
WHERE s.deleted_at IS NULL
GROUP BY date_trunc('month', e.enrolled_at), c.id, c.name
ORDER BY month DESC, total_discount_given DESC;

COMMENT ON VIEW v_finance_discount_impact IS
'Revenue leakage from discounts, grouped by month and course. discount_rate_pct = total discounts / gross billed. High rates may indicate policy drift or systematic data errors.';


-- -----------------------------------------------------------------------------
-- v_finance_high_risk_balances
-- Risk: AR aging — active enrollments with unpaid balance AND enrolled > 30 days
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_high_risk_balances AS
SELECT
    s.id                                                                       AS student_id,
    s.full_name                                                                AS student_name,
    s.phone,
    e.id                                                                       AS enrollment_id,
    g.name                                                                     AS group_name,
    c.name                                                                     AS course_name,
    e.level_number,
    e.enrolled_at,
    CURRENT_DATE - e.enrolled_at::date                                         AS days_overdue,
    e.amount_due,
    COALESCE(e.discount_applied, 0)                                            AS discount_applied,
    e.amount_due - COALESCE(e.discount_applied, 0)                            AS net_due,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
                                                                               AS total_paid,
    (e.amount_due - COALESCE(e.discount_applied, 0))
      - (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
         - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0))
                                                                               AS balance_owed,
    CASE
        WHEN (CURRENT_DATE - e.enrolled_at::date) BETWEEN 30 AND 59  THEN '30-60 days'
        WHEN (CURRENT_DATE - e.enrolled_at::date) BETWEEN 60 AND 89  THEN '60-90 days'
        WHEN (CURRENT_DATE - e.enrolled_at::date) >= 90              THEN '90+ days'
        ELSE 'unknown'
    END                                                                        AS aging_bucket
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN groups   g ON g.id = e.group_id
JOIN courses  c ON c.id = g.course_id
LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
WHERE s.deleted_at IS NULL
  AND e.status = 'active'
GROUP BY s.id, s.full_name, s.phone,
         e.id, g.name, c.name, e.level_number,
         e.enrolled_at, e.amount_due, e.discount_applied
HAVING
    -- has an outstanding balance
    (e.amount_due - COALESCE(e.discount_applied, 0))
    - (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
       - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)) > 0
    -- enrolled more than 30 days ago
    AND (CURRENT_DATE - e.enrolled_at::date) > 30
ORDER BY balance_owed DESC;

COMMENT ON VIEW v_finance_high_risk_balances IS
'AR aging: active enrollments with outstanding balance and enrolled > 30 days. aging_bucket groups by 30-60, 60-90, 90+ days. Sort by balance_owed DESC for collections priority. Subset of v_finance_outstanding_balances with age filter applied.';


-- =============================================================================
-- CATEGORY 4 — GROUP & ENROLLMENT HEALTH
-- =============================================================================

-- -----------------------------------------------------------------------------
-- v_finance_group_revenue_summary
-- Per-group P&L: billed, collected, outstanding, dropped count
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_group_revenue_summary AS
SELECT
    g.id                                                                       AS group_id,
    g.name                                                                     AS group_name,
    c.name                                                                     AS course_name,
    g.status                                                                   AS group_status,
    COUNT(DISTINCT e.id)                                                       AS total_enrollments,
    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'active')                   AS active_enrollments,
    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'dropped')                  AS dropped_enrollments,
    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'transferred')              AS transferred_enrollments,
    SUM(e.amount_due)                                                          AS gross_billed,
    COALESCE(SUM(e.discount_applied), 0)                                       AS discounts_given,
    SUM(e.amount_due) - COALESCE(SUM(e.discount_applied), 0)                  AS net_billed,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'),  0)
      - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
                                                                               AS net_collected,
    (SUM(e.amount_due) - COALESCE(SUM(e.discount_applied), 0))
      - (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'),  0)
         - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0))
                                                                               AS outstanding
FROM groups g
JOIN courses  c  ON c.id = g.course_id
JOIN enrollments e ON e.group_id = g.id
JOIN students  s   ON s.id = e.student_id AND s.deleted_at IS NULL
LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
GROUP BY g.id, g.name, c.name, g.status
ORDER BY net_collected DESC;

COMMENT ON VIEW v_finance_group_revenue_summary IS
'Per-group financial summary: enrollment counts by status, gross billed, discounts, net collected, and outstanding balance. Use for group-level P&L reporting.';


-- -----------------------------------------------------------------------------
-- v_finance_waiting_list_revenue_potential
-- Forecast: estimated revenue if all waiting students convert, per course
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_finance_waiting_list_revenue_potential AS
WITH active_avg_fee AS (
    SELECT
        g.course_id,
        ROUND(AVG(e.amount_due), 0) AS avg_fee
    FROM enrollments e
    JOIN groups g ON g.id = e.group_id
    WHERE e.status = 'active'
      AND e.amount_due > 0
    GROUP BY g.course_id
)
SELECT
    c.id                                                                       AS course_id,
    c.name                                                                     AS course_name,
    COUNT(DISTINCT s.id)                                                       AS waiting_students,
    COALESCE(aaf.avg_fee, 0)                                                   AS avg_enrollment_fee,
    COALESCE(ROUND(COUNT(DISTINCT s.id) * aaf.avg_fee, 0), 0)                 AS potential_revenue_egp
FROM students s
JOIN enrollments e ON e.student_id = s.id
JOIN groups     g ON g.id = e.group_id
JOIN courses    c ON c.id = g.course_id
LEFT JOIN active_avg_fee aaf ON aaf.course_id = c.id
WHERE s.status = 'waiting'
  AND s.deleted_at IS NULL
GROUP BY c.id, c.name, aaf.avg_fee
ORDER BY potential_revenue_egp DESC NULLS LAST;

COMMENT ON VIEW v_finance_waiting_list_revenue_potential IS
'Revenue forecast if all waiting students convert. avg_enrollment_fee derived from active enrollments in same course. potential_revenue_egp is an upper bound — actual will be lower due to discounts and drop-outs.';


-- =============================================================================
-- SUMMARY VIEW — v_finance_summary
-- Single-row KPI snapshot for dashboard header
-- =============================================================================
CREATE OR REPLACE VIEW v_finance_summary AS
SELECT
    -- Revenue KPIs (current month)
    (
        SELECT COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'), 0)
                 - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
        FROM payments p JOIN receipts r ON r.id = p.receipt_id
        WHERE p.deleted_at IS NULL
          AND date_trunc('month', r.paid_at) = date_trunc('month', CURRENT_DATE)
    )                                                                          AS revenue_this_month,

    -- Revenue KPIs (all time)
    (
        SELECT COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'payment'), 0)
                 - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
        FROM payments p
        WHERE p.deleted_at IS NULL
    )                                                                          AS total_net_revenue,

    -- Accounts Receivable
    (
        SELECT COUNT(*) FROM v_finance_outstanding_balances
    )                                                                          AS ar_enrollment_count,

    (
        SELECT COALESCE(SUM(balance_owed), 0) FROM v_finance_outstanding_balances
    )                                                                          AS ar_total_owed,

    -- High risk (30+ days unpaid)
    (
        SELECT COUNT(*) FROM v_finance_high_risk_balances
    )                                                                          AS high_risk_count,

    (
        SELECT COALESCE(SUM(balance_owed), 0) FROM v_finance_high_risk_balances
    )                                                                          AS high_risk_total_owed,

    -- Discounts (current month)
    (
        SELECT COALESCE(SUM(discount_applied), 0)
        FROM enrollments e
        JOIN students s ON s.id = e.student_id
        WHERE s.deleted_at IS NULL
          AND date_trunc('month', e.enrolled_at) = date_trunc('month', CURRENT_DATE)
    )                                                                          AS discounts_this_month,

    -- Contract payroll (all active rounds)
    (
        SELECT COALESCE(SUM(instructor_cost), 0)
        FROM v_finance_contract_instructor_costs
        WHERE level_status = 'active'
    )                                                                          AS active_contract_payroll,

    -- Waiting list potential
    (
        SELECT COALESCE(SUM(potential_revenue_egp), 0)
        FROM v_finance_waiting_list_revenue_potential
    )                                                                          AS waiting_list_potential;

COMMENT ON VIEW v_finance_summary IS
'Single-row financial KPI snapshot for dashboard headers. Covers: current month revenue, total AR, high-risk AR, discounts this month, active contract payroll, and waiting-list revenue potential.';


-- =============================================================================
-- VERIFICATION
-- =============================================================================
SELECT
    'Migration 075 applied successfully — 13 finance views created' AS status,
    (
        SELECT COUNT(*)
        FROM pg_views
        WHERE schemaname = 'public'
          AND viewname LIKE 'v_finance%'
    ) AS finance_view_count;

-- ---- from db/migrations/076_bi_report_views.sql ----
-- =============================================================================
-- Migration 076 — BI Dashboard Report Views
-- Date: 2026-07-09
-- Ref: "Techno Kids — BI Dashboard Query Documentation" (Overall Business Report)
--
-- Encodes every named query from the BI documentation as a permanent, queryable
-- Postgres view. Organized by section:
--   §1  Customer Growth
--   §2  Waiting List & Conversion
--   §3  Revenue & Collections
--   §4  Course Performance
--   §5  Staffing & Instructor Cost
--   §7  Attendance & Enrollment Lifecycle
--   §8  Weekly Schedule
--   §KPI  Summary header row for dashboard
-- =============================================================================


-- =============================================================================
-- §1 — CUSTOMER GROWTH
-- =============================================================================

-- §1.1 New students per month
CREATE OR REPLACE VIEW v_bi_new_students_monthly AS
SELECT
    to_char(date_trunc('month', created_at), 'YYYY-MM') AS month,
    date_trunc('month', created_at)::date               AS month_date,
    count(*)                                            AS new_students
FROM students
WHERE deleted_at IS NULL
GROUP BY 1, 2
ORDER BY 2;

COMMENT ON VIEW v_bi_new_students_monthly IS
'§1.1 — Monthly new student registrations. Bar/line chart input. month_date is machine-sortable; month is display-friendly.';


-- §1.2 Founding cohort (old customers) status breakdown
-- Cutoff '2026-06-01' matches the system earliest cohort (May 2026 bulk import).
-- Update cutoff as the business accumulates more history.
CREATE OR REPLACE VIEW v_bi_founding_cohort_status AS
WITH old_cohort AS (
    SELECT id, status, full_name, created_at
    FROM students
    WHERE deleted_at IS NULL
      AND created_at < '2026-06-01'   -- parameterize this in your BI tool
)
SELECT
    status,
    count(*) AS student_count
FROM old_cohort
GROUP BY status
ORDER BY student_count DESC;

COMMENT ON VIEW v_bi_founding_cohort_status IS
'§1.2 — Status breakdown of the founding cohort (registered before 2026-06-01). Update the cutoff date as history accumulates. Use as a retention widget.';


-- §1.3a Gender / age demographic breakdown
CREATE OR REPLACE VIEW v_bi_gender_age_breakdown AS
SELECT
    gender,
    count(*)                                                          AS student_count,
    round(avg(date_part('year', age(date_of_birth)))::numeric, 1)    AS avg_age,
    min(date_part('year', age(date_of_birth))::integer)              AS min_age,
    max(date_part('year', age(date_of_birth))::integer)              AS max_age
FROM students
WHERE deleted_at IS NULL
  AND gender IS NOT NULL
  AND date_of_birth IS NOT NULL
GROUP BY gender;

COMMENT ON VIEW v_bi_gender_age_breakdown IS
'§1.3a — Gender and age distribution. Filters rows with NULL gender or date_of_birth — pair with v_bi_demographics_completeness to show coverage.';


-- §1.3b Demographics completeness check
CREATE OR REPLACE VIEW v_bi_demographics_completeness AS
SELECT
    count(*) FILTER (WHERE gender IS NULL OR date_of_birth IS NULL) AS missing_demographics,
    count(*) FILTER (WHERE gender IS NULL)                           AS missing_gender,
    count(*) FILTER (WHERE date_of_birth IS NULL)                   AS missing_dob,
    count(*)                                                         AS total_students,
    round(
        100.0 * count(*) FILTER (WHERE gender IS NOT NULL AND date_of_birth IS NOT NULL)
        / NULLIF(count(*), 0), 1
    )                                                                AS completeness_pct
FROM students
WHERE deleted_at IS NULL;

COMMENT ON VIEW v_bi_demographics_completeness IS
'§1.3b — Demographic data completeness KPI. Shows how many students are missing gender or date_of_birth. Use as a data-quality tile alongside v_bi_gender_age_breakdown.';


-- =============================================================================
-- §2 — WAITING LIST & CONVERSION
-- =============================================================================

-- §2.1 Waiting list size and enrollment status
CREATE OR REPLACE VIEW v_bi_waiting_list_summary AS
SELECT
    count(*)                                                               AS waiting_total,
    count(*) FILTER (WHERE EXISTS (
        SELECT 1 FROM enrollments en WHERE en.student_id = s.id
    ))                                                                     AS waiting_with_enrollment,
    count(*) FILTER (WHERE NOT EXISTS (
        SELECT 1 FROM enrollments en WHERE en.student_id = s.id
    ))                                                                     AS waiting_never_enrolled
FROM students s
WHERE s.status = 'waiting'
  AND s.deleted_at IS NULL;

COMMENT ON VIEW v_bi_waiting_list_summary IS
'§2.1 — Single-row waiting list summary: total waiting, those with ≥1 enrollment (were active, returned to waiting), and those who never enrolled.';


-- §2.2 Waiting list by join month
CREATE OR REPLACE VIEW v_bi_waiting_list_by_month AS
SELECT
    to_char(date_trunc('month', created_at), 'YYYY-MM') AS joined_month,
    date_trunc('month', created_at)::date                AS joined_month_date,
    count(*)                                             AS waiting_students
FROM students
WHERE status = 'waiting'
  AND deleted_at IS NULL
GROUP BY 1, 2
ORDER BY 2;

COMMENT ON VIEW v_bi_waiting_list_by_month IS
'§2.2 — Monthly cohorts of students currently in waiting status, by registration month. Note: waiting_since is not yet populated; created_at is used as proxy.';


-- §2.3 Current wait duration for students still waiting
CREATE OR REPLACE VIEW v_bi_current_wait_duration AS
SELECT
    round(avg(current_date - created_at::date)::numeric, 1)  AS avg_days_waiting,
    max(current_date - created_at::date)                      AS longest_wait_days,
    min(current_date - created_at::date)                      AS shortest_wait_days,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY current_date - created_at::date)
                                                              AS median_wait_days,
    count(*)                                                  AS waiting_students
FROM students
WHERE status = 'waiting'
  AND deleted_at IS NULL;

COMMENT ON VIEW v_bi_current_wait_duration IS
'§2.3 — Wait duration statistics for students currently in waiting status. Uses created_at as proxy for wait start (waiting_since not yet populated).';


-- §2.4 Waiting → active conversions (from student_activity_log)
-- Note: requires student_activity_log table with activity_type = ''status_change''
-- and activity_subtype = ''waiting_to_active''. Returns 0 rows if no conversions logged.
CREATE OR REPLACE VIEW v_bi_waiting_conversion_stats AS
SELECT
    count(*)                                                            AS total_conversions,
    round(avg(extract(day FROM (sal.created_at - s.created_at)))::numeric, 1)
                                                                        AS avg_days_to_convert,
    min(extract(day FROM (sal.created_at - s.created_at))::integer)    AS min_days,
    max(extract(day FROM (sal.created_at - s.created_at))::integer)    AS max_days,
    percentile_cont(0.5) WITHIN GROUP (
        ORDER BY extract(day FROM (sal.created_at - s.created_at))
    )                                                                   AS median_days
FROM student_activity_log sal
JOIN students s ON s.id = sal.student_id
WHERE sal.activity_type = 'status_change'
  AND sal.activity_subtype = 'waiting_to_active';

COMMENT ON VIEW v_bi_waiting_conversion_stats IS
'§2.4 — Waiting → active conversion statistics. Reads from student_activity_log. avg_days_to_convert is the key funnel metric. Pair with v_bi_waiting_list_summary to compute conversion rate.';


-- =============================================================================
-- §3 — REVENUE & COLLECTIONS
-- =============================================================================

-- §3.1 Monthly revenue (payments only, no refunds)
CREATE OR REPLACE VIEW v_bi_monthly_revenue AS
SELECT
    to_char(date_trunc('month', created_at), 'YYYY-MM')                AS month,
    date_trunc('month', created_at)::date                              AS month_date,
    count(*) FILTER (WHERE transaction_type = 'payment')               AS num_payments,
    coalesce(sum(amount) FILTER (WHERE transaction_type = 'payment'), 0) AS revenue
FROM payments
WHERE deleted_at IS NULL
GROUP BY 1, 2
ORDER BY 2;

COMMENT ON VIEW v_bi_monthly_revenue IS
'§3.1 — Monthly revenue from payment-type transactions only (excludes refunds). The source report additionally removes same-minute duplicates and 1 EGP test entries — encode that as a WHERE filter here if the cleanup becomes systematic.';


-- §3.2 Total billed vs. collected summary (single row)
CREATE OR REPLACE VIEW v_bi_billed_vs_collected AS
SELECT
    coalesce(sum(e.amount_due), 0)                       AS total_billed_gross,
    coalesce(sum(e.discount_applied), 0)                 AS total_discounts,
    coalesce(sum(e.amount_due - e.discount_applied), 0)  AS total_billed_net,
    count(*)                                             AS enrollment_count,
    count(DISTINCT e.student_id)                         AS unique_students,
    coalesce(
        (SELECT sum(p.amount) FROM payments p
         WHERE p.transaction_type = 'payment' AND p.deleted_at IS NULL), 0
    )                                                    AS total_collected,
    round(
        coalesce(
            (SELECT sum(p.amount) FROM payments p
             WHERE p.transaction_type = 'payment' AND p.deleted_at IS NULL), 0
        )
        / NULLIF(coalesce(sum(e.amount_due - e.discount_applied), 0), 0) * 100, 1
    )                                                    AS collection_rate_pct
FROM enrollments e;

COMMENT ON VIEW v_bi_billed_vs_collected IS
'§3.2 — Single-row total billed vs collected summary. collection_rate_pct = total_collected / total_billed_net. Use as a collection-rate gauge KPI.';


-- §3.3 Payment completeness per enrollment (unpaid / partial / full / no-charge)
CREATE OR REPLACE VIEW v_bi_payment_completeness AS
WITH enr AS (
    SELECT
        e.id,
        e.amount_due,
        coalesce(e.discount_applied, 0)   AS discount_applied,
        coalesce((
            SELECT sum(p.amount)
            FROM payments p
            WHERE p.enrollment_id = e.id
              AND p.deleted_at IS NULL
              AND p.transaction_type = 'payment'
        ), 0)                             AS paid
    FROM enrollments e
)
SELECT
    CASE
        WHEN amount_due - discount_applied <= 0 THEN 'no_charge'
        WHEN paid = 0                            THEN 'unpaid'
        WHEN paid >= (amount_due - discount_applied) THEN 'fully_paid'
        ELSE 'partially_paid'
    END                               AS payment_state,
    count(*)                          AS enrollments,
    coalesce(sum(amount_due - discount_applied), 0) AS billed,
    coalesce(sum(paid), 0)            AS collected,
    round(
        100.0 * count(*) / NULLIF(sum(count(*)) OVER (), 0), 1
    )                                 AS pct_of_enrollments
FROM enr
GROUP BY 1
ORDER BY enrollments DESC;

COMMENT ON VIEW v_bi_payment_completeness IS
'§3.3 — Enrollment payment state breakdown: no_charge / unpaid / partially_paid / fully_paid. Reveals partial payments that a simple SUM() on payments misses. Use as a stacked bar chart.';


-- §3.4 Payment method mix
CREATE OR REPLACE VIEW v_bi_payment_method_mix AS
SELECT
    r.payment_method,
    count(DISTINCT r.id)                           AS receipt_count,
    coalesce(sum(p.amount), 0)                     AS total_collected,
    round(
        100.0 * coalesce(sum(p.amount), 0)
        / NULLIF(sum(sum(p.amount)) OVER (), 0), 1
    )                                              AS pct_of_total
FROM receipts r
JOIN payments p ON p.receipt_id = r.id AND p.deleted_at IS NULL
WHERE p.transaction_type = 'payment'
GROUP BY r.payment_method
ORDER BY total_collected DESC;

COMMENT ON VIEW v_bi_payment_method_mix IS
'§3.4 — Payment method share: cash vs digital. pct_of_total is window-computed. Use as a pie/donut chart.';


-- §3.5 Average revenue per paying student
CREATE OR REPLACE VIEW v_bi_avg_revenue_per_student AS
SELECT
    count(DISTINCT student_id)                                                 AS paying_students,
    coalesce(sum(amount), 0)                                                   AS total_revenue,
    round(coalesce(sum(amount), 0)::numeric / NULLIF(count(DISTINCT student_id), 0), 0)
                                                                               AS avg_revenue_per_student
FROM payments
WHERE transaction_type = 'payment'
  AND deleted_at IS NULL;

COMMENT ON VIEW v_bi_avg_revenue_per_student IS
'§3.5 — Single-row average revenue per paying student. Use as a KPI tile alongside total revenue.';


-- =============================================================================
-- §4 — COURSE PERFORMANCE
-- =============================================================================

-- §4.1 Course-level breakdown
CREATE OR REPLACE VIEW v_bi_course_performance AS
SELECT
    c.id                                                                        AS course_id,
    c.name                                                                      AS course,
    c.category,
    c.price_per_level,
    count(DISTINCT g.id)                                                        AS groups,
    count(DISTINCT e.student_id)                                                AS students,
    coalesce(sum(p.amount) FILTER (WHERE p.transaction_type = 'payment'
                                     AND p.deleted_at IS NULL), 0)             AS revenue,
    coalesce(sum(e.amount_due), 0)                                              AS total_billed,
    round(
        coalesce(sum(p.amount) FILTER (WHERE p.transaction_type = 'payment'
                                        AND p.deleted_at IS NULL), 0)
        / NULLIF(coalesce(sum(e.amount_due - coalesce(e.discount_applied,0)), 0), 0) * 100, 1
    )                                                                           AS collection_rate_pct
FROM courses c
LEFT JOIN groups      g  ON g.course_id = c.id
LEFT JOIN enrollments e  ON e.group_id  = g.id
LEFT JOIN payments    p  ON p.enrollment_id = e.id
GROUP BY c.id, c.name, c.category, c.price_per_level
ORDER BY revenue DESC;

COMMENT ON VIEW v_bi_course_performance IS
'§4.1 — Ranked course performance: groups, students, revenue, and collection rate. Use as a treemap or ranked table. Courses with 0 groups still appear (LEFT JOIN).';


-- §4.2 Groups over capacity
CREATE OR REPLACE VIEW v_bi_groups_over_capacity AS
SELECT
    g.id                                        AS group_id,
    g.name                                      AS group_name,
    c.name                                      AS course_name,
    g.max_capacity,
    count(DISTINCT e.student_id)                AS enrolled,
    count(DISTINCT e.student_id) - g.max_capacity AS over_by
FROM groups g
JOIN courses      c ON c.id = g.course_id
JOIN enrollments  e ON e.group_id = g.id AND e.status = 'active'
WHERE g.max_capacity IS NOT NULL
GROUP BY g.id, g.name, c.name, g.max_capacity
HAVING count(DISTINCT e.student_id) > g.max_capacity
ORDER BY over_by DESC;

COMMENT ON VIEW v_bi_groups_over_capacity IS
'§4.2 — Groups currently over their max_capacity. Alert/exception list — run as a scheduled check. over_by = enrolled - max_capacity.';


-- =============================================================================
-- §5 — STAFFING & INSTRUCTOR COST
-- =============================================================================

-- §5.1 Instructor load — active groups only
CREATE OR REPLACE VIEW v_bi_instructor_load AS
SELECT
    emp.id                                      AS employee_id,
    emp.full_name,
    emp.employment_type,
    count(DISTINCT g.id)                        AS active_groups,
    count(DISTINCT e.student_id)                AS active_students
FROM groups g
JOIN employees    emp ON emp.id = g.instructor_id
LEFT JOIN enrollments e ON e.group_id = g.id AND e.status = 'active'
WHERE g.status = 'active'
GROUP BY emp.id, emp.full_name, emp.employment_type
ORDER BY active_students DESC;

COMMENT ON VIEW v_bi_instructor_load IS
'§5.1 — Instructor utilization: active groups and students per instructor, filterable by employment_type. sessions count removed (sessions table may not exist) — add back if available.';


-- §5.2 Contract instructor cost (revenue-share model)
-- NOTE: Uses emp.contract_percentage from the employees table (per-instructor rate).
-- The BI doc hardcodes 25%; this view uses the stored per-instructor rate instead,
-- which is more accurate. If contract_percentage is NULL, falls back to 25%.
CREATE OR REPLACE VIEW v_bi_contract_instructor_cost AS
SELECT
    emp.id                                                              AS employee_id,
    emp.full_name,
    coalesce(emp.contract_percentage, 25)                              AS revenue_share_pct,
    count(DISTINCT g.id)                                               AS active_groups,
    count(en.id)                                                       AS active_enrollments,
    coalesce(sum(c.price_per_level), 0)                                AS total_level_value,
    round(
        coalesce(sum(c.price_per_level), 0)
        * coalesce(emp.contract_percentage, 25) / 100
    )                                                                  AS estimated_cost
FROM groups g
JOIN employees    emp ON emp.id = g.instructor_id AND emp.employment_type = 'contract'
JOIN courses      c   ON c.id = g.course_id
JOIN enrollments  en  ON en.group_id = g.id AND en.status = 'active'
WHERE g.status = 'active'
GROUP BY emp.id, emp.full_name, emp.contract_percentage
ORDER BY estimated_cost DESC;

COMMENT ON VIEW v_bi_contract_instructor_cost IS
'§5.2 — Estimated cost per contract instructor based on active enrollments × price_per_level × contract_percentage. Uses stored per-instructor rate (employees.contract_percentage), falling back to 25% if NULL. See §6 in BI doc for business parameter notes.';


-- §5.3 Contract instructors with no active classes
CREATE OR REPLACE VIEW v_bi_contract_instructors_idle AS
SELECT
    emp.id          AS employee_id,
    emp.full_name,
    emp.employment_type
FROM employees emp
WHERE emp.employment_type = 'contract'
  AND NOT EXISTS (
      SELECT 1 FROM groups g
      WHERE g.instructor_id = emp.id
        AND g.status = 'active'
  );

COMMENT ON VIEW v_bi_contract_instructors_idle IS
'§5.3 — Contract instructors with no currently active groups. Removed is_active filter (column may not exist); add back if confirmed. Use as an exception/alert list.';


-- §5.4 Headcount by employment type
CREATE OR REPLACE VIEW v_bi_headcount_by_type AS
SELECT
    employment_type,
    count(*)                    AS headcount,
    coalesce(sum(monthly_salary), 0) AS total_monthly_salary
FROM employees
GROUP BY employment_type
ORDER BY employment_type;

COMMENT ON VIEW v_bi_headcount_by_type IS
'§5.4 — Employee headcount and total monthly salary by employment type. monthly_salary may be NULL for some full-time staff (see §6 in BI doc — needs to be filled in).';


-- =============================================================================
-- §7 — ATTENDANCE & ENROLLMENT LIFECYCLE
-- =============================================================================

-- §7.1 Attendance rate breakdown
CREATE OR REPLACE VIEW v_bi_attendance_rate AS
SELECT
    status,
    count(*)                                                          AS records,
    round(100.0 * count(*) / NULLIF(sum(count(*)) OVER (), 0), 1)   AS pct
FROM attendance
GROUP BY status
ORDER BY records DESC;

COMMENT ON VIEW v_bi_attendance_rate IS
'§7.1 — Attendance status distribution with percentage of total. Use as a KPI tile or donut chart.';


-- §7.2 Enrollment status breakdown
CREATE OR REPLACE VIEW v_bi_enrollment_status AS
SELECT
    status,
    count(*)                                                          AS enrollments,
    round(100.0 * count(*) / NULLIF(sum(count(*)) OVER (), 0), 1)   AS pct
FROM enrollments
GROUP BY status
ORDER BY enrollments DESC;

COMMENT ON VIEW v_bi_enrollment_status IS
'§7.2 — Enrollment lifecycle status distribution. Pair with v_bi_payment_completeness to understand financial state by enrollment status.';


-- =============================================================================
-- §8 — WEEKLY SCHEDULE
-- =============================================================================

CREATE OR REPLACE VIEW v_bi_weekly_schedule AS
SELECT
    g.default_day                                                       AS day,
    count(*) FILTER (WHERE g.default_time_start < '17:00:00')          AS afternoon_groups,
    count(*) FILTER (WHERE g.default_time_start >= '17:00:00')         AS evening_groups,
    count(*)                                                            AS total_groups,
    count(DISTINCT e.student_id)                                        AS students_enrolled
FROM groups g
LEFT JOIN enrollments e ON e.group_id = g.id AND e.status = 'active'
WHERE g.status = 'active'
  AND g.default_day IS NOT NULL
GROUP BY g.default_day
ORDER BY
    CASE g.default_day
        WHEN 'sunday'    THEN 0
        WHEN 'monday'    THEN 1
        WHEN 'tuesday'   THEN 2
        WHEN 'wednesday' THEN 3
        WHEN 'thursday'  THEN 4
        WHEN 'friday'    THEN 5
        WHEN 'saturday'  THEN 6
        ELSE 7
    END;

COMMENT ON VIEW v_bi_weekly_schedule IS
'§8 — Active groups per day of week, split by afternoon (<17:00) vs evening (≥17:00). The 17:00 cutoff should be confirmed as a business rule. Rows ordered Sun→Sat.';


-- =============================================================================
-- KPI SUMMARY — v_bi_kpi_header
-- Dashboard header strip: revenue, collection %, waitlist, active students
-- =============================================================================
CREATE OR REPLACE VIEW v_bi_kpi_header AS
SELECT
    -- Active students
    (SELECT count(*) FROM students WHERE status = 'active' AND deleted_at IS NULL)
                                                AS active_students,

    -- Waiting list
    (SELECT count(*) FROM students WHERE status = 'waiting' AND deleted_at IS NULL)
                                                AS waiting_students,

    -- New this month
    (SELECT count(*) FROM students
     WHERE deleted_at IS NULL
       AND date_trunc('month', created_at) = date_trunc('month', CURRENT_DATE))
                                                AS new_students_this_month,

    -- Revenue this month
    (SELECT coalesce(sum(amount), 0) FROM payments
     WHERE transaction_type = 'payment'
       AND deleted_at IS NULL
       AND date_trunc('month', created_at) = date_trunc('month', CURRENT_DATE))
                                                AS revenue_this_month,

    -- Revenue all time
    (SELECT coalesce(sum(amount), 0) FROM payments
     WHERE transaction_type = 'payment' AND deleted_at IS NULL)
                                                AS revenue_all_time,

    -- Collection rate
    (SELECT collection_rate_pct FROM v_bi_billed_vs_collected)
                                                AS collection_rate_pct,

    -- Avg revenue per paying student
    (SELECT avg_revenue_per_student FROM v_bi_avg_revenue_per_student)
                                                AS avg_revenue_per_student,

    -- Active groups
    (SELECT count(*) FROM groups WHERE status = 'active')
                                                AS active_groups,

    -- Courses
    (SELECT count(*) FROM courses)              AS total_courses,

    -- Groups over capacity
    (SELECT count(*) FROM v_bi_groups_over_capacity)
                                                AS groups_over_capacity,

    -- Idle contract instructors
    (SELECT count(*) FROM v_bi_contract_instructors_idle)
                                                AS idle_contract_instructors,

    -- Demographics completeness
    (SELECT completeness_pct FROM v_bi_demographics_completeness)
                                                AS demographics_completeness_pct;

COMMENT ON VIEW v_bi_kpi_header IS
'Single-row KPI strip for the BI Report dashboard header: active/waiting/new students, revenue this month, collection rate, avg revenue per student, active groups, capacity alerts. Mirrors the "KPI header" tile layout from the BI documentation.';


-- =============================================================================
-- VERIFICATION
-- =============================================================================
SELECT
    'Migration 076 applied successfully' AS status,
    (SELECT count(*) FROM pg_views
     WHERE schemaname = 'public' AND viewname LIKE 'v_bi%') AS bi_view_count;
