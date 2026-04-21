"""
app/api/schemas/finance/payment.py
───────────────────────────────────
Public-facing Payment DTOs for student payments API.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator


class PaymentListItem(BaseModel):
    """Payment item for student payments list."""
    id: int
    student_id: int
    amount: Decimal
    payment_date: datetime
    payment_method: Optional[str] = None
    status: str = "completed"
    receipt_id: int
    receipt_number: Optional[str] = None
    course_name: Optional[str] = None
    group_name: Optional[str] = None
    level_number: Optional[int] = None
    transaction_type: str

    model_config = {"from_attributes": True}


class ReceiptDetails(BaseModel):
    """Receipt details within payment details response."""
    receipt_id: int
    receipt_number: Optional[str] = None
    issued_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    issued_by: Optional[str] = None  # resolved from received_by → user
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class EnrollmentInfo(BaseModel):
    """Enrollment info within payment details response."""
    enrollment_id: Optional[int] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    course_name: Optional[str] = None
    level_number: Optional[int] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None

    model_config = {"from_attributes": True}


class StudentSnapshot(BaseModel):
    """Student snapshot within payment details response."""
    full_name: str
    phone: Optional[str] = None

    model_config = {"from_attributes": True}


class ParentInfo(BaseModel):
    """Parent info within payment details response."""
    parent_id: Optional[int] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None

    model_config = {"from_attributes": True}


class PaymentDetailsResponse(BaseModel):
    """Comprehensive payment details response."""
    # Payment fields
    id: int
    student_id: int
    amount: Decimal
    payment_type: Optional[str] = None
    transaction_type: str
    discount_amount: Decimal = Decimal("0")
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Related data
    receipt: ReceiptDetails
    enrollment: EnrollmentInfo
    student: StudentSnapshot
    parent: ParentInfo

    model_config = {"from_attributes": True}


class SendReceiptRequest(BaseModel):
    """Request to send receipt to parent."""
    method: str  # "whatsapp" or "email"
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        if v not in ('whatsapp', 'email'):
            raise ValueError('method must be "whatsapp" or "email"')
        return v


class SendReceiptResponse(BaseModel):
    """Response from sending receipt."""
    success: bool
    message: str
    receipt_id: int
    recipient_contact: Optional[str] = None
    sent_at: datetime

    model_config = {"from_attributes": True}
