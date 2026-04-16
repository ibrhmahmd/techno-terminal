"""
StudentProfileService - Handles student profile details, balance, siblings, and attendance.
Replaces the deprecated ReportingService naming.
"""
from typing import Optional, List

from app.modules.crm.models.student_models import Student, StudentStatus
from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
from app.modules.crm.validators.student_validator import StudentValidator
from app.api.schemas.crm.student_details import (
    StudentWithDetails,
    ParentInfo,
    SiblingInfo,
    EnrollmentInfo,
    StudentBalanceSummary,
)
from app.modules.crm.interfaces.dtos import AttendanceStatsDTO
from app.shared.exceptions import NotFoundError


class StudentProfileService:
    """
    Service for retrieving comprehensive student profile information.
    Handles: details, balance summary, siblings, attendance stats.
    """
    
    def __init__(self, uow: StudentUnitOfWork) -> None:
        self._uow = uow
    
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
        enrollments_data = self._uow.students.get_student_enrollments_with_details(student_id)
        
        # Get balance summary
        balance_data = self._uow.students.get_student_balance_summary(student_id)
        
        # Get siblings
        siblings_data = self._uow.students.get_student_siblings_with_details(student_id)
        
        # Get attendance stats
        attendance_stats = self._uow.students.get_student_attendance_stats(student_id)
        
        return StudentWithDetails(
            id=student.id,
            full_name=student.full_name,
            date_of_birth=student.date_of_birth,
            age=age,
            gender=student.gender,
            phone=student.phone,
            notes=student.notes,
            status=str(student.status) if student.status else "active",
            is_active=student.is_active,
            waiting_since=student.waiting_since,
            waiting_priority=student.waiting_priority,
            waiting_notes=student.waiting_notes,
            created_at=student.created_at,
            updated_at=student.updated_at,
            primary_parent=primary_parent,
            enrollments=enrollments_data,
            balance_summary=balance_data if balance_data else StudentBalanceSummary(),
            siblings=siblings_data,
            attendance_stats=attendance_stats,
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
