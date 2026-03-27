from typing import Sequence
from sqlmodel import Session, select
from sqlalchemy import or_
from app.modules.crm.models import Guardian
from app.shared.audit_utils import apply_create_audit

def create_guardian(session: Session, guardian: Guardian) -> Guardian:
    session.add(guardian)
    session.flush()
    return guardian

def get_guardian_by_id(session: Session, guardian_id: int) -> Guardian | None:
    return session.get(Guardian, guardian_id)

def get_guardian_by_phone(session: Session, phone: str) -> Guardian | None:
    stmt = select(Guardian).where(Guardian.phone_primary == phone)
    return session.exec(stmt).first()

def get_all_guardians(session: Session, skip: int = 0, limit: int = 200) -> Sequence[Guardian]:
    stmt = select(Guardian).offset(skip).limit(limit)
    return session.exec(stmt).all()

def search_guardians(session: Session, query: str) -> Sequence[Guardian]:
    search_term = f"%{query}%"
    stmt = (
        select(Guardian)
        .where(
            or_(
                Guardian.full_name.ilike(search_term),
                Guardian.phone_primary.ilike(search_term),
                Guardian.phone_secondary.ilike(search_term),
            )
        )
        .limit(50)
    )
    return session.exec(stmt).all()
