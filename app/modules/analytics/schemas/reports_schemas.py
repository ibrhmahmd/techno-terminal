"""
app/modules/analytics/schemas/reports_schemas.py
─────────────────────────────────────────────────
Internal Data Transfer Objects for Business Reports.

Four reports are supported:
  - DailyReportDTO       → payments + enrollments + groups created today
  - WeeklyReportDTO      → payments + enrollments for the current week (Mon–Sun)
  - AttendanceReportDTO  → attendance patterns, absence rates, class participation
  - CompetitionReportDTO → competition participation, results, performance
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


# ── Shared ────────────────────────────────────────────────────────────────────

class ReportMeta(BaseModel):
    """Metadata block present in every report response."""
    report_type: str
    title: str
    generated_at: datetime
    period_start: Optional[date] = None
    period_end: Optional[date] = None


# ── Daily Report ───────────────────────────────────────────────────────────────

class DailyPaymentSummaryDTO(BaseModel):
    """A single payment-method breakdown line for the daily report."""
    payment_method: str
    transaction_count: int
    gross_amount: float
    refund_amount: float
    net_amount: float


class DailyEnrollmentDTO(BaseModel):
    """A newly enrolled student row for the daily report."""
    enrollment_id: int
    student_name: str
    course_name: str
    group_name: str
    enrolled_at: datetime


class DailyGroupDTO(BaseModel):
    """A newly created group for the daily report."""
    group_id: int
    group_name: str
    course_name: str
    instructor_name: Optional[str]
    created_at: datetime


class DailyReportDTO(BaseModel):
    """Full daily business report bundle."""
    meta: ReportMeta
    # Financial totals
    total_gross_revenue: float
    total_refunds: float
    total_net_revenue: float
    total_transactions: int
    payment_breakdown: list[DailyPaymentSummaryDTO]
    # Academic activity
    new_enrollments_count: int
    new_enrollments: list[DailyEnrollmentDTO]
    new_groups_count: int
    new_groups: list[DailyGroupDTO]


# ── Weekly Report ──────────────────────────────────────────────────────────────

class WeeklyDayRevenueDTO(BaseModel):
    """Daily revenue total within the week."""
    day: date
    net_revenue: float
    transaction_count: int


class WeeklyEnrollmentStatsDTO(BaseModel):
    """Enrollment statistics per course for the week."""
    course_name: str
    new_enrollments: int
    drops: int
    net_change: int


class WeeklyReportDTO(BaseModel):
    """Full weekly business report bundle (Mon–Sun)."""
    meta: ReportMeta
    week_number: int
    # Financial
    total_gross_revenue: float
    total_refunds: float
    total_net_revenue: float
    total_transactions: int
    daily_revenue_breakdown: list[WeeklyDayRevenueDTO]
    payment_method_breakdown: list[DailyPaymentSummaryDTO]  # reused DTO
    # Academic
    total_new_enrollments: int
    total_drops: int
    net_enrollment_change: int
    enrollment_by_course: list[WeeklyEnrollmentStatsDTO]
    new_groups_count: int


# ── Attendance Report ──────────────────────────────────────────────────────────

class AttendanceGroupSummaryDTO(BaseModel):
    """Attendance rate summary for a single group."""
    group_id: int
    group_name: str
    course_name: str
    instructor_name: Optional[str]
    total_sessions: int
    total_students: int
    total_attendances: int
    total_absences: int
    attendance_rate: float          # % present of total expected slots
    absence_rate: float             # % absent of total expected slots


class AbsenceStreakStudentDTO(BaseModel):
    """A student with 3+ consecutive absences — potential flight risk."""
    student_id: int
    student_name: str
    group_name: str
    course_name: str
    consecutive_absences: int
    last_present_date: Optional[date]
    parent_name: Optional[str]
    phone_primary: Optional[str]


class AttendanceReportDTO(BaseModel):
    """Full attendance report for a given date range."""
    meta: ReportMeta
    # Aggregate
    overall_attendance_rate: float
    overall_absence_rate: float
    total_sessions_held: int
    total_expected_slots: int       # sessions × enrolled students
    total_present: int
    total_absent: int
    flight_risk_count: int          # students with 3+ consecutive absences
    # Per-group breakdown
    group_summaries: list[AttendanceGroupSummaryDTO]
    # At-risk list
    absence_streak_students: list[AbsenceStreakStudentDTO]


# ── Competition Report ─────────────────────────────────────────────────────────

class CompetitionSummaryDTO(BaseModel):
    """Overview of a single competition event."""
    competition_id: int
    competition_name: str
    start_date: Optional[date]
    end_date: Optional[date]
    teams_registered: int
    students_participating: int
    fee_per_student: Optional[float]
    total_fees_expected: float
    total_fees_collected: float
    collection_rate: float          # % collected of expected


class TeamStandingDTO(BaseModel):
    """A team's summary within a competition."""
    team_id: int
    team_name: str
    competition_name: str
    student_count: int
    group_name: Optional[str]


class CompetitionReportDTO(BaseModel):
    """Full competition report for a given period."""
    meta: ReportMeta
    # Aggregate
    total_competitions: int
    total_teams: int
    total_participating_students: int
    total_fees_expected: float
    total_fees_collected: float
    overall_collection_rate: float
    # Per-competition breakdown
    competitions: list[CompetitionSummaryDTO]
    # Team roster
    teams: list[TeamStandingDTO]
