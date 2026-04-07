"""
app/api/routers/crm/students.py
───────────────────────────────
Students router.

Endpoints for student management.
"""
from fastapi import APIRouter, Depends, Query, HTTPException

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.crm.student import StudentPublic, StudentListItem
from app.api.schemas.crm.parent import ParentPublic
from app.api.dependencies import require_admin, require_any, get_student_service
from app.modules.crm.schemas import (
    RegisterStudentCommandDTO, 
    UpdateStudentDTO,
    UpdateStudentStatusDTO,
    SetWaitingPriorityDTO,
    StudentResponseDTO,
    StudentStatusSummaryDTO,
    StudentStatus,
)
from app.modules.auth import User
from app.modules.crm.services.student_service import StudentService
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/crm", tags=["CRM — Students"])


# List / search students
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


# Get student by ID
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
    if student is None:
        raise NotFoundError("Student not found")
    return ApiResponse(data=StudentPublic.model_validate(student))


# Register a new student
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
    # Normalize frontend-sent 0 values to None
    if body.parent_id == 0:
        body.parent_id = None
    # register_student returns (student, siblings) — drop siblings here
    student, _siblings = svc.register_student(body)
    return ApiResponse(
        data=StudentPublic.model_validate(student),
        message="Student registered successfully.",
    )

# Update student profile
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

# Get all parents linked to a student
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


# ── NEW: Student Status Management Endpoints ─────────────────────────────────

# Update student enrollment status
@router.patch(
    "/students/{student_id}/status",
    response_model=ApiResponse[StudentResponseDTO],
    summary="Update student enrollment status",
    description="Update student status (active/waiting/inactive/graduated) with optional audit notes."
)
def update_student_status(
    student_id: int,
    body: UpdateStudentStatusDTO,
    current_user: User = Depends(require_admin),
    svc: StudentService = Depends(get_student_service),
):
    try:
        status_enum = StudentStatus(body.status)
        student = svc.update_student_status(
            student_id=student_id,
            new_status=status_enum,
            user_id=current_user.id,
            notes=body.notes
        )
        return ApiResponse(
            data=student,
            message=f"Student status updated to {body.status}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")


# Toggle student status between active and waiting
@router.post(
    "/students/{student_id}/status/toggle",
    response_model=ApiResponse[StudentResponseDTO],
    summary="Toggle student status between active and waiting",
    description="Convenience endpoint to quickly toggle between active and waiting states."
)
def toggle_student_status(
    student_id: int,
    notes: str | None = None,
    current_user: User = Depends(require_admin),
    svc: StudentService = Depends(get_student_service),
):
    try:
        student = svc.toggle_student_status(
            student_id=student_id,
            user_id=current_user.id,
            notes=notes
        )
        return ApiResponse(
            data=student,
            message=f"Student status toggled to {student.status}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")


# Get waiting list
@router.get(
    "/students/waiting-list",
    response_model=ApiResponse[list[StudentResponseDTO]],
    summary="Get waiting list",
    description="Retrieve students on the waiting list, ordered by priority and wait time."
)
def get_waiting_list(
    skip: int = 0,
    limit: int = 200,
    order_by_priority: bool = True,
    current_user: User = Depends(require_admin),
    svc: StudentService = Depends(get_student_service),
):
    students = svc.get_waiting_list(skip, limit, order_by_priority)
    return ApiResponse(data=students, message=f"Retrieved {len(students)} students from waiting list")

# Set waiting list priority
@router.patch(
    "/students/{student_id}/waiting-priority",
    response_model=ApiResponse[StudentResponseDTO],
    summary="Set waiting list priority",
    description="Set priority for a student on the waiting list (1 = highest)."
)
def set_waiting_priority(
    student_id: int,
    body: SetWaitingPriorityDTO,
    current_user: User = Depends(require_admin),
    svc: StudentService = Depends(get_student_service),
):
    try:
        student = svc.set_waiting_priority(
            student_id=student_id,
            priority=body.priority,
            user_id=current_user.id
        )
        return ApiResponse(
            data=student,
            message=f"Waiting priority set to {body.priority}"
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found or not on waiting list")

# Get students by status
@router.get(
    "/students/by-status/{status}",
    response_model=ApiResponse[list[StudentResponseDTO]],
    summary="Get students by status",
    description="Retrieve students filtered by their enrollment status."
)
def get_students_by_status(
    status: str,
    skip: int = 0,
    limit: int = 200,
    current_user: User = Depends(require_admin),
    svc: StudentService = Depends(get_student_service),
):
    try:
        status_enum = StudentStatus(status)
        students = svc.get_students_by_status(status_enum, skip, limit)
        return ApiResponse(
            data=students,
            message=f"Retrieved {len(students)} {status} students"
        )
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")


# Get student status summary
@router.get(
    "/students/status-summary",
    response_model=ApiResponse[StudentStatusSummaryDTO],
    summary="Get student status summary",
    description="Get counts of students by enrollment status."
)
def get_student_status_summary(
    current_user: User = Depends(require_admin),
    svc: StudentService = Depends(get_student_service),
):
    summary = svc.get_student_status_summary()
    return ApiResponse(data=summary)


# Get student status history
@router.get(
    "/students/{student_id}/status-history",
    response_model=ApiResponse[list[dict]],
    summary="Get student status history",
    description="Retrieve audit log of status changes for a student."
)
def get_student_status_history(
    student_id: int,
    current_user: User = Depends(require_admin),
    svc: StudentService = Depends(get_student_service),
):
    try:
        history = svc.get_student_status_history(student_id)
        return ApiResponse(data=history)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")

# Delete student by ID
@router.delete(
    "/students/{student_id}",
    response_model=ApiResponse[None],
    summary="Delete a student by ID",
    description="Delete a student by ID."
)
def delete_student_by_id(
    student_id: int,
    current_user: User = Depends(require_admin),
    svc: StudentService = Depends(get_student_service),
):
    try:
        svc.delete_student_by_id(student_id)
        return ApiResponse(data=None, message="Student deleted successfully.")
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")