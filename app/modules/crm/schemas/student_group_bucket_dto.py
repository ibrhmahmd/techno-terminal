"""
StudentGroupBucketDTO - A single group bucket in grouped results.
"""
from typing import List
from pydantic import BaseModel

from .student_summary_dto import StudentSummaryDTO


class StudentGroupBucketDTO(BaseModel):
    """A bucket/group in grouped student results."""
    model_config = {"frozen": True}

    key: str  # e.g., "active", "male", "10-15"
    label: str  # Human readable label
    count: int
    students: List[StudentSummaryDTO]
