-- Migration 016: Add Payment Allocations Table
-- Created: 2026-04-08
-- Purpose: Track partial payment allocations across multiple enrollments

CREATE TABLE IF NOT EXISTS payment_allocations (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE SET NULL,
    competition_id INTEGER REFERENCES competitions(id) ON DELETE SET NULL,
    team_member_id INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
    allocated_amount DECIMAL(10,2) NOT NULL,
    allocation_type VARCHAR(30) NOT NULL,  -- 'course_fee', 'competition_fee', 'refund', 'adjustment', 'credit', 'other'
    allocated_at TIMESTAMPTZ DEFAULT NOW(),
    allocated_by INTEGER REFERENCES users(id),
    notes TEXT,
    -- Ensure at least one reference is provided
    CONSTRAINT chk_payment_allocation_reference CHECK (
        (enrollment_id IS NOT NULL) OR 
        (competition_id IS NOT NULL) OR 
        (team_member_id IS NOT NULL) OR
        (allocation_type = 'credit')
    ),
    -- Ensure positive allocation amount
    CONSTRAINT chk_allocation_amount_positive CHECK (allocated_amount > 0)
);

-- Indexes for payment allocations
CREATE INDEX idx_payment_allocations_payment ON payment_allocations(payment_id);
CREATE INDEX idx_payment_allocations_enrollment ON payment_allocations(enrollment_id);
CREATE INDEX idx_payment_allocations_competition ON payment_allocations(competition_id);
CREATE INDEX idx_payment_allocations_type ON payment_allocations(allocation_type);
CREATE INDEX idx_payment_allocations_allocated_at ON payment_allocations(allocated_at);

-- Composite index for common query pattern
CREATE INDEX idx_payment_allocations_enrollment_type ON payment_allocations(enrollment_id, allocation_type);

-- Backfill existing payments into allocations
-- This creates allocation records for payments that don't have them yet
INSERT INTO payment_allocations (payment_id, enrollment_id, allocated_amount, allocation_type, notes)
SELECT 
    p.id as payment_id,
    p.enrollment_id,
    p.amount as allocated_amount,
    COALESCE(p.payment_type, 'course_fee') as allocation_type,
    'Auto-migrated from existing payment' as notes
FROM payments p
LEFT JOIN payment_allocations pa ON pa.payment_id = p.id
WHERE pa.id IS NULL
  AND p.enrollment_id IS NOT NULL
  AND p.transaction_type = 'payment';

-- Create view for easy payment allocation queries
CREATE OR REPLACE VIEW v_payment_allocations_detailed AS
SELECT 
    pa.id as allocation_id,
    pa.payment_id,
    pa.enrollment_id,
    pa.competition_id,
    pa.team_member_id,
    pa.allocated_amount,
    pa.allocation_type,
    pa.allocated_at,
    pa.notes,
    p.student_id,
    p.receipt_id,
    p.transaction_type,
    r.receipt_number,
    s.full_name as student_name,
    e.group_id,
    g.name as group_name,
    c.name as competition_name
FROM payment_allocations pa
JOIN payments p ON pa.payment_id = p.id
LEFT JOIN receipts r ON p.receipt_id = r.id
LEFT JOIN students s ON p.student_id = s.id
LEFT JOIN enrollments e ON pa.enrollment_id = e.id
LEFT JOIN groups g ON e.group_id = g.id
LEFT JOIN competitions c ON pa.competition_id = c.id;
