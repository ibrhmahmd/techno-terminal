from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StudentEnrollmentSummaryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    student_id: int
    student_name: str
    enrollment_id: int
    level_number: int
    status: str
    sessions_attended: int
    sessions_total: int
    payment_status: str
    amount_remaining: float
    amount_due: float
    discount_applied: float


class EnrollmentBalanceDTO(BaseModel):
    """Enrollment balance snapshot read from the v_enrollment_balance view.

    Enrollments-owned copy of the finance DTO of the same fields (ticket #19
    boundaries: no upward import of the finance repository/DTO).
    """
    model_config = ConfigDict(from_attributes=True)
    enrollment_id: int
    student_id: int
    group_id: int
    level_number: int
    amount_due: Decimal
    discount_applied: Decimal
    amount_paid: Decimal
    total_refunded: Decimal
    balance: Decimal
    status: str


class EnrollmentAttendanceSummaryDTO(BaseModel):
    """Total attendance stats for an enrollment (v_enrollment_attendance view).

    Enrollments-owned copy of the attendance DTO of the same fields.
    """
    model_config = ConfigDict(from_attributes=True)
    enrollment_id: int
    sessions_attended: int
    sessions_missed: int
