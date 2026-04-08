-- Migration 017: Add Student Activity Log and History Tables
-- Created: 2026-04-08
-- Purpose: Comprehensive audit trail for all student activities

-- Main activity log table (append-only)
CREATE TABLE IF NOT EXISTS student_activity_log (
    id BIGSERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    activity_type VARCHAR(50) NOT NULL,  -- 'enrollment', 'payment', 'group_change', 'competition', 'status_change', 'note', 'communication'
    activity_subtype VARCHAR(50),  -- 'enrollment_created', 'payment_received', 'group_transferred', 'level_progressed', etc.
    reference_type VARCHAR(50),  -- 'enrollment', 'payment', 'group', 'competition', 'team', 'student', 'receipt'
    reference_id INTEGER,  -- ID of the referenced entity
    description TEXT NOT NULL,
    metadata JSONB,  -- Flexible additional data (e.g., previous_value, new_value)
    performed_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for activity log
CREATE INDEX idx_activity_log_student_time ON student_activity_log(student_id, created_at DESC);
CREATE INDEX idx_activity_log_type_time ON student_activity_log(activity_type, created_at DESC);
CREATE INDEX idx_activity_log_reference ON student_activity_log(reference_type, reference_id);
CREATE INDEX idx_activity_log_created_at ON student_activity_log(created_at DESC);
CREATE INDEX idx_activity_log_performed_by ON student_activity_log(performed_by);

-- Note: Partial indexes with NOW() are not allowed (NOW() is not immutable)
-- The regular idx_activity_log_student_time index handles recent queries efficiently

-- Index for metadata JSONB queries
CREATE INDEX idx_activity_log_metadata ON student_activity_log USING GIN(metadata);

-- Student enrollment history table (lifecycle tracking)
CREATE TABLE IF NOT EXISTS student_enrollment_history (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    enrollment_id INTEGER REFERENCES enrollments(id),
    group_id INTEGER REFERENCES groups(id),
    level_number INTEGER,
    action VARCHAR(20) NOT NULL,  -- 'enrolled', 'transferred_in', 'transferred_out', 'completed', 'cancelled', 'reinstated'
    action_date TIMESTAMPTZ NOT NULL,
    previous_group_id INTEGER REFERENCES groups(id),  -- For transfers
    previous_level_number INTEGER,  -- For level changes
    amount_due DECIMAL(10,2),
    amount_paid DECIMAL(10,2),
    final_status VARCHAR(20),
    performed_by INTEGER REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_enrollment_history_student ON student_enrollment_history(student_id, action_date DESC);
CREATE INDEX idx_enrollment_history_enrollment ON student_enrollment_history(enrollment_id);
CREATE INDEX idx_enrollment_history_group ON student_enrollment_history(group_id);
CREATE INDEX idx_enrollment_history_action ON student_enrollment_history(action, action_date DESC);

-- Payment history detail table (denormalized for fast queries)
CREATE TABLE IF NOT EXISTS student_payment_history (
    id BIGSERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    payment_id INTEGER NOT NULL REFERENCES payments(id),
    receipt_id INTEGER REFERENCES receipts(id),
    enrollment_id INTEGER REFERENCES enrollments(id),
    competition_id INTEGER REFERENCES competitions(id),
    team_member_id INTEGER REFERENCES team_members(id),
    payment_date TIMESTAMPTZ NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,  -- 'payment', 'refund', 'charge', 'adjustment'
    payment_type VARCHAR(30),  -- 'course_level', 'competition', 'other'
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    allocated_amount DECIMAL(10,2),
    balance_after DECIMAL(10,2),
    receipt_number VARCHAR(50),
    payment_method VARCHAR(20),
    payer_name VARCHAR(255),
    received_by INTEGER REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payment_history_student ON student_payment_history(student_id, payment_date DESC);
CREATE INDEX idx_payment_history_payment ON student_payment_history(payment_id);
CREATE INDEX idx_payment_history_receipt ON student_payment_history(receipt_id);
CREATE INDEX idx_payment_history_enrollment ON student_payment_history(enrollment_id);
CREATE INDEX idx_payment_history_type ON student_payment_history(transaction_type, payment_type);

-- Competition participation history
CREATE TABLE IF NOT EXISTS student_competition_history (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    competition_id INTEGER NOT NULL REFERENCES competitions(id),
    team_id INTEGER REFERENCES teams(id),
    team_member_id INTEGER REFERENCES team_members(id),
    participation_type VARCHAR(20) NOT NULL,  -- 'registered', 'participated', 'awarded', 'cancelled'
    registration_date TIMESTAMPTZ,
    fee_amount DECIMAL(10,2),
    fee_paid BOOLEAN DEFAULT FALSE,
    payment_id INTEGER REFERENCES payments(id),
    result_position INTEGER,  -- For awards
    result_notes TEXT,
    performed_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_competition_history_student ON student_competition_history(student_id, created_at DESC);
CREATE INDEX idx_competition_history_competition ON student_competition_history(competition_id);
