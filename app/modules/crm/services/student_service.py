from datetime import date, datetime

from app.db.connection import get_session
from app.shared.datetime_utils import date_at_utc_midnight
from app.modules.crm.models.student_models import Student
from app.modules.crm.schemas.student_schemas import UpdateStudentDTO, RegisterStudentCommandDTO
import app.modules.crm.repositories.student_repository as repo
import app.modules.crm.repositories.parent_repository as parent_repository
from app.shared.audit_utils import apply_create_audit, apply_update_audit
from app.shared.exceptions import NotFoundError

class StudentService:
    """Encapsulates all Student business logic and interactions."""

    def register_student(
        self,
        command_dto: RegisterStudentCommandDTO,
    ) -> tuple[Student, list[dict]]:
        """
        Registers a student and links them to an existing parent as primary contact
        using the unified RegisterStudentCommandDTO parameters.
        Returns (student, siblings) so the UI can offer the sibling discount.
        """

        with get_session() as session:
            if command_dto.parent_id is not None:
                parent = parent_repository.get_parent_by_id(session, command_dto.parent_id)
                if not parent:
                    raise NotFoundError(f"Parent with ID {command_dto.parent_id} not found.")

            dob = command_dto.student_data.date_of_birth
            if dob is not None and isinstance(dob, date) and not isinstance(dob, datetime):
                dob = date_at_utc_midnight(dob)

            student = Student(
                full_name=command_dto.student_data.full_name,
                date_of_birth=dob,
                gender=command_dto.student_data.gender,
                phone=command_dto.student_data.phone,
                notes=command_dto.student_data.notes,
            )
            apply_create_audit(student, user_id=command_dto.created_by_user_id)
            created_student = repo.create_student(session, student)
            
            if command_dto.parent_id is not None:
                repo.link_parent(
                    session=session,
                    student_id=created_student.id,
                    parent_id=command_dto.parent_id,
                    relationship=command_dto.relationship,
                    is_primary=True,
                )
            student_id = created_student.id
            student_obj = created_student

        # Sibling detection in a separate session so the committed link is visible
        siblings = self.find_siblings(student_id)
        return student_obj, siblings

    def get_student_by_id(self, student_id: int) -> Student | None:
        with get_session() as session:
            return repo.get_student_by_id(session, student_id)

    def get_student_parents(self, student_id: int) -> list:
        with get_session() as session:
            links = list(repo.get_student_parents(session, student_id))
            for link in links:
                _ = link.parent  # force lazy load inside session
            return links

    def search_students(self, query: str) -> list[Student]:
        if not query or len(query.strip()) < 2:
            return []
        with get_session() as session:
            return list(repo.search_students(session, query.strip()))

    def list_all_students(self, skip: int = 0, limit: int = 200) -> list[Student]:
        with get_session() as session:
            return list(repo.get_all_students(session, skip, limit))

    def update_student(self, student_id: int, data: UpdateStudentDTO) -> Student:
        """Updates an existing student's fields."""
        with get_session() as session:
            student = repo.get_student_by_id(session, student_id)
            if not student:
                raise NotFoundError(f"Student with ID {student_id} not found.")

            for key, value in data.model_dump(exclude_unset=True).items():
                if hasattr(student, key) and key != "id":
                    setattr(student, key, value)
            apply_update_audit(student)
            session.add(student)
            session.commit()
            session.refresh(student)
            return student

    def find_siblings(self, student_id: int) -> list[dict]:
        with get_session() as session:
            return repo.get_siblings(session, student_id)

    def get_parent_students(self, parent_id: int) -> list[Student]:
        with get_session() as session:
            return repo.get_students_by_parent_id(session, parent_id)
