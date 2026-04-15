from typing import Optional
from datetime import date

from app.modules.crm.models.student_models import StudentStatus
from app.shared.exceptions import BusinessRuleError, ValidationError

class StudentValidator:
    """
    Pure validation — no DB access, no side effects.
    Services call this before mutating any student record.
    """

    @staticmethod
    def validate_status_transition(
        current: StudentStatus, new: StudentStatus
    ) -> None:
        """Raises BusinessRuleError for illegal transitions."""
        ILLEGAL = {
            (StudentStatus.INACTIVE, StudentStatus.WAITING),  # must reactivate first
        }
        if (current, new) in ILLEGAL:
            raise BusinessRuleError(
                f"Cannot transition from '{current.value}' to '{new.value}' directly."
            )

    @staticmethod
    def validate_waiting_priority(priority: int) -> None:
        if not 1 <= priority <= 1000:
            raise ValidationError("Waiting priority must be between 1 and 1000.")

    @staticmethod
    def compute_age(dob: Optional[date]) -> Optional[int]:
        """Pure function. Returns integer age or None."""
        if not dob:
            return None
        dob_d = dob.date() if hasattr(dob, 'date') else dob
        today = date.today()
        age = today.year - dob_d.year
        if (today.month, today.day) < (dob_d.month, dob_d.day):
            age -= 1
        return age

    @staticmethod
    def classify_age_bracket(age: Optional[int]) -> str:
        """Returns age bracket key per grouping spec."""
        if age is None:
            return "unknown"
        if 4 <= age < 7:   return "age_4_7"
        if 7 <= age < 9:   return "age_7_9"
        if 9 <= age < 12:  return "age_9_12"
        if 12 <= age < 15: return "age_12_15"
        if age >= 15:      return "age_15_plus"
        return "unknown"
