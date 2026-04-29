-- =============================================================================
-- VIEWS
-- Analytical and filter views for reporting and application logic
-- =============================================================================

-- =============================================================================
-- SOFT-DELETE FILTER VIEWS
-- Provide filtered views of tables with soft-delete support
-- =============================================================================

-- Active students (excludes soft-deleted)
CREATE OR REPLACE VIEW active_students AS
SELECT * FROM students WHERE deleted_at IS NULL;

COMMENT ON VIEW active_students IS 'View of non-deleted students';

-- Deleted students (only soft-deleted)
CREATE OR REPLACE VIEW deleted_students AS
SELECT * FROM students WHERE deleted_at IS NOT NULL;

COMMENT ON VIEW deleted_students IS 'View of soft-deleted students (for recovery/admin)';

-- Active payments (excludes soft-deleted)
CREATE OR REPLACE VIEW active_payments AS
SELECT * FROM payments WHERE deleted_at IS NULL;

COMMENT ON VIEW active_payments IS 'View of non-voided payments';

-- Deleted payments (only soft-deleted)
CREATE OR REPLACE VIEW deleted_payments AS
SELECT * FROM payments WHERE deleted_at IS NOT NULL;

COMMENT ON VIEW deleted_payments IS 'View of voided payments (for audit)';

-- Active competitions (excludes soft-deleted)
CREATE OR REPLACE VIEW active_competitions AS
SELECT * FROM competitions WHERE deleted_at IS NULL;

COMMENT ON VIEW active_competitions IS 'View of active (non-deleted) competitions';

-- Active teams (excludes soft-deleted)
CREATE OR REPLACE VIEW active_teams AS
SELECT * FROM teams WHERE deleted_at IS NULL AND is_deleted = FALSE;

COMMENT ON VIEW active_teams IS 'View of active (non-deleted) teams';

-- =============================================================================
-- CORE BUSINESS VIEWS
-- =============================================================================

-- Student information with parent details
CREATE OR REPLACE VIEW v_students AS
SELECT s.id,
    s.full_name,
    s.date_of_birth,
    EXTRACT(YEAR FROM AGE(s.date_of_birth))::INTEGER AS age,
    s.gender,
    s.phone AS student_phone,
    s.notes,
    s.is_active,
    s.status,
    s.created_at,
    s.updated_at,
    s.metadata,
    p.full_name AS primary_parent_name,
    p.phone_primary AS primary_parent_phone,
    p.email AS primary_parent_email
FROM students s
    LEFT JOIN student_parents sp ON s.id = sp.student_id AND sp.is_primary = TRUE
    LEFT JOIN parents p ON sp.parent_id = p.id
WHERE s.deleted_at IS NULL;

COMMENT ON VIEW v_students IS 'Student information with primary parent details (excludes deleted)';

-- Enrollment balance with payment status
CREATE OR REPLACE VIEW v_enrollment_balance AS
SELECT e.id AS enrollment_id,
    e.student_id,
    e.group_id,
    e.level_number,
    e.amount_due,
    e.discount_applied,
    (e.amount_due - COALESCE(e.discount_applied, 0)) AS net_due,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')), 0)
    - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS total_paid,
    (
        COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')), 0)
        - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)
    ) - (e.amount_due - COALESCE(e.discount_applied, 0)) AS balance,
    (
        CASE
            WHEN COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')), 0) = 0 
                THEN 'not_paid'::text
            WHEN (e.amount_due - COALESCE(e.discount_applied, 0)) <= 
                (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')), 0)
                - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0))
                THEN 'paid'::text
            ELSE 'partially_paid'::text
        END
    )::character varying(20) AS payment_status,
    GREATEST(
        ((e.amount_due - COALESCE(e.discount_applied, 0)) 
        - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')), 0)
        + COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)),
        0
    )::numeric AS amount_remaining
FROM enrollments e
    LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL
WHERE e.deleted_at IS NULL
GROUP BY e.id, e.student_id, e.group_id, e.level_number, e.amount_due, e.discount_applied;

COMMENT ON VIEW v_enrollment_balance IS 'Real-time enrollment balance with payment status (not_paid/partially_paid/paid)';

-- Unpaid enrollments report
CREATE OR REPLACE VIEW v_unpaid_enrollments AS
SELECT 
    eb.enrollment_id,
    eb.student_id,
    s.full_name AS student_name,
    eb.group_id,
    g.name AS group_name,
    eb.level_number,
    eb.net_due,
    eb.total_paid,
    eb.balance,
    eb.payment_status,
    eb.amount_remaining
FROM v_enrollment_balance eb
JOIN students s ON eb.student_id = s.id
JOIN groups g ON eb.group_id = g.id
WHERE eb.payment_status IN ('not_paid', 'partially_paid')
    AND s.deleted_at IS NULL;

COMMENT ON VIEW v_unpaid_enrollments IS 'Report of enrollments with outstanding balances';

