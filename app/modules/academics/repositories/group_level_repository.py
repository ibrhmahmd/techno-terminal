"""
app/modules/academics/repositories/group_level_repository.py
─────────────────────────────────────────────────────────────
Repository functions for Group Levels (OTS Levels).
"""
from typing import Sequence
from sqlmodel import Session, select
from app.shared.datetime_utils import utc_now
from app.shared.audit_utils import apply_update_audit
from app.modules.academics.models.group_level_models import GroupLevel
from app.modules.academics.constants import (
    LEVEL_STATUS_ACTIVE, LEVEL_STATUS_COMPLETED,
)


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


def update_group_level(session: Session, level: GroupLevel) -> GroupLevel:
    """Update a group level (limited fields allowed)."""
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


def get_previous_active_level(
    session: Session, group_id: int, before_level_number: int
) -> GroupLevel | None:
    """Get the highest active or completed level number strictly below before_level_number."""
    stmt = (
        select(GroupLevel)
        .where(GroupLevel.group_id == group_id)
        .where(GroupLevel.level_number < before_level_number)
        .where(GroupLevel.status.in_([LEVEL_STATUS_ACTIVE, LEVEL_STATUS_COMPLETED]))
        .order_by(GroupLevel.level_number.desc())
    )
    return session.exec(stmt).first()


