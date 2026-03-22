from datetime import date
from typing import Optional
from sqlmodel import Session, select
from app.shared.datetime_utils import utc_now
from app.modules.competitions.competition_models import (
    Competition,
    CompetitionCategory,
    Team,
    TeamMember,
)


# ── Competitions ──────────────────────────────────────────────────────────────


def create_competition(
    db: Session,
    name: str,
    edition: Optional[str],
    competition_date: Optional[date],
    location: Optional[str],
    notes: Optional[str],
) -> Competition:
    c = Competition(
        name=name,
        edition=edition,
        competition_date=competition_date,
        location=location,
        notes=notes,
        created_at=utc_now(),
    )
    db.add(c)
    db.flush()
    return c


def list_competitions(db: Session) -> list[Competition]:
    stmt = select(Competition).order_by(Competition.competition_date.desc())
    return list(db.exec(stmt).all())


def get_competition(db: Session, competition_id: int) -> Competition | None:
    return db.get(Competition, competition_id)


def update_competition(
    db: Session, competition_id: int, **kwargs
) -> Competition | None:
    c = db.get(Competition, competition_id)
    if c:
        for k, v in kwargs.items():
            setattr(c, k, v)
        db.add(c)
        db.flush()
    return c


def delete_competition(db: Session, competition_id: int) -> bool:
    c = db.get(Competition, competition_id)
    if c:
        db.delete(c)
        db.flush()
        return True
    return False


# ── Categories ────────────────────────────────────────────────────────────────


def add_category(
    db: Session,
    competition_id: int,
    category_name: str,
    notes: Optional[str] = None,
) -> CompetitionCategory:
    cat = CompetitionCategory(
        competition_id=competition_id,
        category_name=category_name,
        notes=notes,
    )
    db.add(cat)
    db.flush()
    return cat


def list_categories(db: Session, competition_id: int) -> list[CompetitionCategory]:
    stmt = select(CompetitionCategory).where(
        CompetitionCategory.competition_id == competition_id
    )
    return list(db.exec(stmt).all())


def get_category(db: Session, category_id: int) -> CompetitionCategory | None:
    return db.get(CompetitionCategory, category_id)


def update_category(
    db: Session, category_id: int, **kwargs
) -> CompetitionCategory | None:
    cat = db.get(CompetitionCategory, category_id)
    if cat:
        for k, v in kwargs.items():
            setattr(cat, k, v)
        db.add(cat)
        db.flush()
    return cat


def delete_category(db: Session, category_id: int) -> bool:
    cat = db.get(CompetitionCategory, category_id)
    if cat:
        db.delete(cat)
        db.flush()
        return True
    return False


# ── Teams ─────────────────────────────────────────────────────────────────────


def create_team(
    db: Session,
    category_id: int,
    team_name: str,
    coach_id: Optional[int] = None,
    group_id: Optional[int] = None,
    fee_per_student: Optional[float] = None,
) -> Team:
    t = Team(
        category_id=category_id,
        group_id=group_id,
        team_name=team_name,
        coach_id=coach_id,
        enrollment_fee_per_student=fee_per_student,
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


def add_team_member(db: Session, team_id: int, student_id: int) -> TeamMember:
    m = TeamMember(team_id=team_id, student_id=student_id, fee_paid=False)
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


# ── RepositoryProtocol aliases ────────────────────────────────────────────────
# Primary entity: Competition
get_by_id = get_competition
create = create_competition
list_all = list_competitions
