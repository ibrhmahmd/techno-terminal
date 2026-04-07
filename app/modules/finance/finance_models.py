from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Column as SAColumn
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship, Column, String
from app.shared.constants import PaymentMethod, TransactionType, PaymentType

# --- Receipt Schemas ---

class ReceiptBase(SQLModel):
    payer_name: Optional[str] = None
    payment_method: Optional[PaymentMethod] = Field(default=None, sa_column=Column(String))  # cash | card | transfer | online
    received_by: Optional[int] = Field(default=None, foreign_key="users.id")
    receipt_number: Optional[str] = None
    notes: Optional[str] = None

class Receipt(ReceiptBase, table=True):
    __tablename__ = "receipts"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class ReceiptCreate(ReceiptBase):
    pass

class ReceiptRead(ReceiptBase):
    id: int
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

# --- Payment Schemas ---

class PaymentBase(SQLModel):
    receipt_id: int = Field(foreign_key="receipts.id")
    student_id: int = Field(foreign_key="students.id")
    enrollment_id: Optional[int] = Field(default=None, foreign_key="enrollments.id")
    amount: float  # always positive; direction set by transaction_type
    transaction_type: TransactionType = Field(sa_column=Column(String))  # 'charge' | 'payment' | 'refund'
    payment_type: Optional[PaymentType] = Field(default=None, sa_column=Column(String))  # 'course_level' | 'competition' | 'other'
    discount_amount: float = 0.0
    notes: Optional[str] = None

class Payment(PaymentBase, table=True):
    __tablename__ = "payments"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
    payment_metadata: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=SAColumn("metadata", JSONB),
    )

class PaymentCreate(PaymentBase):
    pass

class PaymentRead(PaymentBase):
    id: int
    created_at: Optional[datetime] = None
