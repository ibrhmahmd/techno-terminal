"""
app/modules/academics/services/group_details_service.py
────────────────────────────────────────────────────────
Service for Group Details API endpoints.

Follows dashboard API patterns with lookup tables and 4-query strategy.
"""
from app.db.connection import get_session
from app.modules.academics.models import CourseSession
from app.modules.academics.models.course_models import Course
from app.modules.hr.hr_models import Employee
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.academics.schemas.group_details_schemas import (
    LevelDeleteResultDTO,
    CourseLookupDTO,
    InstructorLookupDTO,
    SessionInLevelDTO,
    PaymentSummaryDTO,
    LevelWithSessionsDTO,
    GroupLevelsDetailedResponseDTO,
)
from app.shared.datetime_utils import utc_now

import app.modules.academics.repositories.group_level_repository as level_repo
import app.modules.academics.repositories.session_repository as session_repo


class GroupDetailsService:
    """Service for group details endpoints with lookup table patterns."""

    # ═══════════════════════════════════════════════════════════════════════════
    # DELETE Level (P0)
    # ═══════════════════════════════════════════════════════════════════════════

    def delete_level(
        self, group_id: int, level_number: int
    ) -> LevelDeleteResultDTO:
        """
        Soft delete a level after checking constraints.
        
        Raises:
            ValueError: If level not found
            ConflictError: If level has sessions or enrollments
        """
        with get_session() as session:
            # Check level exists
            level = level_repo.get_group_level_by_number(session, group_id, level_number)
            if not level:
                raise ValueError(f"Level {level_number} not found for group {group_id}")
            
            # Check constraints
            if level_repo.has_sessions_for_level(session, group_id, level_number):
                from app.shared.exceptions import ConflictError
                raise ConflictError(
                    f"Cannot delete level {level_number}: it has scheduled sessions"
                )
            
            if level_repo.has_enrollments_for_level(session, group_id, level_number):
                from app.shared.exceptions import ConflictError
                raise ConflictError(
                    f"Cannot delete level {level_number}: it has active enrollments"
                )
            
            # Soft delete
            deleted = level_repo.soft_delete_level(session, group_id, level_number)
            if deleted:
                session.commit()
                return LevelDeleteResultDTO(
                    level_id=deleted.id,
                    level_number=deleted.level_number,
                    group_id=deleted.group_id,
                    deleted_at=utc_now().isoformat(),
                )
            raise ValueError(f"Failed to delete level {level_number}")

    # ═══════════════════════════════════════════════════════════════════════════
    # GET Levels Detailed (P0)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_levels_detailed(
        self, group_id: int
    ) -> GroupLevelsDetailedResponseDTO:
        """
        Get all levels with sessions, stats, and payment summaries.
        
        Uses 4-query pattern:
        1. Get all levels for group
        2. Get all sessions for all levels
        3. Get enrollment stats per level
        4. Get payment aggregates per level
        """
        with get_session() as session:
            # Query 1: Get all levels for group
            levels = level_repo.list_group_levels(
                session, group_id, include_inactive=True
            )
            
            if not levels:
                # Return empty response
                return GroupLevelsDetailedResponseDTO(
                    group_id=group_id,
                    generated_at=utc_now().isoformat(),
                    cache_ttl=300,
                    courses={},
                    instructors={},
                    levels=[],
                )
            
            # Collect level numbers and related IDs for lookups
            level_numbers = [level.level_number for level in levels]
            course_ids = list(set(level.course_id for level in levels if level.course_id))
            instructor_ids = list(set(
                level.instructor_id for level in levels if level.instructor_id
            ))
            
            # Query 2: Get all sessions for these levels
            sessions = session_repo.get_sessions_for_levels(
                session, group_id, level_numbers
            )
            
            # Query 3: Get enrollment stats per level
            enrollment_stats = self._get_enrollment_stats_for_levels(
                session, group_id, level_numbers
            )
            
            # Query 4: Get payment aggregates per level
            payment_stats = self._get_payment_stats_for_levels(
                session, group_id, level_numbers
            )
            
            # Build lookup tables
            courses_lookup = self._build_courses_lookup(session, course_ids)
            instructors_lookup = self._build_instructors_lookup(
                session, instructor_ids
            )
            
            # Map sessions to levels
            sessions_by_level: dict[int, list[CourseSession]] = {
                ln: [] for ln in level_numbers
            }
            for s in sessions:
                if s.level_number in sessions_by_level:
                    sessions_by_level[s.level_number].append(s)
            
            # Build level DTOs
            level_dtos: list[LevelWithSessionsDTO] = []
            for level in levels:
                ln = level.level_number
                stats = enrollment_stats.get(ln, {
                    "total": 0, "completed": 0, "dropped": 0
                })
                payments = payment_stats.get(ln, {
                    "expected": 0.0, "collected": 0.0, "due": 0.0,
                    "unpaid_count": 0
                })
                
                # Convert sessions to DTOs
                session_dtos = [
                    SessionInLevelDTO(
                        session_id=s.id,
                        session_number=s.session_number,
                        date=str(s.session_date),
                        time_start=str(s.start_time)[:5] if s.start_time else "",
                        time_end=str(s.end_time)[:5] if s.end_time else "",
                        status=s.status,
                        is_extra_session=s.is_extra_session,
                        actual_instructor_id=s.actual_instructor_id,
                        is_substitute=s.is_substitute,
                    )
                    for s in sessions_by_level.get(ln, [])
                ]
                
                # Calculate dates from sessions
                start_date = None
                end_date = None
                if session_dtos:
                    dates = [s.date for s in session_dtos]
                    start_date = min(dates) if dates else None
                    end_date = max(dates) if dates else None
                
                # Calculate collection rate
                collection_rate = 0.0
                if payments["expected"] > 0:
                    collection_rate = payments["collected"] / payments["expected"]
                
                level_dtos.append(LevelWithSessionsDTO(
                    level_number=level.level_number,
                    level_id=level.id,
                    course_id=level.course_id,
                    instructor_id=level.instructor_id or 0,
                    status=level.status,
                    start_date=start_date,
                    end_date=end_date,
                    sessions=session_dtos,
                    students_count=stats["total"],
                    students_completed=stats["completed"],
                    students_dropped=stats["dropped"],
                    payment_summary=PaymentSummaryDTO(
                        total_expected=payments["expected"],
                        total_collected=payments["collected"],
                        total_due=payments["due"],
                        collection_rate=collection_rate,
                        unpaid_students_count=payments["unpaid_count"],
                    ),
                ))
            
            return GroupLevelsDetailedResponseDTO(
                group_id=group_id,
                generated_at=utc_now().isoformat(),
                cache_ttl=300,
                courses=courses_lookup,
                instructors=instructors_lookup,
                levels=level_dtos,
            )

    def _get_enrollment_stats_for_levels(
        self, session, group_id: int, level_numbers: list[int]
    ) -> dict[int, dict]:
        """Get enrollment counts per level."""
        from sqlmodel import select, func
        
        stmt = (
            select(
                Enrollment.level_number,
                Enrollment.status,
                func.count().label("count")
            )
            .where(Enrollment.group_id == group_id)
            .where(Enrollment.level_number.in_(level_numbers))
            .group_by(Enrollment.level_number, Enrollment.status)
        )
        results = session.exec(stmt).all()
        
        # Aggregate per level
        stats: dict[int, dict] = {ln: {"total": 0, "completed": 0, "dropped": 0} for ln in level_numbers}
        for row in results:
            ln = row.level_number
            status = row.status
            count = row.count
            stats[ln]["total"] += count
            if status == "completed":
                stats[ln]["completed"] += count
            elif status == "dropped":
                stats[ln]["dropped"] += count
        
        return stats

    def _get_payment_stats_for_levels(
        self, session, group_id: int, level_numbers: list[int]
    ) -> dict[int, dict]:
        """Get payment aggregates per level using enrollment data."""
        from sqlmodel import select, func
        from app.modules.finance.models.payment import Payment
        
        # Get enrollments with their payment status per level
        stmt = (
            select(
                Enrollment.level_number,
                Enrollment.amount_due,
                Enrollment.discount_applied,
                func.coalesce(
                    func.sum(Payment.amount),
                    0
                ).label("total_paid")
            )
            .outerjoin(
                Payment,
                (Payment.enrollment_id == Enrollment.id) & 
                (Payment.deleted_at.is_(None))
            )
            .where(Enrollment.group_id == group_id)
            .where(Enrollment.level_number.in_(level_numbers))
            .where(Enrollment.status.in_(["active", "completed"]))
            .group_by(Enrollment.id, Enrollment.level_number, Enrollment.amount_due, Enrollment.discount_applied)
        )
        results = session.exec(stmt).all()
        
        # Aggregate per level
        stats: dict[int, dict] = {
            ln: {"expected": 0.0, "collected": 0.0, "due": 0.0, "unpaid_count": 0}
            for ln in level_numbers
        }
        
        for row in results:
            ln = row.level_number
            amount_due = float(row.amount_due or 0)
            discount = float(row.discount_applied or 0)
            total_paid = float(row.total_paid or 0)
            
            expected = amount_due - discount
            due = expected - total_paid
            
            stats[ln]["expected"] += expected
            stats[ln]["collected"] += total_paid
            stats[ln]["due"] += max(0, due)
            if due > 0:
                stats[ln]["unpaid_count"] += 1
        
        return stats

    def _build_courses_lookup(
        self, session, course_ids: list[int]
    ) -> dict[int, CourseLookupDTO]:
        """Build lookup table for courses."""
        lookup: dict[int, CourseLookupDTO] = {}
        for cid in course_ids:
            course = session.get(Course, cid)
            if course:
                lookup[cid] = CourseLookupDTO(
                    course_id=course.id,
                    course_name=course.name or "Unknown Course",
                )
        return lookup

    def _build_instructors_lookup(
        self, session, instructor_ids: list[int]
    ) -> dict[int, InstructorLookupDTO]:
        """Build lookup table for instructors."""
        lookup: dict[int, InstructorLookupDTO] = {}
        for iid in instructor_ids:
            instructor = session.get(Employee, iid)
            if instructor:
                lookup[iid] = InstructorLookupDTO(
                    instructor_id=instructor.id,
                    instructor_name=instructor.full_name or "Unnamed",
                )
        return lookup
