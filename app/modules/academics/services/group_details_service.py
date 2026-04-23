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

    # ═══════════════════════════════════════════════════════════════════════════
    # GET Attendance Grid (P1)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_attendance_grid(
        self, group_id: int, level_number: int
    ) -> "GroupAttendanceResponseDTO":  # type: ignore
        """
        Get attendance data for a specific level.
        
        Returns roster + sessions with attendance map.
        Uses 3-query pattern similar to dashboard.
        """
        from app.modules.academics.schemas.group_details_schemas import (
            GroupAttendanceResponseDTO,
            AttendanceRosterStudentDTO,
            AttendanceSessionDTO,
        )
        import app.modules.enrollments.repositories.enrollment_repository as enrollment_repo
        import app.modules.attendance.repositories.attendance_repository as attendance_repo
        
        with get_session() as session:
            # Query 1: Get roster (active enrollments with billing status)
            roster_data = enrollment_repo.get_roster_for_group_level(
                session, group_id, level_number
            )
            
            # Query 2: Get sessions for this level
            sessions = session_repo.get_sessions_for_level(
                session, group_id, level_number
            )
            
            # Query 3: Get all attendance records for these sessions
            attendance_records = attendance_repo.get_attendance_for_group_level(
                session, group_id, level_number
            )
            
            # Build roster DTOs
            roster: list[AttendanceRosterStudentDTO] = [
                AttendanceRosterStudentDTO(
                    student_id=r["student_id"],
                    student_name=r["student_name"],
                    enrollment_id=r["enrollment_id"],
                    billing_status=r["billing_status"],
                    joined_at=r["joined_at"].isoformat() if r["joined_at"] else None,
                )
                for r in roster_data
            ]
            
            # Build attendance map: (session_id, student_id) -> status
            attendance_map: dict[tuple[int, int], str] = {
                (a.session_id, a.student_id): a.status
                for a in attendance_records
            }
            
            # Build session DTOs with attendance maps
            session_dtos: list[AttendanceSessionDTO] = []
            for s in sessions:
                # Build attendance map for this session
                session_attendance: dict[int, str | None] = {}
                for r in roster_data:
                    key = (s.id, r["student_id"])
                    session_attendance[r["student_id"]] = attendance_map.get(key)
                
                session_dtos.append(AttendanceSessionDTO(
                    session_id=s.id,
                    session_number=s.session_number,
                    date=str(s.session_date),
                    time_start=str(s.start_time)[:5] if s.start_time else "",
                    time_end=str(s.end_time)[:5] if s.end_time else "",
                    status=s.status,
                    is_extra_session=s.is_extra_session,
                    attendance=session_attendance,
                ))
            
            return GroupAttendanceResponseDTO(
                group_id=group_id,
                level_number=level_number,
                generated_at=utc_now().isoformat(),
                cache_ttl=300,
                roster=roster,
                sessions=session_dtos,
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # GET Group Payments (Phase 3)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_group_payments(
        self, group_id: int
    ) -> "GroupPaymentsResponseDTO":  # type: ignore
        """
        Get payments grouped by level for Payments tab.
        
        Returns payment summary and per-level breakdown.
        """
        from app.modules.academics.schemas.group_details_schemas import (
            GroupPaymentsResponseDTO,
            GroupPaymentsSummaryDTO,
            LevelPaymentSummaryDTO,
            PaymentInLevelDTO,
        )
        from app.modules.finance.repositories.payment_repository import PaymentRepository
        from app.modules.academics.repositories.group_level_repository import list_group_levels
        from collections import defaultdict
        
        with get_session() as session:
            # Get all levels for this group
            levels = list_group_levels(session, group_id, include_inactive=True)
            
            # Get all payments with level info
            payment_repo = PaymentRepository(session)
            payments_data = payment_repo.get_payments_by_group_with_levels(group_id)
            
            # Group payments by level
            payments_by_level: dict[int, list[dict]] = defaultdict(list)
            for p in payments_data:
                payments_by_level[p["level_number"]].append(p)
            
            # Build per-level summaries
            by_level: list[LevelPaymentSummaryDTO] = []
            total_expected = 0.0
            total_collected = 0.0
            total_due = 0.0
            
            for level in levels:
                ln = level.level_number
                level_payments = payments_by_level.get(ln, [])
                
                # Calculate aggregates
                expected = sum(p["amount_due"] - p["discount_applied"] for p in level_payments)
                collected = sum(p["amount"] for p in level_payments if p["transaction_type"] != "refund")
                refunds = sum(p["amount"] for p in level_payments if p["transaction_type"] == "refund")
                net_collected = collected - refunds
                due = max(0, expected - net_collected)
                
                # Count unique students who paid
                paid_students = set(
                    p["student_id"] for p in level_payments 
                    if p["transaction_type"] != "refund"
                )
                total_students = len(set(p["student_id"] for p in level_payments))
                
                # Get course name
                course = session.get(Course, level.course_id) if level.course_id else None
                course_name = course.name if course else "Unknown"
                
                # Build payment DTOs
                payment_dtos = [
                    PaymentInLevelDTO(
                        payment_id=p["payment_id"],
                        student_id=p["student_id"],
                        student_name=p["student_name"],
                        amount=p["amount"],
                        discount_amount=p["discount_amount"],
                        payment_date=str(p["payment_date"])[:10] if p["payment_date"] else "",
                        payment_method=p["payment_method"],
                        status=p["status"],
                        receipt_number=p["receipt_number"],
                        transaction_type=p["transaction_type"],
                    )
                    for p in level_payments
                ]
                
                by_level.append(LevelPaymentSummaryDTO(
                    level_number=ln,
                    level_status=level.status,
                    course_name=course_name,
                    expected=expected,
                    collected=net_collected,
                    due=due,
                    total_students=total_students,
                    paid_count=len(paid_students),
                    unpaid_count=total_students - len(paid_students),
                    payments=payment_dtos,
                ))
                
                total_expected += expected
                total_collected += net_collected
                total_due += due
            
            # Calculate overall collection rate
            collection_rate = 0.0
            if total_expected > 0:
                collection_rate = total_collected / total_expected
            
            return GroupPaymentsResponseDTO(
                group_id=group_id,
                generated_at=utc_now().isoformat(),
                cache_ttl=300,
                summary=GroupPaymentsSummaryDTO(
                    total_expected_all_levels=total_expected,
                    total_collected_all_levels=total_collected,
                    total_due_all_levels=total_due,
                    collection_rate=collection_rate,
                ),
                by_level=by_level,
            )
