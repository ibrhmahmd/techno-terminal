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
