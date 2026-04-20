"""
app/api/routers/crm/students.py
───────────────────────────────
Students router.

Endpoints for student management.
"""
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.crm.student import StudentPublic, StudentListItem
from app.api.schemas.crm.parent import ParentPublic
from app.api.schemas.crm.student_details import StudentWithDetails, SiblingInfo
from app.modules.crm.interfaces.dtos import StudentGroupedResultDTO
from app.api.dependencies import (
    require_any,
    require_admin,
    get_student_profile_service,
    get_student_search_service,
    get_student_crud_service,
)
from app.modules.crm.services.student_profile_service import StudentProfileService
from app.modules.crm.services.search_service import SearchService
from app.modules.crm.services.student_crud_service import StudentCrudService
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
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/crm", tags=["CRM — Students"])


# List / search students
@router.get(
    "/students",
    response_model=PaginatedResponse[StudentListItem],
    summary="List / search students",
)
def search_students(
    q: str = Query(None, min_length=1, max_length=100, description="Search by name or phone (min 2 chars). Empty → all students."),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: SearchService = Depends(get_student_search_service),
):
    if q is not None and len(q.strip()) >= 2:
        results = svc.search(query=q)
        total = len(results)  # search returns bounded set (max 50)
    else:
        total = svc.count()
        results = svc.list_all(skip=skip, limit=limit)

    return PaginatedResponse(
        data=[StudentListItem.model_validate(s) for s in results],
        total=total,
        skip=skip,
        limit=limit,
    )


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
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    # Normalize frontend-sent 0 values to None
    if body.parent_id == 0:
        body.parent_id = None
    # Set created_by to current user if not provided or is 0
    if body.created_by_user_id is None or body.created_by_user_id == 0:
        body.created_by_user_id = _user.id
    # register_student returns (student, siblings) — drop siblings here
    student, _siblings = svc.register_student(body)
    return ApiResponse(
        data=StudentPublic.model_validate(student),
        message="Student registered successfully.",
    )


# ── Static/Semi-static routes (must be before /{student_id}) ─────────────────

# Get grouped students
@router.get(
    "/students/grouped",
    response_model=ApiResponse[StudentGroupedResultDTO],
    summary="Get grouped students",
    description="Group students by status, gender, or age_bucket. Supports pagination within groups."
)
def get_grouped_students(
    group_by: str = Query("status", description="Group by: status, gender, age_bucket"),
    include_inactive: bool = Query(False, description="Include inactive students"),
    skip: int = Query(0, ge=0, description="Number of students to skip per group"),
    limit: int = Query(50, ge=1, le=200, description="Max students per group"),
    current_user: User = Depends(require_admin),
    svc: SearchService = Depends(get_student_search_service),
):
    result = svc.get_grouped(
        group_by=group_by,
        include_inactive=include_inactive,
        skip=skip,
        limit=limit
    )
    return ApiResponse(data=result)


# Get waiting list
@router.get(
    "/students/waiting-list",
    response_model=ApiResponse[list[StudentResponseDTO]],
    summary="Get waiting list",
    description="Retrieve students on the waiting list, ordered by priority and wait time."
)
def get_waiting_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=200),
    order_by_priority: bool = True,
    current_user: User = Depends(require_admin),
    svc: SearchService = Depends(get_student_search_service),
):
    students = svc.get_waiting_list()
    return ApiResponse(data=students, message=f"Retrieved {len(students)} students from waiting list")


# Get students by status
@router.get(
    "/students/by-status/{status}",
    response_model=ApiResponse[list[StudentResponseDTO]],
    summary="Get students by status",
    description="Retrieve students filtered by their enrollment status."
)
def get_students_by_status(
    status: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=200),
    current_user: User = Depends(require_admin),
    svc: SearchService = Depends(get_student_search_service),
):
    try:
        status_enum = StudentStatus(status)
        students = svc.get_by_status(status_enum)
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
    svc: SearchService = Depends(get_student_search_service),
):
    summary = svc.get_status_summary()
    return ApiResponse(data=summary)


# ── Dynamic routes with {student_id} path parameter ─────────────────────────

