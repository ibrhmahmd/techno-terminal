"""
app/api/schemas/academics/course.py
─────────────────────────────────────
Public-facing Course DTOs.
"""
from typing import Optional

from pydantic import BaseModel


class CoursePublic(BaseModel):
    """
    Full course profile — safe for API consumers.
    """

    id: int
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    price_per_level: Optional[float] = None
    sessions_per_level: Optional[int] = None
    is_active: bool = True

    model_config = {"from_attributes": True}
