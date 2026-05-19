from datetime import date
from typing import Optional
from sqlmodel import Session, select
from app.modules.competitions.models.competition_models import Competition
from app.modules.competitions.schemas.team_schemas import (
    CompetitionSummaryDataDTO,
    TeamMemberWithNameDTO,
    TeamDTO,
    TeamMemberDTO,
)
from app.modules.competitions.schemas.competition_schemas import CompetitionDTO

ALLOWED_COMPETITION_UPDATES = {
    "name", "edition", "edition_year", "competition_date",
    "location", "notes", "fee_per_student",
}


# ── Competitions ──────────────────────────────────────────────────────────────

def create_competition(
    db: Session,
    name: str,
    edition: Optional[str],
    competition_date: Optional[date],
    location: Optional[str],
    notes: Optional[str],
    fee_per_student: float = 0.0,
    edition_year: Optional[int] = None,
) -> Competition:
    from app.shared.datetime_utils import utc_now
    if edition_year is None and competition_date:
        edition_year = competition_date.year
    elif edition_year is None:
        edition_year = utc_now().year

    c = Competition(
        name=name,
        edition=edition,
        edition_year=edition_year,
        competition_date=competition_date,
        location=location,
        notes=notes,
        fee_per_student=fee_per_student,
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
            if k in ALLOWED_COMPETITION_UPDATES:
                setattr(c, k, v)
        db.add(c)
        db.flush()
    return c


def delete_competition(db: Session, competition_id: int) -> bool:
    """Hard delete a competition."""
    c = db.get(Competition, competition_id)
    if c:
        db.delete(c)
        db.flush()
        return True
    return False


# ── Batch Loading (N+1 Elimination) ──────────────────────────────────────────

def get_competition_summary_data(
    db: Session, competition_id: int
) -> CompetitionSummaryDataDTO:
    """
    Batch-load all data needed for competition summary in a single query.
    Returns CompetitionSummaryDataDTO.
    """
    from app.modules.competitions.models.team_models import Team, TeamMember
    from app.modules.crm.models.student_models import Student

    comp = get_competition(db, competition_id)
    if not comp:
        return CompetitionSummaryDataDTO(competition=None, teams=[], members_by_team={})

    stmt = (
        select(Team, TeamMember, Student.full_name)
        .join(TeamMember, Team.id == TeamMember.team_id, isouter=True)
        .join(Student, TeamMember.student_id == Student.id, isouter=True)
        .where(Team.competition_id == competition_id)
        .order_by(Team.category, Team.subcategory, Team.team_name)
    )
    rows = list(db.exec(stmt).all())

    teams: list[Team] = []
    members_by_team: dict[int, list[TeamMemberWithNameDTO]] = {}
    seen_team_ids = set()

    for team, member, student_name in rows:
        if team.id not in seen_team_ids:
            teams.append(team)
            seen_team_ids.add(team.id)
        if member:
            members_by_team.setdefault(team.id, []).append(
                TeamMemberWithNameDTO(
                    member=TeamMemberDTO.model_validate(member),
                    student_name=student_name or f"Student #{member.student_id}",
                )
            )

    return CompetitionSummaryDataDTO(
        competition=CompetitionDTO.model_validate(comp),
        teams=[TeamDTO.model_validate(t) for t in teams],
        members_by_team=members_by_team,
    )
