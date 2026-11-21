"""Student soft-delete routes: they drop enrollments too, so they live in enrollments (ADR-0006)."""
from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.api.schemas.common import ApiResponse
from app.modules.auth import User
from app.modules.crm import StudentDeletionResult
from app.modules.enrollments.api.deps import get_student_deletion_service
from app.modules.enrollments.services.student_deletion_service import StudentDeletionService
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/crm", tags=["CRM — Students"])


@router.delete(
    "/students/{student_id}",
    response_model=ApiResponse[None],
    summary="Delete a student by ID",
    description="Soft-deletes the student (recoverable via restore) and drops their active enrollments. Hard delete is DELETE /students/{student_id}/hard."
)
def delete_student_by_id(
    student_id: int,
    current_user: User = Depends(require_admin),
    svc: StudentDeletionService = Depends(get_student_deletion_service),
):
    if not svc.delete_student(student_id, deleted_by=current_user.id):
        raise NotFoundError(f"Student {student_id} not found")
    return ApiResponse(data=None, message="Student deleted successfully.")


@router.delete(
    "/students/{student_id}/soft",
    response_model=ApiResponse[StudentDeletionResult],
    summary="Soft delete a student",
    description="Marks a student as deleted without removing from database. Student can be restored later."
)
def soft_delete_student(
    student_id: int,
    current_user: User = Depends(require_admin),
    svc: StudentDeletionService = Depends(get_student_deletion_service),
):
    """
    Soft delete a student (logically removed, recoverable).
    Payments stay live (#175); active enrollments are dropped.
    """
    if not svc.delete_student(student_id, deleted_by=current_user.id):
        raise NotFoundError(f"Student {student_id} not found")
    return ApiResponse(
        data={"student_id": student_id, "status": "soft_deleted"},
        message="Student soft-deleted successfully. Use restore endpoint to recover."
    )
