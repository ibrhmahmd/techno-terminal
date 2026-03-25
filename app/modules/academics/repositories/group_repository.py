"""
app/modules/academics/repositories/group_repository.py
───────────────────────────────────────────────────────
Repository functions for the Group entity.
"""
from typing import Sequence
from sqlmodel import Session, select
from sqlalchemy import text
from app.modules.academics.academics_models import Group
from app.modules.academics.schemas import EnrichedGroupDTO
from app.modules.academics.constants import GROUP_STATUS_ACTIVE, INSTRUCTOR_PLACEHOLDER


def create_group(session: Session, group: Group) -> Group:
    session.add(group)
    session.flush()
    return group


def list_groups_by_course(session: Session, course_id: int) -> Sequence[Group]:
    stmt = (
        select(Group)
        .where(Group.course_id == course_id)
        .where(Group.status == "active")
    )
    return session.exec(stmt).all()


def list_all_active_groups(
    session: Session, include_inactive: bool = False
) -> Sequence[Group]:
    stmt = select(Group)
    if not include_inactive:
        stmt = stmt.where(Group.status == "active")
    return session.exec(stmt).all()


def get_group_by_id(session: Session, group_id: int) -> Group | None:
    return session.get(Group, group_id)


def increment_group_level(session: Session, group_id: int) -> Group | None:
    group = session.get(Group, group_id)
    if group:
        group.level_number += 1
        session.add(group)
    return group


def get_enriched_groups(session: Session) -> list[EnrichedGroupDTO]:
    """Returns active groups joined with instructor name and course name for display."""
    stmt = text(f"""
        SELECT
            g.id,
            g.name AS group_name,
            c.name AS course_name,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.status
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON g.instructor_id = e.id
        WHERE g.status = '{GROUP_STATUS_ACTIVE}'
        ORDER BY g.id
    """)
    result = session.execute(stmt)
    return [EnrichedGroupDTO(**dict(row._mapping)) for row in result.all()]


def get_enriched_groups_by_date(session: Session, target_date: str) -> list[EnrichedGroupDTO]:
    """Returns active groups that have at least one session on the given date."""
    stmt = text(f"""
        SELECT DISTINCT
            g.id,
            g.name AS group_name,
            c.name AS course_name,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.status
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON g.instructor_id = e.id
        JOIN sessions s ON g.id = s.group_id
        WHERE g.status = '{GROUP_STATUS_ACTIVE}' AND s.session_date = :target_date
        ORDER BY g.id
    """)
    result = session.execute(stmt, {"target_date": target_date})
    return [EnrichedGroupDTO(**dict(row._mapping)) for row in result.all()]
