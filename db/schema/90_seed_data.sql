-- =============================================================================
-- SEED DATA (SYNCED FROM LIVE DB)
-- =============================================================================

-- Default Admin Employee
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

-- Default Notification Templates
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('enrollment_confirmation', 'EMAIL', 'New Enrollment: {{student_name}} - {{group_name}}', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600;">Enrollment Confirmation</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">This is an administrative confirmation that <strong>{{student_name}}</strong> has been successfully enrolled.</p>
      
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Course</span> <strong>{{course_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Group</span> <strong>{{group_name}}</strong> (Level {{level_number}})</p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Instructor</span> <strong>{{instructor_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Enrollment ID</span> <strong>{{enrollment_id}}</strong></p>
        <div style="border-top: 1px solid rgba(198,198,205,0.3); padding-top: 8px; margin-top: 8px;">
          <p style="margin: 0; font-size: 12px; color: #64748b;">Processed by <strong>{{admin_name}} ({{admin_email}})</strong> on {{date}} at {{time}}</p>
        </div>
      </div>
      
      <p style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600;">Next Steps:</p>
      <ul style="margin: 0 0 24px 0; padding-left: 20px; font-size: 14px; line-height: 1.6;">
        <li>Review the schedule for the assigned group.</li>
        <li>Ensure any pending balances are settled before the first session.</li>
      </ul>
      <p style="line-height: 1.6;">Thank you for choosing Techno Kids &amp; Techno Future KFS.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY['parent_name', 'student_name', 'group_name', 'course_name']::TEXT[], True, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('absence_alert', 'WHATSAPP', 'Absence Notice: {{student_name}} missed {{session_name}}', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600; color: #b45309;">Absence Recorded</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">This is to inform you that <strong>{{student_name}}</strong> was marked absent for the following session.</p>
      <div style="background-color: #fffbeb; border-left: 4px solid #b45309; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Session</span> <strong>{{session_name}}</strong></p>
        <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Date</span> <strong>{{session_date}}</strong></p>
      </div>
      <p style="line-height: 1.6;">If this absence was unexpected or you have any concerns, please contact the administration desk.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY['parent_name', 'student_name', 'session_name', 'session_date']::TEXT[], True, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('payment_receipt', 'EMAIL', 'Payment Recorded: {{student_name}} - {{amount}} EGP', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600;">Payment Recorded</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">This is an administrative confirmation that a payment has been successfully recorded for <strong>{{student_name}}</strong>.</p>
      
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 12px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Amount</span> <strong style="font-size: 16px; color: #006a61;">{{amount}} EGP</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Group</span> <strong>{{group_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Instructor</span> <strong>{{instructor_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Payment Date</span> <strong>{{payment_date}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Method</span> <strong>{{payment_method}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Receipt #</span> <strong style="font-family: monospace;">{{receipt_number}}</strong></p>
      </div>
      
      <p style="line-height: 1.6; font-size: 14px; font-weight: 600; color: #0b1c30;">Attachment:</p>
      <p style="line-height: 1.6; font-size: 14px;">A detailed PDF receipt is attached to this email for your financial records.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY['parent_name', 'student_name', 'amount', 'group_name', 'instructor_name', 'payment_date', 'payment_method', 'receipt_number']::TEXT[], True, True)
ON CONFLICT (name) DO UPDATE SET 
    subject = EXCLUDED.subject,
    body = EXCLUDED.body,
    variables = EXCLUDED.variables;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('competition_fee_payment', 'EMAIL', 'Competition Fee Payment - {{student_name}}', 'Competition Fee Payment Received

Dear Admin,

A competition fee payment has been received.

Student: {{student_name}}
Team: {{team_name}}
Competition: {{competition_name}}
Amount Paid: {{amount}}
Receipt Number: {{receipt_number}}

Please verify the payment details in the system.

Best regards,
Notification System', ARRAY['student_name', 'team_name', 'competition_name', 'amount', 'receipt_number']::TEXT[], True, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('competition_team_registration', 'EMAIL', 'Competition Team Registration - {{student_name}}', 'Competition Team Registration

Dear Admin,

A student has been registered for a competition team.

Student: {{student_name}}
Team: {{team_name}}
Competition: {{competition_name}}
Category: {{category}}

Please review the registration details in the system.

Best regards,
Notification System', ARRAY['student_name', 'team_name', 'competition_name', 'category']::TEXT[], True, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('competition_placement', 'EMAIL', 'Competition Results - {{student_name}}', 'Competition Placement Announcement

Dear Admin,

Competition results have been announced.

Student: {{student_name}}
Team: {{team_name}}
Competition: {{competition_name}}
Placement: {{rank_display}}

Please check the full results in the system.

Best regards,
Notification System', ARRAY['student_name', 'team_name', 'competition_name', 'placement_rank', 'placement_label', 'rank_display']::TEXT[], True, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('bulk_marketing', 'WHATSAPP', 'Message from Techno Kids & Techno Future KFS', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <div style="font-size: 15px; line-height: 1.8; color: #0b1c30;">
        {{custom_message}}
      </div>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY['custom_message']::TEXT[], True, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('enrollment_dropped', 'EMAIL', 'Enrollment Cancellation: {{student_name}} - {{course_name}}', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600;">Enrollment Cancellation</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">This is an administrative notice that the enrollment for <strong>{{student_name}}</strong> has been dropped.</p>
      <div style="background-color: #fff1f2; border-left: 4px solid #e11d48; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Course</span> <strong>{{course_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Group</span> <strong>{{group_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Instructor</span> <strong>{{instructor_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Reason</span> <strong>{{reason}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Enrollment ID</span> <strong>{{enrollment_id}}</strong></p>
        <div style="border-top: 1px solid rgba(225,29,72,0.2); padding-top: 8px; margin-top: 8px;">
          <p style="margin: 0; font-size: 12px; color: #be123c;">Processed by <strong>{{admin_name}} ({{admin_email}})</strong> on {{date}} at {{time}}</p>
        </div>
      </div>
      <p style="line-height: 1.6;">If this action was taken in error or if you require a refund analysis, please contact the administration desk immediately.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY[]::TEXT[], False, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('enrollment_transferred', 'EMAIL', 'Group Transfer: {{student_name}} moved to {{to_group_name}}', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600;">Enrollment Transfer Executed</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">This confirms the administrative transfer of <strong>{{student_name}}</strong> to a new group assignment.</p>
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 110px;">From Group</span> <strong>{{from_group_name}}</strong></p>
        <p style="margin: 0 0 12px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 110px;">To Group</span> <strong>{{to_group_name}}</strong></p>
        <div style="border-top: 1px solid rgba(198,198,205,0.3); padding-top: 12px;">
          <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 110px;">Course</span> <strong>{{course_name}}</strong></p>
          <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 110px;">Instructor</span> <strong>{{instructor_name}}</strong></p>
          <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 110px;">Old Enrollment</span> <strong>#{{from_enrollment_id}}</strong></p>
          <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 110px;">New Enrollment</span> <strong>#{{to_enrollment_id}}</strong></p>
        </div>
        <div style="border-top: 1px solid rgba(198,198,205,0.3); padding-top: 8px; margin-top: 8px;">
          <p style="margin: 0; font-size: 12px; color: #64748b;">Processed by <strong>{{admin_name}} ({{admin_email}})</strong> on {{date}} at {{time}}</p>
        </div>
      </div>
      <p style="line-height: 1.6;">The previous enrollment record has been marked as transferred. Please ensure the student attends sessions scheduled for the new group.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY[]::TEXT[], False, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('level_progression', 'EMAIL', 'Level Progression: {{student_name}} advanced to Level {{new_level}}', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600; color: #006a61;">Level Progression Registered</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">This is an administrative notification that <strong>{{student_name}}</strong> has progressed within their curriculum track.</p>
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Course</span> <strong>{{course_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Group</span> <strong>{{group_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Instructor</span> <strong>{{instructor_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Progression</span> Level <strong>{{old_level}}</strong> to Level <strong>{{new_level}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Enrollment ID</span> <strong>{{enrollment_id}}</strong></p>
        <div style="border-top: 1px solid rgba(198,198,205,0.3); padding-top: 8px; margin-top: 8px;">
          <p style="margin: 0; font-size: 12px; color: #64748b;">Processed by <strong>{{admin_name}} ({{admin_email}})</strong> on {{date}} at {{time}}</p>
        </div>
      </div>
      <p style="line-height: 1.6;">Academic records have been updated accordingly.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY[]::TEXT[], False, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('enrollment_updated', 'EMAIL', 'Update to {{student_name}}''s enrollment', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600;">Enrollment Update Notice</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">This is an administrative notification regarding updates to the enrollment profile for <strong>{{student_name}}</strong>.</p>
      
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600; color: #006a61;">Modification Log</p>
        <p style="margin: 0 0 12px 0; font-size: 14px; line-height: 1.5; font-family: monospace; background: #e2e8f0; padding: 8px; border-radius: 4px;">{{changes_summary}}</p>
        <div style="border-top: 1px solid rgba(198,198,205,0.3); padding-top: 12px;">
            <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Course</span> <strong>{{course_name}}</strong></p>
            <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Group</span> <strong>{{group_name}}</strong></p>
            <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Instructor</span> <strong>{{instructor_name}}</strong></p>
            <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Enrollment ID</span> <strong>{{enrollment_id}}</strong></p>
        </div>
        <div style="border-top: 1px solid rgba(198,198,205,0.3); padding-top: 8px; margin-top: 8px;">
          <p style="margin: 0; font-size: 12px; color: #64748b;">Processed by <strong>{{admin_name}} ({{admin_email}})</strong> on {{date}} at {{time}}</p>
        </div>
      </div>
      
      <p style="line-height: 1.6;">If these financial or administrative changes are unexpected, please contact the administration desk immediately.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY['parent_name', 'student_name', 'group_name', 'changes_summary', 'enrollment_id']::TEXT[], True, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('enrollment_completed', 'EMAIL', 'Course Completion: {{student_name}} - {{course_name}}', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600; color: #006a61;">Course Completion Certificate</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">This confirms that <strong>{{student_name}}</strong> has successfully completed the curriculum requirements for their course.</p>
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Course</span> <strong>{{course_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Group</span> <strong>{{group_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Instructor</span> <strong>{{instructor_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Level Achieved</span> <strong>{{level_number}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Completion Date</span> <strong>{{completion_date}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Enrollment ID</span> <strong>{{enrollment_id}}</strong></p>
        <div style="border-top: 1px solid rgba(198,198,205,0.3); padding-top: 8px; margin-top: 8px;">
          <p style="margin: 0; font-size: 12px; color: #64748b;">Processed by <strong>{{admin_name}} ({{admin_email}})</strong> on {{date}} at {{time}}</p>
        </div>
      </div>
      <p style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600;">Next Steps:</p>
      <ul style="margin: 0 0 24px 0; padding-left: 20px; font-size: 14px; line-height: 1.6;">
        <li>Consult with the instructor for the recommended next level.</li>
        <li>Register for the upcoming term to secure a slot.</li>
      </ul>
      <p style="line-height: 1.6;">Thank you for choosing Techno Kids &amp; Techno Future KFS.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY[]::TEXT[], False, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('payment_reminder', 'EMAIL', 'Payment Reminder: {{amount_due}} EGP due for {{student_name}}', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600; color: #b45309;">Payment Reminder</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">This is a friendly reminder that a payment is due for <strong>{{student_name}}</strong>.</p>
      <div style="background-color: #fffbeb; border-left: 4px solid #b45309; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Amount Due</span> <strong style="font-size: 18px; color: #b45309;">{{amount_due}} EGP</strong></p>
        <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Due Date</span> <strong>{{due_date}}</strong></p>
      </div>
      <p style="line-height: 1.6;">Please settle this balance at the administration desk or contact us if you have any questions.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY[]::TEXT[], False, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('daily_report', 'EMAIL', 'Daily Business Report: {{date}}', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 700px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
      <p style="color: #9ca3af; margin: 8px 0 0 0; font-size: 14px;">Daily Business Report</p>
    </div>
    <div style="padding: 32px 0;">
      <div style="padding: 0 32px 20px 32px;">
        <h2 style="margin: 0; font-size: 20px; font-weight: 600; color: #0b1c30;">Overview for {{date}}</h2>
      </div>
      
      <!-- Key Metrics -->
      <div style="background: #ffffff; padding: 0 32px 20px 32px;">
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
          <tr>
            <td style="width: 50%; padding: 16px; background: #eff4ff; border-radius: 8px 0 0 8px; border-right: 2px solid #ffffff;">
              <p style="margin: 0 0 4px 0; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Net Revenue</p>
              <p style="margin: 0; font-size: 24px; font-family: ''Space Grotesk'', sans-serif; font-weight: 700; color: #006a61;">{{total_revenue}} <span style="font-size: 14px; font-weight: 500;">EGP</span></p>
            </td>
            <td style="width: 50%; padding: 16px; background: #eff4ff; border-radius: 0 8px 8px 0;">
              <p style="margin: 0 0 4px 0; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Attendance Rate</p>
              <p style="margin: 0; font-size: 24px; font-family: ''Space Grotesk'', sans-serif; font-weight: 700; color: #006a61;">{{attendance_rate}}</p>
            </td>
          </tr>
        </table>
        
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="width: 33.3%; padding: 12px; text-align: center; border-right: 1px solid #e2e8f0;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">New Enrollments</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #0b1c30;">{{new_enrollments}}</p>
            </td>
            <td style="width: 33.3%; padding: 12px; text-align: center; border-right: 1px solid #e2e8f0;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Sessions Held</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #0b1c30;">{{sessions_held}}</p>
            </td>
            <td style="width: 33.3%; padding: 12px; text-align: center;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Payments</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #0b1c30;">{{payment_count}}</p>
            </td>
          </tr>
        </table>
      </div>

      {{debtors_section}}
      {{cumulative_debtors_section}}
      {{payment_details}}
      {{session_details}}
      {{instructor_summary}}
      {{tomorrow_preview_section}}
      
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
      <p style="color: #9ca3af; font-size: 11px; margin: 4px 0 0 0;">System generated report</p>
    </div>
  </div>
</body>
</html>', ARRAY['date', 'total_revenue', 'new_enrollments', 'sessions_held', 'payment_details', 'session_details', 'instructor_summary', 'debtors_section', 'tomorrow_preview_section']::TEXT[], True, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('weekly_report', 'EMAIL', 'Weekly Business Report: {{week_start}} to {{week_end}}', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 700px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
      <p style="color: #9ca3af; margin: 8px 0 0 0; font-size: 14px;">Weekly Business Report</p>
    </div>
    <div style="padding: 32px 0;">
      <div style="padding: 0 32px 20px 32px;">
        <h2 style="margin: 0; font-size: 18px; font-weight: 600; color: #0b1c30;">Week: {{week_start}} to {{week_end}}</h2>
      </div>
      
      <!-- Key Metrics -->
      <div style="background: #ffffff; padding: 0 32px 20px 32px;">
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
          <tr>
            <td style="width: 50%; padding: 16px; background: #eff4ff; border-radius: 8px 0 0 8px; border-right: 2px solid #ffffff;">
              <p style="margin: 0 0 4px 0; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Net Revenue</p>
              <p style="margin: 0; font-size: 24px; font-family: ''Space Grotesk'', sans-serif; font-weight: 700; color: #006a61;">{{total_revenue}} <span style="font-size: 14px; font-weight: 500;">EGP</span></p>
            </td>
            <td style="width: 50%; padding: 16px; background: #eff4ff; border-radius: 0 8px 8px 0;">
              <p style="margin: 0 0 4px 0; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Attendance Rate</p>
              <p style="margin: 0; font-size: 24px; font-family: ''Space Grotesk'', sans-serif; font-weight: 700; color: #006a61;">{{attendance_rate}}%</p>
            </td>
          </tr>
        </table>
        
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="width: 25%; padding: 12px; text-align: center; border-right: 1px solid #e2e8f0;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">New Students</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #0b1c30;">{{new_students}}</p>
            </td>
            <td style="width: 25%; padding: 12px; text-align: center; border-right: 1px solid #e2e8f0;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">New Enrollments</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #0b1c30;">{{new_enrollments}}</p>
            </td>
            <td style="width: 25%; padding: 12px; text-align: center; border-right: 1px solid #e2e8f0;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Total Sessions</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #0b1c30;">{{total_sessions}}</p>
            </td>
            <td style="width: 25%; padding: 12px; text-align: center;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Debtors</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #9a3412;">{{debtor_count}}</p>
            </td>
          </tr>
        </table>
      </div>

      <!-- Financial Insights -->
      <div style="background: #f8f9ff; padding: 20px 32px;">
        <h3 style="margin: 0 0 12px 0; font-size: 15px; font-weight: 600; color: #0b1c30;">Financial Insights</h3>
        
        <div style="margin-bottom: 20px;">
          <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #64748b; font-weight: 600;">Top Performing Groups</h4>
          {{top_groups}}
        </div>
        
        <div style="margin-bottom: 20px;">
          <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #64748b; font-weight: 600;">Revenue by Course</h4>
          {{revenue_by_course}}
        </div>

        <div>
          <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #9a3412; font-weight: 600;">Outstanding Debt</h4>
          <p style="margin: 0; font-size: 14px; font-weight: 600; color: #9a3412;">{{total_debt}} EGP</p>
        </div>
      </div>
      
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY['week_start', 'week_end', 'total_revenue', 'new_students', 'attendance_rate']::TEXT[], True, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('monthly_report', 'EMAIL', 'Monthly Business Report: {{month}}', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 700px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
      <p style="color: #9ca3af; margin: 8px 0 0 0; font-size: 14px;">Monthly Business Report</p>
    </div>
    <div style="padding: 32px 0;">
      <div style="padding: 0 32px 20px 32px;">
        <h2 style="margin: 0; font-size: 20px; font-weight: 600; color: #0b1c30;">Overview for {{month}}</h2>
      </div>
      
      <!-- Key Metrics -->
      <div style="background: #ffffff; padding: 0 32px 20px 32px;">
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
          <tr>
            <td style="width: 50%; padding: 16px; background: #eff4ff; border-radius: 8px 0 0 8px; border-right: 2px solid #ffffff;">
              <p style="margin: 0 0 4px 0; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Net Revenue</p>
              <p style="margin: 0; font-size: 24px; font-family: ''Space Grotesk'', sans-serif; font-weight: 700; color: #006a61;">{{total_revenue}} <span style="font-size: 14px; font-weight: 500;">EGP</span></p>
            </td>
            <td style="width: 50%; padding: 16px; background: #eff4ff; border-radius: 0 8px 8px 0;">
              <p style="margin: 0 0 4px 0; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Attendance Rate</p>
              <p style="margin: 0; font-size: 24px; font-family: ''Space Grotesk'', sans-serif; font-weight: 700; color: #006a61;">{{attendance_rate}}%</p>
            </td>
          </tr>
        </table>
        
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="width: 20%; padding: 12px; text-align: center; border-right: 1px solid #e2e8f0;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">New Students</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #0b1c30;">{{new_students}}</p>
            </td>
            <td style="width: 20%; padding: 12px; text-align: center; border-right: 1px solid #e2e8f0;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">New Enrolls</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #0b1c30;">{{new_enrollments}}</p>
            </td>
            <td style="width: 20%; padding: 12px; text-align: center; border-right: 1px solid #e2e8f0;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Total Enrolls</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #0b1c30;">{{active_students}}</p>
            </td>
            <td style="width: 20%; padding: 12px; text-align: center; border-right: 1px solid #e2e8f0;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Total Sessions</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #0b1c30;">{{total_sessions}}</p>
            </td>
            <td style="width: 20%; padding: 12px; text-align: center;">
              <p style="margin: 0 0 4px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Dropped</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #9a3412;">{{dropped_enrollments}}</p>
            </td>
          </tr>
        </table>
      </div>

      <div style="background: #f8f9ff; padding: 20px 32px;">
        <h3 style="margin: 0 0 12px 0; font-size: 15px; font-weight: 600; color: #0b1c30;">Monthly Analytics</h3>
        
        <div style="margin-bottom: 20px;">
          <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #64748b; font-weight: 600;">Top Courses (by Enrollment)</h4>
          {{top_courses}}
        </div>
        
        <div style="margin-bottom: 20px;">
          <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #64748b; font-weight: 600;">Revenue Breakdown</h4>
          {{revenue_breakdown}}
        </div>

        <div style="margin-bottom: 20px;">
          <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #9a3412; font-weight: 600;">Outstanding Debt at Month End</h4>
          <p style="margin: 0; font-size: 14px; font-weight: 600; color: #9a3412;">{{total_debt}} EGP ({{debtor_count}} accounts)</p>
        </div>
      </div>
      
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY['month', 'total_revenue', 'new_enrollments', 'active_students']::TEXT[], True, True)
ON CONFLICT (name) DO NOTHING;

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('admin_login_alert', 'EMAIL', 'Security Alert: New Login ({{username}})', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px;">Techno Kids &amp; Techno Future KFS</h1>
      <p style="color: #9ca3af; margin: 8px 0 0 0; font-size: 14px;">System Security Alert</p>
    </div>
    <div style="padding: 32px;">
      <p style="margin-top: 0; font-size: 16px; line-height: 1.5;">A new login was detected on the system.</p>
      
      <div style="background: #eff4ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 0 0 12px 0; font-size: 14px;"><strong style="color: #64748b;">User:</strong> <span style="font-weight: 600;">{{username}}</span> ({{email}})</p>
        <p style="margin: 0 0 12px 0; font-size: 14px;"><strong style="color: #64748b;">Role:</strong> {{role}}</p>
        <p style="margin: 0 0 12px 0; font-size: 14px;"><strong style="color: #64748b;">Time:</strong> {{time}}</p>
        <p style="margin: 0 0 12px 0; font-size: 14px;"><strong style="color: #64748b;">IP Address:</strong> {{ip_address}}</p>
        <p style="margin: 0; font-size: 14px;"><strong style="color: #64748b;">Device/Browser:</strong> {{user_agent}}</p>
      </div>

      <p style="font-size: 14px; color: #64748b; margin-bottom: 0;">Reason for alert: <strong>{{alert_reason}}</strong></p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY[]::TEXT[], False, True)
ON CONFLICT (name) DO NOTHING;

