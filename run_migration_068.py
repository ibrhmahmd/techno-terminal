"""
Migration 068: Enrich Daily, Weekly, and Monthly Templates
Run with: .venv/Scripts/python.exe run_migration_068.py
"""
import sys
sys.path.insert(0, '.')
from app.db.connection import get_engine
from sqlalchemy import text

UPDATES = [
    {
        "name": "daily_report",
        "subject": "Daily Business Report: {{date}}",
        "body": """<html>
<body style="background-color: #f8f9ff; font-family: 'Inter', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 700px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
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
              <p style="margin: 0; font-size: 24px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; color: #006a61;">{{total_revenue}} <span style="font-size: 14px; font-weight: 500;">EGP</span></p>
            </td>
            <td style="width: 50%; padding: 16px; background: #eff4ff; border-radius: 0 8px 8px 0;">
              <p style="margin: 0 0 4px 0; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Attendance Rate</p>
              <p style="margin: 0; font-size: 24px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; color: #006a61;">{{attendance_rate}}</p>
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
</html>"""
    },
    {
        "name": "weekly_report",
        "subject": "Weekly Business Report: {{week_start}} to {{week_end}}",
        "body": """<html>
<body style="background-color: #f8f9ff; font-family: 'Inter', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 700px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
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
              <p style="margin: 0; font-size: 24px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; color: #006a61;">{{total_revenue}} <span style="font-size: 14px; font-weight: 500;">EGP</span></p>
            </td>
            <td style="width: 50%; padding: 16px; background: #eff4ff; border-radius: 0 8px 8px 0;">
              <p style="margin: 0 0 4px 0; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Attendance Rate</p>
              <p style="margin: 0; font-size: 24px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; color: #006a61;">{{attendance_rate}}%</p>
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
</html>"""
    },
    {
        "name": "monthly_report",
        "subject": "Monthly Business Report: {{month}}",
        "body": """<html>
<body style="background-color: #f8f9ff; font-family: 'Inter', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 700px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
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
              <p style="margin: 0; font-size: 24px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; color: #006a61;">{{total_revenue}} <span style="font-size: 14px; font-weight: 500;">EGP</span></p>
            </td>
            <td style="width: 50%; padding: 16px; background: #eff4ff; border-radius: 0 8px 8px 0;">
              <p style="margin: 0 0 4px 0; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Attendance Rate</p>
              <p style="margin: 0; font-size: 24px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; color: #006a61;">{{attendance_rate}}%</p>
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
</html>"""
    }
]

engine = get_engine()
with engine.begin() as conn:
    for u in UPDATES:
        conn.execute(text("""
            UPDATE notification_templates
            SET subject = :subject, body = :body
            WHERE name = :name
        """), {"name": u["name"], "subject": u["subject"], "body": u["body"]})
        print(f"Updated: {u['name']}")

print("Migration 068 applied successfully.")
