"""
app/api/schemas/finance/balance.py
───────────────────────────────────
Public-facing DTOs for student financial balances.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FinancialSummaryPublic(BaseModel):
    """
    Financial summary per enrollment returned from v_enrollment_balance.
    """
    student_id: int
    group_id: int
    enrollment_id: int
    group_name: Optional[str] = None
    net_due: float
    total_paid: float
    balance: float

    model_config = {"from_attributes": True}


class BalanceAdjustmentRequest(BaseModel):
    """Request schema for balance adjustment."""
    enrollment_id: Optional[int] = None
    adjustment_amount: float
    reason: str
    adjustment_type: str = "manual"
    notes: Optional[str] = None


class UnpaidEnrollmentResponse(BaseModel):
    """Response schema for unpaid enrollment listing."""
    enrollment_id: int
    student_id: int
    student_name: str
    group_id: int
    group_name: str
    course_name: Optional[str]
    level_number: int
    amount_due: float
    discount_applied: float
    total_paid: float
    remaining_balance: float
    enrolled_at: Optional[str]


class EnrollmentBalanceResponse(BaseModel):
    """Response schema for enrollment balance."""
    enrollment_id: int
    student_id: int
    group_id: int
    level_number: int
    amount_due: float
    discount_applied: float
    total_paid: float
    total_refunded: float
    remaining_balance: float
    status: str
    is_paid: bool

    model_config = {"from_attributes": True}


class BalanceAdjustmentResponseDTO(BaseModel):
    """Response after adjusting a student balance."""
    student_id: int
    previous_balance: float
    adjustment_amount: float
    new_balance: float
    reason: str
    adjustment_type: str
    adjusted_at: datetime
    adjusted_by: Optional[int] = None

    model_config = {"from_attributes": True}


class StudentBalanceSummaryDTO(BaseModel):
    """Quick balance summary for dashboard display."""
    student_id: int
    net_balance: float
    total_due: float
    total_paid: float
    enrollment_count: int
    unpaid_enrollments: int
    as_of_date: datetime

    model_config = {"from_attributes": True}
