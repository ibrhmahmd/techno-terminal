-- Migration 020: Create History and Dashboard Views
-- Created: 2026-04-08
-- Purpose: Create optimized views for history queries and admin dashboards

-- View: Comprehensive Student Payment History
CREATE OR REPLACE VIEW v_student_payment_history AS
SELECT 
    p.id as payment_id,
    p.student_id,
    r.id as receipt_id,
    r.receipt_number,
    r.paid_at as payment_date,
    p.amount,
    p.transaction_type,
    p.payment_type,
    p.discount_amount,
    pa.allocated_amount,
    pa.allocation_type,
    pa.enrollment_id,
    e.group_id,
    g.name as group_name,
    c.name as course_name,
    pa.competition_id,
    comp.name as competition_name,
    r.payment_method,
    r.payer_name,
    u.id as received_by_id,
    u.username as received_by_name,
    r.receipt_template,
    r.auto_generated,
    r.sent_to_parent,
    r.parent_email,
    -- Calculate running balance for each student (window function)
    SUM(CASE 
        WHEN p.transaction_type = 'payment' THEN p.amount 
        WHEN p.transaction_type = 'refund' THEN -p.amount 
        ELSE 0 
    END) OVER (
        PARTITION BY p.student_id 
        ORDER BY r.paid_at, p.id
    ) as running_balance
FROM payments p
JOIN receipts r ON p.receipt_id = r.id
LEFT JOIN users u ON r.received_by = u.id
LEFT JOIN payment_allocations pa ON pa.payment_id = p.id
LEFT JOIN enrollments e ON pa.enrollment_id = e.id
LEFT JOIN groups g ON e.group_id = g.id
LEFT JOIN courses c ON g.course_id = c.id
LEFT JOIN competitions comp ON pa.competition_id = comp.id
ORDER BY p.student_id, r.paid_at DESC;

-- View: Student Financial Summary (for quick balance overview)
CREATE OR REPLACE VIEW v_student_financial_summary AS
SELECT 
    s.id as student_id,
    s.full_name as student_name,
    s.status as student_status,
    sb.total_amount_due,
    sb.total_discounts,
    sb.total_paid,
    sb.net_balance,
    CASE 
        WHEN sb.net_balance < 0 THEN 'in_debt'
        WHEN sb.net_balance > 0 THEN 'credit'
        ELSE 'settled'
    END as balance_status,
    sb.last_updated as balance_last_updated,
    -- Count of active enrollments
    (SELECT COUNT(*) FROM enrollments e 
     WHERE e.student_id = s.id AND e.status = 'active') as active_enrollments,
    -- Count of completed enrollments
    (SELECT COUNT(*) FROM enrollments e 
     WHERE e.student_id = s.id AND e.status = 'completed') as completed_enrollments,
    -- Last payment date
    (SELECT MAX(r.paid_at) FROM payments p 
     JOIN receipts r ON p.receipt_id = r.id 
     WHERE p.student_id = s.id AND p.transaction_type = 'payment') as last_payment_date,
    -- Total payments count
    (SELECT COUNT(*) FROM payments p 
     WHERE p.student_id = s.id AND p.transaction_type = 'payment') as total_payments_count
FROM students s
LEFT JOIN student_balances sb ON sb.student_id = s.id
WHERE s.status IN ('active', 'waiting', 'inactive');

-- View: Student Activity Timeline (comprehensive)
CREATE OR REPLACE VIEW v_student_activity_timeline AS
SELECT 
    sal.id as activity_id,
    sal.student_id,
    s.full_name as student_name,
    sal.activity_type,
    sal.activity_subtype,
    sal.reference_type,
    sal.reference_id,
    sal.description,
    sal.metadata,
    sal.performed_by,
    u.username as performed_by_name,
    sal.created_at,
    -- Format for display
    CASE sal.activity_type
        WHEN 'enrollment' THEN 'Enrollment Activity'
        WHEN 'payment' THEN 'Payment Activity'
        WHEN 'group_change' THEN 'Group Change'
        WHEN 'competition' THEN 'Competition Activity'
        WHEN 'status_change' THEN 'Status Change'
        ELSE 'Other Activity'
    END as activity_category
FROM student_activity_log sal
JOIN students s ON sal.student_id = s.id
LEFT JOIN users u ON sal.performed_by = u.id
ORDER BY sal.created_at DESC;

-- View: Unpaid Enrollments with Student Details
CREATE OR REPLACE VIEW v_unpaid_enrollments AS
SELECT 
    e.id as enrollment_id,
    e.student_id,
    s.full_name as student_name,
    s.phone as student_phone,
    e.group_id,
    g.name as group_name,
    c.name as course_name,
    e.level_number,
    e.amount_due,
    e.discount_applied,
    (e.amount_due - e.discount_applied) as net_due,
    COALESCE(paid_query.total_paid, 0) as total_paid,
    (e.amount_due - e.discount_applied - COALESCE(paid_query.total_paid, 0)) as remaining_balance,
    e.status as enrollment_status,
    e.enrolled_at,
    e.notes
FROM enrollments e
JOIN students s ON e.student_id = s.id
JOIN groups g ON e.group_id = g.id
LEFT JOIN courses c ON g.course_id = c.id
LEFT JOIN (
    SELECT 
        pa.enrollment_id,
        SUM(pa.allocated_amount) as total_paid
    FROM payment_allocations pa
    JOIN payments p ON pa.payment_id = p.id
    WHERE p.transaction_type = 'payment'
    GROUP BY pa.enrollment_id
) paid_query ON paid_query.enrollment_id = e.id
WHERE e.status = 'active'
  AND (e.amount_due - e.discount_applied - COALESCE(paid_query.total_paid, 0)) > 0
ORDER BY remaining_balance DESC;

-- View: Daily Collections Report
CREATE OR REPLACE VIEW v_daily_collections AS
SELECT 
    DATE(r.paid_at) as collection_date,
    r.payment_method,
    COUNT(*) as transaction_count,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0) as collected_amount,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) as refunded_amount,
    COALESCE(SUM(p.discount_amount), 0) as total_discounts,
    (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0) - 
     COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)) as net_collection
FROM receipts r
JOIN payments p ON p.receipt_id = r.id
WHERE r.paid_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(r.paid_at), r.payment_method
ORDER BY collection_date DESC, collected_amount DESC;
