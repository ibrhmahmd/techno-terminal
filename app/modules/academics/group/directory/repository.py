"""
app/modules/academics/group/directory/repository.py
────────────────────────────────────────
Repository functions for the Group Directory slice.
"""
from typing import Any, Sequence
from sqlmodel import Session, select, func
from sqlalchemy import text
from app.modules.academics.models import Group
from app.modules.academics.group.core.schemas import EnrichedGroupDTO
from app.modules.academics.group.directory.schemas import GroupFilterDTO
from app.modules.academics.constants import (
    GROUP_STATUS_ACTIVE, INSTRUCTOR_PLACEHOLDER,
    ENROLLMENT_STATUS_ACTIVE,
)


def list_all_active_groups(
    session: Session, include_inactive: bool = False
) -> Sequence[Group]:
    stmt = select(Group)
    if not include_inactive:
        stmt = stmt.where(Group.status == GROUP_STATUS_ACTIVE)
    return session.exec(stmt).all()


def get_enriched_group_by_id(session: Session, group_id: int) -> EnrichedGroupDTO | None:
    """Returns a single enriched group by ID."""
    stmt = text(f"""
        SELECT
            g.id,
            g.name AS group_name,
            g.course_id,
            c.name AS course_name,
            g.instructor_id,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.notes,
            g.status,
            (
                SELECT COUNT(*) 
                FROM enrollments e2 
                WHERE e2.group_id = g.id 
                AND e2.level_number = g.level_number 
                AND e2.status = '{ENROLLMENT_STATUS_ACTIVE}'
            ) AS current_student_count
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON g.instructor_id = e.id
        WHERE g.id = :group_id
    """)
    result = session.execute(stmt, {"group_id": group_id}).fetchone()
    if not result:
        return None
    return EnrichedGroupDTO(**result._asdict())

def get_enriched_groups(session: Session) -> list[EnrichedGroupDTO]:
    """Returns active groups joined with instructor name and course name for display."""
    stmt = text(f"""
        SELECT
            g.id,
            g.name AS group_name,
            g.course_id,
            c.name AS course_name,
            g.instructor_id,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.notes,
            g.status,
            (
                SELECT COUNT(*) 
                FROM enrollments e2 
                WHERE e2.group_id = g.id 
                AND e2.level_number = g.level_number 
                AND e2.status = '{ENROLLMENT_STATUS_ACTIVE}'
            ) AS current_student_count
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
            g.course_id,
            c.name AS course_name,
            g.instructor_id,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.notes,
            g.status,
            (
                SELECT COUNT(*) 
                FROM enrollments e2 
                WHERE e2.group_id = g.id 
                AND e2.level_number = g.level_number 
                AND e2.status = '{ENROLLMENT_STATUS_ACTIVE}'
            ) AS current_student_count
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON g.instructor_id = e.id
        JOIN sessions s ON g.id = s.group_id
        WHERE g.status = '{GROUP_STATUS_ACTIVE}' AND s.session_date = :target_date
        ORDER BY g.id
    """)
    result = session.execute(stmt, {"target_date": target_date})
    return [EnrichedGroupDTO(**dict(row._mapping)) for row in result.all()]


def get_transfer_options(
    session: Session, exclude_group_id: int
) -> Sequence[Group]:
    """Returns active groups excluding the specified group (for transfer options)."""
    stmt = select(Group).where(
        Group.status == GROUP_STATUS_ACTIVE,
        Group.id != exclude_group_id
    )
    return session.exec(stmt).all()







