-- =============================================================================
-- NOTIFICATIONS TABLES
-- Notification system for alerts, reminders, and communication
-- Dependencies: users (02_tables_core.sql)
-- =============================================================================

DROP TABLE IF EXISTS notification_additional_recipients CASCADE;
DROP TABLE IF EXISTS notification_logs CASCADE;
DROP TABLE IF EXISTS notification_subscribers CASCADE;
DROP TABLE IF EXISTS notification_templates CASCADE;
DROP TABLE IF EXISTS admin_notification_settings CASCADE;

-- =============================================================================
-- NOTIFICATION_TEMPLATES
-- Templates for notification messages
-- =============================================================================
CREATE TABLE notification_templates (
    id SERIAL PRIMARY KEY,
    template_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    subject_template TEXT,
    body_template TEXT NOT NULL,
    channel TEXT NOT NULL CHECK (channel IN ('email', 'sms', 'push', 'whatsapp')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE notification_templates IS 'Templates for notification messages';
COMMENT ON COLUMN notification_templates.template_key IS 'Unique identifier for template (e.g., enrollment_confirmation)';
COMMENT ON COLUMN notification_templates.channel IS 'Delivery channel: email, sms, push, or whatsapp';

-- =============================================================================
-- NOTIFICATION_LOGS
-- History of sent notifications
-- =============================================================================
CREATE TABLE notification_logs (
    id BIGSERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES notification_templates(id) ON DELETE SET NULL,
    recipient_type TEXT NOT NULL CHECK (recipient_type IN ('student', 'parent', 'employee', 'admin')),
    recipient_id INTEGER NOT NULL,
    recipient_contact TEXT,
    channel TEXT NOT NULL,
    subject TEXT,
    body TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'delivered')),
    error_message TEXT,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE notification_logs IS 'History of sent notifications';
COMMENT ON COLUMN notification_logs.recipient_type IS 'Type of recipient: student, parent, employee, admin';
COMMENT ON COLUMN notification_logs.recipient_contact IS 'Contact info used (email/phone)';
COMMENT ON COLUMN notification_logs.status IS 'Delivery status: pending, sent, failed, delivered';

-- =============================================================================
-- NOTIFICATION_SUBSCRIBERS
-- Subscribers to notification topics
-- =============================================================================
CREATE TABLE notification_subscribers (
    id SERIAL PRIMARY KEY,
    notification_type TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(notification_type, user_id)
);

COMMENT ON TABLE notification_subscribers IS 'Users subscribed to specific notification types';
COMMENT ON COLUMN notification_subscribers.notification_type IS 'Type of notification to subscribe to';

-- =============================================================================
-- NOTIFICATION_ADDITIONAL_RECIPIENTS
-- Additional recipients for specific notification instances
-- =============================================================================
CREATE TABLE notification_additional_recipients (
    id SERIAL PRIMARY KEY,
    notification_type TEXT NOT NULL,
    reference_type TEXT NOT NULL,
    reference_id INTEGER NOT NULL,
    recipient_type TEXT NOT NULL CHECK (recipient_type IN ('email', 'phone')),
    recipient_value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE notification_additional_recipients IS 'Additional recipients for specific notification instances';
COMMENT ON COLUMN notification_additional_recipients.reference_type IS 'Table name of referenced entity';
COMMENT ON COLUMN notification_additional_recipients.reference_id IS 'ID of referenced entity';

-- =============================================================================
-- ADMIN_NOTIFICATION_SETTINGS
-- Admin-specific notification preferences
-- =============================================================================
CREATE TABLE admin_notification_settings (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type TEXT NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    whatsapp_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(admin_id, notification_type)
);

COMMENT ON TABLE admin_notification_settings IS 'Admin-specific notification preferences';
COMMENT ON COLUMN admin_notification_settings.notification_type IS 'Type of notification setting';
COMMENT ON COLUMN admin_notification_settings.email_enabled IS 'Whether to send email notifications';
COMMENT ON COLUMN admin_notification_settings.whatsapp_enabled IS 'Whether to send WhatsApp notifications';
