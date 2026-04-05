"""
app/modules/academics/repositories/group_level_repository.py
─────────────────────────────────────────────────────────────
Repository functions for Group Levels (OTS Levels).
"""
from typing import Sequence
from sqlmodel import Session, select
from app.modules.academics.models.group_level_models import GroupLevel


def create_group_level(session: Session, level: GroupLevel) -> GroupLevel:
    """Create a new group level snapshot."""
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
        stmt = stmt.where(GroupLevel.status == "active")
    
    stmt = stmt.order_by(GroupLevel.level_number.asc())
    return session.exec(stmt).all()


def update_group_level(session: Session, level: GroupLevel) -> GroupLevel:
    """Update a group level (limited fields allowed)."""
    session.add(level)
    session.flush()
    return level


def complete_group_level(
    session: Session, group_id: int, level_number: int
) -> GroupLevel | None:
    """Mark a group level as completed."""
    from datetime import datetime
    
    level = get_group_level_by_number(session, group_id, level_number)
    if level:
        level.status = "completed"
        level.effective_to = datetime.utcnow()
        session.add(level)
        session.flush()
    return level


def cancel_group_level(
    session: Session, group_id: int, level_number: int
) -> GroupLevel | None:
    """Mark a group level as cancelled."""
    from datetime import datetime
    
    level = get_group_level_by_number(session, group_id, level_number)
    if level:
        level.status = "cancelled"
        level.effective_to = datetime.utcnow()
        session.add(level)
        session.flush()
    return level


def get_current_group_level(session: Session, group_id: int) -> GroupLevel | None:
    """Get the currently active level for a group."""
    stmt = (
        select(GroupLevel)
        .where(GroupLevel.group_id == group_id)
        .where(GroupLevel.status == "active")
        .order_by(GroupLevel.level_number.desc())
    )
    return session.exec(stmt).first()
