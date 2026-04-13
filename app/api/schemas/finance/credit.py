"""
app/api/schemas/finance/credit.py
───────────────────────────────────
Credit-related DTOs for student credit balance operations.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreditApplicationItem(BaseModel):
    """Individual credit application record."""
    credit_id: int = Field(..., description="ID of the credit record applied")
    amount_applied: float = Field(..., description="Amount applied from this credit")
    credit_remaining: float = Field(..., description="Remaining credit after application")
    
    model_config = {"from_attributes": True}


class ApplyCreditRequest(BaseModel):
    """Request to apply credit to an enrollment."""
    student_id: int = Field(..., description="Student ID with available credit")
    enrollment_id: int = Field(..., description="Enrollment to apply credit to")
    amount: Optional[float] = Field(None, description="Specific amount to apply (default: all available)")
    
    model_config = {"from_attributes": True}


class ApplyCreditResponse(BaseModel):
    """Response after applying credit to an enrollment."""
    student_id: int = Field(..., description="Student ID")
    enrollment_id: int = Field(..., description="Target enrollment ID")
    amount_applied: float = Field(..., description="Total amount applied")
    credit_applications: List[CreditApplicationItem] = Field(..., description="Individual credit applications")
    enrollment_balance_after: float = Field(..., description="Enrollment balance after credit application")
    applied_at: datetime = Field(..., description="Timestamp of credit application")
    applied_by: Optional[int] = Field(None, description="User ID who performed the action")
    
    model_config = {"from_attributes": True}


class CreditBalanceResponse(BaseModel):
    """Student credit balance response."""
    student_id: int = Field(..., description="Student ID")
    available_credit: float = Field(..., description="Total available credit amount")
    currency: str = Field(default="USD", description="Currency code")
    
    model_config = {"from_attributes": True}


class StudentCreditInfo(BaseModel):
    """Detailed student credit information."""
    credit_id: int = Field(..., description="Credit record ID")
    student_id: int = Field(..., description="Student ID")
    payment_id: int = Field(..., description="Originating payment ID")
    credit_amount: float = Field(..., description="Original credit amount")
    used_amount: float = Field(..., description="Amount already used")
    remaining_credit: float = Field(..., description="Remaining available credit")
    status: str = Field(..., description="Credit status (active, used, expired)")
    created_at: datetime = Field(..., description="When credit was created")
    
    model_config = {"from_attributes": True}
