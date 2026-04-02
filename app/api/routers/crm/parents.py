"""
app/api/routers/crm/parents.py
──────────────────────────────
Parents router.

Endpoints for parent management.
"""
from fastapi import APIRouter, Depends, Query

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.crm.parent import ParentPublic, ParentListItem
from app.api.dependencies import require_admin, require_any, get_parent_service
from app.modules.crm.schemas import RegisterParentInput, UpdateParentDTO
from app.modules.auth import User
from app.modules.crm.services.parent_service import ParentService

router = APIRouter(prefix="/crm", tags=["CRM — Parents"])


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
    svc: ParentService = Depends(get_parent_service),
):
    if len(q.strip()) >= 2:
        results = svc.search_parents(query=q)
        total = len(results)  # search returns bounded set (max 50)
    else:
        total = svc.count_parents()
        results = svc.list_all_parents(skip=skip, limit=limit)

    return PaginatedResponse(
        data=[ParentListItem.model_validate(p) for p in results],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/parents/{parent_id}",
    response_model=ApiResponse[ParentPublic],
    summary="Get parent by ID",
)
def get_parent(
    parent_id: int,
    _user: User = Depends(require_any),
    svc: ParentService = Depends(get_parent_service),
):
    parent = svc.get_parent_by_id(parent_id)
    return ApiResponse(data=ParentPublic.model_validate(parent))


@router.post(
    "/parents",
    response_model=ApiResponse[ParentPublic],
    status_code=201,
    summary="Register a new parent",
)
def create_parent(
    body: RegisterParentInput,
    _user: User = Depends(require_admin),
    svc: ParentService = Depends(get_parent_service),
):
    parent = svc.register_parent(body)
    return ApiResponse(
        data=ParentPublic.model_validate(parent),
        message="Parent registered successfully.",
    )


@router.patch(
    "/parents/{parent_id}",
    response_model=ApiResponse[ParentPublic],
    summary="Update parent profile",
)
def update_parent(
    parent_id: int,
    body: UpdateParentDTO,
    _user: User = Depends(require_admin),
    svc: ParentService = Depends(get_parent_service),
):
    parent = svc.update_parent(parent_id, body)
    return ApiResponse(data=ParentPublic.model_validate(parent))
