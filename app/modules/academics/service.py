from datetime import time, date, timedelta, datetime as dt
from app.db.connection import get_session
from app.modules.academics.models import Course, Group
from app.modules.academics.session_models import CourseSession
from app.shared.exceptions import ValidationError, NotFoundError, BusinessRuleError, ConflictError
from app.shared.validators import validate_positive_amount
from . import repository as repo

# ── Time constraints ──────────────────────────────────────────────────────────
_EARLIEST = time(11, 0)  # 11:00 AM
_LATEST = time(21, 0)  # 9:00 PM

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# ── Helpers ───────────────────────────────────────────────────────────────────


def _fmt_12h(t: time) -> str:
    h12 = t.hour % 12 or 12
    ampm = "PM" if t.hour >= 12 else "AM"
    return f"{h12}:{t.minute:02d} {ampm}"


def _next_weekday(from_date: date, day_name: str) -> date:
    target = WEEKDAYS.index(day_name)
    delta = (target - from_date.weekday()) % 7
    return from_date + timedelta(days=delta)


def _validate_times(start_time: time, end_time: time) -> None:
    if start_time < _EARLIEST or end_time > _LATEST:
        raise ValidationError(
            f"Groups must be scheduled between 11:00 AM and 9:00 PM. "
            f"Got {_fmt_12h(start_time)} – {_fmt_12h(end_time)}."
        )
    if start_time >= end_time:
        raise ValidationError("End time must be after start time.")


# ── Course Service ────────────────────────────────────────────────────────────


def add_new_course(data: dict) -> Course:
    """Validates and creates a new course."""
    validate_positive_amount(data.get("price_per_level", 0), field="price per level")
    if data.get("sessions_per_level", 0) <= 0:
        raise ValidationError("Sessions per level must be at least 1.")

    with get_session() as session:
        if repo.get_course_by_name(session, data["name"]):
            raise ConflictError(f"Course '{data['name']}' already exists.")

        course = Course(
            name=data["name"],
            category=data.get("category"),
            description=data.get("description"),
            price_per_level=data["price_per_level"],
            sessions_per_level=data["sessions_per_level"],
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


def get_active_courses() -> list[Course]:
    with get_session() as session:
        return list(repo.list_active_courses(session))


# ── Group Service ─────────────────────────────────────────────────────────────


def schedule_group(data: dict) -> tuple[Group, list[CourseSession]]:
    """
    Creates a group, auto-generates its name, validates time window (11AM-9PM),
    and immediately generates the first level sessions starting from today.
    Returns (group, sessions).
    """
    start_time: time = data["default_time_start"]
    end_time: time = data["default_time_end"]

    _validate_times(start_time, end_time)

    with get_session() as session:
        course = session.get(Course, data["course_id"])
        if not course:
            raise NotFoundError(f"Course with ID {data['course_id']} not found.")

        auto_name = f"{data['default_day']} {_fmt_12h(start_time)} - {course.name}"

        group = Group(
            name=auto_name,
            course_id=data["course_id"],
            instructor_id=data["instructor_id"],
            level_number=1,
            max_capacity=data.get("max_capacity", 15),
            default_day=data["default_day"],
            default_time_start=start_time,
            default_time_end=end_time,
        )
        created_group = repo.create_group(session, group)
        group_id = created_group.id
        sessions_per_level = course.sessions_per_level
        instructor_id = created_group.instructor_id

    # Auto-generate level 1 sessions in a fresh session so the group is committed
    start_date = (
        _next_weekday(date.today(), data["default_day"])
        if data.get("default_day")
        else date.today()
    )
    sessions = _create_sessions(
        group_id, 1, start_date, sessions_per_level, start_time, end_time, instructor_id
    )

    # Refresh group object
    with get_session() as session:
        group_obj = repo.get_group_by_id(session, group_id)

    return group_obj, sessions


def _create_sessions(
    group_id, level_number, start_date, count, start_time, end_time, instructor_id
):
    created = []
    session_date = start_date
    with get_session() as session:
        for i in range(count):
            cs = CourseSession(
                group_id=group_id,
                level_number=level_number,
                session_number=i + 1,
                session_date=session_date.isoformat(),
                start_time=start_time,
                end_time=end_time,
                actual_instructor_id=instructor_id,
                is_extra_session=False,
                created_at=dt.utcnow().isoformat(),
            )
            created.append(repo.create_session(session, cs))
            session_date += timedelta(weeks=1)
    return created


def get_groups_by_course(course_id: int) -> list[Group]:
    with get_session() as session:
        return list(repo.list_groups_by_course(session, course_id))


def get_all_active_groups(include_inactive: bool = False) -> list[Group]:
    with get_session() as session:
        return list(repo.list_all_active_groups(session, include_inactive))


def get_all_active_groups_enriched() -> list[dict]:
    """Returns groups with instructor_name and course_name joined for display."""
    with get_session() as session:
        return repo.get_enriched_groups(session)


def get_todays_groups_enriched() -> list[dict]:
    """Returns active groups that have at least one session scheduled for today."""
    with get_session() as session:
        return repo.get_enriched_groups_by_date(session, date.today().isoformat())


def get_group_by_id(group_id: int) -> Group | None:
    with get_session() as session:
        return repo.get_group_by_id(session, group_id)


# ── Session Service ───────────────────────────────────────────────────────────


def generate_level_sessions(
    group_id: int, level_number: int, start_date: date
) -> list[CourseSession]:
    """
    Generates N weekly sessions for a group level.
    Raises if sessions for this level already exist.
    """
    with get_session() as session:
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
            _next_weekday(start_date, group.default_day)
            if group.default_day
            else start_date
        )
        instructor_id = group.instructor_id
        sessions_per_level = course.sessions_per_level
        start_t = group.default_time_start
        end_t = group.default_time_end

    return _create_sessions(
        group_id,
        level_number,
        snapped,
        sessions_per_level,
        start_t,
        end_t,
        instructor_id,
    )


def add_extra_session(
    group_id: int, level_number: int, extra_date: date, notes: str | None = None
) -> CourseSession:
    """Adds an extra session numbered after the last existing session."""
    with get_session() as session:
        group = repo.get_group_by_id(session, group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        all_sessions = repo.list_sessions(session, group_id, level_number)
        next_num = max((s.session_number for s in all_sessions), default=0) + 1

        cs = CourseSession(
            group_id=group_id,
            level_number=level_number,
            session_number=next_num,
            session_date=extra_date.isoformat(),
            start_time=group.default_time_start,
            end_time=group.default_time_end,
            actual_instructor_id=group.instructor_id,
            is_extra_session=True,
            notes=notes,
            created_at=dt.utcnow().isoformat(),
        )
        return repo.create_session(session, cs)


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
    """Returns True if all regular sessions for the level exist (used to trigger level increment)."""
    with get_session() as session:
        group = repo.get_group_by_id(session, group_id)
        if not group:
            return False
        course = session.get(Course, group.course_id)
        if not course:
            return False
        count = repo.count_sessions(session, group_id, level_number)
        return count >= course.sessions_per_level


def advance_group_level(group_id: int) -> Group:
    """Increments group.level_number. Call after a level is confirmed complete."""
    with get_session() as session:
        group = repo.increment_group_level(session, group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        return group
