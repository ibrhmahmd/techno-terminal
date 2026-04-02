from typing import Optional
from sqlmodel import Session, select
from app.shared.datetime_utils import utc_now
from app.modules.competitions.models.team_models import (
    Team,
    TeamMember,
)


# ── Teams ─────────────────────────────────────────────────────────────────────

def create_team(
    db: Session,
    category_id: int,
    team_name: str,
    coach_id: Optional[int] = None,
    group_id: Optional[int] = None,
) -> Team:
    t = Team(
        category_id=category_id,
        group_id=group_id,
        team_name=team_name,
        coach_id=coach_id,
        created_at=utc_now(),
    )
    db.add(t)
    db.flush()
    return t


def list_teams(db: Session, category_id: int) -> list[Team]:
    stmt = select(Team).where(Team.category_id == category_id)
    return list(db.exec(stmt).all())


def get_team(db: Session, team_id: int) -> Team | None:
    return db.get(Team, team_id)


def update_team(db: Session, team_id: int, **kwargs) -> Team | None:
    t = db.get(Team, team_id)
    if t:
        for k, v in kwargs.items():
            setattr(t, k, v)
        db.add(t)
        db.flush()
    return t


def delete_team(db: Session, team_id: int) -> bool:
    t = db.get(Team, team_id)
    if t:
        db.delete(t)
        db.flush()
        return True
    return False


# ── Team Members ──────────────────────────────────────────────────────────────

def add_team_member(db: Session, team_id: int, student_id: int, member_share: float = 0.0) -> TeamMember:
    m = TeamMember(team_id=team_id, student_id=student_id, member_share=member_share, fee_paid=False)
    db.add(m)
    db.flush()
    return m


def get_team_member(db: Session, team_id: int, student_id: int) -> TeamMember | None:
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id, TeamMember.student_id == student_id
    )
    return db.exec(stmt).first()


def list_team_members(db: Session, team_id: int) -> list[TeamMember]:
    stmt = select(TeamMember).where(TeamMember.team_id == team_id)
    return list(db.exec(stmt).all())


def list_student_memberships(db: Session, student_id: int) -> list[TeamMember]:
    stmt = select(TeamMember).where(TeamMember.student_id == student_id)
    return list(db.exec(stmt).all())


def mark_fee_paid(
    db: Session, team_id: int, student_id: int, payment_id: int | None
) -> TeamMember | None:
    m = get_team_member(db, team_id, student_id)
    if m:
        m.fee_paid = payment_id is not None
        m.payment_id = payment_id
        db.add(m)
        db.flush()
    return m


def remove_team_member(db: Session, team_id: int, student_id: int) -> bool:
    m = get_team_member(db, team_id, student_id)
    if m:
        db.delete(m)
        db.flush()
        return True
    return False


def get_members_by_payment_id(db: Session, payment_id: int) -> list[TeamMember]:
    """Returns all TeamMembers whose fee was linked to a given payment ID."""
    stmt = select(TeamMember).where(TeamMember.payment_id == payment_id)
    return list(db.exec(stmt).all())
