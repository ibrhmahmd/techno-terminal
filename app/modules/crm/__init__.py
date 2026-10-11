"""
app/modules/crm/__init__.py
────────────────────────────

CRM Module Facade (ADR-0003)

Other modules must import CRM ONLY via this facade, except
app.modules.crm.models which anyone may import (ADR-0004).

Exports:
- Models: Parent, Student, StudentParent, StudentStatus
- Services: StudentCrudService, ParentCrudService, SearchService,
            StudentProfileService, StudentActivityService
- DTOs: LogEnrollmentDTO, LogEnrollmentChangeDTO, LogStatusChangeDTO,
        LogPaymentDTO, LogCompetitionRegistrationDTO, TimelineFilterDTO,
        StudentFilterDTO, StudentFilterResultDTO, StudentGroupedResultDTO
"""

# Models (ADR-0004: anyone may import models directly)
from app.modules.crm.models import Parent, Student, StudentParent, StudentStatus

# Services (via facade only)
from app.modules.crm.services import (
    StudentCrudService,
    ParentCrudService,
    SearchService,
    StudentProfileService,
    StudentActivityService,
)

# DTOs (via facade only)
from app.modules.crm.schemas import (
    LogEnrollmentDTO,
    LogEnrollmentChangeDTO,
    LogStatusChangeDTO,
    LogPaymentDTO,
    LogCompetitionRegistrationDTO,
    TimelineFilterDTO,
    StudentFilterDTO,
    StudentFilterResultDTO,
    StudentGroupedResultDTO,
)

# Legacy DTOs kept for backward compatibility (used by existing callers)
from app.modules.crm.schemas import (
    RegisterParentInput,
    RegisterStudentDTO,
    RegisterStudentCommandDTO,
    UpdateParentDTO,
    UpdateStudentDTO,
)

__all__ = [
    # Models
    "Parent",
    "Student",
    "StudentParent",
    "StudentStatus",
    # Services
    "StudentCrudService",
    "ParentCrudService",
    "SearchService",
    "StudentProfileService",
    "StudentActivityService",
    # DTOs
    "LogEnrollmentDTO",
    "LogEnrollmentChangeDTO",
    "LogStatusChangeDTO",
    "LogPaymentDTO",
    "LogCompetitionRegistrationDTO",
    "TimelineFilterDTO",
    "StudentFilterDTO",
    "StudentFilterResultDTO",
    "StudentGroupedResultDTO",
    # Legacy DTOs (backward compatibility)
    "RegisterParentInput",
    "RegisterStudentDTO",
    "RegisterStudentCommandDTO",
    "UpdateParentDTO",
    "UpdateStudentDTO",
]