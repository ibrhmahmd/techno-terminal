-- Migration 015: Add Student Balance Tables
-- Created: 2026-04-08
-- Purpose: Create materialized balance tracking and payment allocation tables

-- Student Balances table (materialized aggregate)
CREATE TABLE IF NOT EXISTS student_balances (
    student_id INTEGER PRIMARY KEY REFERENCES students(id),
    total_amount_due DECIMAL(10,2) DEFAULT 0.00,
    total_discounts DECIMAL(10,2) DEFAULT 0.00,
    total_paid DECIMAL(10,2) DEFAULT 0.00,
    net_balance DECIMAL(10,2) DEFAULT 0.00,  -- negative = debt, positive = credit
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    updated_by INTEGER REFERENCES users(id)
);

-- Indexes for balance table
CREATE INDEX idx_student_balances_net_balance ON student_balances(net_balance) WHERE net_balance < 0;
CREATE INDEX idx_student_balances_last_updated ON student_balances(last_updated);

-- Enrollment Balance History table (tracks balance changes over time)
CREATE TABLE IF NOT EXISTS enrollment_balance_history (
    id BIGSERIAL PRIMARY KEY,
    enrollment_id INTEGER REFERENCES enrollments(id),
    student_id INTEGER REFERENCES students(id),
    amount_due DECIMAL(10,2) NOT NULL,
    discount_applied DECIMAL(10,2) DEFAULT 0.00,
    total_paid DECIMAL(10,2) DEFAULT 0.00,
    remaining_balance DECIMAL(10,2) NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    recorded_by INTEGER REFERENCES users(id),
    notes TEXT
);

CREATE INDEX idx_enrollment_balance_history_enrollment ON enrollment_balance_history(enrollment_id, recorded_at DESC);
CREATE INDEX idx_enrollment_balance_history_student ON enrollment_balance_history(student_id, recorded_at DESC);

-- Credit tracking table (for overpayments)
CREATE TABLE IF NOT EXISTS student_credits (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    payment_id INTEGER REFERENCES payments(id),
    credit_amount DECIMAL(10,2) NOT NULL,
    used_amount DECIMAL(10,2) DEFAULT 0.00,
    remaining_credit DECIMAL(10,2) GENERATED ALWAYS AS (credit_amount - used_amount) STORED,
    status VARCHAR(20) DEFAULT 'active',  -- active, used, expired
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    notes TEXT
);

CREATE INDEX idx_student_credits_active ON student_credits(student_id, status) WHERE status = 'active';
