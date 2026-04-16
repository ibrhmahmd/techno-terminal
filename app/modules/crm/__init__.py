"""
app/modules/crm/__init__.py
────────────────────────────

CRM module exports — SOLID Architecture (no backward compatibility).

Import patterns:
    - Services via dependency injection (see app/api/dependencies.py)
    - Models directly from app.modules.crm.models
    - DTOs from app.modules.crm.schemas or app.api.schemas.crm
"""

# Models
from app.modules.crm.models import Parent, Student, StudentParent

# DTOs (Pydantic schemas)
from app.modules.crm.schemas import (
    RegisterParentInput,
    RegisterStudentDTO,
    RegisterStudentCommandDTO,
    UpdateParentDTO,
    UpdateStudentDTO,
)

# Services (for type hints and direct use)
from app.modules.crm.services import (
    StudentCrudService,
    ParentCrudService,
    SearchService,
    StudentProfileService,
)

__all__ = [
    # Models
    "Parent",
    "Student",
    "StudentParent",
    # DTOs
    "RegisterParentInput",
    "RegisterStudentDTO",
    "RegisterStudentCommandDTO",
    "UpdateParentDTO",
    "UpdateStudentDTO",
    # Services (SOLID)
    "StudentCrudService",
    "ParentCrudService",
    "SearchService",
    "StudentProfileService",
]

