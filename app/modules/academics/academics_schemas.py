"""
app/modules/academics/academics_schemas.py
───────────────────────────────────────────
Typed input DTOs for the Academics service layer.
"""
from datetime import time, date
from typing import Literal, Optional
from pydantic import BaseModel, model_validator, field_validator
from app.shared.validators import validate_positive_amount

WeekDay = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]


class AddNewCourseInput(BaseModel):
    """Input for academics_service.add_new_course()."""
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


class ScheduleGroupInput(BaseModel):
    """Input for academics_service.schedule_group()."""
    course_id: int
    instructor_id: int
    default_day: WeekDay
    default_time_start: time
    default_time_end: time
    max_capacity: int = 15

    @model_validator(mode="after")
    def validate_time_window(self) -> "ScheduleGroupInput":
        """Reuse the service-level time window check (11AM–9PM)."""
        from app.modules.academics.academics_service import _validate_times
        _validate_times(self.default_time_start, self.default_time_end)
        return self


class AddExtraSessionInput(BaseModel):
    """Input for academics_service.add_extra_session()."""
    group_id: int
    level_number: int
    extra_date: date
    notes: Optional[str] = None


class GenerateLevelSessionsInput(BaseModel):
    """Input for academics_service.generate_level_sessions()."""
    group_id: int
    level_number: int
    start_date: date

class UpdateCourseDTO(BaseModel):
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

class UpdateGroupDTO(BaseModel):
    name: Optional[str] = None
    course_id: Optional[int] = None
    level_number: Optional[int] = None
    max_capacity: Optional[int] = None
    instructor_id: Optional[int] = None
    default_day: Optional[str] = None
    default_time_start: Optional[time] = None
    default_time_end: Optional[time] = None
    status: Optional[str] = None

class UpdateSessionDTO(BaseModel):
    session_date: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    actual_instructor_id: Optional[int] = None
    is_substitute: Optional[bool] = None
    notes: Optional[str] = None
    status: Optional[str] = None
