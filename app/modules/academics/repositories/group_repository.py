"""
app/modules/academics/repositories/group_repository.py
────────────────────────────────────────
Repository functions for the Group Core slice.
"""
from sqlmodel import Session
from app.modules.academics.models import Group
from app.shared.audit_utils import apply_update_audit


class GroupRepository:
    """Repository for Group data access.

    Session is injected via constructor — never acquired internally.
    Only flush(), never commit().
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_group(self, group: Group) -> Group:
        self._session.add(group)
        self._session.flush()
        return group

    def get_group_by_id(self, group_id: int) -> Group | None:
        return self._session.get(Group, group_id)

    def update_group_status(self, group_id: int, status: str) -> Group | None:
        group = self._session.get(Group, group_id)
        if group:
            group.status = status
            apply_update_audit(group)
            self._session.add(group)
        return group

    def increment_group_level(self, group_id: int) -> Group | None:
        group = self._session.get(Group, group_id)
        if group:
            group.level_number += 1
            apply_update_audit(group)
            self._session.add(group)
        return group