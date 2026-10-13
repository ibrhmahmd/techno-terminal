"""
app/modules/academics/services/group_analytics_service.py
───────────────────────────────────────────────────────
Service for group analytics and history endpoints.
"""
from app.shared.constants import EnrollmentStatus
from app.db.uow import UnitOfWork
from app.modules.academics.schemas.group_analytics_schemas import (
    EnrollmentHistoryItemDTO,
    GroupEnrollmentHistoryResponseDTO,
    InstructorHistoryItemDTO,
    GroupInstructorHistoryResponseDTO,
)
from app.modules.academics.repositories.group_analytics_repository import (
    get_group_enrollments_with_details,
    get_group_enrollment_stats,
    get_enrollment_payments,
    get_group_instructors_summary,
)
from app.modules.academics.models import Group


class GroupAnalyticsService:
    """Service for group analytics and history endpoints."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def get_enrollment_history(
        self,
        group_id: int,
        status: EnrollmentStatus | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> GroupEnrollmentHistoryResponseDTO:
        """
        Get enrollment history for a group.
        Returns full enrollment details with payment info.
        """
        session = self._uow.session
        # Get group info
        group = session.get(Group, group_id)
        group_name = group.name if group else "Unknown"

        # Get enrollment stats
        stats = get_group_enrollment_stats(session, group_id)

        # Get enrollments with student details
        enrollments_data = get_group_enrollments_with_details(
            session, group_id, status, skip, limit
        )

        # Build enrollment DTOs
        enrollment_dtos = []
        for dto in enrollments_data:
            # Calculate payments
            payments_made = get_enrollment_payments(session, dto.enrollment_id)
            amount_due = dto.amount_due
            discount_applied = dto.discount_applied
            balance_remaining = amount_due - payments_made - discount_applied

            enrollment_dtos.append(EnrollmentHistoryItemDTO(
                enrollment_id=dto.enrollment_id,
                student_id=dto.student_id,
                student_name=dto.student_name,
                student_phone=dto.student_phone,
                level_number_at_enrollment=dto.level_number,
                enrolled_at=dto.enrolled_at,
                status=dto.status,
                amount_due=dto.amount_due,
                discount_applied=dto.discount_applied,
                payments_made=payments_made,
                balance_remaining=balance_remaining,
            ))

        return GroupEnrollmentHistoryResponseDTO(
            group_id=group_id,
            group_name=group_name,
            total_enrollments=stats.total,
            active_enrollments=stats.active,
            completed_enrollments=stats.completed,
            dropped_enrollments=stats.dropped,
            enrollments=enrollment_dtos
        )

    def get_instructor_history(self, group_id: int) -> GroupInstructorHistoryResponseDTO:
        """
        Get instructor assignment history for a group.
        Simple list format with assignment counts.
        """
        session = self._uow.session
        # Get group info
        group = session.get(Group, group_id)
        group_name = group.name if group else "Unknown"

        # Get instructor summary
        instructors_data = get_group_instructors_summary(session, group_id)

        # Build instructor DTOs
        instructor_dtos = []
        current_instructor = None

        for summary in instructors_data:
            dto = InstructorHistoryItemDTO(
                instructor_id=summary.instructor_id,
                instructor_name=summary.instructor_name,
                is_current=summary.is_current,
                levels_taught_count=summary.levels_count,
                first_assigned_at=summary.first_assigned,
                last_assigned_at=summary.last_assigned,
            )
            instructor_dtos.append(dto)

            if summary.is_current:
                current_instructor = dto

        return GroupInstructorHistoryResponseDTO(
            group_id=group_id,
            group_name=group_name,
            total_instructors=len(instructor_dtos),
            current_instructor=current_instructor,
            instructors=instructor_dtos
        )
