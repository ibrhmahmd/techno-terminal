from app.db.connection import get_session
from app.modules.crm.models.guardian_models import Guardian
from app.modules.crm.schemas.guardian_schemas import RegisterGuardianInput, UpdateGuardianDTO
import app.modules.crm.repositories.guardian_repository as repo
from app.shared.audit_utils import apply_create_audit, apply_update_audit
from app.shared.exceptions import ConflictError, NotFoundError

class GuardianService:
    """Encapsulates all Guardian business logic and interactions."""

    def get_guardian_by_id(self, guardian_id: int) -> Guardian | None:
        with get_session() as session:
            return repo.get_guardian_by_id(session, guardian_id)

    def register_guardian(self, data: RegisterGuardianInput) -> Guardian:
        """Registers a new guardian. Raises ConflictError if phone already exists."""
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
            apply_create_audit(guardian)
            return repo.create_guardian(session, guardian)

    def find_or_create_guardian(self, data: RegisterGuardianInput) -> tuple[Guardian, bool]:
        """
        Returns (guardian, created: bool).
        If a guardian with the same primary phone already exists, return it (created=False).
        Otherwise create a new one (created=True).
        Preferred entry point for the student registration workflow.
        """
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
            apply_create_audit(guardian)
            created = repo.create_guardian(session, guardian)
            return created, True

    def update_guardian(self, guardian_id: int, data: UpdateGuardianDTO) -> Guardian:
        """Updates an existing guardian's fields."""
        with get_session() as session:
            guardian = repo.get_guardian_by_id(session, guardian_id)
            if not guardian:
                raise NotFoundError(f"Guardian with ID {guardian_id} not found.")

            for key, value in data.model_dump(exclude_unset=True).items():
                if hasattr(guardian, key) and key != "id":
                    setattr(guardian, key, value)
            apply_update_audit(guardian)
            session.add(guardian)
            session.commit()
            session.refresh(guardian)
            return guardian

    def search_guardians(self, query: str) -> list[Guardian]:
        """Search guardians by name or phone."""
        if not query or len(query.strip()) < 2:
            return []
        with get_session() as session:
            return list(repo.search_guardians(session, query.strip()))

    def list_all_guardians(self, skip: int = 0, limit: int = 200) -> list[Guardian]:
        """Return a paginated list of all guardians."""
        with get_session() as session:
            return list(repo.get_all_guardians(session, skip, limit))
