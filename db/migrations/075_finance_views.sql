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
