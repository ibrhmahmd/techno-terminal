"""Database ledger for scheduled report delivery claims."""
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select

from app.db.connection import get_session
from app.modules.notifications.models.notification_log import NotificationLog


_REPORT_DELIVERY_INDEX = "uq_notification_logs_report_delivery"
_STALE_CLAIM_ERROR = "abandoned claim (stale PENDING)"


class SqlReportDeliveryLedger:
    def claim(
        self,
        template_id: int,
        period_start: date,
        recipient_type: str,
        recipient_id: int,
        recipient_contact: str,
        subject: Optional[str],
        body: str,
    ) -> Optional[int]:
        with get_session() as session:
            stale_cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
            stale_claims = session.exec(
                select(NotificationLog).where(
                    NotificationLog.template_id == template_id,
                    NotificationLog.report_period_start == period_start,
                    NotificationLog.recipient_contact == recipient_contact,
                    NotificationLog.status == "PENDING",
                    col(NotificationLog.created_at) < stale_cutoff,
                )
            ).all()
            for stale_claim in stale_claims:
                stale_claim.status = "FAILED"
                stale_claim.error_message = _STALE_CLAIM_ERROR
                session.add(stale_claim)
            session.commit()

            claim = NotificationLog(
                template_id=template_id,
                channel="EMAIL",
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                recipient_contact=recipient_contact,
                subject=subject,
                body=body,
                status="PENDING",
                report_period_start=period_start,
            )
            session.add(claim)
            try:
                session.commit()
            except IntegrityError as error:
                session.rollback()
                if self._is_report_delivery_conflict(error):
                    return None
                raise
            return claim.id

    def mark(self, log_id: int, status: str, error_message: Optional[str]) -> None:
        with get_session() as session:
            claim = session.get(NotificationLog, log_id)
            if claim:
                claim.status = status
                claim.error_message = error_message
                claim.sent_at = datetime.now(timezone.utc) if status == "SENT" else None
                session.add(claim)
            session.commit()

    @staticmethod
    def _is_report_delivery_conflict(error: IntegrityError) -> bool:
        constraint_name = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        if constraint_name is not None:
            return constraint_name == _REPORT_DELIVERY_INDEX
        return _REPORT_DELIVERY_INDEX in str(error.orig)
