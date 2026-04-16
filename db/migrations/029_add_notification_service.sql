-- Migration 029: Add Notification Service Tables
-- Created: 2026-04-16
-- Purpose: Notification templates, logs, and report subscribers for WhatsApp/Email dispatch

-- ── notification_templates ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notification_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    channel VARCHAR(20) NOT NULL,           -- 'WHATSAPP', 'EMAIL'
    subject VARCHAR(255),                   -- Email only; NULL for WhatsApp
    body TEXT NOT NULL,                      -- Body with {{variable}} placeholders
    variables TEXT[] NOT NULL DEFAULT '{}',  -- Expected placeholder names
    is_standard BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Constraints
ALTER TABLE notification_templates
    ADD CONSTRAINT notification_templates_channel_check
    CHECK (channel IN ('WHATSAPP', 'EMAIL'));

-- ── notification_logs ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notification_logs (
    id BIGSERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES notification_templates(id),
    channel VARCHAR(20) NOT NULL,
    recipient_type VARCHAR(20) NOT NULL,    -- 'PARENT', 'EMPLOYEE'
    recipient_id INTEGER NOT NULL,
    recipient_contact VARCHAR(255) NOT NULL, -- Phone or email at send time
    subject VARCHAR(255),
    body TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    error_message TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Constraints
ALTER TABLE notification_logs
    ADD CONSTRAINT notification_logs_channel_check
    CHECK (channel IN ('WHATSAPP', 'EMAIL'));

ALTER TABLE notification_logs
    ADD CONSTRAINT notification_logs_status_check
    CHECK (status IN ('PENDING', 'SENT', 'FAILED'));

ALTER TABLE notification_logs
    ADD CONSTRAINT notification_logs_recipient_type_check
    CHECK (recipient_type IN ('PARENT', 'EMPLOYEE'));

-- Indexes
CREATE INDEX idx_notification_logs_recipient ON notification_logs(recipient_type, recipient_id, created_at DESC);
CREATE INDEX idx_notification_logs_status ON notification_logs(status, created_at DESC);
CREATE INDEX idx_notification_logs_template ON notification_logs(template_id);
CREATE INDEX idx_notification_logs_created_at ON notification_logs(created_at DESC);

-- ── notification_subscribers ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notification_subscribers (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    report_type VARCHAR(20) NOT NULL,       -- 'DAILY', 'WEEKLY', 'MONTHLY', 'ALL'
    channel VARCHAR(20) NOT NULL,           -- 'EMAIL', 'WHATSAPP'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(employee_id, report_type, channel)
);

ALTER TABLE notification_subscribers
    ADD CONSTRAINT notification_subscribers_report_type_check
    CHECK (report_type IN ('DAILY', 'WEEKLY', 'MONTHLY', 'ALL'));

ALTER TABLE notification_subscribers
    ADD CONSTRAINT notification_subscribers_channel_check
    CHECK (channel IN ('EMAIL', 'WHATSAPP'));

-- ── Seed Standard Templates ──────────────────────────────────────────────────

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard) VALUES
(
    'absence_alert',
    'WHATSAPP',
    NULL,
    'مرحباً {{parent_name}} 👋
نود إعلامكم بأن الطالب/ة {{student_name}} لم يحضر حصة {{session_name}} بتاريخ {{session_date}}.
للاستفسار أو الاعتذار يرجى التواصل مع الإدارة.
— Techno Kids',
    ARRAY['parent_name', 'student_name', 'session_name', 'session_date'],
    TRUE
),
(
    'enrollment_confirmation',
    'WHATSAPP',
    NULL,
    'مرحباً {{parent_name}} 👋
تم تسجيل الطالب/ة {{student_name}} بنجاح في مجموعة {{group_name}} ({{course_name}}).
نتمنى لكم تجربة تعليمية ممتعة! 🎓
— Techno Kids',
    ARRAY['parent_name', 'student_name', 'group_name', 'course_name'],
    TRUE
),
(
    'payment_receipt',
    'WHATSAPP',
    NULL,
    'مرحباً {{parent_name}} 👋
تم استلام دفعة بقيمة {{amount}} ج.م للطالب/ة {{student_name}}.
رقم الإيصال: {{receipt_number}}
شكراً لكم! 💰
— Techno Kids',
    ARRAY['parent_name', 'student_name', 'amount', 'receipt_number'],
    TRUE
),
(
    'daily_report',
    'EMAIL',
    'Techno Kids — Daily Report ({{date}})',
    '<h2>📊 Daily Report — {{date}}</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total Revenue</td><td>{{total_revenue}} EGP</td></tr>
<tr><td>New Enrollments</td><td>{{new_enrollments}}</td></tr>
<tr><td>Sessions Held</td><td>{{sessions_held}}</td></tr>
<tr><td>Absent Students</td><td>{{absent_count}}</td></tr>
</table>
<p style="color:#888;">— Techno Terminal Automated Report</p>',
    ARRAY['date', 'total_revenue', 'new_enrollments', 'sessions_held', 'absent_count'],
    TRUE
),
(
    'weekly_report',
    'EMAIL',
    'Techno Kids — Weekly Report ({{week_start}} – {{week_end}})',
    '<h2>📊 Weekly Report</h2>
<p><strong>Period:</strong> {{week_start}} – {{week_end}}</p>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total Revenue</td><td>{{total_revenue}} EGP</td></tr>
<tr><td>New Students</td><td>{{new_students}}</td></tr>
<tr><td>Attendance Rate</td><td>{{attendance_rate}}%</td></tr>
</table>
<p style="color:#888;">— Techno Terminal Automated Report</p>',
    ARRAY['week_start', 'week_end', 'total_revenue', 'new_students', 'attendance_rate'],
    TRUE
),
(
    'monthly_report',
    'EMAIL',
    'Techno Kids — Monthly Report ({{month}})',
    '<h2>📊 Monthly Report — {{month}}</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total Revenue</td><td>{{total_revenue}} EGP</td></tr>
<tr><td>New Enrollments</td><td>{{new_enrollments}}</td></tr>
<tr><td>Active Students</td><td>{{active_students}}</td></tr>
</table>
<p style="color:#888;">— Techno Terminal Automated Report</p>',
    ARRAY['month', 'total_revenue', 'new_enrollments', 'active_students'],
    TRUE
),
(
    'bulk_marketing',
    'WHATSAPP',
    NULL,
    '{{custom_message}}',
    ARRAY['custom_message'],
    TRUE
);
