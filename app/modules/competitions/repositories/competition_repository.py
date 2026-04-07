from datetime import date
from typing import Optional
from sqlmodel import Session, select
from app.shared.datetime_utils import utc_now
from app.modules.competitions.models.competition_models import (
    Competition,
    CompetitionCategory,
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
