"""
StudentFilterResultDTO - Result of student filtering operation.
"""
from typing import List, Optional
from pydantic import BaseModel


class StudentFilterItemDTO(BaseModel):
    """A single student in filter results with enriched data."""
    model_config = {"from_attributes": True}

    id: int
    full_name: str
    age: Optional[int] = None
    status: str
    gender: Optional[str] = None
    phone: Optional[str] = None

    # Group info
    current_group_id: Optional[int] = None
    current_group_name: Optional[str] = None
    group_default_day: Optional[str] = None

    # Instructor info
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None

    # Enrollment info
    enrollment_count: int = 0
    enrolled_courses: List[int] = []

    # Balance info
    unpaid_balance: Optional[float] = None


class StudentFilterResultDTO(BaseModel):
    """Result of student filter query with pagination."""
    model_config = {"frozen": True}

    students: List[StudentFilterItemDTO]
    total: int
    skip: int
    limit: int
