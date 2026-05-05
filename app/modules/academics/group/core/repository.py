"""
app/modules/academics/group/core/repository.py
────────────────────────────────────────
Repository functions for the Group Core slice.
"""
from sqlmodel import Session, select
from app.modules.academics.models import Group


def create_group(session: Session, group: Group) -> Group:
    session.add(group)
    session.flush()
    return group


def get_group_by_id(session: Session, group_id: int) -> Group | None:
    return session.get(Group, group_id)


def update_group_status(session: Session, group_id: int, status: str) -> Group | None:
    group = session.get(Group, group_id)
    if group:
        group.status = status
        from app.shared.audit_utils import apply_update_audit
        apply_update_audit(group)
        session.add(group)
    return group


def increment_group_level(session: Session, group_id: int) -> Group | None:
    group = session.get(Group, group_id)
    if group:
        group.level_number += 1
        from app.shared.audit_utils import apply_update_audit
        apply_update_audit(group)
        session.add(group)
    return group
