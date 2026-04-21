-- Migration: Create admin notification settings table
-- This enables per-admin notification preferences (future feature)

CREATE TABLE admin_notification_settings (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL, -- 'enrollment_created', 'enrollment_completed', 'enrollment_dropped', 'enrollment_transferred', 'level_progression', 'payment_received', 'payment_reminder', 'daily_report', 'weekly_report', 'monthly_report'
    is_enabled BOOLEAN DEFAULT true,
    channel VARCHAR(20) DEFAULT 'EMAIL', -- 'EMAIL', 'WHATSAPP', 'BOTH'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(admin_id, notification_type)
);

-- Index for faster lookups
CREATE INDEX idx_admin_notification_settings_admin_id ON admin_notification_settings(admin_id);
CREATE INDEX idx_admin_notification_settings_type ON admin_notification_settings(notification_type);

COMMENT ON TABLE admin_notification_settings IS 'Stores per-admin notification preferences for granular control';
