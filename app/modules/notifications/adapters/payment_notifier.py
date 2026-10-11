"""Adapter implementing PaymentNotifier using NotificationService (ADR-0007)."""

from decimal import Decimal

from fastapi import BackgroundTasks, Depends

from app.modules.notifications.api.deps import get_notification_service
from app.modules.finance import PaymentNotifier
from app.modules.notifications.services.notification_service import NotificationService


class NotificationServicePaymentNotifier:
    """Adapts NotificationService to the PaymentNotifier port."""

    def __init__(self, background_tasks: BackgroundTasks, notif_svc: NotificationService):
        self._background_tasks = background_tasks
        self._notif_svc = notif_svc

    def payment_received(
        self, *, receipt_id: int, student_id: int, amount: str, receipt_number: str
    ) -> None:
        self._notif_svc.payment.notify_payment_received(
            receipt_id=receipt_id,
            student_id=student_id,
            amount=amount,
            receipt_number=receipt_number,
            background_tasks=self._background_tasks,
        )

    def competition_fee_paid(
        self,
        *,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        amount: Decimal,
        receipt_number: str,
    ) -> None:
        self._notif_svc.competition.notify_competition_fee_paid(
            student_id=student_id,
            team_id=team_id,
            team_name=team_name,
            competition_name=competition_name,
            amount=amount,
            receipt_number=receipt_number,
            background_tasks=self._background_tasks,
        )


def get_payment_notifier(
    background_tasks: BackgroundTasks,
    notif_svc: NotificationService = Depends(get_notification_service),
) -> PaymentNotifier:
    """FastAPI dependency factory for the PaymentNotifier adapter."""
    return NotificationServicePaymentNotifier(
        background_tasks=background_tasks, notif_svc=notif_svc
    )
