from pydantic import BaseModel, ConfigDict


class PaymentDetailItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    student_name: str
    group_name: str
    amount: float
    payment_type: str


class DailyReportAggregateDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: str
    total_revenue: float
    new_enrollments: int
    sessions_held: int
    absent_count: int
    present_count: int
    attendance_rate: float
    payment_count: int
    payment_methods: dict[str, int]
    payment_details: list[PaymentDetailItem]
    instructors_list: list[str]
    unpaid_count: int
