"""
app/modules/academics/schemas/session_schemas.py
─────────────────────────────────────────────────
Input DTOs for the CourseSession entity.
"""
from datetime import date, time
from typing import Optional
from pydantic import BaseModel, field_validator


class AddExtraSessionInput(BaseModel):
    """Input for SessionService.add_extra_session()."""
    group_id: int
    level_number: int
    extra_date: date
    notes: Optional[str] = None


class GenerateLevelSessionsInput(BaseModel):
    """Input for SessionService.generate_level_sessions()."""
    group_id: int
    level_number: int
    start_date: date


class UpdateSessionDTO(BaseModel):
    """Partial update DTO for SessionService.update_session()."""
    session_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    actual_instructor_id: Optional[int] = None
    is_substitute: Optional[bool] = None
    notes: Optional[str] = None
    status: Optional[str] = None

    @field_validator('actual_instructor_id', mode='before')
    @classmethod
    def coerce_zero_to_none(cls, v: int | None) -> int | None:
        """Convert 0 to None — frontend may send 0 to mean 'no instructor'."""
        if v == 0:
            return None
        return v
