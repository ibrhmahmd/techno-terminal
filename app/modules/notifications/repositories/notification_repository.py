"""
app/modules/notifications/repositories/notification_repository.py
────────────────────────────────────────────────────────────────
Pure data-access layer for the notification domain.

Follows the established repository pattern:
  - Session injected from Unit-of-Work / service layer
  - No business logic
  - ORM in, ORM out
"""
from datetime import datetime
from typing import Optional, List

from sqlmodel import Session, select, col

from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.notifications.models.notification_log import NotificationLog
from app.modules.notifications.models.notification_subscriber import NotificationSubscriber


class NotificationRepository:
    """Concrete implementation of INotificationRepository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Templates ────────────────────────────────────────────────────────────

    def get_template_by_name(self, name: str) -> Optional[NotificationTemplate]:
        stmt = select(NotificationTemplate).where(NotificationTemplate.name == name)
        return self._session.exec(stmt).first()

    def get_template_by_id(self, template_id: int) -> Optional[NotificationTemplate]:
        return self._session.get(NotificationTemplate, template_id)

    def get_all_templates(self) -> List[NotificationTemplate]:
        stmt = select(NotificationTemplate).order_by(NotificationTemplate.name)
        return list(self._session.exec(stmt).all())

    def create_template(
        self,
        name: str,
        channel: str,
        body: str,
        variables: List[str],
        subject: Optional[str] = None,
        is_standard: bool = False,
    ) -> NotificationTemplate:
        template = NotificationTemplate(
            name=name,
            channel=channel,
            body=body,
            variables=variables,
            subject=subject,
            is_standard=is_standard,
            created_at=datetime.utcnow(),
        )
        self._session.add(template)
        self._session.flush()
        self._session.refresh(template)
        return template

    def update_template(
        self, template_id: int, **kwargs
    ) -> Optional[NotificationTemplate]:
        template = self._session.get(NotificationTemplate, template_id)
        if not template:
            return None
        for key, val in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, val)
        template.updated_at = datetime.utcnow()
        self._session.add(template)
        self._session.flush()
        self._session.refresh(template)
        return template

    def delete_template(self, template_id: int) -> bool:
        template = self._session.get(NotificationTemplate, template_id)
        if not template:
            return False
        self._session.delete(template)
        self._session.flush()
        return True

    # ── Logs ─────────────────────────────────────────────────────────────────

    def create_log(
        self,
        template_id: Optional[int],
        channel: str,
        recipient_type: str,
        recipient_id: int,
        recipient_contact: str,
        body: str,
        subject: Optional[str] = None,
    ) -> NotificationLog:
        log = NotificationLog(
            template_id=template_id,
            channel=channel,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            recipient_contact=recipient_contact,
            body=body,
            subject=subject,
            status="PENDING",
            created_at=datetime.utcnow(),
        )
        self._session.add(log)
        self._session.flush()
        self._session.refresh(log)
        return log

    def update_log_status(
        self,
        log_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        log = self._session.get(NotificationLog, log_id)
        if log:
            log.status = status
            log.error_message = error_message
            if status == "SENT":
                log.sent_at = datetime.utcnow()
            self._session.add(log)
            self._session.flush()

    def get_logs(
        self,
        recipient_type: Optional[str] = None,
        recipient_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[NotificationLog]:
        stmt = select(NotificationLog)
        if recipient_type:
            stmt = stmt.where(NotificationLog.recipient_type == recipient_type)
        if recipient_id is not None:
            stmt = stmt.where(NotificationLog.recipient_id == recipient_id)
        stmt = stmt.order_by(col(NotificationLog.created_at).desc())
        stmt = stmt.offset(offset).limit(limit)
        return list(self._session.exec(stmt).all())

    def count_logs(
        self,
        recipient_type: Optional[str] = None,
        recipient_id: Optional[int] = None,
    ) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(NotificationLog)
        if recipient_type:
            stmt = stmt.where(NotificationLog.recipient_type == recipient_type)
        if recipient_id is not None:
            stmt = stmt.where(NotificationLog.recipient_id == recipient_id)
        return self._session.exec(stmt).one()

    # ── Subscribers ──────────────────────────────────────────────────────────

    def get_report_subscribers(
        self, report_type: str
    ) -> List[NotificationSubscriber]:
        stmt = select(NotificationSubscriber).where(
            NotificationSubscriber.is_active == True,
            (NotificationSubscriber.report_type == report_type)
            | (NotificationSubscriber.report_type == "ALL"),
        )
        return list(self._session.exec(stmt).all())

    def add_subscriber(
        self, employee_id: int, report_type: str, channel: str
    ) -> NotificationSubscriber:
        sub = NotificationSubscriber(
            employee_id=employee_id,
            report_type=report_type,
            channel=channel,
            is_active=True,
        )
        self._session.add(sub)
        self._session.flush()
        self._session.refresh(sub)
        return sub

    def remove_subscriber(self, subscriber_id: int) -> bool:
        sub = self._session.get(NotificationSubscriber, subscriber_id)
        if not sub:
            return False
        self._session.delete(sub)
        self._session.flush()
        return True

    def get_all_subscribers(self) -> List[NotificationSubscriber]:
        stmt = select(NotificationSubscriber).where(
            NotificationSubscriber.is_active == True
        ).order_by(NotificationSubscriber.employee_id)
        return list(self._session.exec(stmt).all())
