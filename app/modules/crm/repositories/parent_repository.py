from typing import Optional
from sqlmodel import Session, select, func
from sqlalchemy import or_

from app.modules.crm.models import Parent
from app.modules.crm.models.link_models import StudentParent

class ParentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, parent: Parent) -> Parent:
        self._session.add(parent)
        self._session.flush()
        return parent

    def get_by_id(self, parent_id: int) -> Optional[Parent]:
        return self._session.get(Parent, parent_id)

    @staticmethod
    def _matches(query: Optional[str]):
        """Name/phone filter for a search term; None lists every parent."""
        if not query:
            return None
        term = f"%{query}%"
        return or_(
            Parent.full_name.ilike(term),
            Parent.phone_primary.ilike(term),
            Parent.phone_secondary.ilike(term),
        )

    def list_page(self, query: Optional[str], skip: int, limit: int) -> list[Parent]:
        """One page of parents, optionally filtered; stable order so pages do not overlap (#53)."""
        stmt = select(Parent)
        where = self._matches(query)
        if where is not None:
            stmt = stmt.where(where)
        stmt = stmt.order_by(Parent.full_name, Parent.id).offset(skip).limit(limit)
        return list(self._session.exec(stmt).all())

    def count(self, query: Optional[str] = None) -> int:
        stmt = select(func.count()).select_from(Parent)
        where = self._matches(query)
        if where is not None:
            stmt = stmt.where(where)
        return self._session.exec(stmt).one()

    def delete(self, parent_id: int) -> Optional[Parent]:
        parent = self._session.get(Parent, parent_id)
        if parent:
            self._session.delete(parent)
            self._session.flush()
        return parent

    def get_parent_students(self, parent_id: int) -> list[StudentParent]:
        """Get all student links for a parent."""
        stmt = select(StudentParent).where(StudentParent.parent_id == parent_id)
        return list(self._session.exec(stmt).all())