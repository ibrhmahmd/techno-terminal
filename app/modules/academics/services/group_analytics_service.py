"""
app/modules/academics/services/group_analytics_service.py
───────────────────────────────────────────────────────
Service for group analytics and history endpoints.
"""
from datetime import datetime

from app.db.connection import get_session
from app.api.schemas.academics.group_analytics import (
    GroupLevelHistoryItemDTO,
    GroupLevelHistoryResponseDTO,
    EnrollmentHistoryItemDTO,
    GroupEnrollmentHistoryResponseDTO,
    CompetitionHistoryItemDTO,
    GroupCompetitionHistoryResponseDTO,
    InstructorHistoryItemDTO,
    GroupInstructorHistoryResponseDTO,
)
from app.modules.academics.repositories import (
    get_group_levels_with_details,
    get_level_student_counts,
    get_group_enrollments_with_details,
    get_group_enrollment_stats,
    get_enrollment_payments,
    get_group_instructors_summary,
    get_group_competition_participations,
)
from app.modules.academics.models import Group


class GroupAnalyticsService:
    """Service for group analytics and history endpoints."""

    def get_level_progression_history(self, group_id: int) -> GroupLevelHistoryResponseDTO:
        """
        Get complete level progression history for a group.
        Includes student counts per level.
        """
        with get_session() as session:
            # Get group info
            group = session.get(Group, group_id)
            if not group:
                return GroupLevelHistoryResponseDTO(
                    group_id=group_id,
                    group_name="Unknown",
                    total_levels=0,
                    completed_levels=0,
                    active_level=None,
                    levels=[]
                )

            # Get all levels with course and instructor names
            levels_with_details = get_group_levels_with_details(session, group_id)

            # Get student counts per level
            student_counts = get_level_student_counts(session, group_id)

            # Build level DTOs
            level_dtos = []
            active_level = None
            completed_count = 0

            for level, course_name, instructor_name in levels_with_details:
                if level.status == "completed":
                    completed_count += 1
                if level.status == "active":
                    active_level = level.level_number

                # Calculate sessions completed (placeholder - would need attendance data)
                sessions_completed = 0  # TODO: Query from attendance/sessions

                level_dtos.append(GroupLevelHistoryItemDTO(
                    level_id=level.id,
                    level_number=level.level_number,
                    status=level.status,
                    course_id=level.course_id,
                    course_name=course_name,
                    instructor_id=level.instructor_id,
                    instructor_name=instructor_name,
                    sessions_planned=level.sessions_planned,
                    sessions_completed=sessions_completed,
                    student_count=student_counts.get(level.level_number, 0),
                    effective_from=level.effective_from,
                    effective_to=level.effective_to,
                ))

            return GroupLevelHistoryResponseDTO(
                group_id=group_id,
                group_name=group.name,
                total_levels=len(level_dtos),
                completed_levels=completed_count,
                active_level=active_level,
                levels=level_dtos
            )

    def get_enrollment_history(
        self,
        group_id: int,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> GroupEnrollmentHistoryResponseDTO:
        """
        Get enrollment history for a group.
        Returns full enrollment details with payment info.
        """
        with get_session() as session:
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
            for enrollment, student_name, student_phone in enrollments_data:
                # Calculate payments
                payments_made = get_enrollment_payments(session, enrollment.id)
                amount_due = enrollment.amount_due or 0.0
                discount_applied = enrollment.discount_applied or 0.0
                balance_remaining = amount_due - payments_made - discount_applied

                enrollment_dtos.append(EnrollmentHistoryItemDTO(
                    enrollment_id=enrollment.id,
                    student_id=enrollment.student_id,
                    student_name=student_name,
                    student_phone=student_phone,
                    level_number_at_enrollment=enrollment.level_number,
                    enrolled_at=enrollment.enrolled_at,
                    status=enrollment.status,
                    amount_due=enrollment.amount_due or 0.0,
                    discount_applied=enrollment.discount_applied or 0.0,
                    payments_made=payments_made,
                    balance_remaining=balance_remaining,
                ))

            return GroupEnrollmentHistoryResponseDTO(
                group_id=group_id,
                group_name=group_name,
                total_enrollments=stats["total"],
                active_enrollments=stats["active"],
                completed_enrollments=stats["completed"],
                dropped_enrollments=stats["dropped"],
                enrollments=enrollment_dtos
            )

    def get_competition_history(self, group_id: int) -> GroupCompetitionHistoryResponseDTO:
        """
        Get competition participation history for a group.
        """
        with get_session() as session:
            # Get group info
            group = session.get(Group, group_id)
            group_name = group.name if group else "Unknown"

            # Get competition participations
            participations = get_group_competition_participations(session, group_id)

            # Build competition DTOs
            competition_dtos = []
            active_count = 0
            completed_count = 0

            for participation, competition_name, team_name, category_name in participations:
                if participation.is_active:
                    active_count += 1
                else:
                    completed_count += 1

                competition_dtos.append(CompetitionHistoryItemDTO(
                    participation_id=participation.id,
                    competition_id=participation.competition_id,
                    competition_name=competition_name or "Unknown",
                    team_id=participation.team_id,
                    team_name=team_name or "Unknown",
                    category_name=category_name,
                    entered_at=participation.entered_at,
                    left_at=participation.left_at,
                    is_active=participation.is_active,
                    final_placement=participation.final_placement,
                    notes=participation.notes,
                ))

            return GroupCompetitionHistoryResponseDTO(
                group_id=group_id,
                group_name=group_name,
                total_participations=len(competition_dtos),
                active_participations=active_count,
                completed_participations=completed_count,
                competitions=competition_dtos
            )

    def get_instructor_history(self, group_id: int) -> GroupInstructorHistoryResponseDTO:
        """
        Get instructor assignment history for a group.
        Simple list format with assignment counts.
        """
        with get_session() as session:
            # Get group info
            group = session.get(Group, group_id)
            group_name = group.name if group else "Unknown"

            # Get instructor summary
            instructors_data = get_group_instructors_summary(session, group_id)

            # Build instructor DTOs
            instructor_dtos = []
            current_instructor = None

            for (
                instructor_id,
                instructor_name,
                first_assigned,
                last_assigned,
                levels_count,
                is_current
            ) in instructors_data:
                dto = InstructorHistoryItemDTO(
                    instructor_id=instructor_id,
                    instructor_name=instructor_name,
                    is_current=is_current,
                    levels_taught_count=levels_count,
                    first_assigned_at=first_assigned,
                    last_assigned_at=last_assigned,
                )
                instructor_dtos.append(dto)

                if is_current:
                    current_instructor = dto

            return GroupInstructorHistoryResponseDTO(
                group_id=group_id,
                group_name=group_name,
                total_instructors=len(instructor_dtos),
                current_instructor=current_instructor,
                instructors=instructor_dtos
            )