# Get student by ID
@router.get(
    "/students/{student_id}",
    response_model=ApiResponse[StudentPublic],
    summary="Get student by ID",
)
def get_student(
    student_id: int,
    _user: User = Depends(require_any),
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    student = svc.get_by_id(student_id)
    if student is None:
        raise NotFoundError("Student not found")
    return ApiResponse(data=StudentPublic.model_validate(student))


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
    svc: StudentCrudService = Depends(get_student_crud_service),
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
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    links = svc.get_student_parents(student_id)
    # Each link object has a .parent attribute (lazy-loaded inside service)
    parents = [
        ParentPublic.model_validate(link.parent) for link in links if link.parent
    ]
    return ApiResponse(data=parents)


# ── Student Status Management Endpoints ─────────────────────────────────────

# Update student enrollment status
@router.patch(
    "/students/{student_id}/status",
    response_model=ApiResponse[StudentResponseDTO],
    summary="Update student enrollment status",
    description="Update student status (active/waiting/inactive) with optional audit notes."
)
def update_student_status(
    student_id: int,
    body: UpdateStudentStatusDTO,
    current_user: User = Depends(require_admin),
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    try:
        status_enum = StudentStatus(body.status)
        student = svc.update_status(
            student_id=student_id,
            new_status=status_enum,
            notes=body.notes,
            changed_by_user_id=current_user.id,
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
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    try:
        student = svc.toggle_status(student_id=student_id)
        return ApiResponse(
            data=student,
            message=f"Student status toggled to {student.status}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")


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
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    try:
        student = svc.set_waiting_priority(
            student_id=student_id,
            priority=body.priority,
            notes=body.notes,
        )
        return ApiResponse(
            data=student,
            message=f"Waiting priority set to {body.priority}"
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found or not on waiting list")


# Get student status history
@router.get(
    "/students/{student_id}/status-history",
    response_model=ApiResponse[List[dict]],
    summary="Get student status history",
    description="Retrieve audit log of status changes for a student."
)
def get_student_status_history(
    student_id: int,
    current_user: User = Depends(require_admin),
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    try:
        # This method doesn't exist yet - will need to be added to StudentCrudService
        # For now, return empty list
        return ApiResponse(data=[])
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
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    try:
        svc.delete_student(student_id)
        return ApiResponse(data=None, message="Student deleted successfully.")
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")


# ── NEW: Student Detail Endpoints ────────────────────────────────────────────

@router.get(
    "/students/{student_id}/details",
    response_model=ApiResponse[StudentWithDetails],
    summary="Get student with full details",
    description="Get complete student profile including parent info, enrollments, balance summary, and siblings."
)
def get_student_details(
    student_id: int,
    current_user: User = Depends(require_any),
    svc: StudentProfileService = Depends(get_student_profile_service),
):
    """
    Get comprehensive student details including:
    - Core student information
    - Primary parent contact
    - Active enrollments with group/course details
    - Balance summary (total due, discounts, paid, net balance)
    - Siblings sharing the same parent
    """
    try:
        details = svc.get_student_details(student_id)
        return ApiResponse(data=details)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")


@router.get(
    "/students/{student_id}/siblings",
    response_model=ApiResponse[list[SiblingInfo]],
    summary="Get student's siblings",
    description="Get list of siblings who share the same parent(s). Returns empty array if no siblings."
)
def get_student_siblings(
    student_id: int,
    current_user: User = Depends(require_any),
    svc: StudentProfileService = Depends(get_student_profile_service),
):
    """
    Get siblings for a student.

    Returns siblings who share the same parent(s), including:
    - Student ID and name
    - Age and gender
    - Parent information
    - Enrollment count

    Returns empty array [] if:
    - Student has no linked parent
    - Student is an only child
    """
    siblings = svc.get_student_siblings(student_id)
    return ApiResponse(data=siblings)


# ── Soft Delete Endpoints ─────────────────────────────────────────────────────

@router.delete(
    "/students/{student_id}/soft",
    response_model=ApiResponse[dict],
    summary="Soft delete a student",
    description="Marks a student as deleted without removing from database. Student can be restored later."
)
def soft_delete_student(
    student_id: int,
    current_user: User = Depends(require_admin),
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    """
    Soft delete a student (logically removed, recoverable).
    Also cascades soft-delete to related payments.
    """
    try:
        success = svc.soft_delete_student(student_id, deleted_by=current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found or already deleted")

        return ApiResponse(
            data={"student_id": student_id, "status": "soft_deleted"},
            message="Student soft-deleted successfully. Use restore endpoint to recover."
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")


@router.post(
    "/students/{student_id}/restore",
    response_model=ApiResponse[dict],
    summary="Restore a soft-deleted student",
    description="Restores a previously soft-deleted student and their payments."
)
def restore_student(
    student_id: int,
    current_user: User = Depends(require_admin),
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    """Restore a soft-deleted student."""
    try:
        success = svc.restore_student(student_id, restored_by=current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found or not deleted")

        return ApiResponse(
            data={"student_id": student_id, "status": "restored"},
            message="Student restored successfully"
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")


@router.delete(
    "/students/{student_id}/hard",
    response_model=ApiResponse[dict],
    summary="Permanently delete a student",
    description="Admin-only: Permanently removes a student and all related data. Cannot be undone."
)
def hard_delete_student(
    student_id: int,
    current_user: User = Depends(require_admin),
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    """Permanently delete a student (cannot be undone)."""
    try:
        success = svc.hard_delete_student(student_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")

        return ApiResponse(
            data={"student_id": student_id, "status": "permanently_deleted"},
            message="Student permanently deleted. This action cannot be undone."
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")


@router.get(
    "/admin/deleted-students",
    response_model=ApiResponse[List[StudentListItem]],
    summary="List deleted students (Admin)",
    description="Admin-only: List all soft-deleted students for recovery."
)
def list_deleted_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    svc: StudentCrudService = Depends(get_student_crud_service),
):
    """List all soft-deleted students."""
    students = svc.list_deleted_students(limit=limit, offset=skip)
    return ApiResponse(
        data=[StudentListItem.model_validate(s) for s in students]
    )