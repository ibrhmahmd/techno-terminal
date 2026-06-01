-- 058: Update daily_report template to Precision Engine design system
-- Space Grotesk headlines, Inter body, tonal layering, teal/deep slate palette,
-- Power Gradient KPIs, status chips. New sections: debtors + tomorrow preview.

UPDATE notification_templates
SET body = '<html>
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
      <div class="kpi-card">
        <div class="kpi-gradient"></div>
        <p class="kpi-label">Attendance</p>
        <p class="kpi-value">{{attendance_rate}}</p>
      </div>
      <div class="kpi-card">
        <div class="kpi-gradient"></div>
        <p class="kpi-label">Outstanding Debt</p>
        <p class="kpi-value">{{total_outstanding_debt}}</p>
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
</html>',
    variables = ARRAY['date', 'total_revenue', 'new_enrollments', 'sessions_held', 'absent_count', 'payment_count', 'payment_methods', 'attendance_rate', 'instructors_list', 'payment_details', 'session_details', 'instructor_summary', 'total_outstanding_debt', 'debtor_count', 'debtors_section', 'tomorrow_preview_section']
WHERE name = 'daily_report';
