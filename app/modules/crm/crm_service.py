import re
from datetime import date, datetime

from app.db.connection import get_session
from app.shared.datetime_utils import date_at_utc_midnight
from app.modules.crm.crm_models import Guardian, Student
from app.modules.crm.crm_schemas import RegisterGuardianInput, RegisterStudentInput
from app.shared.exceptions import ValidationError, ConflictError, NotFoundError
from app.shared.validators import validate_phone, validate_required_fields
from . import crm_repository as repo

# --- Guardian Service ---


def get_guardian_by_id(guardian_id: int) -> Guardian | None:
    with get_session() as session:
        return repo.get_guardian_by_id(session, guardian_id)


def register_guardian(data: RegisterGuardianInput | dict) -> Guardian:
    """Registers a new guardian. Raises ConflictError if phone already exists."""
    if isinstance(data, dict):
        validate_required_fields(data, ["full_name", "phone_primary"])
        data = RegisterGuardianInput.model_validate(data)

    with get_session() as session:
        existing = repo.get_guardian_by_phone(session, data.phone_primary)
        if existing:
            raise ConflictError(
                f"A guardian with phone {data.phone_primary} already exists (ID: {existing.id})."
            )
        guardian = Guardian(
            full_name=data.full_name,
            phone_primary=data.phone_primary,
            phone_secondary=data.phone_secondary,
            email=data.email,
            relation=data.relation,
            notes=data.notes,
        )
        return repo.create_guardian(session, guardian)


def find_or_create_guardian(data: RegisterGuardianInput | dict) -> tuple[Guardian, bool]:
    """
    Returns (guardian, created: bool).
    If a guardian with the same primary phone already exists, return it (created=False).
    Otherwise create a new one (created=True).
    This is the preferred entry point for the student registration workflow.
    """
    if isinstance(data, dict):
        validate_required_fields(data, ["full_name", "phone_primary"])
        data = RegisterGuardianInput.model_validate(data)

    with get_session() as session:
        existing = repo.get_guardian_by_phone(session, data.phone_primary)
        if existing:
            return existing, False

        guardian = Guardian(
            full_name=data.full_name,
            phone_primary=data.phone_primary,
            phone_secondary=data.phone_secondary,
            email=data.email,
            relation=data.relation,
            notes=data.notes,
        )
        created = repo.create_guardian(session, guardian)
        return created, True


def update_guardian(guardian_id: int, data: dict) -> Guardian:
    """Updates an existing guardian's fields."""
    with get_session() as session:
        guardian = repo.get_guardian_by_id(session, guardian_id)
        if not guardian:
            raise NotFoundError(f"Guardian with ID {guardian_id} not found.")
        
        for key, value in data.items():
            if hasattr(guardian, key) and key != "id":
                setattr(guardian, key, value)
        
        session.add(guardian)
        session.commit()
        session.refresh(guardian)
        return guardian


def search_guardians(query: str) -> list[Guardian]:
    """Search guardians by name or phone."""
    if not query or len(query.strip()) < 2:
        return []
    with get_session() as session:
        return list(repo.search_guardians(session, query.strip()))


def list_all_guardians(skip: int = 0, limit: int = 200) -> list[Guardian]:
    """Return a paginated list of all guardians."""
    with get_session() as session:
        return list(repo.get_all_guardians(session, skip, limit))


# --- Student Service ---


def register_student(
    student_data: RegisterStudentInput | dict,
    guardian_id: int,
    relationship: str | None = None,
) -> tuple[Student, list[dict]]:
    """
    Registers a student and links them to an existing guardian as primary contact.
    Returns (student, siblings) so the UI can offer the sibling discount.
    Accepts RegisterStudentInput or a plain dict (backward compat).
    """
    if isinstance(student_data, dict):
        if not student_data.get("full_name"):
            raise ValidationError("'Full Name' is required.")
        student_data = RegisterStudentInput.model_validate(student_data)

    with get_session() as session:
        guardian = repo.get_guardian_by_id(session, guardian_id)
        if not guardian:
            raise NotFoundError(f"Guardian with ID {guardian_id} not found.")

        dob = student_data.date_of_birth
        if dob is not None and isinstance(dob, date) and not isinstance(dob, datetime):
            dob = date_at_utc_midnight(dob)

        student = Student(
            full_name=student_data.full_name,
            date_of_birth=dob,
            gender=student_data.gender,
            phone=student_data.phone,
            notes=student_data.notes,
        )
        created_student = repo.create_student(session, student)
        repo.link_guardian(
            session=session,
            student_id=created_student.id,
            guardian_id=guardian_id,
            relationship=relationship,
            is_primary=True,
        )
        student_id = created_student.id
        student_obj = created_student
        # Transaction commits when exiting the 'with' block

    # Sibling detection in a separate session so the committed link is visible
    siblings = find_siblings(student_id)
    return student_obj, siblings


def get_student_by_id(student_id: int) -> Student | None:
    """Returns a student by ID, or None if not found."""
    with get_session() as session:
        return repo.get_student_by_id(session, student_id)


def get_student_guardians(student_id: int) -> list:
    """Returns all guardian links for a student."""
    with get_session() as session:
        links = list(repo.get_student_guardians(session, student_id))
        for link in links:
            _ = link.guardian  # force lazy load inside session
        return links


def search_students(query: str) -> list[Student]:
    """Search students by name."""
    if not query or len(query.strip()) < 2:
        return []
    with get_session() as session:
        return list(repo.search_students(session, query.strip()))


def list_all_students(skip: int = 0, limit: int = 200) -> list[Student]:
    """Return a paginated list of all students."""
    with get_session() as session:
        return list(repo.get_all_students(session, skip, limit))


def update_student(student_id: int, data: dict) -> Student:
    """Updates an existing student's fields."""
    with get_session() as session:
        student = repo.get_student_by_id(session, student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found.")
        
        for key, value in data.items():
            if hasattr(student, key) and key != "id":
                setattr(student, key, value)
                
        session.add(student)
        session.commit()
        session.refresh(student)
        return student


def find_siblings(student_id: int) -> list[dict]:
    """Returns sibling data for the UI using the v_siblings database view."""
    with get_session() as session:
        return repo.get_siblings(session, student_id)


def get_guardian_students(guardian_id: int) -> list[Student]:
    """Returns all active Student objects linked to a given guardian."""
    with get_session() as session:
        return repo.get_students_by_guardian_id(session, guardian_id)
