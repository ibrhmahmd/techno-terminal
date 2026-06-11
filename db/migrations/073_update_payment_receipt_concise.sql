-- db/migrations/073_update_payment_receipt_concise.sql
-- Update payment receipt email template for directness and enriched data

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('payment_receipt', 'EMAIL', 'Payment Recorded: {{student_name}} - {{amount}} EGP', '<html>
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
</html>', ARRAY['parent_name', 'student_name', 'amount', 'group_name', 'instructor_name', 'payment_date', 'payment_time', 'payment_method', 'location', 'device', 'processed_by', 'processed_role', 'transaction_ref', 'balance_remaining', 'receipt_number']::TEXT[], True, True)
ON CONFLICT (name) DO UPDATE SET 
    subject = EXCLUDED.subject,
    body = EXCLUDED.body,
    variables = EXCLUDED.variables;
