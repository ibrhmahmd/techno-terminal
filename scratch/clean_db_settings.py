import asyncio
from app.db.connection import get_session
from app.modules.notifications.repositories.admin_settings_repository import AdminSettingsRepository
from sqlalchemy import text

def clean_db():
    with get_session() as session:
        repo = AdminSettingsRepository(session)
        existing = repo.get_setting(1, 'admin_login_alert')
        if not existing:
            repo.upsert_setting(1, 'admin_login_alert', True, 'EMAIL')
        session.exec(text("DELETE FROM admin_notification_settings WHERE notification_type IN ('enrollment_completed', 'level_progression', 'payment_reminder')"))
        session.commit()
    print("Database settings cleaned up.")

if __name__ == '__main__':
    clean_db()
