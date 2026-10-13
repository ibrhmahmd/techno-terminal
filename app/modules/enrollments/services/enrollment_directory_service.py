from sqlmodel import select

from app.db.uow import UnitOfWork
from app.modules.academics.models import GroupLevel
from app.modules.academics.models.group_models import Group
from app.modules.crm.models import Student
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.enrollments.schemas.enrollment_schemas import EnrollmentDTO
from app.modules.enrollments.schemas.enrollment_directory_schemas import StudentEnrollmentSummaryDTO
from app.modules.enrollments.repositories.enrollment_directory_repository import (
    EnrollmentDirectoryRepository,
)


class EnrollmentDirectoryService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._repo = EnrollmentDirectoryRepository(uow.session)

    def get_student_enrollments(self, student_id: int) -> list[EnrollmentDTO]:
        enrollments = self._repo.get_enrollments_by_student(student_id)
        result = []
        for enrollment in enrollments:
            names = self._repo.get_group_display_names(enrollment.group_id)
            dto = EnrollmentDTO.model_validate(enrollment).model_copy(update=names.model_dump())

            balance_info = self._repo.get_enrollment_balance(enrollment.id)
            if balance_info:
                dto.payment_status = balance_info.status
                dto.amount_remaining = max(0.0, -float(balance_info.balance))
            result.append(dto)
        return result

    def get_enrollments_summary_by_group(
        self, group_id: int, level_number: int | None = None
    ) -> list[StudentEnrollmentSummaryDTO]:
        session = self._uow.session

        stmt = select(Enrollment, Student).join(
            Student, Enrollment.student_id == Student.id
        ).where(Enrollment.group_id == group_id)

        if level_number:
            stmt = stmt.where(Enrollment.level_number == level_number)
        else:
            group = session.get(Group, group_id)
            if group:
                stmt = stmt.where(Enrollment.level_number == group.level_number)

        stmt = stmt.where(Enrollment.status != "dropped")
        results = session.exec(stmt).all()

        summary_list = []
        for enrollment, student in results:
            attendance_summary = self._repo.get_enrollment_attendance(
                enrollment.id
            )
            level = session.exec(
                select(GroupLevel).where(
                    GroupLevel.group_id == group_id,
                    GroupLevel.level_number == enrollment.level_number
                )
            ).first()
            sessions_total = level.sessions_planned if level else 0

            balance_info = self._repo.get_enrollment_balance(enrollment.id)
            payment_status = balance_info.status if balance_info else 'not_paid'
            amount_remaining = float(balance_info.balance) if balance_info else 0.0

            amount_due = float(enrollment.amount_due or 0)
            discount = float(enrollment.discount_applied or 0)

            summary = StudentEnrollmentSummaryDTO(
                student_id=student.id,
                student_name=student.full_name or "Unknown",
                enrollment_id=enrollment.id,
                level_number=enrollment.level_number,
                status=enrollment.status,
                sessions_attended=attendance_summary.sessions_attended,
                sessions_total=sessions_total,
                payment_status=payment_status,
                amount_remaining=amount_remaining,
                amount_due=amount_due,
                discount_applied=discount,
            )
            summary_list.append(summary)

        return summary_list
