-- Migration 024: Update v_enrollment_balance with payment_status and amount_remaining
-- Created: 2026-04-15
-- Purpose: Add computed payment status and remaining amount to enrollment balance view

-- Add payment_status and amount_remaining to existing view
CREATE OR REPLACE VIEW v_enrollment_balance AS
SELECT 
    e.id AS enrollment_id,
    e.student_id,
    e.group_id,
    e.level_number,
    e.amount_due,
    e.discount_applied,
    (e.amount_due - COALESCE(e.discount_applied, 0)) AS net_due,
    COALESCE(
        SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')),
        0
    ) - COALESCE(
        SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'),
        0
    ) AS total_paid,
    -- Amount remaining (never negative - debt is tracked separately in balance)
    GREATEST(
        (e.amount_due - COALESCE(e.discount_applied, 0)) - 
        COALESCE(
            SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')),
            0
        ) + COALESCE(
            SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'),
            0
        ),
        0
    ) AS amount_remaining,
    -- Payment status enum: not_paid, partially_paid, paid
    CASE 
        WHEN COALESCE(
            SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')),
            0
        ) = 0 THEN 'not_paid'
        WHEN (e.amount_due - COALESCE(e.discount_applied, 0)) <= COALESCE(
            SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')),
            0
        ) - COALESCE(
            SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'),
            0
        ) THEN 'paid'
        ELSE 'partially_paid'
    END AS payment_status,
    -- Balance (negative = overpayment/credit, positive = debt)
    (
        COALESCE(
            SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')),
            0
        ) - COALESCE(
            SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'),
            0
        )
    ) - (e.amount_due - COALESCE(e.discount_applied, 0)) AS balance
FROM enrollments e
LEFT JOIN payments p ON p.enrollment_id = e.id
GROUP BY e.id;

COMMENT ON VIEW v_enrollment_balance IS 
'Enrollment balance view with payment_status (not_paid/partially_paid/paid) and amount_remaining. Balance column: negative = credit/overpayment, positive = debt.';
