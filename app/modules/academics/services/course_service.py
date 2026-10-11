"""
app/modules/academics/services/course_service.py
──────────────────────────────────────
Service class for Course-related business logic.
"""
from typing import Sequence
from app.db.uow import UnitOfWork
from app.shared.audit_utils import apply_update_audit
from app.shared.exceptions import ConflictError, NotFoundError
from app.shared.validators import validate_positive_amount
from app.modules.academics.models import Course
from app.modules.academics.schemas.course_schemas import AddNewCourseInput, UpdateCourseDTO, CourseStatsDTO
from app.modules.academics.repositories.course_repository import CourseRepository


class CourseService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._repo = CourseRepository(uow.session)

    def add_new_course(self, data: AddNewCourseInput) -> Course:
        """Validates and creates a new course."""
        if self._repo.get_course_by_name(data.name):
            raise ConflictError(f"Course '{data.name}' already exists.")

        course = Course(
            name=data.name,
            category=data.category,
            description=data.description,
            notes=data.notes,
            price_per_level=data.price_per_level,
            sessions_per_level=data.sessions_per_level,
        )
        course = self._repo.create_course(course)
        self._uow.commit()
        self._uow.session.refresh(course)
        return course

    def update_course_price(self, course_id: int, new_price: float) -> Course:
        """Updates the price per level for an existing course."""
        validate_positive_amount(new_price, field="price")
        course = self._repo.update_course_price(course_id, new_price)
        if not course:
            raise NotFoundError(f"Course {course_id} not found.")
        self._uow.commit()
        self._uow.session.refresh(course)
        return course

    def update_course(self, course_id: int, data: UpdateCourseDTO) -> Course:
        course = self._uow.session.get(Course, course_id)
        if not course:
            raise NotFoundError(f"Course {course_id} not found.")
        for k, v in data.model_dump(exclude_unset=True).items():
            if hasattr(course, k) and k != "id":
                setattr(course, k, v)
        apply_update_audit(course)
        self._uow.session.add(course)
        self._uow.commit()
        self._uow.session.refresh(course)
        return course

    def list_active_courses(self) -> Sequence[Course]:
        return self._repo.list_active_courses()

    def get_all_course_stats(self) -> list[CourseStatsDTO]:
        """
        Returns aggregate stats (group + student counts) for ALL courses.
        Backed by the v_course_stats view — single DB query, no N+1.
        Used by the course overview table.
        """
        return self._repo.get_all_course_stats()

    def get_course_by_id(self, course_id: int) -> Course | None:
        """Get a single course by ID."""
        course = self._repo.get_course_by_id(course_id)
        if not course:
            raise NotFoundError(f"Course {course_id} not found.")
        return course

    def get_course_by_name(self, name: str) -> Course | None:
        """Get a single course by name."""
        return self._repo.get_course_by_name(name)

    def get_course_stats(self, course_id: int) -> CourseStatsDTO | None:
        """
        Returns aggregate stats for a single course from v_course_stats.
        Returns None if the course does not exist.
        Used by the course detail page.
        """
        return self._repo.get_course_stats(course_id)