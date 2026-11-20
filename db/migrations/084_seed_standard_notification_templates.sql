-- =============================================================================
-- Migration 084: seed the standard notification templates (#231)
--
-- The staging project has none of the standard notification_templates rows, so
-- every email flow that renders one fails there. This inserts each standard
-- template by name when missing, with its final content (db/schema seed plus
-- migrations 052-073, 082, 083 applied in order). Existing rows are never
-- updated or deleted: safe to re-run, and a no-op wherever the rows exist.
-- Apply to staging first. On production it only adds templates production
-- lacks (per #231, the task_* templates from 082, if still missing).
-- =============================================================================

BEGIN;

-- enrollment_confirmation
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'enrollment_confirmation', 'EMAIL', 'New Enrollment: {{student_name}} - {{group_name}}', '<html>
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
</html>', ARRAY['parent_name', 'student_name', 'group_name', 'course_name']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'enrollment_confirmation');

-- absence_alert
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'absence_alert', 'WHATSAPP', 'Absence Notice: {{student_name}} missed {{session_name}}', '<html>
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
</html>', ARRAY['parent_name', 'student_name', 'session_name', 'session_date']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'absence_alert');

-- payment_receipt
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'payment_receipt', 'EMAIL', 'Payment Recorded: {{student_name}} - {{amount}} EGP', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30; margin: 0;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06);">
    <!-- Top White Section -->
    <div style="padding: 40px 32px; background-color: #ffffff;">
      <h1 style="margin: 0 0 8px 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em; color: #0b1c30;">Payment Recorded</h1>
      <p style="margin: 0 0 0 0; color: #64748b; font-size: 14px;">Techno Kids &amp; Techno Future KFS</p>
    </div>

    <!-- Bottom Tonal Split (Details) -->
    <div style="background-color: #eff4ff; padding: 32px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="font-size: 14px;">
        <tr>
          <td style="padding-bottom: 12px; color: #64748b; width: 140px;">Student Name</td>
          <td style="padding-bottom: 12px; font-weight: 600; color: #0b1c30;">{{student_name}}</td>
        </tr>
        <tr>
          <td style="padding-bottom: 12px; color: #64748b;">Course / Group</td>
          <td style="padding-bottom: 12px; font-weight: 600; color: #0b1c30;">{{group_name}}</td>
        </tr>
        <tr>
          <td style="padding-bottom: 12px; color: #64748b;">Amount Paid</td>
          <td style="padding-bottom: 12px; color: #006a61; font-weight: 600; font-size: 16px;">{{amount}} EGP</td>
        </tr>
        <tr>
          <td style="padding-bottom: 12px; color: #64748b;">Remaining Balance</td>
          <td style="padding-bottom: 12px; font-weight: 600; color: #0b1c30;">{{balance_remaining}} EGP</td>
        </tr>
        
        <tr><td colspan="2" style="padding: 8px 0;"><hr style="border: 0; border-top: 1px solid #d1dbec; margin: 0;"></td></tr>
        
        <tr>
          <td style="padding-bottom: 12px; padding-top: 8px; color: #64748b;">Payment Date</td>
          <td style="padding-bottom: 12px; padding-top: 8px; font-weight: 600; color: #0b1c30;">{{payment_date}} {{payment_time}}</td>
        </tr>
        <tr>
          <td style="padding-bottom: 12px; color: #64748b;">Location / Device</td>
          <td style="padding-bottom: 12px; font-weight: 600; color: #0b1c30;">{{location}} ({{device}})</td>
        </tr>
        <tr>
          <td style="padding-bottom: 12px; color: #64748b;">Processed By</td>
          <td style="padding-bottom: 12px; font-weight: 600; color: #0b1c30;">{{processed_by}} <span style="font-size: 12px; color: #64748b; font-weight: normal;">({{processed_role}})</span></td>
        </tr>
        <tr>
          <td style="padding-bottom: 12px; color: #64748b;">Method</td>
          <td style="padding-bottom: 12px; font-weight: 600; color: #0b1c30;">{{payment_method}}</td>
        </tr>
        <tr>
          <td style="padding-bottom: 12px; color: #64748b;">Receipt #</td>
          <td style="padding-bottom: 12px; font-family: monospace; font-weight: 600; color: #0b1c30;">{{receipt_number}}</td>
        </tr>
        <tr>
          <td style="color: #64748b;">Transaction Ref</td>
          <td style="font-family: monospace; font-weight: 600; color: #0b1c30;">{{transaction_ref}}</td>
        </tr>
      </table>
    </div>

    <!-- Footer -->
    <div style="background-color: #f8f9ff; padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY['parent_name', 'student_name', 'amount', 'group_name', 'instructor_name', 'payment_date', 'payment_time', 'payment_method', 'location', 'device', 'processed_by', 'processed_role', 'transaction_ref', 'balance_remaining', 'receipt_number']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'payment_receipt');

-- bulk_marketing
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'bulk_marketing', 'WHATSAPP', 'Message from Techno Kids & Techno Future KFS', '<html>
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
</html>', ARRAY['custom_message']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'bulk_marketing');

-- enrollment_dropped
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'enrollment_dropped', 'EMAIL', 'Enrollment Cancellation: {{student_name}} - {{course_name}}', '<html>
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
        <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Reason</span> <strong>{{reason}}</strong></p>
        <div style="border-top: 1px solid rgba(225,29,72,0.2); padding-top: 8px; margin-top: 8px;">
          <p style="margin: 0; font-size: 12px; color: #be123c;">Processed by <strong>{{admin_name}} ({{admin_email}})</strong> on {{date}} at {{time}}</p>
        </div>
      </div>
      
      <p style="line-height: 1.6;">If this action was taken in error or if you require a refund analysis, please contact the administration desk.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY[]::TEXT[], 'f', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'enrollment_dropped');

