-- Sprint 4 (B9): index receipts.paid_at for date-range listing / ordering (Dashboard receipt browser).
-- Idempotent.

CREATE INDEX IF NOT EXISTS idx_receipts_paid_at ON receipts(paid_at DESC);
