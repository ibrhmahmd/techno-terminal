-- Migration: Add notification templates for enrollment, payment, and reports
-- These are required templates for the refactored notification service

-- Enrollment templates
INSERT INTO notification_templates (code, name, channel, subject, body, variables, is_standard, is_active) VALUES
('enrollment_confirmation', 'Enrollment Confirmation', 'EMAIL', 
 'Welcome to {{group_name}}!',
 '<html>
<body>
  <h2>Dear {{parent_name}},</h2>
  <p>We are excited to confirm that <strong>{{student_name}}</strong> has been successfully enrolled in <strong>{{group_name}}</strong> (Level {{level_number}}).</p>
  <p><strong>Instructor:</strong> {{instructor_name}}</p>
  <p><strong>Enrollment ID:</strong> {{enrollment_id}}</p>
  <p>We look forward to an amazing learning journey together!</p>
  <br>
  <p>Best regards,<br>Techno Kids Team</p>
</body>
</html>',
 ARRAY['parent_name', 'student_name', 'group_name', 'level_number', 'instructor_name', 'enrollment_id'],
 TRUE,
 TRUE);

INSERT INTO notification_templates (code, name, channel, subject, body, variables, is_standard, is_active) VALUES
('enrollment_completed', 'Enrollment Completed', 'EMAIL',
 '{{student_name}} has completed {{group_name}}',
 '<html>
<body>
  <h2>Dear {{parent_name}},</h2>
  <p>Congratulations! <strong>{{student_name}}</strong> has successfully completed their enrollment in <strong>{{group_name}}</strong> (Level {{level_number}}).</p>
  <p><strong>Completion Date:</strong> {{completion_date}}</p>
  <p><strong>Enrollment ID:</strong> {{enrollment_id}}</p>
  <p>We hope to see {{student_name}} in our next level soon!</p>
  <br>
  <p>Best regards,<br>Techno Kids Team</p>
</body>
</html>',
 ARRAY['parent_name', 'student_name', 'group_name', 'level_number', 'completion_date', 'enrollment_id'],
 TRUE,
 TRUE);

INSERT INTO notification_templates (code, name, channel, subject, body, variables, is_standard, is_active) VALUES
('enrollment_dropped', 'Enrollment Dropped', 'EMAIL',
 'Update: {{student_name}} enrollment status',
 '<html>
<body>
  <h2>Dear {{parent_name}},</h2>
  <p>We wanted to inform you that <strong>{{student_name}}</strong> has been dropped from <strong>{{group_name}}</strong>.</p>
  <p><strong>Reason:</strong> {{reason}}</p>
  <p><strong>Enrollment ID:</strong> {{enrollment_id}}</p>
  <p>If you have any questions, please don''t hesitate to contact us.</p>
  <br>
  <p>Best regards,<br>Techno Kids Team</p>
</body>
</html>',
 ARRAY['parent_name', 'student_name', 'group_name', 'reason', 'enrollment_id'],
 TRUE,
 TRUE);

INSERT INTO notification_templates (code, name, channel, subject, body, variables, is_standard, is_active) VALUES
('enrollment_transferred', 'Enrollment Transferred', 'EMAIL',
 '{{student_name}} transferred to new group',
 '<html>
<body>
  <h2>Dear {{parent_name}},</h2>
  <p>We are writing to confirm that <strong>{{student_name}}</strong> has been transferred from <strong>{{from_group_name}}</strong> to <strong>{{to_group_name}}</strong>.</p>
  <p><strong>From Enrollment ID:</strong> {{from_enrollment_id}}</p>
  <p><strong>To Enrollment ID:</strong> {{to_enrollment_id}}</p>
  <p>The transfer has been completed successfully.</p>
  <br>
  <p>Best regards,<br>Techno Kids Team</p>
</body>
</html>',
 ARRAY['parent_name', 'student_name', 'from_group_name', 'to_group_name', 'from_enrollment_id', 'to_enrollment_id'],
 TRUE,
 TRUE);

INSERT INTO notification_templates (code, name, channel, subject, body, variables, is_standard, is_active) VALUES
('level_progression', 'Level Progression', 'EMAIL',
 '{{student_name}} has progressed to Level {{new_level}}',
 '<html>
<body>
  <h2>Dear {{parent_name}},</h2>
  <p>Great news! <strong>{{student_name}}</strong> has successfully progressed from Level {{old_level}} to Level {{new_level}} in <strong>{{group_name}}</strong>.</p>
  <p><strong>Enrollment ID:</strong> {{enrollment_id}}</p>
  <p>We are proud of {{student_name}}''s achievements and look forward to continued growth!</p>
  <br>
  <p>Best regards,<br>Techno Kids Team</p>
</body>
</html>',
 ARRAY['parent_name', 'student_name', 'old_level', 'new_level', 'group_name', 'enrollment_id'],
 TRUE,
 TRUE);

