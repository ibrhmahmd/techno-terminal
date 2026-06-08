-- =============================================================================
-- NOTIFICATIONS TABLES (SYNCED FROM LIVE DB)
-- =============================================================================

DROP TABLE IF EXISTS admin_notification_settings CASCADE;
DROP TABLE IF EXISTS notification_additional_recipients CASCADE;
DROP TABLE IF EXISTS notification_logs CASCADE;
DROP TABLE IF EXISTS notification_templates CASCADE;

CREATE TABLE notification_templates (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    channel TEXT NOT NULL,
    subject TEXT,
    body TEXT NOT NULL,
    variables TEXT[] NOT NULL DEFAULT '{}'::text[],
    is_standard BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT notification_templates_channel_check CHECK ((channel = ANY (ARRAY['WHATSAPP'::text, 'EMAIL'::text]))),
    CONSTRAINT notification_templates_name_key UNIQUE (name)
);

CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    template_id INTEGER,
    channel TEXT NOT NULL,
    recipient_type TEXT NOT NULL,
    recipient_id INTEGER NOT NULL,
    recipient_contact TEXT NOT NULL,
    subject TEXT,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING'::text,
    error_message TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP,
    CONSTRAINT notification_logs_channel_check CHECK ((channel = ANY (ARRAY['WHATSAPP'::text, 'EMAIL'::text]))),
    CONSTRAINT notification_logs_recipient_type_check CHECK ((recipient_type = ANY (ARRAY['PARENT'::text, 'EMPLOYEE'::text, 'ADDITIONAL'::text]))),
    CONSTRAINT notification_logs_status_check CHECK ((status = ANY (ARRAY['PENDING'::text, 'SENT'::text, 'FAILED'::text]))),
    CONSTRAINT notification_logs_template_id_fkey FOREIGN KEY (template_id) REFERENCES notification_templates(id) ON DELETE SET NULL
);

CREATE TABLE notification_additional_recipients (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER,
    email VARCHAR(255) NOT NULL,
    notification_types VARCHAR[],
    label VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT notification_additional_recipients_admin_id_email_key UNIQUE (admin_id, email),
    CONSTRAINT notification_additional_recipients_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE admin_notification_settings (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER,
    notification_type VARCHAR(50) NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    channel VARCHAR(20) DEFAULT 'EMAIL'::character varying,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT admin_notification_settings_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT admin_notification_settings_admin_id_notification_type_key UNIQUE (admin_id, notification_type)
);
