from datetime import time
from app.db.connection import get_session
from .models import Course, Group
from . import repository as repo

# --- Course Service ---


def add_new_course(data: dict) -> Course:
    """Validates and creates a new course."""
    if data.get("price_per_level", 0) <= 0:
        raise ValueError("Price must be greater than 0.")
    if data.get("sessions_per_level", 0) <= 0:
        raise ValueError("Sessions per level must be at least 1.")

    with get_session() as session:
        if repo.get_course_by_name(session, data["name"]):
            raise ValueError(f"Course '{data['name']}' already exists.")

        course = Course(
            name=data["name"],
            category=data.get("category"),
            description=data.get("description"),
            price_per_level=data["price_per_level"],
            sessions_per_level=data["sessions_per_level"],
        )
        return repo.create_course(session, course)


def get_active_courses() -> list[Course]:
    with get_session() as session:
        return list(repo.list_active_courses(session))


# --- Group Service ---


def schedule_group(data: dict) -> Group:
    """Validates and schedules a new group.
    Auto-generates the group name as: '{Day} {StartTime} - {CourseName}'
    """
    start_time: time = data["default_time_start"]
    end_time: time = data["default_time_end"]

    if start_time >= end_time:
        raise ValueError("Group end time must be strictly after the start time.")

    with get_session() as session:
        # Look up course name for auto-name generation
        course = session.get(Course, data["course_id"])
        if not course:
            raise ValueError(f"Course with ID {data['course_id']} not found.")

        # Format time in 12h: e.g. "2:00 PM"
        hour = start_time.hour
        minute = start_time.minute
        ampm = "PM" if hour >= 12 else "AM"
        hour_12 = hour % 12 or 12
        time_str = f"{hour_12}:{minute:02d} {ampm}"

        auto_name = f"{data['default_day']} {time_str} - {course.name}"

        group = Group(
            name=auto_name,
            course_id=data["course_id"],
            instructor_id=data["instructor_id"],
            level_number=data.get("level_number", 1),
            max_capacity=data.get("max_capacity", 15),
            default_day=data["default_day"],
            default_time_start=start_time,
            default_time_end=end_time,
        )
        return repo.create_group(session, group)


def get_groups_by_course(course_id: int) -> list[Group]:
    with get_session() as session:
        return list(repo.list_groups_by_course(session, course_id))


def get_all_active_groups() -> list[Group]:
    with get_session() as session:
        return list(repo.list_all_active_groups(session))


def get_group_by_id(group_id: int) -> Group | None:
    with get_session() as session:
        return repo.get_group_by_id(session, group_id)


# --- Session Service ---

from datetime import date, timedelta, datetime as dt
from .session_models import CourseSession

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _next_weekday(from_date: date, day_name: str) -> date:
    """Returns the next occurrence of a named weekday on or after from_date."""
    target = WEEKDAYS.index(day_name)
    current = from_date.weekday()
    delta = (target - current) % 7
    return from_date + timedelta(days=delta)


def generate_level_sessions(
    group_id: int, level_number: int, start_date: date
) -> list[CourseSession]:
    """
    Generates N weekly sessions for a group level.
    N = course.sessions_per_level. Sessions are spaced 1 week apart on the group's default_day.
    First session snaps to the next occurrence of default_day on or after start_date.
    """
    with get_session() as session:
        group = repo.get_group_by_id(session, group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found.")

        course = session.get(Course, group.course_id)
        if not course:
            raise ValueError(f"Course for group {group_id} not found.")

        existing_count = repo.count_sessions(session, group_id, level_number)
        if existing_count > 0:
            raise ValueError(
                f"Sessions for Level {level_number} already exist ({existing_count} found). "
                "Delete them first or add extra sessions instead."
            )

        # Snap start date to the correct weekday
        session_date = (
            _next_weekday(start_date, group.default_day)
            if group.default_day
            else start_date
        )

        created = []
        for i in range(course.sessions_per_level):
            cs = CourseSession(
                group_id=group_id,
                level_number=level_number,
                session_number=i + 1,
                session_date=session_date.isoformat(),
                start_time=group.default_time_start,
                end_time=group.default_time_end,
                actual_instructor_id=group.instructor_id,
                is_extra_session=False,
                created_at=dt.utcnow().isoformat(),
            )
            created.append(repo.create_session(session, cs))
            session_date += timedelta(weeks=1)

        return created


def add_extra_session(
    group_id: int, level_number: int, extra_date: date, notes: str | None = None
) -> CourseSession:
    """Adds a one-off extra session for a group level, numbered after the last existing session."""
    with get_session() as session:
        group = repo.get_group_by_id(session, group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found.")

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


def mark_substitute_instructor(session_id: int, instructor_id: int) -> CourseSession:
    with get_session() as session:
        cs = repo.update_session_instructor(session, session_id, instructor_id)
        if not cs:
            raise ValueError(f"Session {session_id} not found.")
        return cs


def list_group_sessions(
    group_id: int, level_number: int | None = None
) -> list[CourseSession]:
    with get_session() as session:
        return list(repo.list_sessions(session, group_id, level_number))
