"""
app/api/routers/enrollments.py
───────────────────────────────
Enrollments domain router.

Prefix: /api/v1 (mounted in main.py)
Tag:    Enrollments

Role policy:
  READ  -> require_any
  WRITE -> require_admin
"""
from fastapi import APIRouter, Depends

from app.api.schemas.common import ApiResponse
from app.api.schemas.enrollments.enrollment import EnrollmentPublic
from app.api.dependencies import require_admin, require_any, get_enrollment_service
from app.modules.enrollments.schemas.enrollment_schemas import EnrollStudentInput, TransferStudentInput
from app.modules.auth import User
from app.modules.enrollments.services.enrollment_service import EnrollmentService

router = APIRouter(tags=["Enrollments"])

# enroll a student in a group
@router.post(
    "/enrollments",
    response_model=ApiResponse[EnrollmentPublic],
    status_code=201,
    summary="Enroll a student in a group",
)
def enroll_student(
    body: EnrollStudentInput,
    current_user: User = Depends(require_admin),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    enrollment_data = body.model_copy(update={"created_by": current_user.id})
    enrollment, capacity_exceeded = svc.enroll_student(enrollment_data)
    
    msg = "Student enrolled successfully."
    if capacity_exceeded:
        msg += " WARNING: Group capacity exceeded."
        
    return ApiResponse(
        data=EnrollmentPublic.model_validate(enrollment),
        message=msg
    )


# drop an enrollment
@router.delete(
    "/enrollments/{enrollment_id}",
    response_model=ApiResponse[EnrollmentPublic],
    summary="Drop an enrollment",
)
def drop_enrollment(
    enrollment_id: int,
    _user: User = Depends(require_admin),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    enr = svc.drop_enrollment(enrollment_id)
    return ApiResponse(
        data=EnrollmentPublic.model_validate(enr),
        message="Enrollment dropped successfully."
    )


# transfer a student to a new group
@router.post(
    "/enrollments/transfer",
    response_model=ApiResponse[EnrollmentPublic],
    summary="Transfer a student to a new group",
)
def transfer_student(
    body: TransferStudentInput,
    current_user: User = Depends(require_admin),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    transfer_data = body.model_copy(update={"created_by": current_user.id})
    new_enr = svc.transfer_student(transfer_data)
    
    return ApiResponse(
        data=EnrollmentPublic.model_validate(new_enr),
        message="Student transferred successfully."
    )


# get student enrollment history
@router.get(
    "/enrollments/student/{student_id}",
    response_model=ApiResponse[list[EnrollmentPublic]],
    summary="Get student enrollment history",
)
def get_student_enrollments(
    student_id: int,
    _user: User = Depends(require_any),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    enrollments = svc.get_student_enrollments(student_id)
    return ApiResponse(data=[EnrollmentPublic.model_validate(e) for e in enrollments])
