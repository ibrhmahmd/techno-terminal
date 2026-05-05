"""
app/modules/academics/services/group_details_service.py
────────────────────────────────────────────────────────
Service for Group Details API endpoints.

Follows dashboard API patterns with lookup tables and 4-query strategy.
"""
from app.db.connection import get_session
from app.modules.academics.models import CourseSession
from app.modules.academics.models.course_models import Course
from app.modules.hr.models import Employee
from app.modules.academics.group.details.schemas import (
    LevelDeleteResultDTO,
    CourseLookupDTO,
    InstructorLookupDTO,
    StudentLookupDTO,
    SessionInLevelDTO,
    PaymentSummaryDTO,
    LevelWithSessionsDTO,
    GroupLevelsDetailedResponseDTO,
    EnrollmentStatsDTO,
    PaymentStatsDTO,
    GroupAttendanceResponseDTO,
    AttendanceRosterStudentDTO,
    AttendanceSessionDTO,
    GroupPaymentsResponseDTO,
    GroupPaymentsSummaryDTO,
    LevelPaymentSummaryDTO,
    PaymentInLevelDTO,
    GroupEnrollmentsResponseDTO,
    LevelWithEnrollmentsDTO,
    EnrollmentInLevelDTO,
    LevelEnrollmentSummaryDTO,
    TransferOptionDTO,
)
from collections import defaultdict
from app.modules.finance.repositories.payment_repository import PaymentRepository
from app.shared.datetime_utils import utc_now
from app.shared.exceptions import ConflictError

