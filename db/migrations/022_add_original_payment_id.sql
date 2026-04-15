-- Migration 022: Add original_payment_id for refund traceability
-- Purpose: Link refund payment rows to the original payment row

ALTER TABLE payments
    ADD COLUMN IF NOT EXISTS original_payment_id INTEGER REFERENCES payments(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_payments_original_payment_id
    ON payments(original_payment_id);
