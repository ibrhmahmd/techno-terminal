from decimal import Decimal
from typing import Sequence
from sqlalchemy import text
from sqlmodel import Session, select
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.enrollments.schemas.enrollment_directory_schemas import (
    EnrollmentAttendanceSummaryDTO,
    EnrollmentBalanceDTO,
)


class EnrollmentDirectoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_enrollments(
        self,
        group_id: int | None = None,
        level_number: int | None = None,
        status: str | None = "active",
    ) -> Sequence[Enrollment]:
        stmt = select(Enrollment)
        if group_id is not None:
            stmt = stmt.where(Enrollment.group_id == group_id)
        if level_number is not None:
            stmt = stmt.where(Enrollment.level_number == level_number)
        if status is not None:
            stmt = stmt.where(Enrollment.status == status)
        return self._session.exec(stmt).all()

    def get_enrollments_by_student(self, student_id: int) -> list[Enrollment]:
        stmt = select(Enrollment).where(Enrollment.student_id == student_id)
        return list(self._session.exec(stmt).all())

    def get_enrollment_balance(
        self, enrollment_id: int
    ) -> EnrollmentBalanceDTO | None:
        """Read the v_enrollment_balance view (moved from finance repository)."""
        stmt = text("""
            SELECT
                enrollment_id,
                student_id,
                group_id,
                level_number,
                amount_due,
                discount_applied,
                total_paid as amount_paid,
                balance,
                payment_status as status
            FROM v_enrollment_balance
            WHERE enrollment_id = :eid
        """)
        row = self._session.execute(stmt, {"eid": enrollment_id}).first()

        if not row:
            return None

        return EnrollmentBalanceDTO(
            enrollment_id=row.enrollment_id,
            student_id=row.student_id,
            group_id=row.group_id,
            level_number=row.level_number,
            amount_due=Decimal(str(row.amount_due or 0)),
            discount_applied=Decimal(str(row.discount_applied or 0)),
            amount_paid=Decimal(str(row.amount_paid or 0)),
            total_refunded=Decimal("0"),
            balance=Decimal(str(row.balance or 0)),
            status=row.status or "unknown",
        )

    def get_enrollment_attendance(
        self, enrollment_id: int
    ) -> EnrollmentAttendanceSummaryDTO:
        """Read the v_enrollment_attendance view (moved from attendance repository)."""
        stmt = text("""
            SELECT enrollment_id, sessions_attended, sessions_missed
            FROM v_enrollment_attendance
            WHERE enrollment_id = :enrollment_id
        """)
        row = self._session.execute(
            stmt, {"enrollment_id": enrollment_id}
        ).first()
        if row:
            return EnrollmentAttendanceSummaryDTO(**row._mapping)
        return EnrollmentAttendanceSummaryDTO(
            enrollment_id=enrollment_id,
            sessions_attended=0,
            sessions_missed=0,
        )
