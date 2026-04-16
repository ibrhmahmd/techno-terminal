"""
StudentGroupedResultDTO - Result of a student grouping operation.
"""
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class StudentGroupedResultDTO:
    """Result of a grouping operation."""
    group_by: str
    total_unique_students: int
    groups: List["StudentGroupBucketDTO"]
