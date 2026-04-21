-- Migration: Create notification additional recipients table
-- Allows admins to add non-admin emails to receive notifications

CREATE TABLE notification_additional_recipients (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Email of non-admin recipient
    email VARCHAR(255) NOT NULL,
    
    -- Which notification types this recipient gets
    -- NULL = all notifications, otherwise specific types only
    notification_types VARCHAR(50)[],
    
    -- Optional label (e.g., "Manager", "Finance Team")
    label VARCHAR(100),
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(admin_id, email)
);

-- Indexes for faster lookups
CREATE INDEX idx_additional_recipients_admin_id ON notification_additional_recipients(admin_id);
CREATE INDEX idx_additional_recipients_email ON notification_additional_recipients(email);
CREATE INDEX idx_additional_recipients_active ON notification_additional_recipients(is_active);

COMMENT ON TABLE notification_additional_recipients IS 'Additional email recipients (non-admins) who can receive notifications';
