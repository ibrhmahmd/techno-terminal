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
from app.modules.crm.services.parent_service import ParentService
from app.modules.crm.services.student_service import StudentService
from app.modules.crm.models import Parent, Student, StudentParent
from app.modules.crm.schemas import (
    RegisterParentInput,
    RegisterStudentInput,
    RegisterStudentCommandDTO,
    UpdateParentDTO,
    UpdateStudentDTO,
)

# ── Service instances ────────────────────────────────────────────────
parent_svc = ParentService()
student_svc = StudentService()

# ── Direct function aliases (backward compatibility) ─────────────────────────
get_parent_by_id       = parent_svc.get_parent_by_id
register_parent        = parent_svc.register_parent
find_or_create_parent  = parent_svc.find_or_create_parent
update_parent          = parent_svc.update_parent
search_parents         = parent_svc.search_parents
list_all_parents       = parent_svc.list_all_parents

register_student         = student_svc.register_student
get_student_by_id        = student_svc.get_student_by_id
get_student_parents    = student_svc.get_student_parents
search_students          = student_svc.search_students
list_all_students        = student_svc.list_all_students
update_student           = student_svc.update_student
find_siblings            = student_svc.find_siblings
get_parent_students    = student_svc.get_parent_students

# ── Virtual Object (backward compatibility) ─────────────────────────
class _CRMServiceFacade:
    pass

crm_service = _CRMServiceFacade()
crm_service.get_parent_by_id = get_parent_by_id
crm_service.register_parent = register_parent
crm_service.find_or_create_parent = find_or_create_parent
crm_service.update_parent = update_parent
crm_service.search_parents = search_parents
crm_service.list_all_parents = list_all_parents

crm_service.register_student = register_student
crm_service.get_student_by_id = get_student_by_id
crm_service.get_student_parents = get_student_parents
crm_service.search_students = search_students
crm_service.list_all_students = list_all_students
crm_service.update_student = update_student
crm_service.find_siblings = find_siblings
crm_service.get_parent_students = get_parent_students

__all__ = [
    # Service
    "crm_service",
    "parent_svc",
    "student_svc",
    # Models
    "Parent",
    "Student",
    "StudentParent",
    # DTOs
    "RegisterParentInput",
    "RegisterStudentInput",
    "RegisterStudentCommandDTO",
    "UpdateParentDTO",
    "UpdateStudentDTO",
    # Parent functions
    "get_parent_by_id",
    "register_parent",
    "find_or_create_parent",
    "update_parent",
    "search_parents",
    "list_all_parents",
    # Student functions
    "register_student",
    "get_student_by_id",
    "get_student_parents",
    "search_students",
    "list_all_students",
    "update_student",
    "find_siblings",
    "get_parent_students",
]
