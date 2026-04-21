-- Migration: Create admin notification settings table
-- Enables per-admin notification preferences

CREATE TABLE admin_notification_settings (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification type identifier
    notification_type VARCHAR(50) NOT NULL,
    -- Valid types:
    -- 'enrollment_created', 'enrollment_completed', 'enrollment_dropped',
    -- 'enrollment_transferred', 'level_progression',
    -- 'payment_received', 'payment_reminder',
    -- 'daily_report', 'weekly_report', 'monthly_report',
    -- 'competition_team_registration', 'competition_fee_payment', 'competition_placement'
    
    -- Is this notification enabled for this admin?
    is_enabled BOOLEAN DEFAULT true,
    
    -- Channel preference (currently EMAIL only, future: WHATSAPP, BOTH)
    channel VARCHAR(20) DEFAULT 'EMAIL',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(admin_id, notification_type)
);

-- Indexes for faster lookups
CREATE INDEX idx_admin_settings_admin_id ON admin_notification_settings(admin_id);
CREATE INDEX idx_admin_settings_type ON admin_notification_settings(notification_type);

COMMENT ON TABLE admin_notification_settings IS 'Stores per-admin notification preferences for granular control';
