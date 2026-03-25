from datetime import date
from sqlmodel import Session
from app.db.connection import get_session
from app.shared.audit_utils import apply_update_audit
from app.shared.datetime_utils import utc_now
from app.modules.academics.academics_models import Course, Group
from app.modules.academics.academics_session_models import CourseSession
from app.modules.academics.schemas import (
    AddNewCourseInput, ScheduleGroupInput,
    UpdateCourseDTO, UpdateGroupDTO, UpdateSessionDTO,
    CourseStatsDTO, EnrichedGroupDTO,
)
from app.modules.academics.helpers.time_helpers import fmt_12h, next_weekday, validate_times
from app.modules.academics.helpers.session_planning import create_sessions_in_session
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError
from app.shared.validators import validate_positive_amount
from . import repositories as repo

# ── Course Service ────────────────────────────────────────────────────────────


def add_new_course(data: AddNewCourseInput) -> Course:
    """Validates and creates a new course."""
    with get_session() as session:
        if repo.get_course_by_name(session, data.name):
            raise ConflictError(f"Course '{data.name}' already exists.")

        course = Course(
            name=data.name,
            category=data.category,
            description=data.description,
            price_per_level=data.price_per_level,
            sessions_per_level=data.sessions_per_level,
        )
        return repo.create_course(session, course)


def update_course_price(course_id: int, new_price: float) -> Course:
    """Updates the price per level for an existing course."""
    validate_positive_amount(new_price, field="price")
    with get_session() as session:
        course = repo.update_course_price(session, course_id, new_price)
        if not course:
            raise NotFoundError(f"Course {course_id} not found.")
        return course


def update_course(course_id: int, data: UpdateCourseDTO) -> Course:
    with get_session() as session:
        course = session.get(Course, course_id)
        if not course:
            raise NotFoundError(f"Course {course_id} not found.")
        for k, v in data.model_dump(exclude_unset=True).items():
            if hasattr(course, k) and k != "id":
                setattr(course, k, v)
        apply_update_audit(course)
        session.add(course)
        session.commit()
        session.refresh(course)
        return course


def get_active_courses() -> list[Course]:
    with get_session() as session:
        return list(repo.list_active_courses(session))


def get_all_course_stats() -> list[CourseStatsDTO]:
    """
    Returns aggregate stats (group + student counts) for ALL courses.
    Backed by the v_course_stats view — single DB query, no N+1.
    Used by the course overview table.
    """
    with get_session() as session:
        return repo.get_all_course_stats(session)


def get_course_stats(course_id: int) -> CourseStatsDTO | None:
    """
    Returns aggregate stats for a single course from v_course_stats.
    Returns None if the course does not exist.
    Used by the course detail page.
    """
    with get_session() as session:
        return repo.get_course_stats(session, course_id)


# ── Group Service ─────────────────────────────────────────────────────────────


# _create_sessions_in_session has been moved to helpers/session_planning.py
# Use: from app.modules.academics.helpers.session_planning import create_sessions_in_session


def schedule_group(data: ScheduleGroupInput) -> tuple[Group, list[CourseSession]]:
    """
    Creates a group, auto-generates its name, validates time window (11AM-9PM),
    and immediately generates the first level sessions starting from today.
    Returns (group, sessions).
    ATOMIC — group + sessions commit together or not at all.
    """
    validate_times(data.default_time_start, data.default_time_end)

    with get_session() as session:                          # ← ONE session
        course = session.get(Course, data.course_id)
        if not course:
            raise NotFoundError(f"Course with ID {data.course_id} not found.")

        auto_name = (
            f"{data.default_day} "
            f"{fmt_12h(data.default_time_start)} - {course.name}"
        )
        group = Group(
            name=auto_name,
            course_id=data.course_id,
            instructor_id=data.instructor_id,
            level_number=1,
            max_capacity=data.max_capacity,
            default_day=data.default_day,
            default_time_start=data.default_time_start,
            default_time_end=data.default_time_end,
        )
        session.add(group)
        session.flush()                                     # get group.id without commit

        start_date = (
            next_weekday(date.today(), data.default_day)
            if data.default_day else date.today()
        )
        sessions = create_sessions_in_session(            # ← SAME session
            session, group.id, 1, start_date,
            course.sessions_per_level,
            data.default_time_start, data.default_time_end,
            group.instructor_id,
        )
        return group, sessions
    # ← SINGLE COMMIT — group + sessions or nothing


def get_groups_by_course(course_id: int) -> list[Group]:
    with get_session() as session:
        return list(repo.list_groups_by_course(session, course_id))


def get_all_active_groups(include_inactive: bool = False) -> list[Group]:
    with get_session() as session:
        return list(repo.list_all_active_groups(session, include_inactive))


def get_all_active_groups_enriched() -> list[EnrichedGroupDTO]:
    """Returns groups with instructor_name and course_name joined for display."""
    with get_session() as session:
        return repo.get_enriched_groups(session)


