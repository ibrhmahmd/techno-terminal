-- Migration: Add competition notification templates
-- Competition fee payment receipt template (admin-first pattern)

INSERT INTO notification_templates (name, channel, body, subject, variables, is_active, is_standard)
VALUES (
    'competition_fee_payment',
    'EMAIL',
    'Competition Fee Payment Received

Dear Admin,

A competition fee payment has been received.

Student: {{student_name}}
Team: {{team_name}}
Competition: {{competition_name}}
Amount Paid: {{amount}}
Receipt Number: {{receipt_number}}

Please verify the payment details in the system.

Best regards,
Notification System',
    'Competition Fee Payment - {{student_name}}',
    ARRAY['student_name', 'team_name', 'competition_name', 'amount', 'receipt_number'],
    true,
    true
);

-- Competition team registration template
INSERT INTO notification_templates (name, channel, body, subject, variables, is_active, is_standard)
VALUES (
    'competition_team_registration',
    'EMAIL',
    'Competition Team Registration

Dear Admin,

A student has been registered for a competition team.

Student: {{student_name}}
Team: {{team_name}}
Competition: {{competition_name}}
Category: {{category}}

Please review the registration details in the system.

Best regards,
Notification System',
    'Competition Team Registration - {{student_name}}',
    ARRAY['student_name', 'team_name', 'competition_name', 'category'],
    true,
    true
);

-- Competition placement announcement template
INSERT INTO notification_templates (name, channel, body, subject, variables, is_active, is_standard)
VALUES (
    'competition_placement',
    'EMAIL',
    'Competition Placement Announcement

Dear Admin,

Competition results have been announced.

Student: {{student_name}}
Team: {{team_name}}
Competition: {{competition_name}}
Placement: {{rank_display}}

Please check the full results in the system.

Best regards,
Notification System',
    'Competition Results - {{student_name}}',
    ARRAY['student_name', 'team_name', 'competition_name', 'placement_rank', 'placement_label', 'rank_display'],
    true,
    true
);
