"""
StudentProfileService - Handles student profile details, balance, siblings, and attendance.
Replaces the deprecated ReportingService naming.
"""
from typing import Optional, List

from app.modules.crm.models.student_models import Student
from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
from app.modules.crm.validators.student_validator import StudentValidator
from app.api.schemas.crm.student_details import (
    StudentWithDetails,
    ParentInfo,
    SiblingInfo,
    StudentBalanceSummary,
    CurrentEnrollmentInfo,
    StudentEnrollmentAttendanceItem,
    SessionAttendanceItem,
    EnrollmentInfo,
)
from app.modules.crm.interfaces.dtos import AttendanceStatsDTO
from app.modules.attendance.schemas import StudentEnrollmentAttendanceDTO
from app.shared.exceptions import NotFoundError


class StudentProfileService:
    """
    Service for retrieving comprehensive student profile information.
    Handles: details, balance summary, siblings, attendance stats.
    """
    
    def __init__(self, uow: StudentUnitOfWork) -> None:
        self._uow = uow
    
    def _get_current_enrollment_info(self, student_id: int) -> Optional[CurrentEnrollmentInfo]:
        """Fetch active enrollment with group, course, and instructor details."""
        result = self._uow.students.get_active_enrollment_with_details(student_id)
        if not result:
            return None

        enrollment_id, group_name, group_id, course_name, course_id, instructor_name, level_number = result
        return CurrentEnrollmentInfo(
            enrollment_id=enrollment_id,
            group_id=group_id,
            group_name=group_name,
            course_id=course_id,
            course_name=course_name,
            level_number=level_number,
            instructor_name=instructor_name,
        )

    def _get_school_name(self, student: Student) -> Optional[str]:
        """Extract school name from profile_metadata JSONB."""
        if student.profile_metadata and isinstance(student.profile_metadata, dict):
            return student.profile_metadata.get("school_name")
        return None

    def _get_attendance_summary(self, student_id: int) -> List[StudentEnrollmentAttendanceDTO]:
        """Get attendance summary grouped by enrollment with all session records."""
        from app.modules.attendance.repositories.attendance_repository import (
            get_student_attendance_summary,
        )

        return get_student_attendance_summary(self._uow._session, student_id)

    def get_student_details(self, student_id: int) -> StudentWithDetails:
        """
        Get complete student profile with parent, enrollments, balance, and siblings.
        """
        # Get student with primary parent
        student, parent = self._uow.students.get_student_with_parent(student_id)
        if not student:
            raise NotFoundError(f"Student {student_id} not found")

        # Compute age
        age = StudentValidator.compute_age(student.date_of_birth)

        # Build parent info
        primary_parent = None
        if parent:
            primary_parent = ParentInfo(
                id=parent.id,
                full_name=parent.full_name,
                phone=parent.phone,
                email=parent.email,
                relationship=None,  # Could be fetched from link if needed
            )

        # Get enrollments
        enrollments_data = self._uow.students.get_active_enrollment_with_details(student_id)

        # Convert tuple to EnrollmentInfo list
        enrollments_list = []
        if enrollments_data:
            enrollments_list = [EnrollmentInfo(
                enrollment_id=enrollments_data[0],
                group_name=enrollments_data[1],
                group_id=enrollments_data[2],
                course_name=enrollments_data[3],
                course_id=enrollments_data[4],
                level_number=enrollments_data[6],
                status="active",
                amount_due=None,
                discount_applied=0.0,
                enrolled_at=None,
            )]

        # Get balance summary
        balance_data = self._uow.students.get_student_balance_summary(student_id)

        # Get siblings
        siblings_data = self._uow.students.get_student_siblings_with_details(student_id)

        # Get attendance stats (existing field)
        attendance_stats = self._uow.students.get_attendance_stats(student_id)

        # NEW: Current enrollment info
        current_enrollment = self._get_current_enrollment_info(student_id)

        # NEW: Attendance summary per enrollment
        enrollment_attendance_data = self._get_attendance_summary(student_id)

        # Calculate totals from enrollment attendance
        total_present = sum(e.present_count for e in enrollment_attendance_data)
        total_absent = sum(e.absent_count for e in enrollment_attendance_data)
        # Find last attended date across all enrollments
        last_attended = None
        for e in enrollment_attendance_data:
            for s in e.sessions:
                if s.status in ("present", "late"):
                    if last_attended is None or s.session_date > last_attended:
                        last_attended = s.session_date

        # Convert to API schema types
        enrollment_attendance = [
            StudentEnrollmentAttendanceItem(
                enrollment_id=e.enrollment_id,
                group_id=e.group_id,
                group_name=e.group_name,
                course_name=e.course_name,
                level_number=e.level_number,
                present_count=e.present_count,
                absent_count=e.absent_count,
                sessions=[
                    SessionAttendanceItem(session_date=s.session_date, status=s.status)
                    for s in e.sessions
                ],
            )
            for e in enrollment_attendance_data
        ]

        # NEW: School name from metadata
        school_name = self._get_school_name(student)

        return StudentWithDetails(
            id=student.id,
            full_name=student.full_name,
            date_of_birth=student.date_of_birth,
            age=age,
            gender=student.gender,
            phone=student.phone,
            notes=student.notes,
            status=str(student.status) if student.status else "inactive",
            school_name=school_name,
            waiting_since=student.waiting_since,
            waiting_priority=student.waiting_priority,
            waiting_notes=student.waiting_notes,
            created_at=student.created_at,
            updated_at=student.updated_at,
            primary_parent=primary_parent,
            enrollments=enrollments_list,
            current_enrollment=current_enrollment,
            sessions_attended_count=total_present,
            sessions_absent_count=total_absent,
            last_session_attended=last_attended,
            balance_summary=balance_data if balance_data else StudentBalanceSummary(),
            siblings=siblings_data,
            attendance_stats=attendance_stats,
            enrollment_attendance=enrollment_attendance,
        )
    
    def get_student_siblings(self, student_id: int) -> List[SiblingInfo]:
        """Get student's siblings (same parent)."""
        # Verify student exists
        student = self._uow.students.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Student {student_id} not found")
        
        return self._uow.students.get_student_siblings_with_details(student_id)
    
    def get_balance_summary(self, student_id: int) -> StudentBalanceSummary:
        """Get financial balance summary for a student."""
        student = self._uow.students.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Student {student_id} not found")
        
        balance = self._uow.students.get_student_balance_summary(student_id)
        return balance if balance else StudentBalanceSummary()
    
    def get_attendance_stats(self, student_id: int) -> AttendanceStatsDTO:
        """Get attendance statistics for a student."""
        student = self._uow.students.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Student {student_id} not found")
        
        return self._uow.students.get_student_attendance_stats(student_id)
