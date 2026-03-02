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
