"""
app/modules/academics/repositories/group_repository.py
───────────────────────────────────────────────────────
Repository functions for the Group entity.
"""
from typing import Sequence
from sqlmodel import Session, select, func, delete
from sqlalchemy import text
from app.modules.academics.models import Group
from app.modules.academics.schemas import EnrichedGroupDTO
from app.modules.academics.constants import GROUP_STATUS_ACTIVE, INSTRUCTOR_PLACEHOLDER


def create_group(session: Session, group: Group) -> Group:
    session.add(group)
    session.flush()
    return group


def list_groups_by_course(session: Session, course_id: int) -> Sequence[Group]:
    stmt = (
        select(Group)
        .where(Group.course_id == course_id)
        .where(Group.status == "active")
    )
    return session.exec(stmt).all()


def list_all_active_groups(
    session: Session, include_inactive: bool = False
) -> Sequence[Group]:
    stmt = select(Group)
    if not include_inactive:
        stmt = stmt.where(Group.status == "active")
    return session.exec(stmt).all()


def get_group_by_id(session: Session, group_id: int) -> Group | None:
    return session.get(Group, group_id)


def increment_group_level(session: Session, group_id: int) -> Group | None:
    group = session.get(Group, group_id)
    if group:
        group.level_number += 1
        session.add(group)
    return group
def get_enriched_group_by_id(session: Session, group_id: int) -> EnrichedGroupDTO | None:
    """Returns a single enriched group by ID."""
    stmt = text(f"""
        SELECT
            g.id,
            g.name AS group_name,
            c.name AS course_name,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.notes,
            g.status
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
            c.name AS course_name,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.notes,
            g.status
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
            c.name AS course_name,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.notes,
            g.status
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

def delete_group_by_id(session: Session, group_id: int) -> Group | None:
    """Delete a group by ID. Returns the deleted group or None if not found."""
    # Local imports to avoid circular dependency
    from app.modules.academics.models.session_models import CourseSession
    from app.modules.attendance.models.attendance_models import Attendance
    from app.modules.competitions.models.team_models import Team, TeamMember
    from app.modules.enrollments.models.enrollment_models import Enrollment
    from app.modules.finance.finance_models import Payment
    
    group = session.get(Group, group_id)
    if not group:
        return None
        
    # Get enrollment IDs for this group (attendance & payments FK)
    enrollment_stmt = select(Enrollment.id).where(Enrollment.group_id == group_id)
    enrollment_ids = list(session.scalars(enrollment_stmt))
    
    if enrollment_ids:
        # Delete attendance for these enrollments
        attendance_stmt = delete(Attendance).where(Attendance.enrollment_id.in_(enrollment_ids))
        session.exec(attendance_stmt)
        
        # Delete payments for these enrollments
        payments_stmt = delete(Payment).where(Payment.enrollment_id.in_(enrollment_ids))
        session.exec(payments_stmt)
        
        # Delete enrollments (FK to groups)
        enrollment_delete_stmt = delete(Enrollment).where(Enrollment.group_id == group_id)
        session.exec(enrollment_delete_stmt)
    
    # Get session IDs for this group
    session_stmt = select(CourseSession.id).where(CourseSession.group_id == group_id)
    session_ids = list(session.scalars(session_stmt))
    
    # Delete attendance records for these sessions (FK to sessions)
    if session_ids:
        session_attendance_stmt = delete(Attendance).where(Attendance.session_id.in_(session_ids))
        session.exec(session_attendance_stmt)
    
    # Delete related sessions (FK constraint)
    stmt = delete(CourseSession).where(CourseSession.group_id == group_id)
    session.exec(stmt)
    
    # Get team IDs for this group
    team_stmt = select(Team.id).where(Team.group_id == group_id)
    team_ids = list(session.scalars(team_stmt))
    
    # Delete team_members for these teams first
    if team_ids:
        team_member_stmt = delete(TeamMember).where(TeamMember.team_id.in_(team_ids))
        session.exec(team_member_stmt)
        
        # Delete teams for this group
        team_stmt = delete(Team).where(Team.group_id == group_id)
        session.exec(team_stmt)
    
    session.delete(group)
    session.commit()
    return group
