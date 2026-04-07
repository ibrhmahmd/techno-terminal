"""
app/modules/academics/repositories/team_repository.py
─────────────────────────────────────────────────────
Team repository functions for database access.
"""
from typing import Optional
from sqlmodel import Session, select, func

from app.modules.competitions.models.team_models import Team


def get_teams_by_group(
    session: Session,
    group_id: int,
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 50
) -> tuple[list[Team], int]:
    """
    Get paginated list of teams for a group.
    
    Args:
        session: Database session
        group_id: The group ID to filter by
        include_inactive: Whether to include deleted teams
        skip: Number of records to skip (pagination)
        limit: Maximum records to return (pagination)
        
    Returns:
        Tuple of (teams list, total count)
    """
    stmt = select(Team).where(Team.group_id == group_id)
    
    if not include_inactive:
        stmt = stmt.where(Team.is_deleted == False)
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()
    
    # Get paginated results
    stmt = stmt.offset(skip).limit(limit)
    results = list(session.exec(stmt).all())
    
    return results, total
