"""
ParentCrudService - Handles parent CRUD operations.
Implements IParentService protocol.
"""
from typing import List, Optional

from app.modules.crm.models.parent_models import Parent
from app.db.uow import UnitOfWork
from app.modules.crm.repositories.parent_repository import ParentRepository
from app.modules.crm.schemas.parent_schemas import RegisterParentInput, UpdateParentDTO
from app.shared.exceptions import NotFoundError


class ParentCrudService:
    """Service for parent CRUD operations."""
    
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._parents = ParentRepository(uow.session)
    
    def create_parent(self, body: RegisterParentInput) -> Parent:
        """Create a new parent."""
        parent = Parent(
            full_name=body.full_name,
            phone_primary=body.phone_primary,
            phone_secondary=body.phone_secondary,
            email=body.email,
            relation=body.relation,
            notes=body.notes,
        )
        created = self._parents.create(parent)
        self._uow.commit()
        return created
    
    def get_parent_by_id(self, parent_id: int) -> Optional[Parent]:
        """Get a parent by ID."""
        return self._parents.get_by_id(parent_id)
    
    def list_parents(self, query: Optional[str], skip: int, limit: int) -> List[Parent]:
        """One page of parents; ``query`` (name or phone) narrows it when given."""
        return self._parents.list_page(query, skip=skip, limit=limit)

    def count_parents(self, query: Optional[str]) -> int:
        """How many parents match ``query`` (all parents when it is None)."""
        return self._parents.count(query)
    
    def update_parent(self, parent_id: int, body: UpdateParentDTO) -> Parent:
        """Update an existing parent."""
        parent = self._parents.get_by_id(parent_id)
        if not parent:
            raise NotFoundError(f"Parent {parent_id} not found")
        
        # Update fields from body
        update_data = body.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(parent, key):
                setattr(parent, key, value)
        
        self._uow.commit()
        self._uow.flush()
        return parent
    
    def delete_parent(self, parent_id: int) -> Optional[Parent]:
        """Delete a parent by ID."""
        parent = self._parents.delete(parent_id)
        self._uow.commit()
        return parent
    
