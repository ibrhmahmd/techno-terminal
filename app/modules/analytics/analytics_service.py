"""
analytics/service.py — Thin service wrappers over the analytics repository.
"""

from datetime import date
from typing import Optional
from app.db.connection import get_session
from app.modules.analytics import analytics_repository as repo


def get_active_enrollment_count() -> int:
    with get_session() as db:
        return repo.get_active_enrollment_count(db)


def get_today_sessions(target_date: Optional[date] = None) -> list[dict]:
    with get_session() as db:
        return repo.get_today_sessions(db, target_date or date.today())


def get_today_unpaid_attendees(target_date: Optional[date] = None) -> list[dict]:
    with get_session() as db:
        return repo.get_today_unpaid_attendees(db, target_date or date.today())


def get_revenue_by_date(start: date, end: date) -> list[dict]:
    with get_session() as db:
        return repo.get_revenue_by_date(db, start, end)


def get_revenue_by_method(start: date, end: date) -> list[dict]:
    with get_session() as db:
        return repo.get_revenue_by_method(db, start, end)


def get_outstanding_by_group() -> list[dict]:
    with get_session() as db:
        return repo.get_outstanding_by_group(db)


def get_top_debtors(limit: int = 10) -> list[dict]:
    with get_session() as db:
        return repo.get_top_debtors(db, limit)


def get_group_roster(group_id: int, level_number: int) -> list[dict]:
    with get_session() as db:
        return repo.get_group_roster(db, group_id, level_number)


def get_attendance_heatmap(group_id: int, level_number: int) -> list[dict]:
    with get_session() as db:
        return repo.get_attendance_heatmap(db, group_id, level_number)


def get_competition_fee_summary() -> list[dict]:
    with get_session() as db:
        return repo.get_competition_fee_summary(db)
