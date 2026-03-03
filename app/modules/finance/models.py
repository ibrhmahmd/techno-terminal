from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Receipt(SQLModel, table=True):
    __tablename__ = "receipts"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    guardian_id: Optional[int] = Field(default=None, foreign_key="guardians.id")
    payment_method: Optional[str] = None  # cash | card | transfer | online
    received_by: Optional[int] = Field(default=None, foreign_key="users.id")
    receipt_number: Optional[str] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class Payment(SQLModel, table=True):
    __tablename__ = "payments"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipts.id")
    student_id: int = Field(foreign_key="students.id")
    enrollment_id: Optional[int] = Field(default=None, foreign_key="enrollments.id")
    amount: float  # always positive; direction set by transaction_type
    transaction_type: str  # 'charge' | 'payment' | 'refund'
    payment_type: Optional[str] = None  # 'course_level' | 'competition' | 'other'
    discount_amount: float = 0.0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
