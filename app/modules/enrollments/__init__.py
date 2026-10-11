"""
app/modules/enrollments/__init__.py
───────────────────────────────────
Enrollments Module Facade (ADR-0003)

Other modules must import Enrollments ONLY via this facade, except
app.modules.enrollments.models which anyone may import (ADR-0004).

Exports:
- Models: Enrollment, EnrollmentBase, EnrollmentLevelHistory
- Ports: EnrollmentNotifier
- Services: EnrollmentService, EnrollmentDirectoryService,
            EnrollmentLifecycleService, EnrollmentAnalyticsService
- DTOs: EnrollStudentInput, TransferStudentInput, UpdateEnrollmentInput,
        UpdateEnrollmentResult, EnrollmentDTO, EnrollmentCoreResult,
        StudentEnrollmentSummaryDTO, GroupRosterEntryDTO, GroupEnrollmentDTO,
        MigrateEnrollmentsDTO, EnrollmentMigrationResult, LevelProgressionResult
"""

# Models (ADR-0004: anyone may import models directly)
from app.modules.enrollments.models import Enrollment, EnrollmentBase, EnrollmentLevelHistory

# Ports (ADR-0007)
from app.modules.enrollments.ports import EnrollmentNotifier

# DTOs (via facade only)
from app.modules.enrollments.schemas.enrollment_schemas import (
    EnrollStudentInput,
    TransferStudentInput,
    UpdateEnrollmentInput,
    UpdateEnrollmentResult,
    EnrollmentDTO,
    EnrollmentCoreResult,
)
from app.modules.enrollments.schemas.enrollment_directory_schemas import StudentEnrollmentSummaryDTO
from app.modules.enrollments.schemas.enrollment_lifecycle_schemas import (
    MigrateEnrollmentsDTO,
    EnrollmentMigrationResult,
    LevelProgressionResult,
)
from app.modules.enrollments.schemas.enrollment_analytics_schemas import (
    GroupRosterEntryDTO,
    GroupEnrollmentDTO,
)

__all__ = [
    # Models
    "Enrollment",
    "EnrollmentBase",
    "EnrollmentLevelHistory",
    # Ports
    "EnrollmentNotifier",
    # Services
    "EnrollmentService",
    "EnrollmentDirectoryService",
    "EnrollmentLifecycleService",
    "EnrollmentAnalyticsService",
    # DTOs
    "EnrollStudentInput",
    "TransferStudentInput",
    "UpdateEnrollmentInput",
    "UpdateEnrollmentResult",
    "EnrollmentDTO",
    "EnrollmentCoreResult",
    "StudentEnrollmentSummaryDTO",
    "GroupRosterEntryDTO",
    "GroupEnrollmentDTO",
    "MigrateEnrollmentsDTO",
    "EnrollmentMigrationResult",
    "LevelProgressionResult",
]


_LAZY_SERVICES = {
    "EnrollmentService": "app.modules.enrollments.services.enrollment_service",
    "EnrollmentDirectoryService": "app.modules.enrollments.services.enrollment_directory_service",
    "EnrollmentLifecycleService": "app.modules.enrollments.services.enrollment_lifecycle_service",
    "EnrollmentAnalyticsService": "app.modules.enrollments.services.enrollment_analytics_service",
}


def __getattr__(name: str):
    """Load the service classes on first access.

    Lower modules (academics, crm, finance) import ``app.modules.enrollments.models``, which
    runs this package's ``__init__``. Importing the services eagerly would pull in academics'
    facade while academics itself is still initialising, so the services resolve lazily and
    ``import app.modules.<any module>`` works in any order.
    """
    module = _LAZY_SERVICES.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    return getattr(importlib.import_module(module), name)
