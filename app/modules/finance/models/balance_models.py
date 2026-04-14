"""
app/modules/finance/models/balance_models.py
──────────────────────────────────────────
Balance tracking models for real-time student financial management.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any

from sqlalchemy import Column as SAColumn
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship


# ── Student Balance ──────────────────────────────────────────────────────────

class StudentBalanceBase(SQLModel):
    """Base model for student balance tracking."""
    total_amount_due: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    total_discounts: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    total_paid: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    net_balance: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    last_updated: Optional[datetime] = None


class StudentBalance(StudentBalanceBase, table=True):
    """Materialized student balance table - updated via triggers."""
    __tablename__ = "student_balances"
    __table_args__ = {"extend_existing": True}
    
    student_id: int = Field(primary_key=True, foreign_key="students.id")
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")


class StudentBalanceItem(StudentBalanceBase):
    """DTO for reading student balance."""
    student_id: int
    updated_by: Optional[int] = None


# ── Payment Allocation ───────────────────────────────────────────────────────

class PaymentAllocationBase(SQLModel):
    """Base model for tracking how payments are allocated across enrollments."""
    allocated_amount: Decimal = Field(decimal_places=2)
    allocation_type: str = Field(default="course_fee")  # 'course_fee', 'competition_fee', 'refund', 'adjustment', 'credit', 'other'
    allocated_at: Optional[datetime] = None
    notes: Optional[str] = None


class PaymentAllocation(PaymentAllocationBase, table=True):
    """Tracks partial payment allocations to specific enrollments/charges."""
    __tablename__ = "payment_allocations"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    payment_id: int = Field(foreign_key="payments.id")
    enrollment_id: Optional[int] = Field(default=None, foreign_key="enrollments.id")
    competition_id: Optional[int] = Field(default=None, foreign_key="competitions.id")
    team_member_id: Optional[int] = Field(default=None, foreign_key="team_members.id")
    allocated_by: Optional[int] = Field(default=None, foreign_key="users.id")


class PaymentAllocationItem(PaymentAllocationBase):
    """DTO for reading payment allocation."""
    id: int
    payment_id: int
    enrollment_id: Optional[int] = None
    competition_id: Optional[int] = None
    team_member_id: Optional[int] = None
    allocated_by: Optional[int] = None


class PaymentAllocationInput(SQLModel):
    """DTO for creating payment allocation."""
    payment_id: int
    enrollment_id: Optional[int] = None
    competition_id: Optional[int] = None
    team_member_id: Optional[int] = None
    allocated_amount: Decimal
    allocation_type: str = "course_fee"
    notes: Optional[str] = None


# ── Enrollment Balance History ──────────────────────────────────────────────

class EnrollmentBalanceHistoryBase(SQLModel):
    """Base model for enrollment balance history snapshots."""
    amount_due: Decimal = Field(decimal_places=2)
    discount_applied: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    total_paid: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    remaining_balance: Decimal = Field(decimal_places=2)
    recorded_at: Optional[datetime] = None
    notes: Optional[str] = None


class EnrollmentBalanceHistory(EnrollmentBalanceHistoryBase, table=True):
    """Historical snapshots of enrollment balance states."""
    __tablename__ = "enrollment_balance_history"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    enrollment_id: int = Field(foreign_key="enrollments.id")
    student_id: int = Field(foreign_key="students.id")
    recorded_by: Optional[int] = Field(default=None, foreign_key="users.id")


# ── Student Credits ─────────────────────────────────────────────────────────

class StudentCreditBase(SQLModel):
    """Base model for tracking student credit balances (overpayments)."""
    credit_amount: Decimal = Field(decimal_places=2)
    used_amount: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    remaining_credit: Optional[Decimal] = Field(default=None, decimal_places=2)
    status: str = Field(default="active")  # 'active', 'used', 'expired'
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class StudentCredit(StudentCreditBase, table=True):
    """Tracks credit from overpayments available for future use."""
    __tablename__ = "student_credits"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    payment_id: int = Field(foreign_key="payments.id")


# ── DTOs for Balance Operations ──────────────────────────────────────────────

class EnrollmentBalanceItem(SQLModel):
    """Detailed balance for a single enrollment."""
    enrollment_id: int
    group_id: int
    level_number: int
    amount_due: float
    discount_applied: float
    amount_paid: float
    remaining_balance: float
    status: str  # 'paid', 'partial', 'unpaid'


class StudentBalanceItem(SQLModel):
    """Complete student balance response."""
    student_id: int
    total_amount_due: float
    total_discounts: float
    total_paid: float
    net_balance: float  # negative = debt, positive = credit
    enrollment_details: List[EnrollmentBalanceItem]
    as_of_date: datetime


class PaymentAllocationResponse(SQLModel):
    """Result of payment allocation operation."""
    payment_id: int
    total_allocated: float
    credit_remaining: float
    allocations: List[PaymentAllocationItem]
    credit_applied: bool


class BalanceAdjustmentInput(SQLModel):
    """Input for manual balance adjustment."""
    student_id: int
    enrollment_id: Optional[int] = None
    adjustment_amount: Decimal
    reason: str
    adjustment_type: str = "manual"  # 'manual', 'correction', 'waiver', 'scholarship'
    notes: Optional[str] = None
