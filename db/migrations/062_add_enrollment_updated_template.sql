-- Migration: Add enrollment_updated template for notifications
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active) VALUES
('enrollment_updated', 'EMAIL',
 'Update to {{student_name}}''s enrollment',
 '<html>
<body>
  <h2>Dear {{parent_name}},</h2>
  <p>We are writing to inform you of an update regarding <strong>{{student_name}}</strong>''s enrollment in <strong>{{group_name}}</strong>.</p>
  <p><strong>Changes made:</strong> {{changes_summary}}</p>
  <p><strong>Enrollment ID:</strong> {{enrollment_id}}</p>
  <p>If you have any questions about these changes, please contact us.</p>
  <br>
  <p>Best regards,<br>Techno Kids Team</p>
</body>
</html>',
 ARRAY['parent_name', 'student_name', 'group_name', 'changes_summary', 'enrollment_id'],
 TRUE,
 TRUE);
