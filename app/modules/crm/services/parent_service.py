from app.db.connection import get_session
from app.modules.crm.models.parent_models import Parent
from app.modules.crm.schemas.parent_schemas import RegisterParentInput, UpdateParentDTO
import app.modules.crm.repositories.parent_repository as repo
from app.shared.audit_utils import apply_create_audit, apply_update_audit
from app.shared.exceptions import ConflictError, NotFoundError

class ParentService:
    """Encapsulates all Parent business logic and interactions."""

    def get_parent_by_id(self, parent_id: int) -> Parent | None:
        with get_session() as session:
            return repo.get_parent_by_id(session, parent_id)

    def register_parent(self, data: RegisterParentInput) -> Parent:
        """Registers a new parent. Raises ConflictError if phone already exists."""
        with get_session() as session:
            existing = repo.get_parent_by_phone(session, data.phone_primary)
            if existing:
                raise ConflictError(
                    f"A parent with phone {data.phone_primary} already exists (ID: {existing.id})."
                )
            parent = Parent(
                full_name=data.full_name,
                phone_primary=data.phone_primary,
                phone_secondary=data.phone_secondary,
                email=data.email,
                relation=data.relation,
                notes=data.notes,
            )
            apply_create_audit(parent)
            return repo.create_parent(session, parent)

    def find_or_create_parent(self, data: RegisterParentInput) -> tuple[Parent, bool]:
        """
        Returns (parent, created: bool).
        If a parent with the same primary phone already exists, return it (created=False).
        Otherwise create a new one (created=True).
        Preferred entry point for the student registration workflow.
        """
        with get_session() as session:
            existing = repo.get_parent_by_phone(session, data.phone_primary)
            if existing:
                return existing, False

            parent = Parent(
                full_name=data.full_name,
                phone_primary=data.phone_primary,
                phone_secondary=data.phone_secondary,
                email=data.email,
                relation=data.relation,
                notes=data.notes,
            )
            apply_create_audit(parent)
            created = repo.create_parent(session, parent)
            return created, True

    def update_parent(self, parent_id: int, data: UpdateParentDTO) -> Parent:
        """Updates an existing parent's fields."""
        with get_session() as session:
            parent = repo.get_parent_by_id(session, parent_id)
            if not parent:
                raise NotFoundError(f"Parent with ID {parent_id} not found.")

            for key, value in data.model_dump(exclude_unset=True).items():
                if hasattr(parent, key) and key != "id":
                    setattr(parent, key, value)
            apply_update_audit(parent)
            session.add(parent)
            session.commit()
            session.refresh(parent)
            return parent

    def search_parents(self, query: str) -> list[Parent]:
        """Search parents by name or phone."""
        if not query or len(query.strip()) < 2:
            return []
        with get_session() as session:
            return list(repo.search_parents(session, query.strip()))

    def list_all_parents(self, skip: int = 0, limit: int = 200) -> list[Parent]:
        """Return a paginated list of all parents."""
        with get_session() as session:
            return list(repo.get_all_parents(session, skip, limit))

    def count_parents(self) -> int:
        """Returns total count of parents for pagination."""
        with get_session() as session:
            return repo.count_parents(session)
    
    def delete_parent(self, parent_id: int) -> Parent | None:
        """Deletes a parent by ID."""
        with get_session() as session:
            return repo.delete_parent(session, parent_id)