-- enrollment_transferred
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'enrollment_transferred', 'EMAIL', 'Group Transfer: {{student_name}} moved to {{to_group_name}}', '<html>
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
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">From Group</span> <strong>{{from_group_name}}</strong></p>
        <p style="margin: 0 0 12px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">To Group</span> <strong>{{to_group_name}}</strong></p>
        <div style="border-top: 1px solid rgba(198,198,205,0.3); padding-top: 12px;">
            <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">New Course</span> <strong>{{course_name}}</strong></p>
            <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Instructor</span> <strong>{{instructor_name}}</strong></p>
        </div>
        <div style="border-top: 1px solid rgba(198,198,205,0.3); padding-top: 8px; margin-top: 8px;">
          <p style="margin: 0; font-size: 12px; color: #64748b;">Processed by <strong>{{admin_name}} ({{admin_email}})</strong> on {{date}} at {{time}}</p>
        </div>
      </div>
      
      <p style="line-height: 1.6;">The previous enrollment record has been marked as transferred. Please ensure the student attends the sessions scheduled for the new group.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY[]::TEXT[], 'f', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'enrollment_transferred');

-- level_progression
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'level_progression', 'EMAIL', 'Level Progression: {{student_name}} advanced to Level {{new_level}}', '<html>
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
        <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Progression</span> Level <strong>{{old_level}}</strong> &rarr; Level <strong>{{new_level}}</strong></p>
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
</html>', ARRAY[]::TEXT[], 'f', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'level_progression');

-- enrollment_updated
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'enrollment_updated', 'EMAIL', 'Update to {{student_name}}''s enrollment', '<html>
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
</html>', ARRAY['parent_name', 'student_name', 'group_name', 'changes_summary', 'enrollment_id']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'enrollment_updated');

-- enrollment_completed
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'enrollment_completed', 'EMAIL', 'Course Completion: {{student_name}} - {{course_name}}', '<html>
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
        <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Completion Date</span> <strong>{{completion_date}}</strong></p>
        <div style="border-top: 1px solid rgba(198,198,205,0.3); padding-top: 8px; margin-top: 8px;">
          <p style="margin: 0; font-size: 12px; color: #64748b;">Processed by <strong>{{admin_name}} ({{admin_email}})</strong> on {{date}} at {{time}}</p>
        </div>
      </div>
      
      <p style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600;">Next Steps:</p>
      <ul style="margin: 0 0 24px 0; padding-left: 20px; font-size: 14px; line-height: 1.6;">
        <li>Consult with the instructor for the recommended next level.</li>
        <li>Register for the upcoming term to secure a slot.</li>
      </ul>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY[]::TEXT[], 'f', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'enrollment_completed');

-- payment_reminder
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'payment_reminder', 'EMAIL', 'Payment Reminder: {{amount_due}} EGP due for {{student_name}}', '<html>
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
</html>', ARRAY[]::TEXT[], 'f', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'payment_reminder');

