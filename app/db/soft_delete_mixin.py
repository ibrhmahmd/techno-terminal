"""
app/db/soft_delete_mixin.py
─────────────────────────
Soft delete mixin for SQLModel repositories.
Provides standardized soft-delete operations.
"""
from datetime import datetime
from typing import TypeVar, Generic, List
from sqlmodel import SQLModel, select, Session

T = TypeVar("T", bound=SQLModel)


class SoftDeleteMixin(Generic[T]):
    """
    Mixin to add soft-delete capabilities to any repository.
    Assumes model has: deleted_at, deleted_by fields.
    """

    def __init__(self, session: Session):
        self._session = session

    def soft_delete(
        self,
        model_class: type[T],
        record_id: int,
        deleted_by: int
    ) -> bool:
        """Marks record as deleted without removing from database."""
        record = self._session.get(model_class, record_id)
        if not record or getattr(record, 'deleted_at', None) is not None:
            return False

        record.deleted_at = datetime.utcnow()
        record.deleted_by = deleted_by
        self._session.add(record)
        self._session.flush()
        return True

    def restore(self, model_class: type[T], record_id: int) -> bool:
        """Restores a soft-deleted record."""
        record = self._session.get(model_class, record_id)
        if not record or getattr(record, 'deleted_at', None) is None:
            return False

        record.deleted_at = None
        record.deleted_by = None
        self._session.add(record)
        self._session.flush()
        return True

    def hard_delete(self, model_class: type[T], record_id: int) -> bool:
        """Permanently removes record (admin-only)."""
        record = self._session.get(model_class, record_id)
        if not record:
            return False
        self._session.delete(record)
        self._session.flush()
        return True

    def get_active(
        self,
        model_class: type[T],
        limit: int = 100,
        offset: int = 0
    ) -> List[T]:
        """Get non-deleted records only."""
        stmt = select(model_class).where(
            getattr(model_class, 'deleted_at').is_(None)
        ).offset(offset).limit(limit)
        return list(self._session.exec(stmt).all())

    def get_deleted(
        self,
        model_class: type[T],
        limit: int = 100,
        offset: int = 0
    ) -> List[T]:
        """Get soft-deleted records (for admin recovery)."""
        stmt = select(model_class).where(
            getattr(model_class, 'deleted_at').is_not(None)
        ).order_by(getattr(model_class, 'deleted_at').desc())
        return list(self._session.exec(stmt).all())
