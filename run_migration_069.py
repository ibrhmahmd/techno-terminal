"""
Migration 069: Insert admin_login_alert template
Run with: .venv/Scripts/python.exe run_migration_069.py
"""
import sys
sys.path.insert(0, '.')
from app.db.connection import get_engine
from sqlalchemy import text

TEMPLATE = {
    "name": "admin_login_alert",
    "channel": "EMAIL",
    "subject": "Security Alert: New Login ({{username}})",
    "body": """<html>
<body style="background-color: #f8f9ff; font-family: 'Inter', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 24px;">Techno Kids &amp; Techno Future KFS</h1>
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
</html>"""
}

engine = get_engine()
with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO notification_templates (name, channel, subject, body, updated_at)
        VALUES (:name, :channel, :subject, :body, CURRENT_TIMESTAMP)
        ON CONFLICT (name) DO UPDATE 
        SET subject = EXCLUDED.subject, body = EXCLUDED.body, updated_at = CURRENT_TIMESTAMP
    """), TEMPLATE)

print("Migration 069 applied successfully.")
