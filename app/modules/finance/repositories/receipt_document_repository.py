"""Read queries behind formatted receipt generation (reads any model, ADR-0004).

Kept apart from ``ReceiptRepository`` because it reads academics/enrollments/crm
models; importing those at module load from the finance facade's own import chain
would create a cycle, and only the receipt generation service needs them.
"""
from typing import Optional

from sqlalchemy import text
from sqlmodel import Session, select

from app.modules.academics.models.group_models import Group
from app.modules.crm.models.student_models import Student
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.finance.models import Payment, Receipt


class ReceiptDocumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_receipt(self, receipt_id: int) -> Optional[Receipt]:
        """Receipt row by id (used by receipt text generation)."""
        return self._session.get(Receipt, receipt_id)

    def get_payment_rows_with_group(self, receipt_id: int) -> list:
        """(Payment, Enrollment, Group) rows for a receipt, outer-joined."""
        return self._session.exec(
            select(Payment, Enrollment, Group)
            .outerjoin(Enrollment, Payment.enrollment_id == Enrollment.id)
            .outerjoin(Group, Enrollment.group_id == Group.id)
            .where(Payment.receipt_id == receipt_id)
        ).all()

    def get_student(self, student_id: int) -> Optional[Student]:
        return self._session.get(Student, student_id)

    def get_student_net_balance(self, student_id: int) -> float:
        """Sum of v_enrollment_balance.balance for a student (0.0 when none)."""
        result = self._session.execute(
            text("""
                SELECT COALESCE(SUM(balance), 0) as net_balance
                FROM v_enrollment_balance
                WHERE student_id = :sid
            """),
            {"sid": student_id},
        ).first()
        return float(result[0] or 0) if result else 0.0
