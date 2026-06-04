-- Enable all enrollment-related notifications for admin 1 (EMAIL channel)

-- Update existing ones
UPDATE admin_notification_settings
SET is_enabled = true, updated_at = NOW()
WHERE admin_id = 1 AND channel = 'EMAIL' AND notification_type IN (
    'enrollment_created', 'enrollment_updated', 'enrollment_dropped',
    'enrollment_transferred', 'enrollment_completed', 'level_progression'
);

-- Insert missing ones (using a simple NOT EXISTS check)
INSERT INTO admin_notification_settings (admin_id, notification_type, channel, is_enabled, created_at, updated_at)
SELECT 1, t.type, 'EMAIL', true, NOW(), NOW()
FROM (VALUES 
    ('enrollment_created'),
    ('enrollment_updated'),
    ('enrollment_dropped'),
    ('enrollment_transferred'),
    ('enrollment_completed'),
    ('level_progression')
) AS t(type)
WHERE NOT EXISTS (
    SELECT 1 FROM admin_notification_settings
    WHERE admin_id = 1 AND channel = 'EMAIL' AND notification_type = t.type
);
