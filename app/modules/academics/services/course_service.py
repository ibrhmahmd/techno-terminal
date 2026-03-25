"""
app/modules/academics/services/course_service.py
─────────────────────────────────────────────────
Service class for Course-related business logic.
"""
from app.db.connection import get_session
from app.shared.audit_utils import apply_update_audit
from app.shared.exceptions import ConflictError, NotFoundError
from app.shared.validators import validate_positive_amount
from app.modules.academics.academics_models import Course
from app.modules.academics.schemas import AddNewCourseInput, UpdateCourseDTO, CourseStatsDTO
from app.modules.academics import repositories as repo


class CourseService:
    def add_new_course(self, data: AddNewCourseInput) -> Course:
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

    def update_course_price(self, course_id: int, new_price: float) -> Course:
        """Updates the price per level for an existing course."""
        validate_positive_amount(new_price, field="price")
        with get_session() as session:
            course = repo.update_course_price(session, course_id, new_price)
            if not course:
                raise NotFoundError(f"Course {course_id} not found.")
            return course

    def update_course(self, course_id: int, data: UpdateCourseDTO) -> Course:
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

    def get_active_courses(self) -> list[Course]:
        with get_session() as session:
            return list(repo.list_active_courses(session))

    def get_all_course_stats(self) -> list[CourseStatsDTO]:
        """
        Returns aggregate stats (group + student counts) for ALL courses.
        Backed by the v_course_stats view — single DB query, no N+1.
        Used by the course overview table.
        """
        with get_session() as session:
            return repo.get_all_course_stats(session)

    def get_course_stats(self, course_id: int) -> CourseStatsDTO | None:
        """
        Returns aggregate stats for a single course from v_course_stats.
        Returns None if the course does not exist.
        Used by the course detail page.
        """
        with get_session() as session:
            return repo.get_course_stats(session, course_id)
