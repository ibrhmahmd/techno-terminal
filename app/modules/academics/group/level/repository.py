"""
app/modules/academics/repositories/group_level_repository.py
─────────────────────────────────────────────────────────────
Repository functions for Group Levels (OTS Levels).
"""
from typing import Sequence, Optional
from sqlmodel import Session, select, func
from app.shared.datetime_utils import utc_now
from app.modules.academics.models.group_level_models import GroupLevel
from app.modules.academics.constants import (
    LEVEL_STATUS_ACTIVE, LEVEL_STATUS_COMPLETED, LEVEL_STATUS_CANCELLED,
    ENROLLMENT_STATUS_ACTIVE,
)


def create_group_level(session: Session, level: GroupLevel) -> GroupLevel:
    """Create a new group level snapshot."""
    from app.shared.audit_utils import apply_create_audit
    apply_create_audit(level)
    session.add(level)
    session.flush()
    return level


def get_group_level_by_id(session: Session, level_id: int) -> GroupLevel | None:
    """Get a specific group level by its ID."""
    return session.get(GroupLevel, level_id)


def get_group_level_by_number(
    session: Session, group_id: int, level_number: int
) -> GroupLevel | None:
    """Get a group level by group ID and level number."""
    stmt = (
        select(GroupLevel)
        .where(GroupLevel.group_id == group_id)
        .where(GroupLevel.level_number == level_number)
    )
    return session.exec(stmt).first()


def list_group_levels(
    session: Session,
    group_id: int,
    status: str | None = None,
    include_inactive: bool = False,
) -> Sequence[GroupLevel]:
    """List all level snapshots for a group."""
    stmt = select(GroupLevel).where(GroupLevel.group_id == group_id)
    
    if status:
        stmt = stmt.where(GroupLevel.status == status)
    elif not include_inactive:
        stmt = stmt.where(GroupLevel.status == LEVEL_STATUS_ACTIVE)
    
    stmt = stmt.order_by(GroupLevel.level_number.asc())
    return session.exec(stmt).all()


def get_levels_by_group(
    session: Session,
    group_id: int,
    status: Optional[str] = None,
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 50
) -> tuple[list[GroupLevel], int]:
    """
    Get paginated list of levels for a group.
    
    Args:
        session: Database session
        group_id: The group ID
        status: Filter by status (active, completed, cancelled)
        include_inactive: Include inactive levels
        skip: Number of records to skip
        limit: Maximum records to return
        
    Returns:
        Tuple of (levels list, total count)
    """
    stmt = select(GroupLevel).where(GroupLevel.group_id == group_id)
    
    if status:
        stmt = stmt.where(GroupLevel.status == status)
    elif not include_inactive:
        stmt = stmt.where(GroupLevel.status == LEVEL_STATUS_ACTIVE)
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()
    
    # Get paginated results
    stmt = stmt.order_by(GroupLevel.level_number).offset(skip).limit(limit)
    results = list(session.exec(stmt).all())
    
    return results, total


def update_group_level(session: Session, level: GroupLevel) -> GroupLevel:
    """Update a group level (limited fields allowed)."""
    from app.shared.audit_utils import apply_update_audit
    apply_update_audit(level)
    session.add(level)
    session.flush()
    return level


def complete_group_level(
    session: Session, group_id: int, level_number: int
) -> GroupLevel | None:
    """Mark a group level as completed."""
    level = get_group_level_by_number(session, group_id, level_number)
    if level:
        level.status = LEVEL_STATUS_COMPLETED
        level.effective_to = utc_now()
        from app.shared.audit_utils import apply_update_audit
        apply_update_audit(level)
        session.add(level)
        session.flush()
    return level


def cancel_group_level(
    session: Session, group_id: int, level_number: int
) -> GroupLevel | None:
    """Mark a group level as cancelled."""
    level = get_group_level_by_number(session, group_id, level_number)
    if level:
        level.status = LEVEL_STATUS_CANCELLED
        level.effective_to = utc_now()
        from app.shared.audit_utils import apply_update_audit
        apply_update_audit(level)
        session.add(level)
        session.flush()
    return level


def get_current_group_level(session: Session, group_id: int) -> GroupLevel | None:
    """Get the currently active level for a group."""
    stmt = (
        select(GroupLevel)
        .where(GroupLevel.group_id == group_id)
        .where(GroupLevel.status == LEVEL_STATUS_ACTIVE)
        .order_by(GroupLevel.level_number.desc())
    )
    return session.exec(stmt).first()


def has_sessions_for_level(session: Session, group_id: int, level_number: int) -> bool:
    """Check if any sessions exist for this group level."""
    from app.modules.academics.models.session_models import CourseSession
    stmt = (
        select(func.count())
        .select_from(CourseSession)
        .where(CourseSession.group_id == group_id)
        .where(CourseSession.level_number == level_number)
    )
    count = session.exec(stmt).one()
    return count > 0


def has_enrollments_for_level(session: Session, group_id: int, level_number: int) -> bool:
    """Check if any active enrollments exist at this level."""
    from app.modules.enrollments.models.enrollment_models import Enrollment
    stmt = (
        select(func.count())
        .select_from(Enrollment)
        .where(Enrollment.group_id == group_id)
        .where(Enrollment.level_number == level_number)
        .where(Enrollment.status == ENROLLMENT_STATUS_ACTIVE)
    )
    count = session.exec(stmt).one()
    return count > 0


def soft_delete_level(
    session: Session, group_id: int, level_number: int
) -> GroupLevel | None:
    """
    Soft delete a level by setting status='deleted' and deleted_at timestamp.
    
    Returns the deleted level or None if not found.
    """
    level = get_group_level_by_number(session, group_id, level_number)
    if level:
        level.status = "deleted"
        level.effective_to = utc_now()
        from app.shared.audit_utils import apply_update_audit
        apply_update_audit(level)
        # Note: GroupLevel model doesn't have deleted_at field, using effective_to
        session.add(level)
        session.flush()
    return level
