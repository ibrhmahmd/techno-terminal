-- =============================================================================
-- FINANCE TABLES (SYNCED FROM LIVE DB)
-- =============================================================================

DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS receipts CASCADE;

CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    payer_name TEXT,
    payment_method TEXT,
    received_by INTEGER,
    receipt_number TEXT,
    notes TEXT,
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    receipt_template VARCHAR(50) DEFAULT 'standard'::character varying,
    generation_metadata JSONB,
    CONSTRAINT receipts_payment_method_check CHECK ((payment_method = ANY (ARRAY['cash'::text, 'card'::text, 'transfer'::text, 'online'::text, 'ewallet'::text, 'instapay'::text, 'other'::text]))),
    CONSTRAINT receipts_receipt_number_key UNIQUE (receipt_number),
    CONSTRAINT receipts_received_by_fkey FOREIGN KEY (received_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    enrollment_id INTEGER,
    amount NUMERIC NOT NULL,
    transaction_type TEXT NOT NULL,
    payment_type TEXT,
    discount_amount NUMERIC DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    original_payment_id INTEGER,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER,
    team_member_id INTEGER,
    CONSTRAINT payments_amount_check CHECK ((amount <> (0)::numeric)),
    CONSTRAINT payments_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT payments_discount_amount_check CHECK ((discount_amount >= (0)::numeric)),
    CONSTRAINT payments_enrollment_id_fkey FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE SET NULL,
    CONSTRAINT payments_original_payment_id_fkey FOREIGN KEY (original_payment_id) REFERENCES payments(id) ON DELETE SET NULL,
    CONSTRAINT payments_payment_type_check CHECK ((payment_type = ANY (ARRAY['course_level'::text, 'competition'::text, 'other'::text]))),
    CONSTRAINT payments_receipt_id_fkey FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE RESTRICT,
    CONSTRAINT payments_student_id_fkey FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE RESTRICT,
    CONSTRAINT payments_transaction_type_check CHECK ((transaction_type = ANY (ARRAY['charge'::text, 'payment'::text, 'refund'::text])))
);
