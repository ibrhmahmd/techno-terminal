"""
app/modules/academics/models/group_level_models.py
───────────────────────────────────────────────────
SQLModel classes for Group Levels (OTS Levels), Course History,
and Competition Participation tracking.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field, Column, String


class GroupLevel(SQLModel, table=True):
    """Immutable per-level configuration snapshot for a group."""
    __tablename__ = "group_levels"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="groups.id", index=True)
    level_number: int = Field(index=True)
    course_id: int = Field(foreign_key="courses.id")
    instructor_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    sessions_planned: int = Field(default=12)
    price_override: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)
    status: str = Field(default="active", sa_column=Column(String, index=True))
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_to: Optional[datetime] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class GroupCourseHistory(SQLModel, table=True):
    """Audit trail for course assignments to groups."""
    __tablename__ = "group_course_history"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="groups.id", index=True)
    course_id: int = Field(foreign_key="courses.id")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    removed_at: Optional[datetime] = None
    assigned_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class GroupCompetitionParticipation(SQLModel, table=True):
    """Track group participation in competitions via teams."""
    __tablename__ = "group_competition_participation"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="groups.id", index=True)
    team_id: int = Field(foreign_key="teams.id", index=True)
    competition_id: int = Field(foreign_key="competitions.id")
    category_id: Optional[int] = Field(default=None, foreign_key="competition_categories.id")
    entered_at: datetime = Field(default_factory=datetime.utcnow)
    left_at: Optional[datetime] = None
    is_active: bool = Field(default=True, index=True)
    final_placement: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class EnrollmentLevelHistory(SQLModel, table=True):
    """Track student enrollment transitions through group levels."""
    __tablename__ = "enrollment_level_history"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    enrollment_id: int = Field(foreign_key="enrollments.id", index=True)
    group_level_id: int = Field(foreign_key="group_levels.id", index=True)
    student_id: int = Field(foreign_key="students.id", index=True)
    level_entered_at: datetime = Field(default_factory=datetime.utcnow)
    level_completed_at: Optional[datetime] = None
    status: str = Field(default="active", sa_column=Column(String))
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)




class GroupLevelCourseAssignment(SQLModel, table=True):
    """Track course assignments to group levels."""
    __tablename__ = "group_level_course_assignments"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    group_level_id: int = Field(foreign_key="group_levels.id", index=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    removed_at: Optional[datetime] = None
    assigned_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)