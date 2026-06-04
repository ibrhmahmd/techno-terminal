"""
StudentFilterDTO - Input parameters for filtering students.
"""
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, validator


class StudentFilterDTO(BaseModel):
    """Input parameters for flexible student filtering."""
    model_config = {"frozen": True}

    @validator("course_ids", "exclude_course_ids", pre=True)
    def parse_comma_separated_ints(cls, v):
        if not v:
            return None
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, str):
                    result.extend([int(x.strip()) for x in item.split(",") if x.strip()])
                elif isinstance(item, (int, float)):
                    result.append(int(item))
            return result
        return v

    # Age filtering
    min_age: Optional[int] = Field(None, ge=0, le=100, description="Minimum student age")
    max_age: Optional[int] = Field(None, ge=0, le=100, description="Maximum student age")

    # Status and demographic filtering
    status: Optional[List[str]] = Field(None, description="Student statuses to include")
    gender: Optional[List[str]] = Field(None, description="Genders to include")

    # Course and group filtering
    course_ids: Optional[List[int]] = Field(None, description="Course IDs to filter by")
    group_default_day: Optional[List[str]] = Field(None, description="Group meeting days (e.g., 'Monday', 'Saturday')")
    instructor_name: Optional[str] = Field(None, description="Partial instructor name search")

    # Payment filtering
    has_unpaid_balance: Optional[bool] = Field(None, description="Filter by unpaid balance status")

    # Enrollment date filtering
    enrollment_date_from: Optional[date] = Field(None, description="Enrolled on or after this date")
    enrollment_date_to: Optional[date] = Field(None, description="Enrolled on or before this date")

    # Enrollment count filtering
    min_enrollments: Optional[int] = Field(None, ge=0, description="Minimum number of enrollments")
    max_enrollments: Optional[int] = Field(None, ge=0, description="Maximum number of enrollments")

    # Advanced Course Exclusion and Enrollment Dates
    exclude_course_ids: Optional[List[int]] = Field(None, description="Course IDs the student must not be enrolled in")
    course_enrollment_date_from: Optional[date] = Field(None, description="Course enrollment date from")
    course_enrollment_date_to: Optional[date] = Field(None, description="Course enrollment date to")

    # Advanced Activity Log Filtering
    min_activity_count: Optional[int] = Field(None, ge=0, description="Minimum number of activity log events")
    max_activity_count: Optional[int] = Field(None, ge=0, description="Maximum number of activity log events")
    activity_types: Optional[List[str]] = Field(None, description="Activity types to filter by")
    activity_date_from: Optional[date] = Field(None, description="Activity created on or after this date")
    activity_date_to: Optional[date] = Field(None, description="Activity created on or before this date")
    activity_search_term: Optional[str] = Field(None, description="Search term in student activity description or metadata")

    # Pagination
    skip: int = Field(0, ge=0, description="Number of students to skip")
    limit: int = Field(50, ge=1, le=200, description="Maximum students to return")
