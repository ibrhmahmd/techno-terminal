-- Migration 067: Fix notification templates â€” add missing, fix subjects, fix variable mismatches
-- Techno Kids & Techno Future KFS

-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
-- 1. FIX: Add subject lines to absence_alert and bulk_marketing
-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

UPDATE notification_templates
SET subject = 'Absence Notice: {{student_name}} missed {{session_name}}'
WHERE name = 'absence_alert';

UPDATE notification_templates
SET subject = 'Message from Techno Kids & Techno Future KFS'
WHERE name = 'bulk_marketing';

-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
-- 2. FIX: bulk_marketing body uses {{custom_message}} â€” ensure it renders
-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

UPDATE notification_templates
SET body = '<html>
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
</html>'
WHERE name = 'bulk_marketing';

-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
-- 3. FIX: Update absence_alert body â€” add branding
-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

UPDATE notification_templates
SET body = '<html>
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
</html>'
WHERE name = 'absence_alert';

-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
-- 4. INSERT: enrollment_completed (MISSING)
-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

INSERT INTO notification_templates (name, subject, body, is_active, created_at)
VALUES (
  'enrollment_completed',
  'Course Completion: {{student_name}} - {{course_name}}',
  '<html>
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
</html>',
  true,
  NOW()
)
ON CONFLICT (name) DO UPDATE SET
  subject = EXCLUDED.subject,
  body = EXCLUDED.body,
  is_active = EXCLUDED.is_active;

-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
-- 5. INSERT: enrollment_dropped (MISSING)
-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

INSERT INTO notification_templates (name, subject, body, is_active, created_at)
VALUES (
  'enrollment_dropped',
  'Enrollment Cancellation: {{student_name}} - {{course_name}}',
  '<html>
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
</html>',
  true,
  NOW()
)
ON CONFLICT (name) DO UPDATE SET
  subject = EXCLUDED.subject,
  body = EXCLUDED.body,
  is_active = EXCLUDED.is_active;

-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
-- 6. INSERT: enrollment_transferred (MISSING)
-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

INSERT INTO notification_templates (name, subject, body, is_active, created_at)
VALUES (
  'enrollment_transferred',
  'Group Transfer: {{student_name}} moved to {{to_group_name}}',
  '<html>
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
</html>',
  true,
  NOW()
)
ON CONFLICT (name) DO UPDATE SET
  subject = EXCLUDED.subject,
  body = EXCLUDED.body,
  is_active = EXCLUDED.is_active;

-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
-- 7. INSERT: level_progression (MISSING)
-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

INSERT INTO notification_templates (name, subject, body, is_active, created_at)
VALUES (
  'level_progression',
  'Level Progression: {{student_name}} advanced to Level {{new_level}}',
  '<html>
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
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Progression</span> Level <strong>{{old_level}}</strong> &#8594; Level <strong>{{new_level}}</strong></p>
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
</html>',
  true,
  NOW()
)
ON CONFLICT (name) DO UPDATE SET
  subject = EXCLUDED.subject,
  body = EXCLUDED.body,
  is_active = EXCLUDED.is_active;

-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
-- 8. INSERT: payment_reminder (MISSING)
-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

INSERT INTO notification_templates (name, subject, body, is_active, created_at)
VALUES (
  'payment_reminder',
  'Payment Reminder: {{amount_due}} EGP due for {{student_name}}',
  '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600; color: #b45309;">Payment Reminder</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">This is a friendly reminder that a payment is due for <strong>{{student_name}}</strong>''s enrollment.</p>
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
</html>',
  true,
  NOW()
)
ON CONFLICT (name) DO UPDATE SET
  subject = EXCLUDED.subject,
  body = EXCLUDED.body,
  is_active = EXCLUDED.is_active;

