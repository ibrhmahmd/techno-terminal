from typing import Optional, Sequence
from sqlmodel import Session, select, func
from sqlalchemy import or_

from app.modules.crm.interfaces import IParentRepository
from app.modules.crm.models import Parent

class ParentRepository(IParentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, parent: Parent) -> Parent:
        self._session.add(parent)
        self._session.flush()
        return parent

    def get_by_id(self, parent_id: int) -> Optional[Parent]:
        return self._session.get(Parent, parent_id)

    def get_by_phone(self, phone: str) -> Optional[Parent]:
        stmt = select(Parent).where(Parent.phone_primary == phone)
        return self._session.exec(stmt).first()

    def get_all(self, skip: int, limit: int) -> list[Parent]:
        stmt = select(Parent).offset(skip).limit(limit)
        return list(self._session.exec(stmt).all())

    def search(self, query: str) -> list[Parent]:
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
        return list(self._session.exec(stmt).all())

    def count(self) -> int:
        return self._session.exec(
            select(func.count()).select_from(Parent)
        ).one()

    def update(self, parent_id: int, data: dict) -> Optional[Parent]:
        parent = self._session.get(Parent, parent_id)
        if not parent:
            return None
        for key, value in data.items():
            if hasattr(parent, key):
                setattr(parent, key, value)
        self._session.add(parent)
        self._session.flush()
        return parent

    def delete(self, parent_id: int) -> Optional[Parent]:
        parent = self._session.get(Parent, parent_id)
        if parent:
            self._session.delete(parent)
            self._session.flush()
        return parent