-- Payment templates
INSERT INTO notification_templates (code, name, channel, subject, body, variables, is_standard, is_active) VALUES
('payment_receipt', 'Payment Receipt', 'EMAIL',
 'Payment Received - Receipt #{{receipt_number}}',
 '<html>
<body>
  <h2>Dear {{parent_name}},</h2>
  <p>Thank you for your payment! We have received <strong>{{amount}}</strong> for <strong>{{student_name}}</strong>.</p>
  <p><strong>Receipt Number:</strong> {{receipt_number}}</p>
  <p><strong>Receipt ID:</strong> {{receipt_id}}</p>
  <p>Keep this email as your payment confirmation.</p>
  <br>
  <p>Best regards,<br>Techno Kids Team</p>
</body>
</html>',
 ARRAY['parent_name', 'student_name', 'amount', 'receipt_number', 'receipt_id'],
 TRUE,
 TRUE);

INSERT INTO notification_templates (code, name, channel, subject, body, variables, is_standard, is_active) VALUES
('payment_reminder', 'Payment Reminder', 'EMAIL',
 'Payment Reminder for {{student_name}}',
 '<html>
<body>
  <h2>Dear {{parent_name}},</h2>
  <p>This is a friendly reminder that a payment of <strong>{{amount_due}}</strong> is due for <strong>{{student_name}}</strong>.</p>
  <p><strong>Due Date:</strong> {{due_date}}</p>
  <p>Please make your payment at your earliest convenience to avoid any interruptions.</p>
  <br>
  <p>Best regards,<br>Techno Kids Team</p>
</body>
</html>',
 ARRAY['parent_name', 'student_name', 'amount_due', 'due_date'],
 TRUE,
 TRUE);

-- Report templates (for employee notifications)
INSERT INTO notification_templates (code, name, channel, subject, body, variables, is_standard, is_active) VALUES
('daily_report', 'Daily Business Report', 'EMAIL',
 'Daily Report - {{date}}',
 '<html>
<body>
  <h2>Daily Business Summary - {{date}}</h2>
  <table border="1" cellpadding="8">
    <tr><td><strong>Total Revenue</strong></td><td>{{total_revenue}}</td></tr>
    <tr><td><strong>New Enrollments</strong></td><td>{{new_enrollments}}</td></tr>
    <tr><td><strong>Sessions Held</strong></td><td>{{sessions_held}}</td></tr>
    <tr><td><strong>Absent Students</strong></td><td>{{absent_count}}</td></tr>
  </table>
  <br>
  <p>This is an automated report from Techno Kids CRM.</p>
</body>
</html>',
 ARRAY['date', 'total_revenue', 'new_enrollments', 'sessions_held', 'absent_count'],
 TRUE,
 TRUE);

INSERT INTO notification_templates (code, name, channel, subject, body, variables, is_standard, is_active) VALUES
('weekly_report', 'Weekly Business Report', 'EMAIL',
 'Weekly Report - {{week_start}} to {{week_end}}',
 '<html>
<body>
  <h2>Weekly Business Summary</h2>
  <p><strong>Week:</strong> {{week_start}} to {{week_end}}</p>
  <table border="1" cellpadding="8">
    <tr><td><strong>Total Revenue</strong></td><td>{{total_revenue}}</td></tr>
    <tr><td><strong>New Students</strong></td><td>{{new_students}}</td></tr>
    <tr><td><strong>Attendance Rate</strong></td><td>{{attendance_rate}}%</td></tr>
  </table>
  <br>
  <p>This is an automated report from Techno Kids CRM.</p>
</body>
</html>',
 ARRAY['week_start', 'week_end', 'total_revenue', 'new_students', 'attendance_rate'],
 TRUE,
 TRUE);

INSERT INTO notification_templates (code, name, channel, subject, body, variables, is_standard, is_active) VALUES
('monthly_report', 'Monthly Business Report', 'EMAIL',
 'Monthly Report - {{month}}',
 '<html>
<body>
  <h2>Monthly Business Summary - {{month}}</h2>
  <table border="1" cellpadding="8">
    <tr><td><strong>Total Revenue</strong></td><td>{{total_revenue}}</td></tr>
    <tr><td><strong>New Enrollments</strong></td><td>{{new_enrollments}}</td></tr>
    <tr><td><strong>Active Students</strong></td><td>{{active_students}}</td></tr>
  </table>
  <br>
  <p>This is an automated report from Techno Kids CRM.</p>
</body>
</html>',
 ARRAY['month', 'total_revenue', 'new_enrollments', 'active_students'],
 TRUE,
 TRUE);

-- Legacy templates for backward compatibility
INSERT INTO notification_templates (code, name, channel, subject, body, variables, is_standard, is_active) VALUES
('absence_alert', 'Absence Alert', 'WHATSAPP', NULL,
 'Dear {{parent_name}}, {{student_name}} was absent from {{session_name}} on {{session_date}}. Please ensure regular attendance.',
 ARRAY['parent_name', 'student_name', 'session_name', 'session_date'],
 TRUE,
 TRUE);
