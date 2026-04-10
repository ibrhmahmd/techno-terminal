"""
app/api/schemas/finance/allocations.py
───────────────────────────────────────
Payment allocation-related DTOs.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AllocationReversalResponseDTO(BaseModel):
    """Response after reversing a payment allocation."""
    original_allocation_id: int = Field(..., description="ID of the original allocation being reversed")
    reversal_allocation_id: int = Field(..., description="ID of the new reversal record")
    amount_reversed: float = Field(..., description="Amount that was reversed")
    reason: str = Field(..., description="Reason for the reversal")
    reversed_at: datetime = Field(..., description="Timestamp of reversal")
    reversed_by: Optional[int] = Field(None, description="User ID who performed the reversal")
    
    model_config = {"from_attributes": True}


class PaymentAllocationItemDTO(BaseModel):
    """Individual payment allocation item."""
    allocation_id: int = Field(..., description="Allocation record ID")
    payment_id: int = Field(..., description="Parent payment ID")
    enrollment_id: Optional[int] = Field(None, description="Target enrollment ID")
    allocated_amount: float = Field(..., description="Amount allocated")
    allocation_type: str = Field(..., description="Type of allocation (course_fee, credit, reversal)")
    allocated_at: datetime = Field(..., description="When allocation was created")
    allocated_by: Optional[int] = Field(None, description="User who created the allocation")
    notes: Optional[str] = Field(None, description="Allocation notes")
    
    model_config = {"from_attributes": True}


class PaymentAllocationsResponseDTO(BaseModel):
    """Response containing all allocations for a payment."""
    payment_id: int = Field(..., description="Payment ID")
    allocations: List[PaymentAllocationItemDTO] = Field(..., description="List of allocations")
    total_allocated: float = Field(..., description="Sum of all allocated amounts")
    
    model_config = {"from_attributes": True}
