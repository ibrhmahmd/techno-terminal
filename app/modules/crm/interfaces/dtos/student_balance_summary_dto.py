from pydantic import BaseModel


class StudentBalanceSummaryDTO(BaseModel):
    total_due: float
    total_discounts: float
    total_paid: float
    net_balance: float
    enrollment_count: int
    unpaid_enrollments: int

    model_config = {"frozen": True}
