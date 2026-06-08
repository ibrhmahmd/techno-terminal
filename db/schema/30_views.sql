-- =============================================================================
-- VIEWS (SYNCED FROM LIVE DB)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- View: active_payments
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW active_payments AS
SELECT id,
    receipt_id,
    student_id,
    enrollment_id,
    amount,
    transaction_type,
    payment_type,
    discount_amount,
    notes,
    created_at,
    metadata,
    original_payment_id,
    deleted_at,
    deleted_by
   FROM payments
  WHERE (deleted_at IS NULL);

-- -----------------------------------------------------------------------------
-- View: active_students
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW active_students AS
SELECT id,
    full_name,
    date_of_birth,
    gender,
    phone,
    notes,
    created_by,
    created_at,
    updated_at,
    metadata,
    status,
    waiting_since,
    waiting_priority,
    waiting_notes,
    deleted_at,
    deleted_by
   FROM students
  WHERE (deleted_at IS NULL);

-- -----------------------------------------------------------------------------
-- View: deleted_payments
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW deleted_payments AS
SELECT id,
    receipt_id,
    student_id,
    enrollment_id,
    amount,
    transaction_type,
    payment_type,
    discount_amount,
    notes,
    created_at,
    metadata,
    original_payment_id,
    deleted_at,
    deleted_by
   FROM payments
  WHERE (deleted_at IS NOT NULL);

-- -----------------------------------------------------------------------------
-- View: deleted_students
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW deleted_students AS
SELECT id,
    full_name,
    date_of_birth,
    gender,
    phone,
    notes,
    created_by,
    created_at,
    updated_at,
    metadata,
    status,
    waiting_since,
    waiting_priority,
    waiting_notes,
    deleted_at,
    deleted_by
   FROM students
  WHERE (deleted_at IS NOT NULL);

-- -----------------------------------------------------------------------------
-- View: v_course_stats
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_course_stats AS
SELECT c.id AS course_id,
    c.name AS course_name,
    count(DISTINCT g.id) AS total_groups,
    count(DISTINCT
        CASE
            WHEN (g.status = 'active'::text) THEN g.id
            ELSE NULL::integer
        END) AS active_groups,
    count(DISTINCT
        CASE
            WHEN (e.status = ANY (ARRAY['active'::text, 'completed'::text, 'dropped'::text])) THEN e.student_id
            ELSE NULL::integer
        END) AS total_students_ever,
    count(DISTINCT
        CASE
            WHEN (e.status = 'active'::text) THEN e.student_id
            ELSE NULL::integer
        END) AS active_students
   FROM ((courses c
     LEFT JOIN groups g ON ((g.course_id = c.id)))
     LEFT JOIN enrollments e ON ((e.group_id = g.id)))
  WHERE (c.is_active = true)
  GROUP BY c.id, c.name;

-- -----------------------------------------------------------------------------
-- View: v_daily_collections
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_daily_collections AS
SELECT date(r.paid_at) AS collection_date,
    r.payment_method,
    count(*) AS transaction_count,
    COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = ANY (ARRAY['payment'::text, 'charge'::text]))), (0)::numeric) AS collected_amount,
    COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = 'refund'::text)), (0)::numeric) AS refunded_amount,
    COALESCE(sum(p.discount_amount), (0)::numeric) AS total_discounts,
    (COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = ANY (ARRAY['payment'::text, 'charge'::text]))), (0)::numeric) - COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = 'refund'::text)), (0)::numeric)) AS net_collection
   FROM (receipts r
     JOIN payments p ON (((p.receipt_id = r.id) AND (p.deleted_at IS NULL))))
  WHERE (r.paid_at >= (CURRENT_DATE - '30 days'::interval))
  GROUP BY (date(r.paid_at)), r.payment_method
  ORDER BY (date(r.paid_at)) DESC, COALESCE(sum(p.amount) FILTER (WHERE (p.transaction_type = ANY (ARRAY['payment'::text, 'charge'::text]))), (0)::numeric) DESC;

-- -----------------------------------------------------------------------------
-- View: v_enrollment_attendance
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_enrollment_attendance AS
SELECT enrollment_id,
    count(*) FILTER (WHERE (status = 'present'::text)) AS sessions_attended,
    count(*) FILTER (WHERE (status = 'absent'::text)) AS sessions_missed,
    count(*) FILTER (WHERE (status = 'cancelled'::text)) AS sessions_cancelled,
    count(*) AS sessions_total
   FROM attendance a
  GROUP BY enrollment_id;

-- -----------------------------------------------------------------------------
-- View: v_enrollment_balance
-- -----------------------------------------------------------------------------
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
     LEFT JOIN payments p ON ((p.enrollment_id = e.id)))
  GROUP BY e.id;

-- -----------------------------------------------------------------------------
-- View: v_group_session_count
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_group_session_count AS
SELECT group_id,
    level_number,
    count(*) FILTER (WHERE (is_extra_session = false)) AS regular_sessions,
    count(*) FILTER (WHERE (is_extra_session = true)) AS extra_sessions,
    count(*) AS total_sessions
   FROM sessions
  GROUP BY group_id, level_number;

-- -----------------------------------------------------------------------------
-- View: v_siblings
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_siblings AS
SELECT sp1.student_id,
    s1.full_name AS student_name,
    sp2.student_id AS sibling_id,
    s2.full_name AS sibling_name,
    p.id AS parent_id,
    p.full_name AS parent_name
   FROM ((((student_parents sp1
     JOIN student_parents sp2 ON (((sp1.parent_id = sp2.parent_id) AND (sp1.student_id <> sp2.student_id))))
     JOIN students s1 ON ((sp1.student_id = s1.id)))
     JOIN students s2 ON ((sp2.student_id = s2.id)))
     JOIN parents p ON ((sp1.parent_id = p.id)))
  WHERE ((s1.deleted_at IS NULL) AND (s2.deleted_at IS NULL));

-- -----------------------------------------------------------------------------
-- View: v_student_activity_timeline
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_student_activity_timeline AS
SELECT sal.id AS activity_id,
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
        CASE sal.activity_type
            WHEN 'enrollment'::text THEN 'Enrollment Activity'::text
            WHEN 'payment'::text THEN 'Payment Activity'::text
            WHEN 'group_change'::text THEN 'Group Change'::text
            WHEN 'competition'::text THEN 'Competition Activity'::text
            WHEN 'status_change'::text THEN 'Status Change'::text
            ELSE 'Other Activity'::text
        END AS activity_category
   FROM ((student_activity_log sal
     JOIN students s ON ((sal.student_id = s.id)))
     LEFT JOIN users u ON ((sal.performed_by = u.id)))
  ORDER BY sal.created_at DESC;

-- -----------------------------------------------------------------------------
-- View: v_students
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_students AS
SELECT s.id,
    s.full_name,
    s.date_of_birth,
    (EXTRACT(year FROM age((s.date_of_birth)::timestamp with time zone)))::integer AS age,
    s.gender,
    s.phone AS student_phone,
    s.notes,
    s.status,
    s.created_at,
    s.updated_at,
    s.metadata,
    p.full_name AS primary_parent_name,
    p.phone_primary AS primary_parent_phone,
    p.email AS primary_parent_email
   FROM ((students s
     LEFT JOIN student_parents sp ON (((s.id = sp.student_id) AND (sp.is_primary = true))))
     LEFT JOIN parents p ON ((sp.parent_id = p.id)))
  WHERE (s.deleted_at IS NULL);

-- -----------------------------------------------------------------------------
-- View: v_unpaid_enrollments
-- -----------------------------------------------------------------------------
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

