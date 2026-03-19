import re
from app.db.connection import get_session
from app.modules.crm.crm_models import Guardian, Student
from app.shared.exceptions import ValidationError, ConflictError, NotFoundError
from app.shared.validators import validate_phone, validate_required_fields
from . import crm_repository as repo

# --- Guardian Service ---


def register_guardian(data: dict) -> Guardian:
    """Registers a new guardian. Raises ConflictError if phone already exists."""
    validate_required_fields(data, ["full_name", "phone_primary"])

    phone_primary = validate_phone(data["phone_primary"])

    with get_session() as session:
        existing = repo.get_guardian_by_phone(session, phone_primary)
        if existing:
            raise ConflictError(
                f"A guardian with phone {phone_primary} already exists (ID: {existing.id})."
            )
        guardian = Guardian(
            full_name=data["full_name"],
            phone_primary=phone_primary,
            phone_secondary=data.get("phone_secondary"),
            email=data.get("email"),
            relation=data.get("relation"),
            notes=data.get("notes"),
        )
        return repo.create_guardian(session, guardian)


def find_or_create_guardian(data: dict) -> tuple[Guardian, bool]:
    """
    Returns (guardian, created: bool).
    If a guardian with the same primary phone already exists, return it (created=False).
    Otherwise create a new one (created=True).
    This is the preferred entry point for the student registration workflow.
    """
    validate_required_fields(data, ["full_name", "phone_primary"])

    phone_primary = validate_phone(data["phone_primary"])

    with get_session() as session:
        existing = repo.get_guardian_by_phone(session, phone_primary)
        if existing:
            return existing, False

        guardian = Guardian(
            full_name=data["full_name"],
            phone_primary=phone_primary,
            phone_secondary=data.get("phone_secondary"),
            email=data.get("email"),
            relation=data.get("relation"),
            notes=data.get("notes"),
        )
        created = repo.create_guardian(session, guardian)
        return created, True


def search_guardians(query: str) -> list[Guardian]:
    """Search guardians by name or phone."""
    if not query or len(query.strip()) < 2:
        return []
    with get_session() as session:
        return list(repo.search_guardians(session, query.strip()))


# --- Student Service ---


def register_student(
    student_data: dict, guardian_id: int, relationship: str | None = None
) -> tuple[Student, list[dict]]:
    """
    Registers a student and links them to an existing guardian as primary contact.
    Returns (student, siblings) so the UI can offer the sibling discount.
    """
    if not student_data.get("full_name"):
        raise ValidationError("'Full Name' is required.")

    with get_session() as session:
        guardian = repo.get_guardian_by_id(session, guardian_id)
        if not guardian:
            raise NotFoundError(f"Guardian with ID {guardian_id} not found.")

        student = Student(
            full_name=student_data["full_name"],
            date_of_birth=student_data.get("date_of_birth"),
            gender=student_data.get("gender"),
            phone=student_data.get("phone"),
            notes=student_data.get("notes"),
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


def search_students(query: str) -> list[Student]:
    """Search students by name."""
    if not query or len(query.strip()) < 2:
        return []
    with get_session() as session:
        return list(repo.search_students(session, query.strip()))


def find_siblings(student_id: int) -> list[dict]:
    """Returns sibling data for the UI using the v_siblings database view."""
    with get_session() as session:
        return repo.get_siblings(session, student_id)


def get_guardian_students(guardian_id: int) -> list[Student]:
    """Returns all active Student objects linked to a given guardian."""
    with get_session() as session:
        return repo.get_students_by_guardian_id(session, guardian_id)
