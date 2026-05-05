"""
app/modules/academics/schemas/group_level_schemas.py
────────────────────────────────────────────────────
Pydantic schemas for Group Level (OTS) data transfer objects.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class GroupLevelReadDTO(BaseModel):
    """Lightweight DTO for listing group levels."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    level_number: int
    course_id: int
    instructor_id: Optional[int] = None
    sessions_planned: int
    price_override: Optional[Decimal] = None
    status: str
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    created_at: Optional[datetime] = None


class GroupLevelDetailDTO(BaseModel):
    """Detailed DTO for group level with related entity names."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    level_number: int
    course_id: int
    course_name: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    sessions_planned: int
    price_override: Optional[Decimal] = None
    status: str
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    created_at: Optional[datetime] = None
