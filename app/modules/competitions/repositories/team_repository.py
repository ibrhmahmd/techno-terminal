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
    project_name: Optional[str] = None,
    project_description: Optional[str] = None,
) -> Team:
    """Create a team in the new 3-table schema."""
    from app.shared.datetime_utils import utc_now
    t = Team(
        competition_id=competition_id,
        team_name=team_name,
        category=category,
        subcategory=subcategory,
        group_id=group_id,
        coach_id=coach_id,
        fee=fee,
        notes=notes,
        project_name=project_name,
        project_description=project_description,
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
) -> list[Team]:
    """List teams for a competition with optional category/subcategory filters."""
    stmt = select(Team).where(Team.competition_id == competition_id)
    if category:
        stmt = stmt.where(Team.category == category)
    if subcategory:
        stmt = stmt.where(Team.subcategory == subcategory)
    return list(db.exec(stmt).all())


def get_team(db: Session, team_id: int) -> Team | None:
    """Get a team by ID."""
    return db.get(Team, team_id)


def update_team(db: Session, team_id: int, **kwargs) -> Team | None:
    """Update team fields."""
    t = db.get(Team, team_id)
    if t:
        for k, v in kwargs.items():
            setattr(t, k, v)
        db.add(t)
        db.flush()
    return t


def delete_team(db: Session, team_id: int) -> bool:
    """Hard delete a team."""
    t = db.get(Team, team_id)
    if t:
        db.delete(t)
        db.flush()
        return True
    return False


def get_distinct_categories(db: Session, competition_id: int) -> list[tuple[str, Optional[str]]]:
    """Returns list of (category, subcategory) tuples for autocomplete."""
    stmt = (
        select(Team.category, Team.subcategory)
        .where(Team.competition_id == competition_id)
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
    )
    return db.exec(stmt).first() is not None


def check_category_has_subcategories(db: Session, competition_id: int, category: str) -> bool:
    """Check if any team in this category has a subcategory."""
    stmt = (
        select(Team)
        .where(Team.competition_id == competition_id)
        .where(Team.category == category)
        .where(Team.subcategory.is_not(None))
    )
    return db.exec(stmt).first() is not None


def get_teams_by_student(db: Session, student_id: int) -> list[Team]:
    """Get all teams a student is a member of."""
    stmt = (
        select(Team)
        .join(TeamMember)
        .where(TeamMember.student_id == student_id)
    )
    return list(db.exec(stmt).all())


# ── Team Members ──────────────────────────────────────────────────────────────

def add_team_member(db: Session, team_id: int, student_id: int, amount_due: float = 0.0) -> TeamMember:
    m = TeamMember(team_id=team_id, student_id=student_id, amount_due=amount_due, amount_paid=0.0)
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


def record_payment(
    db: Session, team_member_id: int, amount: float
) -> TeamMember | None:
    """Increment amount_paid for a team member."""
    m = db.get(TeamMember, team_member_id)
    if m:
        m.amount_paid = float(m.amount_paid) + amount
        db.add(m)
        db.flush()
    return m


def refund_payment(
    db: Session, team_member_id: int, amount: float
) -> TeamMember | None:
    """Decrement amount_paid for a team member (refund)."""
    m = db.get(TeamMember, team_member_id)
    if m:
        m.amount_paid = max(0.0, float(m.amount_paid) - amount)
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
