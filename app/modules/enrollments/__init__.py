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
from app.modules.enrollments.core.service import EnrollmentService
from app.modules.enrollments.directory.service import EnrollmentDirectoryService
from app.modules.enrollments.lifecycle.service import EnrollmentLifecycleService
from app.modules.enrollments.analytics.service import EnrollmentAnalyticsService

# DTOs (via facade only)
from app.modules.enrollments.core.schemas import (
    EnrollStudentInput,
    TransferStudentInput,
    UpdateEnrollmentInput,
    UpdateEnrollmentResult,
    EnrollmentDTO,
    EnrollmentCoreResult,
)
from app.modules.enrollments.directory.schemas import StudentEnrollmentSummaryDTO
from app.modules.enrollments.lifecycle.schemas import (
    MigrateEnrollmentsDTO,
    EnrollmentMigrationResult,
    LevelProgressionResult,
)
from app.modules.enrollments.analytics.schemas import (
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