def get_todays_groups_enriched() -> list[EnrichedGroupDTO]:
    """Returns active groups that have at least one session scheduled for today."""
    with get_session() as session:
        return repo.get_enriched_groups_by_date(session, date.today().isoformat())


def get_group_by_id(group_id: int) -> Group | None:
    with get_session() as session:
        return repo.get_group_by_id(session, group_id)


def update_group(group_id: int, data: UpdateGroupDTO) -> Group:
    with get_session() as session:
        group = repo.get_group_by_id(session, group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        for k, v in data.model_dump(exclude_unset=True).items():
            if hasattr(group, k) and k != "id":
                setattr(group, k, v)
        apply_update_audit(group)
        session.add(group)
        session.commit()
        session.refresh(group)
        return group


# ── Session Service ───────────────────────────────────────────────────────────


def generate_level_sessions(
    group_id: int, level_number: int, start_date: date
) -> list[CourseSession]:
    """
    Generates N weekly sessions for a group level.
    Raises if sessions for this level already exist.
    ATOMIC — validation + session creation in one transaction.
    """
    with get_session() as session:                          # ← ONE session
        group = repo.get_group_by_id(session, group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        course = session.get(Course, group.course_id)
        if not course:
            raise NotFoundError(f"Course for group {group_id} not found.")

        existing = repo.count_sessions(session, group_id, level_number)
        if existing > 0:
            raise BusinessRuleError(
                f"Level {level_number} already has {existing} session(s). "
                "Remove them first or add extra sessions instead."
            )

        snapped = (
            next_weekday(start_date, group.default_day)
            if group.default_day else start_date
        )
        return create_sessions_in_session(                # ← SAME session
            session, group_id, level_number, snapped,
            course.sessions_per_level,
            group.default_time_start, group.default_time_end,
            group.instructor_id,
        )
    # ← SINGLE COMMIT — validation + sessions or nothing


def add_extra_session(
    group_id: int, level_number: int, extra_date: date, notes: str | None = None
) -> CourseSession:
    """
    Adds an extra session numbered after the last existing session.
    ATOMIC — session_number is calculated and the new row is inserted in the
    same transaction, eliminating the race condition that previously allowed
    two concurrent requests to compute the same next number.
    """
    with get_session() as session:
        group = repo.get_group_by_id(session, group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")

        # Atomic: read max session_number from DB within the same transaction
        next_num = repo.get_max_session_number(session, group_id, level_number) + 1

        cs = CourseSession(
            group_id=group_id,
            level_number=level_number,
            session_number=next_num,
            session_date=extra_date,
            start_time=group.default_time_start,
            end_time=group.default_time_end,
            actual_instructor_id=group.instructor_id,
            is_extra_session=True,
            notes=notes,
            created_at=utc_now(),
        )
        return repo.create_session(session, cs)
    # ← SINGLE COMMIT — number read + row inserted atomically


def update_session(session_id: int, data: UpdateSessionDTO) -> CourseSession:
    with get_session() as session:
        cs = session.get(CourseSession, session_id)
        if not cs:
            raise NotFoundError(f"Session {session_id} not found.")
        for k, v in data.model_dump(exclude_unset=True).items():
            if hasattr(cs, k) and k != "id":
                setattr(cs, k, v)
        apply_update_audit(cs)
        session.add(cs)
        session.commit()
        session.refresh(cs)
        return cs


def delete_session(session_id: int) -> bool:
    with get_session() as session:
        return repo.delete_session(session, session_id)


def mark_substitute_instructor(session_id: int, instructor_id: int) -> CourseSession:
    with get_session() as session:
        cs = repo.update_session_instructor(session, session_id, instructor_id)
        if not cs:
            raise NotFoundError(f"Session {session_id} not found.")
        return cs


def list_group_sessions(
    group_id: int, level_number: int | None = None
) -> list[CourseSession]:
    with get_session() as session:
        return list(repo.list_sessions(session, group_id, level_number))


def check_level_complete(group_id: int, level_number: int) -> bool:
    """
    Returns True if all regular sessions for the level exist.
    Raises NotFoundError on missing group or course — never silently returns
    False for data integrity issues. False is reserved for 'level genuinely
    not yet complete'.
    """
    with get_session() as session:
        group = repo.get_group_by_id(session, group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        course = session.get(Course, group.course_id)
        if not course:
            raise NotFoundError(
                f"Course {group.course_id} for group {group_id} not found. "
                "Data integrity issue — verify the groups table."
            )
        count = repo.count_sessions(session, group_id, level_number)
        return count >= course.sessions_per_level


def advance_group_level(group_id: int) -> Group:
    """Increments group.level_number. Call after a level is confirmed complete."""
    with get_session() as session:
        group = repo.increment_group_level(session, group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        return group
