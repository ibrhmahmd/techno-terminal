"""
app/modules/finance/interfaces/dto/enhanced_receipt_line_dto.py
────────────────────────────────────────────────────────────────
Enhanced receipt line DTO with complete payment context.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.modules.crm.models.student_models import Student
    from app.modules.enrollments.models.enrollment_models import Enrollment
    from app.modules.academics.models.group_models import Group
    from app.modules.crm.models.parent_models import Parent
    from app.modules.finance.models.payment import Payment


@dataclass
class EnhancedReceiptLineDTO:
    """
    Enriched payment line data for receipt generation.
    Contains all necessary context for displaying a payment line.
    """
    # Core payment data
    payment_id: int
    amount: float
    transaction_type: str
    payment_type: Optional[str]
    discount_amount: float
    notes: Optional[str]
    
    # Student info
    student_id: int
    student_name: str
    student_phone: Optional[str]
    
    # Parent info (preferred contact)
    parent_id: Optional[int]
    parent_name: Optional[str]
    parent_phone: Optional[str]
    
    # Enrollment context
    enrollment_id: Optional[int]
    enrollment_status: Optional[str]
    level_number: Optional[int]
    
    # Group/Course info
    group_id: Optional[int]
    group_name: Optional[str]
    course_name: Optional[str]
    
    # Balance status (for partial payment indication)
    is_partial_payment: bool
    remaining_amount: float  # Amount still owed (0 if fully paid)
    balance_status: str  # 'paid', 'partial', 'unpaid'
    
    # Original objects (for reference if needed)
    payment: Optional["Payment"] = None
    student: Optional["Student"] = None
    enrollment: Optional["Enrollment"] = None
    group: Optional["Group"] = None
    parent: Optional["Parent"] = None
    
    @property
    def display_phone(self) -> Optional[str]:
        """Get preferred phone number (parent first, then student)."""
        return self.parent_phone or self.student_phone
    
    @property
    def display_contact_name(self) -> str:
        """Get preferred contact name (parent first, then student)."""
        return self.parent_name or self.student_name
    
    @property
    def course_group_display(self) -> str:
        """Format course and group name for display."""
        if self.course_name and self.group_name:
            return f"{self.course_name} - {self.group_name}"
        elif self.group_name:
            return self.group_name
        elif self.course_name:
            return self.course_name
        return "-"
    
    @property
    def net_amount(self) -> float:
        """Calculate net amount after discount."""
        return self.amount - self.discount_amount
