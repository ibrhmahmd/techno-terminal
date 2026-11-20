"""Hard deletes of E2E test data in finance's own tables (#218). Staging only."""
from sqlalchemy import delete, or_, select
from sqlmodel import Session

from app.modules.finance.models import Payment, Receipt


class FinanceE2EPurgeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _ids(self, stmt) -> set[int]:
        return set(self._session.execute(stmt).scalars())

    def find_payment_ids(
        self, student_ids: list[int], enrollment_ids: list[int], team_member_ids: list[int]
    ) -> list[int]:
        base = self._ids(select(Payment.id).where(or_(
            Payment.student_id.in_(student_ids),
            Payment.enrollment_id.in_(enrollment_ids),
            Payment.team_member_id.in_(team_member_ids),
        )))
        refunds = self._ids(select(Payment.id).where(Payment.original_payment_id.in_(base)))
        return list(base | refunds)

    def find_receipt_ids(self, payment_ids: list[int], prefix: str) -> list[int]:
        """Receipts of the given payments plus payer-name orphans; call before the payments go."""
        return list(
            self._ids(select(Payment.receipt_id).where(Payment.id.in_(payment_ids)))
            | self._ids(select(Receipt.id).where(Receipt.payer_name.startswith(prefix, autoescape=True)))
        )

    def delete_payments(self, payment_ids: list[int]) -> int:
        return self._session.execute(delete(Payment).where(Payment.id.in_(payment_ids))).rowcount

    def delete_receipts_without_payments(self, receipt_ids: list[int]) -> int:
        # a receipt that still carries a payment of someone else is kept (payments.receipt_id is RESTRICT)
        still_used = select(Payment.receipt_id).where(Payment.receipt_id.in_(receipt_ids))
        return self._session.execute(
            delete(Receipt).where(Receipt.id.in_(receipt_ids), Receipt.id.not_in(still_used))
        ).rowcount
