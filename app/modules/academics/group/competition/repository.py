"""
app/modules/academics/repositories/group_competition_repository.py
───────────────────────────────────────────────────────────────────
Repository functions for Group Competition Participation tracking.
"""
from typing import Sequence
from sqlmodel import Session, select, func
from datetime import datetime

from app.modules.academics.models.group_level_models import GroupCompetitionParticipation


def create_participation(
    session: Session, participation: GroupCompetitionParticipation
) -> GroupCompetitionParticipation:
    """Record a new competition participation."""
    session.add(participation)
    session.flush()
    return participation


def get_participation_by_id(
    session: Session, participation_id: int
) -> GroupCompetitionParticipation | None:
    """Get a specific participation record by ID."""
    return session.get(GroupCompetitionParticipation, participation_id)


def list_group_participations(
    session: Session,
    group_id: int,
    is_active: bool | None = True,
) -> Sequence[GroupCompetitionParticipation]:
    """List all competition participations for a group."""
    stmt = select(GroupCompetitionParticipation).where(
        GroupCompetitionParticipation.group_id == group_id
    )
    if is_active is not None:
        stmt = stmt.where(GroupCompetitionParticipation.is_active == is_active)
    stmt = stmt.order_by(GroupCompetitionParticipation.entered_at.desc())
    return session.exec(stmt).all()


def list_team_participations(
    session: Session,
    team_id: int,
    is_active: bool | None = None,
) -> Sequence[GroupCompetitionParticipation]:
    """List all competition participations for a team."""
    stmt = select(GroupCompetitionParticipation).where(
        GroupCompetitionParticipation.team_id == team_id
    )
    if is_active is not None:
        stmt = stmt.where(GroupCompetitionParticipation.is_active == is_active)
    stmt = stmt.order_by(GroupCompetitionParticipation.entered_at.desc())
    return session.exec(stmt).all()


def complete_participation(
    session: Session,
    participation_id: int,
    final_placement: int | None = None,
) -> GroupCompetitionParticipation | None:
    """Mark a participation as completed."""
    record = session.get(GroupCompetitionParticipation, participation_id)
    if record:
        record.is_active = False
        record.left_at = datetime.utcnow()
        if final_placement is not None:
            record.final_placement = final_placement
        session.add(record)
        session.flush()
    return record


def update_participation(
    session: Session, participation: GroupCompetitionParticipation
) -> GroupCompetitionParticipation:
    """Update a participation record."""
    session.add(participation)
    session.flush()
    return participation


def get_active_participation_for_team(
    session: Session, group_id: int, team_id: int, competition_id: int
) -> GroupCompetitionParticipation | None:
    """Get active participation for a team in a specific competition."""
    stmt = (
        select(GroupCompetitionParticipation)
        .where(GroupCompetitionParticipation.group_id == group_id)
        .where(GroupCompetitionParticipation.team_id == team_id)
        .where(GroupCompetitionParticipation.competition_id == competition_id)
        .where(GroupCompetitionParticipation.is_active == True)
    )
    return session.exec(stmt).first()
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
        stmt = stmt.where(Team.deleted_at.is_(None))
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()
    
    # Get paginated results
    stmt = stmt.offset(skip).limit(limit)
    results = list(session.exec(stmt).all())
    
    return results, total

