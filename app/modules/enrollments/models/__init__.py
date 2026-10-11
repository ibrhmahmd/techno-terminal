"""Enrollments domain models (ADR-0004: any module may import these)."""
from app.modules.enrollments.models.enrollment_models import (
    Enrollment,
    EnrollmentBase,
)

__all__ = [
    "Enrollment",
    "EnrollmentBase",
]
