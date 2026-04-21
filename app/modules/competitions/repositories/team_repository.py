from typing import Optional
from decimal import Decimal
from sqlmodel import Session, select
from app.shared.datetime_utils import utc_now
from app.modules.competitions.models.team_models import (
    Team,
    TeamMember,
)


# ── Teams ─────────────────────────────────────────────────────────────────────

def create_team(
    db: Session,
    competition_id: int,
    team_name: str,
    category: str,
    subcategory: Optional[str] = None,
    coach_id: Optional[int] = None,
    group_id: Optional[int] = None,
    fee: Optional[Decimal] = None,
    notes: Optional[str] = None,
) -> Team:
    """Create a team in the new 3-table schema."""
    t = Team(
        competition_id=competition_id,
        team_name=team_name,
        category=category,
        subcategory=subcategory,
        group_id=group_id,
        coach_id=coach_id,
        fee=fee,
        notes=notes,
        created_at=utc_now(),
    )
    db.add(t)
    db.flush()
    return t


def list_teams(
    db: Session,
    competition_id: int,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    include_deleted: bool = False,
) -> list[Team]:
    """List teams for a competition with optional category/subcategory filters."""
    stmt = select(Team).where(Team.competition_id == competition_id)

    if not include_deleted:
        stmt = stmt.where(Team.deleted_at.is_(None))
    if category:
        stmt = stmt.where(Team.category == category)  # citext: case-insensitive
    if subcategory:
        stmt = stmt.where(Team.subcategory == subcategory)

    return list(db.exec(stmt).all())


def get_team(db: Session, team_id: int, include_deleted: bool = False) -> Team | None:
    """Get a team by ID."""
    team = db.get(Team, team_id)
    if team and not include_deleted and team.deleted_at is not None:
        return None
    return team


def update_team(db: Session, team_id: int, **kwargs) -> Team | None:
    """Update team fields."""
    t = db.get(Team, team_id)
    if t:
        for k, v in kwargs.items():
            setattr(t, k, v)
        db.add(t)
        db.flush()
    return t


def delete_team(db: Session, team_id: int, deleted_by: Optional[int] = None) -> bool:
    """Soft delete a team."""
    t = db.get(Team, team_id)
    if t:
        t.deleted_at = utc_now()
        t.deleted_by = deleted_by
        db.add(t)
        db.flush()
        return True
    return False


def restore_team(db: Session, team_id: int) -> bool:
    """Restore a soft-deleted team."""
    t = db.get(Team, team_id)
    if t:
        t.deleted_at = None
        t.deleted_by = None
        db.add(t)
        db.flush()
        return True
    return False


def list_deleted_teams(db: Session, competition_id: Optional[int] = None) -> list[Team]:
    """List all soft-deleted teams, optionally filtered by competition."""
    stmt = select(Team).where(Team.deleted_at.is_not(None))
    if competition_id:
        stmt = stmt.where(Team.competition_id == competition_id)
    return list(db.exec(stmt).all())


def get_distinct_categories(db: Session, competition_id: int) -> list[tuple[str, Optional[str]]]:
    """Returns list of (category, subcategory) tuples for autocomplete."""
    stmt = (
        select(Team.category, Team.subcategory)
        .where(Team.competition_id == competition_id)
        .where(Team.deleted_at.is_(None))
        .distinct()
        .order_by(Team.category, Team.subcategory)
    )
    return list(db.exec(stmt).all())


def check_student_in_competition(db: Session, competition_id: int, student_id: int) -> bool:
    """Check if student is already in any team for this competition."""
    stmt = (
        select(TeamMember)
        .join(Team)
        .where(Team.competition_id == competition_id)
        .where(TeamMember.student_id == student_id)
        .where(Team.deleted_at.is_(None))
    )
    return db.exec(stmt).first() is not None


def check_category_has_subcategories(db: Session, competition_id: int, category: str) -> bool:
    """Check if any team in this category has a subcategory."""
    stmt = (
        select(Team)
        .where(Team.competition_id == competition_id)
        .where(Team.category == category)
        .where(Team.subcategory.is_not(None))
        .where(Team.deleted_at.is_(None))
    )
    return db.exec(stmt).first() is not None


def get_teams_by_student(db: Session, student_id: int) -> list[Team]:
    """Get all teams a student is a member of."""
    stmt = (
        select(Team)
        .join(TeamMember)
        .where(TeamMember.student_id == student_id)
        .where(Team.deleted_at.is_(None))
    )
    return list(db.exec(stmt).all())


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


def get_team_member_by_id(db: Session, member_id: int) -> TeamMember | None:
    """Get a team member by their unique member ID."""
    return db.get(TeamMember, member_id)


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