-- Enrollment attendance summary
CREATE OR REPLACE VIEW v_enrollment_attendance AS
SELECT a.enrollment_id,
    COUNT(*) FILTER (WHERE a.status IN ('present', 'late')) AS sessions_attended,
    COUNT(*) FILTER (WHERE a.status = 'absent') AS sessions_missed,
    COUNT(*) AS total_sessions
FROM attendance a
GROUP BY a.enrollment_id;

COMMENT ON VIEW v_enrollment_attendance IS 'Attendance summary by enrollment';

-- =============================================================================
-- ANALYTICS AND REPORTING VIEWS
-- =============================================================================

-- Daily collections report
CREATE OR REPLACE VIEW v_daily_collections AS
SELECT 
    DATE(r.paid_at) AS collection_date,
    r.payment_method,
    COUNT(*) AS transaction_count,
    SUM(CASE WHEN p.transaction_type = 'payment' THEN p.amount ELSE 0 END) AS payments_received,
    SUM(CASE WHEN p.transaction_type = 'refund' THEN ABS(p.amount) ELSE 0 END) AS refunds_issued,
    SUM(CASE WHEN p.transaction_type = 'charge' THEN p.amount ELSE 0 END) AS charges_added,
    SUM(p.amount) AS net_amount
FROM receipts r
JOIN payments p ON p.receipt_id = r.id
WHERE r.paid_at IS NOT NULL 
    AND p.deleted_at IS NULL
    AND r.paid_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(r.paid_at), r.payment_method
ORDER BY collection_date DESC, r.payment_method;

COMMENT ON VIEW v_daily_collections IS 'Daily financial collections report (last 90 days)';

-- Course statistics
CREATE OR REPLACE VIEW v_course_stats AS
SELECT 
    c.id AS course_id,
    c.name AS course_name,
    COUNT(DISTINCT g.id) AS total_groups,
    COUNT(DISTINCT CASE WHEN g.status = 'active' THEN g.id END) AS active_groups,
    COUNT(DISTINCT CASE WHEN e.status IN ('active', 'completed', 'dropped') THEN e.student_id END) AS total_students_ever,
    COUNT(DISTINCT CASE WHEN e.status = 'active' THEN e.student_id END) AS active_students,
    AVG(gl.sessions_planned) AS avg_sessions_planned,
    SUM(gl.sessions_completed) AS total_sessions_completed
FROM courses c
    LEFT JOIN groups g ON g.course_id = c.id
    LEFT JOIN enrollments e ON e.group_id = g.id AND e.deleted_at IS NULL
    LEFT JOIN group_levels gl ON gl.group_id = g.id
WHERE c.is_active = TRUE
GROUP BY c.id, c.name;

COMMENT ON VIEW v_course_stats IS 'Course statistics with enrollment counts';

-- Group session counts
CREATE OR REPLACE VIEW v_group_session_count AS
SELECT 
    group_id,
    level_number,
    COUNT(*) FILTER (WHERE is_extra_session = FALSE) AS regular_sessions,
    COUNT(*) FILTER (WHERE is_extra_session = TRUE) AS extra_sessions,
    COUNT(*) AS total_sessions,
    MIN(session_date) AS first_session_date,
    MAX(session_date) AS last_session_date
FROM sessions
GROUP BY group_id, level_number;

COMMENT ON VIEW v_group_session_count IS 'Session counts by group and level';

-- Sibling relationships
CREATE OR REPLACE VIEW v_siblings AS
SELECT 
    sp1.student_id AS student_id,
    s1.full_name AS student_name,
    sp2.student_id AS sibling_id,
    s2.full_name AS sibling_name,
    sp1.parent_id,
    p.full_name AS parent_name
FROM student_parents sp1
    JOIN student_parents sp2 ON sp1.parent_id = sp2.parent_id AND sp1.student_id < sp2.student_id
    JOIN students s1 ON sp1.student_id = s1.id
    JOIN students s2 ON sp2.student_id = s2.id
    JOIN parents p ON sp1.parent_id = p.id
WHERE s1.deleted_at IS NULL AND s2.deleted_at IS NULL;

COMMENT ON VIEW v_siblings IS 'Sibling relationships (students sharing a parent)';

-- Student activity timeline
CREATE OR REPLACE VIEW v_student_activity_timeline AS
SELECT 
    sal.id AS activity_id,
    sal.student_id,
    s.full_name AS student_name,
    sal.activity_type,
    sal.activity_subtype,
    sal.reference_type,
    sal.reference_id,
    sal.description,
    sal.metadata,
    sal.performed_by,
    u.username AS performed_by_name,
    sal.created_at,
    DATE(sal.created_at) AS activity_date
FROM student_activity_log sal
    JOIN students s ON sal.student_id = s.id
    LEFT JOIN users u ON sal.performed_by = u.id
WHERE s.deleted_at IS NULL
ORDER BY sal.created_at DESC;

COMMENT ON VIEW v_student_activity_timeline IS 'Student activity log with related details';
