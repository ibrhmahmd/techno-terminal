"""
app/modules/enrollments/__init__.py
───────────────────────────────────
Enrollments Module Facade (ADR-0003)

Other modules must import Enrollments ONLY via this facade, except
app.modules.enrollments.models which anyone may import (ADR-0004).

Exports:
- Models: Enrollment, EnrollmentBase
- Services: EnrollmentService, EnrollmentDirectoryService,
            EnrollmentLifecycleService, EnrollmentAnalyticsService
- DTOs: EnrollStudentInput, TransferStudentInput, UpdateEnrollmentInput,
        UpdateEnrollmentResult, EnrollmentDTO, EnrollmentCoreResult,
        StudentEnrollmentSummaryDTO, GroupRosterEntryDTO, GroupEnrollmentDTO,
        MigrateEnrollmentsDTO, EnrollmentMigrationResult, LevelProgressionResult
"""

# Models (ADR-0004: anyone may import models directly)
from app.modules.enrollments.models import Enrollment, EnrollmentBase

# Services (via facade only)
from app.modules.enrollments.services.enrollment_service import EnrollmentService
from app.modules.enrollments.services.enrollment_directory_service import EnrollmentDirectoryService
from app.modules.enrollments.services.enrollment_lifecycle_service import EnrollmentLifecycleService
from app.modules.enrollments.services.enrollment_analytics_service import EnrollmentAnalyticsService

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
