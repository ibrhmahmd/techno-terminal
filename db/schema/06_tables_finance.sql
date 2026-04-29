-- =============================================================================
-- FINANCE TABLES
-- Receipts, payments, and financial transactions
-- Dependencies: students (03_tables_crm.sql), enrollments (05_tables_enrollments.sql),
--               users (02_tables_core.sql)
-- =============================================================================

DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS receipts CASCADE;

-- =============================================================================
-- RECEIPTS
-- Receipt header records
-- =============================================================================
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    payer_name TEXT,
    payment_method TEXT CHECK (
        payment_method IN ('cash', 'card', 'transfer', 'online')
    ),
    received_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    receipt_number TEXT UNIQUE,
    receipt_template TEXT,
    notes TEXT,
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE receipts IS 'Receipt header records for payments';
COMMENT ON COLUMN receipts.receipt_number IS 'Unique receipt identifier/number';
COMMENT ON COLUMN receipts.receipt_template IS 'Name of template used for this receipt';

-- =============================================================================
-- PAYMENTS
-- Financial transactions (charges, payments, refunds)
-- =============================================================================
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER NOT NULL REFERENCES receipts(id) ON DELETE RESTRICT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE SET NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount != 0),
    transaction_type TEXT NOT NULL CHECK (
        transaction_type IN ('charge', 'payment', 'refund')
    ),
    payment_type TEXT CHECK (
        payment_type IN ('course_level', 'competition', 'other')
    ),
    discount_amount DECIMAL(10, 2) DEFAULT 0 CHECK (discount_amount >= 0),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

COMMENT ON TABLE payments IS 'Financial transactions: charges, payments, and refunds';
COMMENT ON COLUMN payments.amount IS 'Transaction amount (positive for charges/payments, negative for refunds)';
COMMENT ON COLUMN payments.transaction_type IS 'Type: charge (debit), payment (credit), or refund';
COMMENT ON COLUMN payments.payment_type IS 'Category: course_level, competition, or other';
COMMENT ON COLUMN payments.discount_amount IS 'Discount applied to this payment';
COMMENT ON COLUMN payments.deleted_at IS 'Soft delete timestamp for voided transactions';

COMMENT ON TABLE payments IS 
'Source of truth for all financial transactions (charge, payment, refund). '
'Enrollment balance is computed in real-time via v_enrollment_balance view. '
'Legacy payment_allocations table deprecated in migration 028 and removed in migration 043.';
