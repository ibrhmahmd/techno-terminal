-- Migration: 080_fix_balance_view_deleted_at
-- Description: Fix v_enrollment_balance view to exclude soft-deleted payments from total_paid calculation
-- Date: 2026-08-25
-- Related: FR-011 - v_enrollment_balance must filter soft-deleted payments

-- Drop and recreate the view with the fix
DROP VIEW IF EXISTS v_unpaid_enrollments;
DROP VIEW IF EXISTS v_enrollment_balance;

-- Recreate v_enrollment_balance with p.deleted_at IS NULL filter
CREATE OR REPLACE VIEW v_enrollment_balance AS
SELECT e.id AS enrollment_id,
    e.student_id,
    e.group_id,
    e.level_number,
    e.amount_due,
    e.discount_applied,
    (e.amount_due - COALESCE(e.discount_applied, (0)::numeric)) AS net_due,
    (COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = ANY (ARRAY['payment'::text, 'charge'::text]))), (0)::numeric) - COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = 'refund'::text)), (0)::numeric)) AS total_paid,
    GREATEST((((e.amount_due - COALESCE(e.discount_applied, (0)::numeric)) - COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = ANY (ARRAY['payment'::text, 'charge'::text]))), (0)::numeric)) + COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = 'refund'::text)), (0)::numeric)), (0)::numeric) AS amount_remaining,
    (
        CASE
            WHEN (COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = ANY (ARRAY['payment'::text, 'charge'::text]))), (0)::numeric) = (0)::numeric) THEN 'not_paid'::text
            WHEN ((e.amount_due - COALESCE(e.discount_applied, (0)::numeric)) <= (COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = ANY (ARRAY['payment'::text, 'charge'::text]))), (0)::numeric) - COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = 'refund'::text)), (0)::numeric))) THEN 'paid'::text
            ELSE 'partially_paid'::text
        END)::character varying(20) AS payment_status,
    ((COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = ANY (ARRAY['payment'::text, 'charge'::text]))), (0)::numeric) - COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = 'refund'::text)), (0)::numeric)) - (e.amount_due - COALESCE(e.discount_applied, (0)::numeric))) AS balance
   FROM (enrollments e
     LEFT JOIN payments p ON ((p.enrollment_id = e.id) AND (p.deleted_at IS NULL)))
  GROUP BY e.id;

-- Recreate v_unpaid_enrollments (depends on v_enrollment_balance)
CREATE OR REPLACE VIEW v_unpaid_enrollments AS
SELECT e.id AS enrollment_id,
    e.student_id,
    s.full_name AS student_name,
    s.phone AS student_phone,
    e.group_id,
    g.name AS group_name,
    c.name AS course_name,
    e.level_number,
    e.amount_due,
    e.discount_applied,
    (e.amount_due - COALESCE(e.discount_applied, (0)::numeric)) AS net_due,
    COALESCE(vb.total_paid, (0)::numeric) AS total_paid,
    GREATEST(((e.amount_due - COALESCE(e.discount_applied, (0)::numeric)) - COALESCE(vb.total_paid, (0)::numeric)), (0)::numeric) AS remaining_balance,
    COALESCE(vb.balance, (e.amount_due - COALESCE(e.discount_applied, (0)::numeric))) AS balance,
    COALESCE(vb.payment_status, 'not_paid'::character varying) AS payment_status,
    e.status AS enrollment_status,
    e.enrolled_at,
    e.notes
   FROM ((((enrollments e
      JOIN students s ON ((s.id = e.student_id)))
      JOIN groups g ON ((g.id = e.group_id)))
      LEFT JOIN courses c ON ((c.id = g.course_id)))
      LEFT JOIN v_enrollment_balance vb ON ((vb.enrollment_id = e.id)))
   WHERE ((e.status = 'active'::text) AND (GREATEST(((e.amount_due - COALESCE(e.discount_applied, (0)::numeric)) - COALESCE(vb.total_paid, (0)::numeric)), (0)::numeric) > (0)::numeric))
   ORDER BY GREATEST(((e.amount_due - COALESCE(e.discount_applied, (0)::numeric)) - COALESCE(vb.total_paid, (0)::numeric)), (0)::numeric) DESC;