def filter_groups_query(
    session: Session,
    filters: GroupFilterDTO,
) -> tuple[list[EnrichedGroupDTO], int]:
    """Dynamic multi-criteria filter query for groups.

    Builds a parameterized SQL query against the enriched groups view
    (groups JOIN courses JOIN employees LEFT JOIN sessions) with
    dynamic WHERE clauses appended for each non-None filter field.

    Returns:
        (list[EnrichedGroupDTO], total_count)
    """
    params: dict[str, Any] = {}
    where_clauses: list[str] = []

    # ── Free-text search ─────────────────────────────────────────────────────
    # OR across: group name, course name, instructor name, notes, schedule time,
    # and enrolled student names (via subquery).
    if filters.q is not None:
        params["q"] = f"%{filters.q}%"
        where_clauses.append("""
            (
                g.name ILIKE :q
                OR c.name ILIKE :q
                OR COALESCE(e.full_name, '') ILIKE :q
                OR COALESCE(g.notes, '') ILIKE :q
                OR CAST(g.default_time_start AS TEXT) ILIKE :q
                OR CAST(g.default_day AS TEXT) ILIKE :q
                OR EXISTS (
                    SELECT 1 FROM enrollments enr
                    JOIN students st ON enr.student_id = st.id
                    WHERE enr.group_id = g.id
                      AND enr.status = 'active'
                      AND st.full_name ILIKE :q
                )
            )
        """)

    # ── Group name (exact substring) ─────────────────────────────────────────
    if filters.name is not None:
        params["name"] = f"%{filters.name}%"
        where_clauses.append("g.name ILIKE :name")

    # ── Course filter ─────────────────────────────────────────────────────────
    if filters.course_ids:
        params["course_ids"] = list(filters.course_ids)
        where_clauses.append("g.course_id = ANY(:course_ids)")

    if filters.course_name is not None:
        params["course_name"] = f"%{filters.course_name}%"
        where_clauses.append("c.name ILIKE :course_name")

    # ── Day of week ───────────────────────────────────────────────────────────
    # Caller must normalize abbreviations to full names before calling.
    if filters.day:
        params["day"] = list(filters.day)
        where_clauses.append("g.default_day = ANY(:day)")

    # ── Instructor filters ────────────────────────────────────────────────────
    if filters.instructor_id is not None:
        params["instructor_id"] = filters.instructor_id
        where_clauses.append("g.instructor_id = :instructor_id")

    if filters.instructor_name is not None:
        params["instructor_name"] = f"%{filters.instructor_name}%"
        where_clauses.append("COALESCE(e.full_name, '') ILIKE :instructor_name")

    # ── Level number ──────────────────────────────────────────────────────────
    if filters.level_number is not None:
        params["level_number"] = filters.level_number
        where_clauses.append("g.level_number = :level_number")

    # ── Status ────────────────────────────────────────────────────────────────
    if filters.status:
        params["status"] = list(filters.status)
        where_clauses.append("g.status = ANY(:status)")
    else:
        if filters.include_inactive:
            params["default_status"] = ["active", "inactive"]
            where_clauses.append("g.status = ANY(:default_status)")
        else:
            params["default_status"] = "active"
            where_clauses.append("g.status = :default_status")

    # ── Instructor presence ───────────────────────────────────────────────────
    if filters.has_instructor is not None:
        if filters.has_instructor:
            where_clauses.append("g.instructor_id IS NOT NULL")
        else:
            where_clauses.append("g.instructor_id IS NULL")

    # ── Capacity ──────────────────────────────────────────────────────────────
    if filters.max_capacity_min is not None:
        params["max_capacity_min"] = filters.max_capacity_min
        where_clauses.append("g.max_capacity >= :max_capacity_min")

    if filters.max_capacity_max is not None:
        params["max_capacity_max"] = filters.max_capacity_max
        where_clauses.append("g.max_capacity <= :max_capacity_max")

    # ── Price range (courses.price_per_level) ─────────────────────────────────
    if filters.price_min is not None:
        params["price_min"] = filters.price_min
        where_clauses.append("c.price_per_level >= :price_min")

    if filters.price_max is not None:
        params["price_max"] = filters.price_max
        where_clauses.append("c.price_per_level <= :price_max")

    # ── Session date range ────────────────────────────────────────────────────
    if filters.start_date_from is not None:
        params["start_date_from"] = filters.start_date_from
        where_clauses.append("""
            EXISTS (
                SELECT 1 FROM sessions s2
                WHERE s2.group_id = g.id
                  AND s2.session_date >= :start_date_from
            )
        """)

    if filters.start_date_to is not None:
        params["start_date_to"] = filters.start_date_to
        where_clauses.append("""
            EXISTS (
                SELECT 1 FROM sessions s2
                WHERE s2.group_id = g.id
                  AND s2.session_date <= :start_date_to
            )
        """)

    # ── Default schedule time range ───────────────────────────────────────────
    if filters.time_from is not None:
        params["time_from"] = filters.time_from
        where_clauses.append("g.default_time_start >= :time_from")

    if filters.time_to is not None:
        params["time_to"] = filters.time_to
        where_clauses.append("g.default_time_start <= :time_to")

    # ── Session number filters ────────────────────────────────────────────────
    if filters.current_session_number is not None:
        params["current_session_number"] = filters.current_session_number
        where_clauses.append("""
            EXISTS (
                SELECT 1 FROM sessions s2
                WHERE s2.group_id = g.id
                  AND s2.session_number = :current_session_number
                  AND s2.level_number = g.level_number
            )
        """)

    if filters.session_number_from is not None:
        params["session_number_from"] = filters.session_number_from
        where_clauses.append("""
            EXISTS (
                SELECT 1 FROM sessions s2
                WHERE s2.group_id = g.id
                  AND s2.level_number = g.level_number
                  AND s2.session_number >= :session_number_from
            )
        """)

    if filters.session_number_to is not None:
        params["session_number_to"] = filters.session_number_to
        where_clauses.append("""
            EXISTS (
                SELECT 1 FROM sessions s2
                WHERE s2.group_id = g.id
                  AND s2.level_number = g.level_number
                  AND s2.session_number <= :session_number_to
            )
        """)

    # ── Build WHERE clause ────────────────────────────────────────────────────
    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # ── Sort clause ───────────────────────────────────────────────────────────
    order_direction = "DESC" if filters.sort_order == "desc" else "ASC"
    if filters.sort_by == "day":
        # Inline CASE maps day names to the Arabic/Islamic week order (Friday=0).
        order_sql = f"""
            CASE g.default_day
                WHEN 'Friday'    THEN 0
                WHEN 'Saturday'  THEN 1
                WHEN 'Sunday'    THEN 2
                WHEN 'Monday'    THEN 3
                WHEN 'Tuesday'   THEN 4
                WHEN 'Wednesday' THEN 5
                WHEN 'Thursday'  THEN 6
                ELSE 99
            END {order_direction}
        """
    elif filters.sort_by == "status":
        order_sql = f"g.status {order_direction}"
    else:  # default: name
        order_sql = f"g.name {order_direction}"

    # ── Base SELECT (same shape as get_enriched_groups) ───────────────────────
    base_select = f"""
        SELECT
            g.id,
            g.name AS group_name,
            g.course_id,
            c.name AS course_name,
            g.instructor_id,
            COALESCE(e.full_name, '{INSTRUCTOR_PLACEHOLDER}') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.notes,
            g.status,
            (
                SELECT COUNT(*)
                FROM enrollments e2
                WHERE e2.group_id = g.id
                  AND e2.level_number = g.level_number
                  AND e2.status = '{ENROLLMENT_STATUS_ACTIVE}'
            ) AS current_student_count
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON g.instructor_id = e.id
    """

    # ── Count query ───────────────────────────────────────────────────────────
    count_sql = f"""
        SELECT COUNT(*) FROM (
            {base_select}
            {where_sql}
        ) AS _sub
    """
    total: int = session.execute(text(count_sql), params).scalar_one()

    # ── Paginated data query ──────────────────────────────────────────────────
    params["limit"] = filters.limit
    params["skip"] = filters.skip
    data_sql = f"""
        {base_select}
        {where_sql}
        ORDER BY {order_sql}
        LIMIT :limit OFFSET :skip
    """
    result = session.execute(text(data_sql), params)
    rows = [EnrichedGroupDTO(**dict(row._mapping)) for row in result.all()]

    return rows, total
