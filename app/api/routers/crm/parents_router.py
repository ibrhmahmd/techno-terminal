"""
app/api/routers/crm/parents.py
──────────────────────────────
Parents router.

Endpoints for parent management.
"""
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.crm.parent import ParentPublic, ParentListItem, ParentCreate, ParentUpdate
from app.api.dependencies import require_admin, require_any, get_parent_crud_service
from app.modules.crm.schemas import RegisterParentInput, UpdateParentDTO
from app.modules.auth import User
from app.modules.crm.services.parent_crud_service import ParentCrudService
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/crm", tags=["CRM — Parents"])

# Search by name or phone (min 2 chars). Empty → all parents
@router.get(
    "/parents",
    response_model=PaginatedResponse[ParentListItem],
    summary="List / search parents",
)
def list_parents(
    q: str = Query(
        "", description="Search by name or phone (min 2 chars). Empty → all parents."
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: ParentCrudService = Depends(get_parent_crud_service),
):
    if len(q.strip()) >= 2:
        results = svc.search_parents(query=q)
        total = len(results)  # search returns bounded set (max 50)
    else:
        # Get all and count manually since ParentRepository doesn't have count
        results = svc.list_parents(skip=skip, limit=limit)
        total = len(results)  # simplified for now

    return PaginatedResponse(
        data=[ParentListItem.model_validate(p) for p in results],
        total=total,
        skip=skip,
        limit=limit,
    )

# Get parent by ID
@router.get(
    "/parents/{parent_id}",
    response_model=ApiResponse[ParentPublic],
    summary="Get parent by ID",
    description="Retrieve a specific parent by their ID."
)
def get_parent(
    parent_id: int,
    _user: User = Depends(require_any),
    svc: ParentCrudService = Depends(get_parent_crud_service),
):
    parent = svc.get_parent_by_id(parent_id)
    if parent is None:
        raise NotFoundError("Parent not found")
    return ApiResponse(data=ParentPublic.model_validate(parent))

# Create new parent
@router.post(
    "/parents",
    response_model=ApiResponse[ParentPublic],
    status_code=201,
    summary="Create new parent",
    description="Create a new parent record.",
)
def create_parent(
    body: ParentCreate,
    current_user: User = Depends(require_admin),
    svc: ParentCrudService = Depends(get_parent_crud_service),
):
    parent = svc.create_parent(body)
    return ApiResponse(
        data=ParentPublic.model_validate(parent),
        message="Parent created successfully.",
    )

# Update parent
@router.patch(
    "/parents/{parent_id}",
    response_model=ApiResponse[ParentPublic],
    summary="Update parent",
    description="Update parent information."
)
def update_parent(
    parent_id: int,
    body: ParentUpdate,
    current_user: User = Depends(require_admin),
    svc: ParentCrudService = Depends(get_parent_crud_service),
):
    try:
        parent = svc.update_parent(parent_id, body)
        return ApiResponse(
            data=ParentPublic.model_validate(parent),
            message="Parent updated successfully.",
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Parent {parent_id} not found")

# Delete parent by ID
@router.delete(
    "/parents/{parent_id}",
    response_model=ApiResponse[ParentPublic],
    summary="Delete parent by ID",
)
def delete_parent(
    parent_id: int,
    _user: User = Depends(require_admin),
    svc: ParentCrudService = Depends(get_parent_crud_service),
):
    parent = svc.delete_parent(parent_id)
    if parent is None:
        raise NotFoundError("Parent not found")
    return ApiResponse(
        data=ParentPublic.model_validate(parent),
        message="Parent deleted successfully.",
    )