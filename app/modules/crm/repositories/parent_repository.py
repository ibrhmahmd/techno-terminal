from typing import Sequence
from sqlmodel import Session, select
from sqlalchemy import or_
from app.modules.crm.models import Parent
from app.shared.audit_utils import apply_create_audit

def create_parent(session: Session, parent: Parent) -> Parent:
    session.add(parent)
    session.flush()
    return parent

def get_parent_by_id(session: Session, parent_id: int) -> Parent | None:
    return session.get(Parent, parent_id)

def get_parent_by_phone(session: Session, phone: str) -> Parent | None:
    stmt = select(Parent).where(Parent.phone_primary == phone)
    return session.exec(stmt).first()

def get_all_parents(session: Session, skip: int = 0, limit: int = 200) -> Sequence[Parent]:
    stmt = select(Parent).offset(skip).limit(limit)
    return session.exec(stmt).all()

def search_parents(session: Session, query: str) -> Sequence[Parent]:
    search_term = f"%{query}%"
    stmt = (
        select(Parent)
        .where(
            or_(
                Parent.full_name.ilike(search_term),
                Parent.phone_primary.ilike(search_term),
                Parent.phone_secondary.ilike(search_term),
            )
        )
        .limit(50)
    )
    return session.exec(stmt).all()


def count_parents(session: Session) -> int:
    """Returns total count of parents for pagination."""
    stmt = select(Parent)
    return len(session.exec(stmt).all())

    
def delete_parent(session: Session, parent_id: int) -> Parent | None:
    """Deletes a parent by ID."""
    parent = session.get(Parent, parent_id)
    if parent:
        session.delete(parent)
        session.commit()
    return parent