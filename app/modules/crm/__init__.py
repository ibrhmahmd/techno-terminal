"""
app/modules/crm/__init__.py — Compatibility Facade
────────────────────────────────────────────────────
Instantiates CRMService and re-exports all operations and types at the top
level so existing imports continue to work without change.

Internal code should always import from here, never from sub-packages directly.

Usage:
    from app.modules.crm import crm_service
    crm_service.get_student_by_id(1)

    # or direct function access:
    from app.modules.crm import get_student_by_id
"""
from app.modules.crm.services.guardian_service import GuardianService
from app.modules.crm.services.student_service import StudentService
from app.modules.crm.models import Guardian, Student, StudentGuardian
from app.modules.crm.schemas import (
    RegisterGuardianInput,
    RegisterStudentInput,
    RegisterStudentCommandDTO,
    UpdateGuardianDTO,
    UpdateStudentDTO,
)

# ── Service instances ────────────────────────────────────────────────
guardian_svc = GuardianService()
student_svc = StudentService()

# ── Direct function aliases (backward compatibility) ─────────────────────────
get_guardian_by_id       = guardian_svc.get_guardian_by_id
register_guardian        = guardian_svc.register_guardian
find_or_create_guardian  = guardian_svc.find_or_create_guardian
update_guardian          = guardian_svc.update_guardian
search_guardians         = guardian_svc.search_guardians
list_all_guardians       = guardian_svc.list_all_guardians

register_student         = student_svc.register_student
get_student_by_id        = student_svc.get_student_by_id
get_student_guardians    = student_svc.get_student_guardians
search_students          = student_svc.search_students
list_all_students        = student_svc.list_all_students
update_student           = student_svc.update_student
find_siblings            = student_svc.find_siblings
get_guardian_students    = student_svc.get_guardian_students

# ── Virtual Object (backward compatibility) ─────────────────────────
class _CRMServiceFacade:
    pass

crm_service = _CRMServiceFacade()
crm_service.get_guardian_by_id = get_guardian_by_id
crm_service.register_guardian = register_guardian
crm_service.find_or_create_guardian = find_or_create_guardian
crm_service.update_guardian = update_guardian
crm_service.search_guardians = search_guardians
crm_service.list_all_guardians = list_all_guardians

crm_service.register_student = register_student
crm_service.get_student_by_id = get_student_by_id
crm_service.get_student_guardians = get_student_guardians
crm_service.search_students = search_students
crm_service.list_all_students = list_all_students
crm_service.update_student = update_student
crm_service.find_siblings = find_siblings
crm_service.get_guardian_students = get_guardian_students

__all__ = [
    # Service
    "crm_service",
    "guardian_svc",
    "student_svc",
    # Models
    "Guardian",
    "Student",
    "StudentGuardian",
    # DTOs
    "RegisterGuardianInput",
    "RegisterStudentInput",
    "RegisterStudentCommandDTO",
    "UpdateGuardianDTO",
    "UpdateStudentDTO",
    # Guardian functions
    "get_guardian_by_id",
    "register_guardian",
    "find_or_create_guardian",
    "update_guardian",
    "search_guardians",
    "list_all_guardians",
    # Student functions
    "register_student",
    "get_student_by_id",
    "get_student_guardians",
    "search_students",
    "list_all_students",
    "update_student",
    "find_siblings",
    "get_guardian_students",
]
