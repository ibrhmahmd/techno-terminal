-- Sprint 6 (B8 / P6): `balance` = total_paid - net_due (negative = debt, positive = credit, zero = settled).
-- Replaces legacy `balance` = net_due - total_paid.
-- Apply after 006; idempotent via CREATE OR REPLACE VIEW.

CREATE OR REPLACE VIEW v_enrollment_balance AS
SELECT e.id AS enrollment_id,
    e.student_id,
    e.group_id,
    e.level_number,
    e.amount_due,
    e.discount_applied,
    (e.amount_due - e.discount_applied) AS net_due,
    COALESCE(
        SUM(p.amount) FILTER (
            WHERE p.transaction_type IN ('payment', 'charge')
        ),
        0
    ) - COALESCE(
        SUM(p.amount) FILTER (
            WHERE p.transaction_type = 'refund'
        ),
        0
    ) AS total_paid,
    (
        COALESCE(
            SUM(p.amount) FILTER (
                WHERE p.transaction_type IN ('payment', 'charge')
            ),
            0
        ) - COALESCE(
            SUM(p.amount) FILTER (
                WHERE p.transaction_type = 'refund'
            ),
            0
        )
    ) - (e.amount_due - e.discount_applied) AS balance
FROM enrollments e
    LEFT JOIN payments p ON p.enrollment_id = e.id
GROUP BY e.id;
