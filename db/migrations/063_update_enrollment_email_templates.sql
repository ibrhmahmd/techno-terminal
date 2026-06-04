-- Migration: Update enrollment email templates to follow Precision Engine design system

UPDATE notification_templates 
SET body = '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600;">Welcome to {{group_name}}!</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">We are excited to confirm that <strong>{{student_name}}</strong> has been successfully enrolled.</p>
      
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Group</span> <strong>{{group_name}}</strong> (Level {{level_number}})</p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Instructor</span> <strong>{{instructor_name}}</strong></p>
        <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Enrollment ID</span> <strong>{{enrollment_id}}</strong></p>
      </div>
      
      <p style="line-height: 1.6;">We look forward to an amazing learning journey together!</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>'
WHERE name = 'enrollment_confirmation';

UPDATE notification_templates 
SET body = '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600;">Enrollment Update</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">We are writing to inform you of a financial or administrative update regarding <strong>{{student_name}}</strong>''s enrollment.</p>
      
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600; color: #006a61;">Changes Applied</p>
        <p style="margin: 0 0 12px 0; font-size: 14px; line-height: 1.5;">{{changes_summary}}</p>
        <div style="border-top: 1px solid rgba(198,198,205,0.3); padding-top: 12px;">
            <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Group</span> <strong>{{group_name}}</strong></p>
            <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Enrollment ID</span> <strong>{{enrollment_id}}</strong></p>
        </div>
      </div>
      
      <p style="line-height: 1.6;">If you have any questions about these changes, please contact administration.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>'
WHERE name = 'enrollment_updated';

UPDATE notification_templates 
SET body = '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600; color: #006a61;">Course Completed!</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">Congratulations! <strong>{{student_name}}</strong> has successfully completed their course.</p>
      
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Group</span> <strong>{{group_name}}</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Level Reached</span> <strong>{{level_number}}</strong></p>
        <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Completion Date</span> <strong>{{completion_date}}</strong></p>
      </div>
      
      <p style="line-height: 1.6;">We hope to see {{student_name}} in our next level soon!</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>'
WHERE name = 'enrollment_completed';

UPDATE notification_templates 
SET body = '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600;">Enrollment Dropped</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">We wanted to inform you that <strong>{{student_name}}</strong> has been dropped from their course.</p>
      
      <div style="background-color: #fff1f2; border-left: 4px solid #e11d48; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Group</span> <strong>{{group_name}}</strong></p>
        <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Reason</span> <strong>{{reason}}</strong></p>
      </div>
      
      <p style="line-height: 1.6;">If you have any questions, please don''t hesitate to contact administration.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>'
WHERE name = 'enrollment_dropped';

UPDATE notification_templates 
SET body = '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600;">Enrollment Transferred</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">We are writing to confirm that <strong>{{student_name}}</strong> has been transferred to a new group.</p>
      
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Previous</span> <strong>{{from_group_name}}</strong></p>
        <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">New Group</span> <strong>{{to_group_name}}</strong></p>
      </div>
      
      <p style="line-height: 1.6;">The transfer has been completed successfully.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>'
WHERE name = 'enrollment_transferred';

UPDATE notification_templates 
SET body = '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600; color: #006a61;">Level Progression!</h2>
      <p style="line-height: 1.6;">Dear {{parent_name}},</p>
      <p style="line-height: 1.6;">Great news! <strong>{{student_name}}</strong> has successfully progressed to the next level.</p>
      
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Group</span> <strong>{{group_name}}</strong></p>
        <p style="margin: 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 100px;">Progression</span> Level <strong>{{old_level}}</strong> &rarr; Level <strong>{{new_level}}</strong></p>
      </div>
      
      <p style="line-height: 1.6;">We are proud of {{student_name}}''s achievements and look forward to continued growth!</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>'
WHERE name = 'level_progression';
