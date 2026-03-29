from .parent_repository import (
    create_parent,
    get_parent_by_id,
    get_parent_by_phone,
    get_all_parents,
    search_parents,
)
from .student_repository import (
    create_student,
    get_student_by_id,
    get_all_students,
    search_students,
    get_student_parents,
    link_parent,
    get_siblings,
    get_students_by_parent_id,
)

__all__ = [
    "create_parent", "get_parent_by_id", "get_parent_by_phone", "get_all_parents", "search_parents",
    "create_student", "get_student_by_id", "get_all_students", "search_students", "get_student_parents", "link_parent", "get_siblings", "get_students_by_parent_id"
]

__all__ = [
    "create_parent",
    "get_parent_by_id",
    "get_parent_by_phone",
    "get_all_parents",
    "search_parents",
    "create_student",
    "get_student_by_id",
    "get_all_students",
    "search_students",
    "get_student_parents",
    "link_parent",
    "get_siblings",
    "get_students_by_parent_id",
]