import app.modules.academics.group.level.repository as level_repo
from app.modules.academics.group.level.repository import list_group_levels
import app.modules.academics.session.repository as session_repo
import app.modules.enrollments.repositories.enrollment_repository as enrollment_repo
import app.modules.academics.group.directory.repository as group_repo
from app.modules.academics.group.analytics.repository import (
    get_enrollment_stats_by_levels,
    get_payment_stats_by_levels,
)


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
                raise ConflictError(
                    f"Cannot delete level {level_number}: it has scheduled sessions"
                )

            if level_repo.has_enrollments_for_level(session, group_id, level_number):
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
        self, group_id: int, level_number: int | None = None
    ) -> GroupLevelsDetailedResponseDTO:
        """
        Get levels with sessions, stats, and payment summaries.
        
        If level_number is provided, returns only that specific level.
        Otherwise, returns all levels for the group.
        
        Uses 4-query pattern:
        1. Get levels for group (all or specific)
        2. Get sessions for those levels
        3. Get enrollment stats per level
        4. Get payment aggregates per level
        """
        with get_session() as session:
            # Query 1: Get levels for group
            if level_number is not None:
                # Get specific level
                level = level_repo.get_group_level_by_number(session, group_id, level_number)
                if not level:
                    return GroupLevelsDetailedResponseDTO(
                        group_id=group_id,
                        generated_at=utc_now().isoformat(),
                        cache_ttl=300,
                        courses={},
                        instructors={},
                        levels=[],
                    )
                levels = [level]
            else:
                # Get all levels
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
                if payments.expected > 0:
                    collection_rate = payments.collected / payments.expected

                level_dtos.append(LevelWithSessionsDTO(
                    level_number=level.level_number,
                    level_id=level.id,
                    course_id=level.course_id,
                    instructor_id=level.instructor_id or 0,
                    status=level.status,
                    start_date=start_date,
                    end_date=end_date,
                    sessions=session_dtos,
                    students_count=stats.total,
                    students_completed=stats.completed,
                    students_dropped=stats.dropped,
                    payment_summary=PaymentSummaryDTO(
                        total_expected=payments.expected,
                        total_collected=payments.collected,
                        total_due=payments.due,
                        collection_rate=collection_rate,
                        unpaid_students_count=payments.unpaid_count,
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
    ) -> dict[int, EnrollmentStatsDTO]:
        """Get enrollment counts per level. Delegates to repository."""
        return get_enrollment_stats_by_levels(session, group_id, level_numbers)

    def _get_payment_stats_for_levels(
        self, session, group_id: int, level_numbers: list[int]
    ) -> dict[int, PaymentStatsDTO]:
        """Get payment aggregates per level. Delegates to repository."""
        return get_payment_stats_by_levels(session, group_id, level_numbers)

    def _build_courses_lookup(
        self, session, course_ids: list[int]
    ) -> dict[int, CourseLookupDTO]: #TODO remove Dict and write a typed DTO class
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
    ) -> dict[int, InstructorLookupDTO]: #TODO remove Dict and write a typed DTO class
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
        import app.modules.enrollments.repositories.enrollment_repository as enrollment_repo
        import app.modules.attendance.repositories.attendance_repository as attendance_repo
        
        with get_session() as session:
            # Query 1: Get roster (active enrollments with billing status)
            roster_data = enrollment_repo.get_roster_for_group_level(
                session, group_id, level_number
            )
            
            # Query 2: Get sessions for this level
            sessions = session_repo.list_sessions_by_level(
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

    # ═══════════════════════════════════════════════════════════════════════════
    # GET Group Enrollments (Phase 4)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_group_enrollments(
        self, group_id: int
    ) -> "GroupEnrollmentsResponseDTO":  # type: ignore
        """
        Get all enrollments grouped by level for Students tab.
        
        Returns enrollments with student lookup table and transfer options.
        """
        
        with get_session() as session:
            # Get all levels for this group
            levels = list_group_levels(session, group_id, include_inactive=True)
            
            # Get all enrollments with student details
            enrollments_data = enrollment_repo.get_enrollments_by_group_with_students(
                session, group_id
            )
            
            # Get transfer options (exclude current group)
            transfer_options_data = group_repo.get_transfer_options(
                session, exclude_group_id=group_id
            )
            
            # Group enrollments by level
            enrollments_by_level: dict[int, list[dict]] = defaultdict(list)
            student_ids: set[int] = set()
            
            for e in enrollments_data:
                enrollments_by_level[e["level_number"]].append(e)
                student_ids.add(e["student_id"])
            
            # Build student lookup table
            students_lookup: dict[int, StudentLookupDTO] = {}
            for e in enrollments_data:
                sid = e["student_id"]
                if sid not in students_lookup:
                    students_lookup[sid] = StudentLookupDTO(
                        student_id=sid,
                        student_name=e["student_name"],
                        phone=e.get("student_phone"),
                        parent_name=e.get("parent_name"),
                    )
            
            # Build per-level enrollment DTOs
            grouped_by_level: list[LevelWithEnrollmentsDTO] = []
            
            for level in levels:
                ln = level.level_number
                level_enrollments = enrollments_by_level.get(ln, [])
                
                # Build enrollment DTOs
                enrollment_dtos = [
                    EnrollmentInLevelDTO(
                        enrollment_id=e["enrollment_id"],
                        student_id=e["student_id"],
                        status=e["status"],
                        enrolled_at=e["enrolled_at"].isoformat() if e["enrolled_at"] else "",
                        sessions_attended=e["sessions_attended"],
                        sessions_total=e["sessions_total"],
                        payment_status=e["payment_status"],
                        amount_due=e["amount_due"],
                        amount_paid=e["amount_paid"],
                        discount_applied=e["discount_applied"],
                        can_transfer=e["can_transfer"],
                        can_drop=e["can_drop"],
                    )
                    for e in level_enrollments
                ]
                
                # Calculate summary
                total = len(level_enrollments)
                active = sum(1 for e in level_enrollments if e["status"] == "active")
                completed = sum(1 for e in level_enrollments if e["status"] == "completed")
                dropped = sum(1 for e in level_enrollments if e["status"] == "dropped")
                paid = sum(1 for e in level_enrollments if e["payment_status"] == "paid")
                unpaid = sum(1 for e in level_enrollments if e["payment_status"] == "due")
                
                # Get course name
                course = session.get(Course, level.course_id) if level.course_id else None
                course_name = course.name if course else "Unknown"
                
                grouped_by_level.append(LevelWithEnrollmentsDTO(
                    level_number=ln,
                    level_status=level.status,
                    course_name=course_name,
                    enrollments=enrollment_dtos,
                    summary=LevelEnrollmentSummaryDTO(
                        total=total,
                        active=active,
                        completed=completed,
                        dropped=dropped,
                        paid=paid,
                        unpaid=unpaid,
                    ),
                ))
            
            # Build transfer options DTOs
            transfer_dtos = []
            for t in transfer_options_data:
                course = session.get(Course, t.course_id) if t.course_id else None
                course_name = course.name if course else "Unknown"
                # Calculate available slots
                from app.modules.enrollments.models.enrollment_models import Enrollment
                from app.modules.academics.constants import ENROLLMENT_STATUS_ACTIVE
                from sqlmodel import select, func
                enrolled_count_stmt = select(func.count(Enrollment.id)).where(
                    Enrollment.group_id == t.id,
                    Enrollment.level_number == t.level_number,
                    Enrollment.status == ENROLLMENT_STATUS_ACTIVE
                )
                enrolled_count = session.exec(enrolled_count_stmt).first() or 0
                available_slots = (t.max_capacity or 15) - enrolled_count
                
                transfer_dtos.append(TransferOptionDTO(
                    group_id=t.id,
                    group_name=t.name,
                    course_name=course_name,
                    available_slots=max(0, available_slots),
                ))
            
            return GroupEnrollmentsResponseDTO(
                group_id=group_id,
                generated_at=utc_now().isoformat(),
                cache_ttl=300,
                students=students_lookup,
                grouped_by_level=grouped_by_level,
                transfer_options=transfer_dtos,
            )
