"""
app/modules/finance/interfaces/dto/payment_with_details_dto.py
──────────────────────────────────────────────────────────────
Detailed payment information DTO with all related data.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class PaymentWithDetailsDTO:
    """
    Immutable DTO containing comprehensive payment details including:
    - Payment fields (amount, type, discount, notes)
    - Receipt fields (number, method, date)
    - Enrollment, group, course, instructor info
    - Student snapshot
    - Parent contact info
    """
    # Payment fields
    payment_id: int
    student_id: int
    amount: Decimal
    payment_type: Optional[str]
    transaction_type: str
    discount_amount: Decimal
    notes: Optional[str]
    created_at: Optional[datetime]
    
    # Receipt fields
    receipt_id: int
    receipt_number: Optional[str]
    payment_method: Optional[str]
    paid_at: Optional[datetime]
    received_by: Optional[int]  # user_id who received payment
    received_by_name: Optional[str]  # resolved name
    receipt_notes: Optional[str]
    
    # Enrollment fields
    enrollment_id: Optional[int]
    
    # Group/Course fields (nullable for non-course payments)
    group_id: Optional[int]
    group_name: Optional[str]
    course_name: Optional[str]
    level_number: Optional[int]
    
    # Instructor (from group.instructor_id joined to team_members)
    instructor_id: Optional[int]
    instructor_name: Optional[str]
    
    # Student snapshot
    student_name: str
    student_phone: Optional[str]
    
    # Parent details if the student has any parents
    parent_id: Optional[int]
    parent_name: Optional[str]
    parent_phone: Optional[str]
