"""
app/api/routers/crm.py
──────────────────────
CRM domain router — Students and Parents.

Prefix: /api/v1/crm  (mounted in main.py)
Tag:    CRM

Role policy:
  - READ  (GET)   → require_any (any authenticated user)
  - WRITE (POST/PATCH) → require_admin (admin or manager only)

Note: register_student returns (student, siblings) — we drop siblings
here because the API consumer doesn't need them in the response.
Sibling info is available via GET /crm/students/{id}/parents.
"""
from fastapi import APIRouter, Depends, Query

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.crm.student import StudentPublic, StudentListItem
from app.api.schemas.crm.parent import ParentPublic, ParentListItem
from app.api.dependencies import (
    require_admin,
    require_any,
    get_student_service,
    get_parent_service,
)
from app.modules.crm.schemas import (
    RegisterStudentCommandDTO,
    UpdateStudentDTO,
    RegisterParentInput,
    UpdateParentDTO,
)
from app.modules.auth import User
from app.modules.crm.services.student_service import StudentService
from app.modules.crm.services.parent_service import ParentService

router = APIRouter(prefix="/crm", tags=["CRM"])


# ── Students ───────────────────────────────────────────────────────────────────

@router.get(
    "/students",
    response_model=PaginatedResponse[StudentListItem],
    summary="List / search students",
)
def list_students(
    q: str = Query("", description="Search by name or phone (min 2 chars). Empty → all students."),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: StudentService = Depends(get_student_service),
):
    if len(q.strip()) >= 2:
        results = svc.search_students(query=q)
    else:
        results = svc.list_all_students(skip=0, limit=1000)  # fetch all, paginate below

    page = results[skip: skip + limit]
    return PaginatedResponse(
        data=[StudentListItem.model_validate(s) for s in page],
        total=len(results),
        skip=skip,
        limit=limit,
    )


@router.get(
    "/students/{student_id}",
    response_model=ApiResponse[StudentPublic],
    summary="Get student by ID",
)
def get_student(
    student_id: int,
    _user: User = Depends(require_any),
    svc: StudentService = Depends(get_student_service),
):
    student = svc.get_student_by_id(student_id)
    return ApiResponse(data=StudentPublic.model_validate(student))


@router.post(
    "/students",
    response_model=ApiResponse[StudentPublic],
    status_code=201,
    summary="Register a new student",
)
def create_student(
    body: RegisterStudentCommandDTO,
    _user: User = Depends(require_admin),
    svc: StudentService = Depends(get_student_service),
):
    # register_student returns (student, siblings) — drop siblings here
    student, _siblings = svc.register_student(body)
    return ApiResponse(
        data=StudentPublic.model_validate(student),
        message="Student registered successfully.",
    )


@router.patch(
    "/students/{student_id}",
    response_model=ApiResponse[StudentPublic],
    summary="Update student profile",
)
def update_student(
    student_id: int,
    body: UpdateStudentDTO,
    _user: User = Depends(require_admin),
    svc: StudentService = Depends(get_student_service),
):
    student = svc.update_student(student_id, body)
    return ApiResponse(data=StudentPublic.model_validate(student))


@router.get(
    "/students/{student_id}/parents",
    response_model=ApiResponse[list[ParentPublic]],
    summary="Get all parents linked to a student",
)
def get_student_parents(
    student_id: int,
    _user: User = Depends(require_any),
    svc: StudentService = Depends(get_student_service),
):
    links = svc.get_student_parents(student_id)
    # Each link object has a .parent attribute (lazy-loaded inside service)
    parents = [ParentPublic.model_validate(link.parent) for link in links if link.parent]
    return ApiResponse(data=parents)


# ── Parents ────────────────────────────────────────────────────────────────────

@router.get(
    "/parents",
    response_model=PaginatedResponse[ParentListItem],
    summary="List / search parents",
)
def list_parents(
    q: str = Query("", description="Search by name or phone (min 2 chars). Empty → all parents."),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: ParentService = Depends(get_parent_service),
):
    if len(q.strip()) >= 2:
        results = svc.search_parents(query=q)
    else:
        results = svc.list_all_parents(skip=0, limit=1000)

    page = results[skip: skip + limit]
    return PaginatedResponse(
        data=[ParentListItem.model_validate(p) for p in page],
        total=len(results),
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
