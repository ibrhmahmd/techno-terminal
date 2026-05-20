from pydantic import BaseModel, ConfigDict


class PaymentDetailItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    student_name: str
    group_name: str
    amount: float
    payment_type: str


class SessionDetailItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    instructor_name: str
    session_time: str
    present_count: int
    absent_count: int
    cancelled_count: int
    student_names_present: str
    student_names_absent: str


class PaymentTypeGroup(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    payment_type: str
    subtotal: float
    count: int
    items: list[PaymentDetailItem]


class InstructorSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    instructor_name: str
    session_count: int


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
    session_details: list[SessionDetailItem] = []
    payments_by_type: list[PaymentTypeGroup] = []
    instructor_summary: list[InstructorSummaryItem] = []
