"""Notifications HTTP-layer service factories (ADR-0002: api/ → services/)."""

from typing import Generator

from app.db.connection import get_session
from app.modules.notifications.repositories.notification_repository import NotificationRepository
from app.modules.notifications.services.notification_service import NotificationService


def get_notification_service() -> Generator[NotificationService, None, None]:
    with get_session() as session:
        yield NotificationService(NotificationRepository(session))
        session.commit()
