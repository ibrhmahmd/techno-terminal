"""AlertNotificationService.notify_user_invited queues the invite email (#148)."""
from datetime import datetime, timezone

from fastapi import BackgroundTasks

from app.modules.notifications.repositories.notification_repository import NotificationRepository
from app.modules.notifications.services.alert_notifications import AlertNotificationService


def test_invite_email_is_queued_to_the_invitee(db_session):
    svc = AlertNotificationService(NotificationRepository(db_session))
    tasks = BackgroundTasks()

    svc.notify_user_invited(
        email="new.person@test.local",
        role="system_admin",
        register_url="https://ui.example.test/register?token=abc",
        expires_at=datetime(2026, 10, 14, 9, 30, tzinfo=timezone.utc),
        employee_id=None,
        background_tasks=tasks,
    )

    assert len(tasks.tasks) == 1
    kwargs = tasks.tasks[0].kwargs
    assert kwargs["template"].name == "user_invite"
    assert kwargs["contact"] == "new.person@test.local"
    assert kwargs["recipient_type"] == "ADDITIONAL"
    assert kwargs["variables"] == {
        "email": "new.person@test.local",
        "role": "System Admin",
        "register_url": "https://ui.example.test/register?token=abc",
        "expires_at": "2026-10-14 09:30 UTC",
    }
