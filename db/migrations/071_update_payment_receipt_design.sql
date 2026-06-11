-- db/migrations/071_update_payment_receipt_design.sql
-- Update payment receipt email template to align with Precision Engine design system

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
