from datetime import date
from typing import Optional
from sqlmodel import Session, select
from app.shared.datetime_utils import utc_now
from app.modules.competitions.models.competition_models import Competition


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
    # Auto-calculate edition_year from competition_date if not provided
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


def list_competitions(db: Session, include_deleted: bool = False) -> list[Competition]:
    stmt = select(Competition)
    if not include_deleted:
        stmt = stmt.where(Competition.deleted_at.is_(None))
    stmt = stmt.order_by(Competition.competition_date.desc())
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


def delete_competition(db: Session, competition_id: int, deleted_by: Optional[int] = None) -> bool:
    """Soft delete a competition."""
    c = db.get(Competition, competition_id)
    if c:
        c.deleted_at = utc_now()
        c.deleted_by = deleted_by
        db.add(c)
        db.flush()
        return True
    return False


def restore_competition(db: Session, competition_id: int) -> bool:
    """Restore a soft-deleted competition."""
    c = db.get(Competition, competition_id)
    if c:
        c.deleted_at = None
        c.deleted_by = None
        db.add(c)
        db.flush()
        return True
    return False


def list_deleted_competitions(db: Session) -> list[Competition]:
    """List all soft-deleted competitions."""
    stmt = select(Competition).where(Competition.deleted_at.is_not(None))
    return list(db.exec(stmt).all())
