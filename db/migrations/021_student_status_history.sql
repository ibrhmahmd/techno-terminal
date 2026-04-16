-- Migration: Create student_status_history table for audit trail
-- Purpose: Log all student status transitions with user attribution

CREATE TABLE IF NOT EXISTS student_status_history (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_status_history_student ON student_status_history(student_id);
CREATE INDEX idx_status_history_created ON student_status_history(created_at DESC);
CREATE INDEX idx_status_history_changed_by ON student_status_history(changed_by_user_id);

-- Comment for documentation
COMMENT ON TABLE student_status_history IS 'Audit log of all student status changes';
COMMENT ON COLUMN student_status_history.previous_status IS 'Previous status value (NULL if initial status)';
COMMENT ON COLUMN student_status_history.new_status IS 'New status value after change';
COMMENT ON COLUMN student_status_history.changed_by_user_id IS 'User who made the status change';
