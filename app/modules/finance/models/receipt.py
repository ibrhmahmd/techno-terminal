"""
app/modules/finance/models/receipt.py
────────────────────────────────────
Receipt SQLModel table definition.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field

from app.shared.constants import PaymentMethod


class Receipt(SQLModel, table=True):
    """Receipt table - immutable record of a completed payment transaction."""
    __tablename__ = "receipts"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    payer_name: Optional[str] = None
    payment_method: Optional[PaymentMethod] = Field(default=None, sa_column=Column(String))
    received_by: Optional[int] = Field(default=None, foreign_key="users.id")
    receipt_number: Optional[str] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
