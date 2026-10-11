"""
StudentGroupedResultDTO - Grouped student data result.
"""
from typing import List
from pydantic import BaseModel

from .student_group_bucket_dto import StudentGroupBucketDTO


class StudentGroupedResultDTO(BaseModel):
    """Result of grouped student query."""
    model_config = {"frozen": True}

    group_by: str
    total_unique_students: int
    groups: List[StudentGroupBucketDTO]
    total: int
