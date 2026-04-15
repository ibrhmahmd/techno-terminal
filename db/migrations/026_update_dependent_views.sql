-- Migration 026: Update dependent views to use new payment_status columns
-- Created: 2026-04-15
-- Purpose: Update views that reference enrollment balance data

-- Update v_unpaid_enrollments to use new payment_status column
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
    vb.net_due,
    vb.total_paid,
    vb.amount_remaining,
    vb.balance,
    vb.payment_status,
    e.status as enrollment_status,
    e.enrolled_at,
    e.notes
FROM enrollments e
JOIN students s ON e.student_id = s.id
JOIN groups g ON e.group_id = g.id
LEFT JOIN courses c ON g.course_id = c.id
JOIN v_enrollment_balance vb ON vb.enrollment_id = e.id
WHERE e.status = 'active'
  AND vb.payment_status IN ('not_paid', 'partially_paid')
ORDER BY vb.amount_remaining DESC;

COMMENT ON VIEW v_unpaid_enrollments IS 
'Active enrollments with remaining balance. Uses payment_status from v_enrollment_balance.';
