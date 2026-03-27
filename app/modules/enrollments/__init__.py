"""
app/modules/enrollments/__init__.py
───────────────────────────────────
Public API facade for the Enrollments module.
Strictly routes calls to the singleton EnrollmentService.
"""
from .schemas import (
    EnrollStudentInput,
    TransferStudentInput,
    EnrollmentDTO,
    EnrollmentCreate,
    EnrollmentRead,
)
from .services.enrollment_service import EnrollmentService

_enrollment_svc = EnrollmentService()

enroll_student = _enrollment_svc.enroll_student
apply_sibling_discount = _enrollment_svc.apply_sibling_discount
transfer_student = _enrollment_svc.transfer_student
drop_enrollment = _enrollment_svc.drop_enrollment
complete_enrollment = _enrollment_svc.complete_enrollment
get_group_roster = _enrollment_svc.get_group_roster
get_student_enrollments = _enrollment_svc.get_student_enrollments

__all__ = [
    "EnrollStudentInput",
    "TransferStudentInput",
    "EnrollmentDTO",
    "EnrollmentCreate",
    "EnrollmentRead",
    "enroll_student",
    "apply_sibling_discount",
    "transfer_student",
    "drop_enrollment",
    "complete_enrollment",
    "get_group_roster",
    "get_student_enrollments",
]
