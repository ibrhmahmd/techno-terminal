"""
app/api/routers/crm/students.py
───────────────────────────────
Students router.

Endpoints for student management.
"""
from fastapi import APIRouter, Depends, Query

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.crm.student import StudentPublic, StudentListItem
from app.api.schemas.crm.parent import ParentPublic
from app.api.dependencies import require_admin, require_any, get_student_service
from app.modules.crm.schemas import RegisterStudentCommandDTO, UpdateStudentDTO
from app.modules.auth import User
from app.modules.crm.services.student_service import StudentService

router = APIRouter(prefix="/crm", tags=["CRM — Students"])


@router.get(
    "/students",
    response_model=PaginatedResponse[StudentListItem],
    summary="List / search students",
)
def list_students(
    q: str = Query(
        "", description="Search by name or phone (min 2 chars). Empty → all students."
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: StudentService = Depends(get_student_service),
):
    if len(q.strip()) >= 2:
        results = svc.search_students(query=q)
        total = len(results)  # search returns bounded set (max 50)
    else:
        total = svc.count_students()
        results = svc.list_all_students(skip=skip, limit=limit)

    return PaginatedResponse(
        data=[StudentListItem.model_validate(s) for s in results],
        total=total,
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
    parents = [
        ParentPublic.model_validate(link.parent) for link in links if link.parent
    ]
    return ApiResponse(data=parents)
