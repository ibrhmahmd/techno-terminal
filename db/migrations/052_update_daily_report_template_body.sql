-- 052: Update daily_report template body with @media print CSS
-- Ensures the email HTML renders correctly in print preview (Bug 5 fix)

UPDATE notification_templates
SET body = '<html>
<head>
  <style>
    @media print {
      body { font-family: Arial, Helvetica, sans-serif; color: #000; background: #fff; padding: 20px; }
      h2 { color: #000 !important; border-bottom: 2px solid #000; padding-bottom: 8px; }
      table { border-collapse: collapse; width: 100%; border: 1px solid #000; }
      th, td { border: 1px solid #000; padding: 8px; text-align: left; }
      th { background: #333 !important; color: #fff !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      td { color: #000; }
      .footer { margin-top: 16px; color: #000; font-style: italic; }
    }
    @media screen {
      body { font-family: Arial, Helvetica, sans-serif; color: #333; background: #f9f9f9; padding: 20px; }
      h2 { color: #333; border-bottom: 2px solid #333; padding-bottom: 8px; }
      table { border-collapse: collapse; width: 100%; border: 1px solid #ddd; }
      th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
      th { background: #333; color: #fff; }
      td { color: #333; }
      .footer { margin-top: 16px; color: #666; font-style: italic; }
    }
  </style>
</head>
<body>
  <h2>Daily Business Summary &mdash; {{date}}</h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td><strong>Total Revenue</strong></td><td>{{total_revenue}} EGP</td></tr>
    <tr><td><strong>New Enrollments</strong></td><td>{{new_enrollments}}</td></tr>
    <tr><td><strong>Sessions Held</strong></td><td>{{sessions_held}}</td></tr>
    <tr><td><strong>Absent Students</strong></td><td>{{absent_count}}</td></tr>
    <tr><td><strong>Payment Transactions</strong></td><td>{{payment_count}}</td></tr>
    <tr><td><strong>Payment Methods</strong></td><td>{{payment_methods}}</td></tr>
    <tr><td><strong>Attendance Rate</strong></td><td>{{attendance_rate}}</td></tr>
    <tr><td><strong>Unpaid Enrollments</strong></td><td>{{unpaid_count}}</td></tr>
    <tr><td><strong>Instructors Today</strong></td><td>{{instructors_list}}</td></tr>
  </table>
  <br>
  {{payment_details}}
  <p class="footer">This is an automated report from Techno Kids CRM.</p>
</body>
</html>',
    variables = ARRAY['date', 'total_revenue', 'new_enrollments', 'sessions_held', 'absent_count', 'payment_count', 'payment_methods', 'attendance_rate', 'unpaid_count', 'instructors_list', 'payment_details']
WHERE name = 'daily_report';
