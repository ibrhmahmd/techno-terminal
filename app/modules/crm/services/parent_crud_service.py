"""
ParentCrudService - Handles parent CRUD operations.
Implements IParentService protocol.
"""
from typing import List, Optional

from app.modules.crm.models.parent_models import Parent
from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
from app.api.schemas.crm.parent import ParentCreate, ParentUpdate
from app.shared.exceptions import NotFoundError


class ParentCrudService:
    """Service for parent CRUD operations."""
    
    def __init__(self, uow: StudentUnitOfWork) -> None:
        self._uow = uow
    
    def create_parent(self, body: ParentCreate) -> Parent:
        """Create a new parent."""
        parent = Parent(
            full_name=body.full_name,
            phone_primary=body.phone_primary,
            phone_secondary=body.phone_secondary,
            email=body.email,
            relation=body.relation,
            notes=body.notes,
        )
        created = self._uow.parents.create(parent)
        self._uow.commit()
        return created
    
    def get_parent_by_id(self, parent_id: int) -> Optional[Parent]:
        """Get a parent by ID."""
        return self._uow.parents.get_by_id(parent_id)
    
    def list_parents(self, skip: int = 0, limit: int = 200) -> List[Parent]:
        """List all parents with pagination."""
        return self._uow.parents.list_all(skip=skip, limit=limit)
    
    def update_parent(self, parent_id: int, body: ParentUpdate) -> Parent:
        """Update an existing parent."""
        parent = self._uow.parents.get_by_id(parent_id)
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
        parent = self._uow.parents.delete(parent_id)
        self._uow.commit()
        return parent
    
    def search_parents(self, query: str) -> List[Parent]:
        """Search parents by name or email."""
        return self._uow.parents.search(query)
