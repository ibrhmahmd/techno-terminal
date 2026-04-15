"""
app/modules/finance/models/payment.py
────────────────────────────────────
Payment SQLModel table definition.
"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column as SAColumn
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Column, String

from app.shared.constants import TransactionType, PaymentType


class Payment(SQLModel, table=True):
    """Payment table - individual line item within a receipt."""
    __tablename__ = "payments"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipts.id")
    student_id: int = Field(foreign_key="students.id")
    enrollment_id: Optional[int] = Field(default=None, foreign_key="enrollments.id")
    amount: float
    transaction_type: TransactionType = Field(sa_column=Column(String))
    payment_type: Optional[PaymentType] = Field(default=None, sa_column=Column(String))
    original_payment_id: Optional[int] = Field(default=None, foreign_key="payments.id")
    discount_amount: float = 0.0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    payment_metadata: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=SAColumn("metadata", JSONB),
    )
