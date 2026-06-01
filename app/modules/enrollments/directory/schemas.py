from pydantic import BaseModel, ConfigDict


class StudentEnrollmentSummaryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    student_id: int
    student_name: str
    enrollment_id: int
    level_number: int
    status: str
    sessions_attended: int
    sessions_total: int
    payment_status: str
    amount_remaining: float
    amount_due: float
    discount_applied: float
