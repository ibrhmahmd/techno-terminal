-- =============================================================================
-- SEED DATA
-- Initial data for system operation
-- Only runs on fresh database setup
-- =============================================================================

-- =============================================================================
-- EMPLOYEES
-- Create a default admin employee for initial setup
-- =============================================================================
INSERT INTO employees (
    full_name,
    phone,
    national_id,
    university,
    major,
    is_graduate,
    job_title,
    employment_type,
    contract_percentage,
    created_at
)
VALUES (
    'Admin',
    '0000000000',
    '00000000000000',
    'Unassigned',
    'Unassigned',
    FALSE,
    'admin',
    'part_time',
    NULL,
    NOW()
)
ON CONFLICT (national_id) DO NOTHING;

-- =============================================================================
-- NOTIFICATION TEMPLATES
-- Default templates for common notifications
-- =============================================================================
INSERT INTO notification_templates (template_key, name, description, channel, subject_template, body_template, is_active, is_default)
VALUES
    ('enrollment_confirmation', 'Enrollment Confirmation', 'Sent when a student is enrolled in a group', 'email', 
     'Enrollment Confirmation - {{student_name}}',
     'Dear {{parent_name}},\n\n{{student_name}} has been successfully enrolled in {{group_name}}.\n\nBest regards,\nTechno Terminal Team',
     TRUE, TRUE),
    
    ('payment_received', 'Payment Received', 'Sent when a payment is recorded', 'email',
     'Payment Received - Receipt #{{receipt_number}}',
     'Dear {{parent_name}},\n\nWe have received payment of {{amount}} for {{student_name}}.\nReceipt Number: {{receipt_number}}\n\nThank you,\nTechno Terminal Team',
     TRUE, FALSE),
    
    ('attendance_reminder', 'Attendance Reminder', 'Reminder for upcoming session', 'sms',
     NULL,
     'Reminder: {{student_name}} has a session on {{session_date}} at {{session_time}}. Techno Terminal',
     TRUE, FALSE),
    
    ('session_cancellation', 'Session Cancelled', 'Notification of cancelled session', 'email',
     'Session Cancelled - {{group_name}}',
     'Dear {{parent_name}},\n\nThe session for {{group_name}} scheduled on {{session_date}} has been cancelled.\n\nBest regards,\nTechno Terminal Team',
     TRUE, FALSE)

ON CONFLICT (template_key) DO NOTHING;

-- =============================================================================
-- ACADEMIC CATEGORIES
-- Default academic categories
-- =============================================================================
INSERT INTO academic_categories (name, description, display_order, is_active)
VALUES
    ('Software', 'Software development and programming courses', 1, TRUE),
    ('Hardware', 'Electronics and hardware engineering courses', 2, TRUE),
    ('STEAM', 'Science, Technology, Engineering, Arts, and Mathematics', 3, TRUE),
    ('Other', 'Miscellaneous courses and activities', 4, TRUE)
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- RECEIPT TEMPLATES
-- Default receipt template
-- =============================================================================
INSERT INTO receipt_templates (template_name, template_content, is_active, is_default)
VALUES (
    'default',
    'TECHNO TERMINAL\n================\nReceipt #: {{receipt_number}}\nDate: {{date}}\n\nReceived From: {{payer_name}}\nAmount: {{amount}}\nPayment Method: {{payment_method}}\n\nThank you for your payment!',
    TRUE,
    TRUE
)
ON CONFLICT (template_name) DO NOTHING;

-- =============================================================================
-- NOTES
-- =============================================================================
-- 
-- Additional seed data that requires application context:
-- - Users must be created via Supabase Auth first, then linked
-- - Courses should be added through admin interface
-- - Groups should be configured per academic schedule
--
-- The admin employee record above is created to allow initial system access.
-- Actual user authentication requires Supabase Auth setup.
--
