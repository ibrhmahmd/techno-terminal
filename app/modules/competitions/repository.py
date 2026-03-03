from datetime import datetime, date
from typing import Optional
from sqlmodel import Session, select
from app.modules.competitions.models import (
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
        created_at=datetime.utcnow(),
    )
    db.add(c)
    db.flush()
    return c


def list_competitions(db: Session) -> list[Competition]:
    stmt = select(Competition).order_by(Competition.competition_date.desc())
    return list(db.exec(stmt).all())


def get_competition(db: Session, competition_id: int) -> Competition | None:
    return db.get(Competition, competition_id)


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
        created_at=datetime.utcnow(),
    )
    db.add(t)
    db.flush()
    return t


def list_teams(db: Session, category_id: int) -> list[Team]:
    stmt = select(Team).where(Team.category_id == category_id)
    return list(db.exec(stmt).all())


def get_team(db: Session, team_id: int) -> Team | None:
    return db.get(Team, team_id)


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
    db: Session, team_id: int, student_id: int, payment_id: int
) -> TeamMember | None:
    m = get_team_member(db, team_id, student_id)
    if m:
        m.fee_paid = True
        m.payment_id = payment_id
        db.add(m)
    return m
