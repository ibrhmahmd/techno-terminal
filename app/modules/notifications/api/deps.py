"""Notifications HTTP-layer service factories (ADR-0002: api/ → services/).

Each request gets one repository over one session; the session is committed after the
endpoint returns (unchanged from the former per-request service). Background processors
spawned by the services open their own ``unit_of_work()`` (the ADR-0001 allowance for
non-HTTP entry points).
"""

from typing import Generator

from fastapi import Depends

from app.db.uow import unit_of_work
from app.modules.notifications.repositories.notification_repository import NotificationRepository
from app.modules.notifications.services.alert_notifications import AlertNotificationService
from app.modules.notifications.services.competition_notifications import CompetitionNotificationService
from app.modules.notifications.services.enrollment_notifications import EnrollmentNotificationService
from app.modules.notifications.services.notification_log_service import NotificationLogService
from app.modules.notifications.services.payment_notifications import PaymentNotificationService
from app.modules.notifications.services.report_notifications import ReportNotificationService
from app.modules.notifications.services.task_notifications import TaskNotificationService
from app.modules.notifications.services.template_service import TemplateService


def get_notification_repository() -> Generator[NotificationRepository, None, None]:
    with unit_of_work() as uow:
        yield NotificationRepository(uow.session)
        uow.commit()


def get_template_service(repo: NotificationRepository = Depends(get_notification_repository)) -> TemplateService:
    return TemplateService(repo)


def get_log_service(repo: NotificationRepository = Depends(get_notification_repository)) -> NotificationLogService:
    return NotificationLogService(repo)


def get_report_service(repo: NotificationRepository = Depends(get_notification_repository)) -> ReportNotificationService:
    return ReportNotificationService(repo)


def get_alert_service(repo: NotificationRepository = Depends(get_notification_repository)) -> AlertNotificationService:
    return AlertNotificationService(repo)


def get_payment_notification_service(
    repo: NotificationRepository = Depends(get_notification_repository),
) -> PaymentNotificationService:
    return PaymentNotificationService(repo)


def get_enrollment_notification_service(
    repo: NotificationRepository = Depends(get_notification_repository),
) -> EnrollmentNotificationService:
    return EnrollmentNotificationService(repo)


def get_competition_notification_service(
    repo: NotificationRepository = Depends(get_notification_repository),
) -> CompetitionNotificationService:
    return CompetitionNotificationService(repo)


def get_task_notification_service(
    repo: NotificationRepository = Depends(get_notification_repository),
) -> TaskNotificationService:
    return TaskNotificationService(repo)
