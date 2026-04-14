"""
app/api/schemas/analytics/financial.py
──────────────────────────────────────
API DTOs for Financial analytics responses.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel


class RevenueByDateItem(BaseModel):
    """Daily revenue total."""
    day: date
    net_revenue: float

    model_config = {"from_attributes": True}


class RevenueByMethodItem(BaseModel):
    """Revenue breakdown by payment method."""
    payment_method: str
    net_revenue: float
    receipt_count: int

    model_config = {"from_attributes": True}


class OutstandingByGroupItem(BaseModel):
    """Outstanding balance summary for a group."""
    group_id: int
    group_name: str
    course_name: str
    students_with_balance: int
    total_outstanding: float

    model_config = {"from_attributes": True}


class TopDebtorItem(BaseModel):
    """Student with high outstanding balance."""
    student_id: int
    student_name: str
    parent_name: Optional[str]
    phone_primary: Optional[str]
    total_outstanding: float

    model_config = {"from_attributes": True}


class RevenueMetricsResponse(BaseModel):
    """Extended revenue metrics with trend analysis."""
    period_start: date
    period_end: date
    total_revenue: float
    total_receipts: int
    avg_revenue_per_receipt: float
    previous_period_revenue: float
    revenue_change_pct: float
    trend_direction: str  # "up", "down", "stable"
    monthly_breakdown: list[RevenueByDateItem]

    model_config = {"from_attributes": True}


class RevenueForecastItem(BaseModel):
    """Revenue forecast for a future month."""
    month: str
    predicted_revenue: float
    confidence_lower: float
    confidence_upper: float

    model_config = {"from_attributes": True}