-- daily_report
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'daily_report', 'EMAIL', 'Daily Business Report: {{date}}', '<html>
<head>
  <style>
    @import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap");
    @media print {
      body { font-family: Arial, Helvetica, sans-serif; color: #000; background: #fff; padding: 20px; }
      h1, h2, h3 { color: #000 !important; font-family: Georgia, serif; }
      table { border-collapse: collapse; width: 100%; border: 1px solid #000; }
      th, td { border: 1px solid #000; padding: 6px; text-align: left; font-size: 10pt; }
      th { background: #333 !important; color: #fff !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      td { color: #000; }
      .kpi-card { border: 1px solid #000; padding: 8px; }
      .status-chip { border: 1px solid #000; padding: 2px 6px; }
      .footer { margin-top: 16px; color: #000; font-style: italic; font-size: 9pt; }
    }
    @media screen {
      body { font-family: Inter, Arial, Helvetica, sans-serif; color: #0b1c30; background: #f8f9ff; margin: 0; padding: 0; }
      h1, h2, h3 { font-family: "Space Grotesk", Arial, Helvetica, sans-serif; font-weight: 600; color: #0b1c30; margin: 0; }
      .header { background: #131b2e; padding: 24px 32px; }
      .header h1 { color: #ffffff; font-size: 22px; letter-spacing: -0.02em; }
      .header p { color: #89f5e7; font-size: 13px; margin: 4px 0 0 0; font-family: Inter, Arial, sans-serif; }
      .section-kpi { background: #eff4ff; padding: 20px 32px; }
      .kpi-grid { display: flex; flex-wrap: wrap; gap: 12px; }
      .kpi-card { background: #ffffff; padding: 14px 20px; flex: 1; min-width: 120px; }
      .kpi-label { font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; font-family: Inter, Arial, sans-serif; margin: 0 0 4px 0; }
      .kpi-value { font-size: 24px; font-weight: 700; font-family: "Space Grotesk", Arial, sans-serif; color: #0b1c30; margin: 0; }
      .kpi-gradient { height: 3px; background: linear-gradient(90deg, #131b2e, #000000); margin: 0 -20px 12px -20px; }
      .section-default { background: #f8f9ff; padding: 20px 32px; }
      .section-white { background: #ffffff; padding: 20px 32px; }
      .section-title { font-size: 15px; margin-bottom: 12px; letter-spacing: -0.01em; }
      .data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
      .data-table td { padding: 8px 10px; vertical-align: top; }
      .row-even { background: #f8f9ff; }
      .row-odd { background: #ffffff; }
      .header-row { background: #131b2e; }
      .header-row td { color: #ffffff; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; padding: 10px; }
      .group-header { background: #e5eeff; font-weight: 600; }
      .group-header td { padding: 8px 10px; font-size: 12px; }
      .total-row { background: #131b2e; }
      .total-row td { color: #ffffff; font-weight: 700; text-align: center; padding: 10px; font-size: 13px; }
      .status-teal { display: inline-block; background: #d1fae5; color: #065f46; font-size: 11px; font-weight: 500; padding: 2px 10px; border-radius: 4px; font-family: Inter, Arial, sans-serif; }
      .status-amber { display: inline-block; background: #fde68a; color: #92400e; font-size: 11px; font-weight: 500; padding: 2px 10px; border-radius: 4px; font-family: Inter, Arial, sans-serif; }
      .alert-card { background: #fff7ed; padding: 14px 18px; margin-bottom: 12px; }
      .alert-card strong { color: #9a3412; }
      .empty-state { color: #9ca3af; font-style: italic; font-size: 13px; padding: 16px; text-align: center; background: #ffffff; }
      .footer { padding: 20px 32px; text-align: center; color: #9ca3af; font-size: 11px; font-family: Inter, Arial, sans-serif; }
      .footer strong { color: #6b7280; }
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>Daily Operations Report</h1>
    <p>&mdash; {{date}} &mdash;</p>
  </div>
  <div class="section-kpi">
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-gradient"></div>
        <p class="kpi-label">Total Revenue</p>
        <p class="kpi-value">{{total_revenue}}</p>
      </div>
      <div class="kpi-card">
        <div class="kpi-gradient"></div>
        <p class="kpi-label">New Enrollments</p>
        <p class="kpi-value">{{new_enrollments}}</p>
      </div>
      <div class="kpi-card">
        <div class="kpi-gradient"></div>
        <p class="kpi-label">Sessions</p>
        <p class="kpi-value">{{sessions_held}}</p>
      </div>
    </div>
  </div>
  {{debtors_section}}
  {{tomorrow_preview_section}}
  {{payment_details}}
  {{session_details}}
  {{instructor_summary}}
  <div class="footer">
    <p><strong>Techno Kids CRM</strong> &mdash; Automated Daily Report</p>
    <p style="margin-top: 4px;">This is an automated report generated by the Techno Terminal system.</p>
  </div>
</body>
</html>', ARRAY['date', 'total_revenue', 'new_enrollments', 'sessions_held', 'payment_details', 'session_details', 'instructor_summary', 'debtors_section', 'tomorrow_preview_section']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'daily_report');

-- weekly_report
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'weekly_report', 'EMAIL', 'Weekly Business Report: {{week_start}} to {{week_end}}', '<html>
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
</html>', ARRAY['week_start', 'week_end', 'total_revenue', 'new_students', 'attendance_rate']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'weekly_report');

-- monthly_report
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'monthly_report', 'EMAIL', 'Monthly Business Report: {{month}}', '<html>
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
</html>', ARRAY['month', 'total_revenue', 'new_enrollments', 'active_students']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'monthly_report');

-- admin_login_alert
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'admin_login_alert', 'EMAIL', 'Security Alert: New Login ({{username}})', '<html>
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
</html>', ARRAY[]::TEXT[], 'f', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'admin_login_alert');

-- task_assigned
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'task_assigned', 'EMAIL', 'New Task Assigned: {{task_title}}', '<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 0;">
  <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 32px 40px;">
      <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 700;">New Task Assigned</h1>
      <p style="margin: 8px 0 0; color: rgba(255,255,255,0.85); font-size: 14px;">Techno Kids — Task Management</p>
    </div>
    <div style="padding: 32px 40px;">
      <p style="color: #374151; font-size: 15px; margin: 0 0 16px;">Hi <strong>{{employee_name}}</strong>,</p>
      <p style="color: #374151; font-size: 15px; margin: 0 0 24px;">A new task has been assigned to you:</p>

      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 20px; margin-bottom: 24px;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; width: 130px; vertical-align: top;">Task</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px; font-weight: 600;">{{task_title}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; vertical-align: top;">Priority</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{task_priority}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; vertical-align: top;">Due Date</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{due_date}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; vertical-align: top;">Assigned by</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{assigned_by_name}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; vertical-align: top;">Description</td>
            <td style="padding: 8px 0; color: #374151; font-size: 14px; line-height: 1.5;">{{task_description}}</td>
          </tr>
        </table>
      </div>

      <p style="color: #6b7280; font-size: 13px; margin: 0;">Please log in to the Techno Kids portal to manage this task.</p>
    </div>
    <div style="background: #f8f9ff; border-top: 1px solid #e5e7eb; padding: 20px 40px; text-align: center;">
      <p style="color: #9ca3af; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>', ARRAY['employee_name', 'task_title', 'task_priority', 'due_date', 'assigned_by_name', 'task_description']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'task_assigned');

-- task_status_changed
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'task_status_changed', 'EMAIL', 'Task Update: {{task_title}} → {{new_status}}', '<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 0;">
  <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    <div style="background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%); padding: 32px 40px;">
      <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 700;">Task Status Updated</h1>
      <p style="margin: 8px 0 0; color: rgba(255,255,255,0.85); font-size: 14px;">Techno Kids — Task Management</p>
    </div>
    <div style="padding: 32px 40px;">
      <p style="color: #374151; font-size: 15px; margin: 0 0 24px;">The status of a task has changed:</p>

      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 20px; margin-bottom: 24px;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; width: 130px;">Task</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px; font-weight: 600;">{{task_title}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">Assigned to</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{employee_name}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">Previous Status</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{old_status}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">New Status</td>
            <td style="padding: 8px 0; color: #0ea5e9; font-size: 14px; font-weight: 600;">{{new_status}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">Changed by</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{changed_by_name}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">Date</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{changed_at}}</td>
          </tr>
        </table>
      </div>
    </div>
    <div style="background: #f8f9ff; border-top: 1px solid #e5e7eb; padding: 20px 40px; text-align: center;">
      <p style="color: #9ca3af; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>', ARRAY['task_title', 'employee_name', 'old_status', 'new_status', 'changed_by_name', 'changed_at']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'task_status_changed');

-- task_comment_added
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'task_comment_added', 'EMAIL', 'New Comment on Task: {{task_title}}', '<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 0;">
  <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    <div style="background: linear-gradient(135deg, #10b981 0%, #0ea5e9 100%); padding: 32px 40px;">
      <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 700;">New Comment on Your Task</h1>
      <p style="margin: 8px 0 0; color: rgba(255,255,255,0.85); font-size: 14px;">Techno Kids — Task Management</p>
    </div>
    <div style="padding: 32px 40px;">
      <p style="color: #374151; font-size: 15px; margin: 0 0 8px;"><strong>{{author_name}}</strong> commented on <strong>{{task_title}}</strong>:</p>

      <div style="background: #f0fdf4; border-left: 4px solid #10b981; border-radius: 4px; padding: 16px 20px; margin: 20px 0;">
        <p style="color: #374151; font-size: 14px; line-height: 1.6; margin: 0;">{{comment_content}}</p>
      </div>

      <p style="color: #6b7280; font-size: 13px; margin: 0;">Commented on {{commented_at}}</p>
    </div>
    <div style="background: #f8f9ff; border-top: 1px solid #e5e7eb; padding: 20px 40px; text-align: center;">
      <p style="color: #9ca3af; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>', ARRAY['task_title', 'author_name', 'comment_content', 'commented_at', 'employee_name']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'task_comment_added');

-- user_invite
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'user_invite', 'EMAIL', 'You are invited to Techno Terminal', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px;">Techno Kids &amp; Techno Future KFS</h1>
      <p style="color: #9ca3af; margin: 8px 0 0 0; font-size: 14px;">Account Invitation</p>
    </div>
    <div style="padding: 32px;">
      <p style="margin-top: 0; font-size: 16px; line-height: 1.5;">You have been invited to Techno Terminal as <strong>{{role}}</strong>.</p>
      <p style="font-size: 14px; line-height: 1.6;">Choose a username and password to activate your account:</p>
      <p style="text-align: center; margin: 28px 0;">
        <a href="{{register_url}}" style="background-color: #006a61; color: #ffffff; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600;">Create my account</a>
      </p>
      <p style="font-size: 13px; color: #64748b; line-height: 1.5;">If the button does not work, open this link: <br><span style="word-break: break-all;">{{register_url}}</span></p>
      <p style="font-size: 13px; color: #64748b; margin-bottom: 0;">The invitation expires on <strong>{{expires_at}}</strong>. If you did not expect it, ignore this email.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY['email', 'role', 'register_url', 'expires_at']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'user_invite');

-- competition_fee_payment
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'competition_fee_payment', 'EMAIL', 'Competition Fee Payment - {{student_name}}', 'Competition Fee Payment Received

Dear Admin,

A competition fee payment has been received.

Student: {{student_name}}
Team: {{team_name}}
Competition: {{competition_name}}
Amount Paid: {{amount}}
Receipt Number: {{receipt_number}}

Please verify the payment details in the system.

Best regards,
Notification System', ARRAY['student_name', 'team_name', 'competition_name', 'amount', 'receipt_number']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'competition_fee_payment');

-- competition_team_registration
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'competition_team_registration', 'EMAIL', 'Competition Team Registration - {{student_name}}', 'Competition Team Registration

Dear Admin,

A student has been registered for a competition team.

Student: {{student_name}}
Team: {{team_name}}
Competition: {{competition_name}}
Category: {{category}}

Please review the registration details in the system.

Best regards,
Notification System', ARRAY['student_name', 'team_name', 'competition_name', 'category']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'competition_team_registration');

-- competition_placement
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
SELECT 'competition_placement', 'EMAIL', 'Competition Results - {{student_name}}', 'Competition Placement Announcement

Dear Admin,

Competition results have been announced.

Student: {{student_name}}
Team: {{team_name}}
Competition: {{competition_name}}
Placement: {{rank_display}}

Please check the full results in the system.

Best regards,
Notification System', ARRAY['student_name', 'team_name', 'competition_name', 'placement_rank', 'placement_label', 'rank_display']::TEXT[], 't', 't'
WHERE NOT EXISTS (SELECT 1 FROM notification_templates WHERE name = 'competition_placement');

COMMIT;
