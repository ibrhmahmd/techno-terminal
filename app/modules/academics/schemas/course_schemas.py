"""
app/modules/academics/schemas/course_schemas.py
────────────────────────────────────────────────
Input DTOs and typed read models for the Course entity.
"""
from typing import Optional
from pydantic import BaseModel, field_validator
from app.shared.validators import validate_positive_amount


# ── Input DTOs ────────────────────────────────────────────────────────────────

class AddNewCourseInput(BaseModel):
    """Input for CourseService.add_new_course()."""
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    price_per_level: float
    sessions_per_level: int

    @field_validator("price_per_level")
    @classmethod
    def price_positive(cls, v: float) -> float:
        validate_positive_amount(v, field="price per level")
        return v

    @field_validator("sessions_per_level")
    @classmethod
    def sessions_positive(cls, v: int) -> int:
        if v <= 0:
            from app.shared.exceptions import ValidationError
            raise ValidationError("Sessions per level must be at least 1.")
        return v


class UpdateCourseDTO(BaseModel):
    """Partial update DTO for CourseService.update_course()."""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price_per_level: Optional[float] = None
    sessions_per_level: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("price_per_level")
    @classmethod
    def price_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            validate_positive_amount(v, field="price per level")
        return v

    @field_validator("sessions_per_level")
    @classmethod
    def sessions_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            from app.shared.exceptions import ValidationError
            raise ValidationError("Sessions per level must be at least 1.")
        return v


# ── Typed Read Models ─────────────────────────────────────────────────────────

class CourseStatsDTO(BaseModel):
    """Typed read model for v_course_stats view rows."""
    course_id: int
    course_name: str
    total_groups: int
    active_groups: int
    total_students_ever: int
    active_students: int
