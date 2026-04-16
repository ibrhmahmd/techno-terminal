"""
StudentGroupBucketDTO - A single bucket in a grouped result.
"""
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class StudentGroupBucketDTO:
    """A single group bucket containing students."""
    key: str
    label: str
    count: int
    students: List["StudentSummaryDTO"]
