"""
app/modules/analytics/schemas/financial_schemas.py
──────────────────────────────────────────────────
Data Transfer Objects (DTOs) for the Financial analytics domain.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel


class RevenueByDateDTO(BaseModel):
    day: date
    net_revenue: float


class RevenueByMethodDTO(BaseModel):
    payment_method: str
    net_revenue: float
    receipt_count: int


class OutstandingByGroupDTO(BaseModel):
    group_id: int
    group_name: str
    course_name: str
    students_with_balance: int
    total_outstanding: float


class TopDebtorDTO(BaseModel):
    student_id: int
    student_name: str
    guardian_name: Optional[str]
    phone_primary: Optional[str]
    total_outstanding: float
