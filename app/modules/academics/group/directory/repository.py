"""
app/modules/academics/group/directory/repository.py
────────────────────────────────────────
Repository functions for the Group Directory slice.
"""
from typing import Sequence
from sqlmodel import Session, select, func
from sqlalchemy import text
from app.modules.academics.models import Group
from app.modules.academics.group.core.schemas import EnrichedGroupDTO
from app.modules.academics.constants import (
    GROUP_STATUS_ACTIVE, INSTRUCTOR_PLACEHOLDER,
    ENROLLMENT_STATUS_ACTIVE,
)


def list_all_active_groups(
    session: Session, include_inactive: bool = False
) -> Sequence[Group]:
    stmt = select(Group)
    if not include_inactive:
        stmt = stmt.where(Group.status == GROUP_STATUS_ACTIVE)
    return session.exec(stmt).all()


def get_enriched_group_by_id(session: Session, group_id: int) -> EnrichedGroupDTO | None:
    """Returns a single enriched group by ID."""
    stmt = text(f"""
        SELECT
            g.id,
            g.name AS group_name,
            g.course_id,
            c.name AS course_name,
            g.instructor_id,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.notes,
            g.status,
            (
                SELECT COUNT(*) 
                FROM enrollments e2 
                WHERE e2.group_id = g.id 
                AND e2.level_number = g.level_number 
                AND e2.status = '{ENROLLMENT_STATUS_ACTIVE}'
            ) AS current_student_count
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON g.instructor_id = e.id
        WHERE g.id = :group_id
    """)
    result = session.execute(stmt, {"group_id": group_id}).fetchone()
    if not result:
        return None
    return EnrichedGroupDTO(**result._asdict())

def get_enriched_groups(session: Session) -> list[EnrichedGroupDTO]:
    """Returns active groups joined with instructor name and course name for display."""
    stmt = text(f"""
        SELECT
            g.id,
            g.name AS group_name,
            g.course_id,
            c.name AS course_name,
            g.instructor_id,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.notes,
            g.status,
            (
                SELECT COUNT(*) 
                FROM enrollments e2 
                WHERE e2.group_id = g.id 
                AND e2.level_number = g.level_number 
                AND e2.status = '{ENROLLMENT_STATUS_ACTIVE}'
            ) AS current_student_count
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON g.instructor_id = e.id
        WHERE g.status = '{GROUP_STATUS_ACTIVE}'
        ORDER BY g.id
    """)
    result = session.execute(stmt)
    return [EnrichedGroupDTO(**dict(row._mapping)) for row in result.all()]


def get_enriched_groups_by_date(session: Session, target_date: str) -> list[EnrichedGroupDTO]:
    """Returns active groups that have at least one session on the given date."""
    stmt = text(f"""
        SELECT DISTINCT
            g.id,
            g.name AS group_name,
            g.course_id,
            c.name AS course_name,
            g.instructor_id,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.notes,
            g.status,
            (
                SELECT COUNT(*) 
                FROM enrollments e2 
                WHERE e2.group_id = g.id 
                AND e2.level_number = g.level_number 
                AND e2.status = '{ENROLLMENT_STATUS_ACTIVE}'
            ) AS current_student_count
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON g.instructor_id = e.id
        JOIN sessions s ON g.id = s.group_id
        WHERE g.status = '{GROUP_STATUS_ACTIVE}' AND s.session_date = :target_date
        ORDER BY g.id
    """)
    result = session.execute(stmt, {"target_date": target_date})
    return [EnrichedGroupDTO(**dict(row._mapping)) for row in result.all()]


def search_groups(
    session: Session,
    query: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 20
) -> tuple[Sequence[Group], int]:
    """Search groups by name using ILIKE for partial matching.
    
    Returns:
        Tuple of (list of groups, total count)
    """
    # Build base query
    base_stmt = select(Group).where(Group.name.ilike(f"%{query}%"))
    
    # Apply status filter if provided
    if status:
        base_stmt = base_stmt.where(Group.status == status)
    
    # Get total count
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = session.exec(count_stmt).one()
    
    # Get paginated results
    results_stmt = base_stmt.offset(skip).limit(limit)
    results = session.exec(results_stmt).all()
    
    return results, total


def get_transfer_options(
    session: Session, exclude_group_id: int
) -> Sequence[Group]:
    """Returns active groups excluding the specified group (for transfer options)."""
    stmt = select(Group).where(
        Group.status == GROUP_STATUS_ACTIVE,
        Group.id != exclude_group_id
    )
    return session.exec(stmt).all()


def get_groups_by_type(
    session: Session,
    group_type: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50
) -> tuple[Sequence[Group], int]:
    """Filter groups by type with pagination.
    
    Returns:
        Tuple of (list of groups, total count)
    """
    # Build base query - assuming group_type maps to a field or category
    # For now, search in name as a proxy for type filtering
    base_stmt = select(Group).where(Group.name.ilike(f"%{group_type}%"))
    
    if status:
        base_stmt = base_stmt.where(Group.status == status)
    else:
        base_stmt = base_stmt.where(Group.status == GROUP_STATUS_ACTIVE)
    
    # Get total count
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = session.exec(count_stmt).one()
    
    # Get paginated results
    results_stmt = base_stmt.offset(skip).limit(limit)
    results = session.exec(results_stmt).all()
    
    return results, total

def get_all_archived_groups(
    session: Session, include_inactive: bool = False
) -> Sequence[Group]:
    stmt = select(Group).where(Group.status == "archived")
    return session.exec(stmt).all()


def get_groups_by_course(
    session: Session,
    course_id: int,
    include_inactive: bool = False,
    level_number: int | None = None,
    skip: int = 0,
    limit: int = 50
) -> tuple[Sequence[Group], int]:
    """Get groups associated with a specific course.
    
    Returns:
        Tuple of (list of groups, total count)
    """
    # Build base query
    base_stmt = select(Group).where(Group.course_id == course_id)
    
    # Apply status filter
    if not include_inactive:
        base_stmt = base_stmt.where(Group.status == GROUP_STATUS_ACTIVE)
    
    # Apply level filter if provided
    if level_number:
        base_stmt = base_stmt.where(Group.level_number == level_number)
    
    # Get total count
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = session.exec(count_stmt).one()
    
    # Get paginated results
    results_stmt = base_stmt.offset(skip).limit(limit)
    results = session.exec(results_stmt).all()
    
    return results, total

