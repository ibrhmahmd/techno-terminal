from datetime import date, timedelta
import logging
from typing import List

from sqlalchemy import text
from sqlmodel import Session, select, func

from app.modules.notifications.schemas.report_dto import (
    DailyReportAggregateDTO,
    InstructorSummaryItem,
    PaymentDetailItem,
    PaymentTypeGroup,
    SessionDetailItem,
)
from app.modules.academics.models.session_models import CourseSession
from app.modules.attendance.models.attendance_models import Attendance
from app.modules.crm.models.student_models import Student
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.finance.models.payment import Payment
from app.modules.finance.models.receipt import Receipt

logger = logging.getLogger(__name__)


class ReportsRepository:
    """Report aggregate queries — single source of truth for daily report metrics."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_daily_aggregates(self, target_date: date) -> DailyReportAggregateDTO:
        revenue = self._fetch_revenue(target_date)
        sessions_held = self._fetch_sessions_held(target_date)
        present_count, absent_count, cancelled_count = self._fetch_attendance(target_date)
        new_enrollments = self._fetch_new_enrollments(target_date)
        payments, payment_count, payment_methods, payment_details, payments_by_type = self._fetch_payments(target_date)
        instructors_list = self._fetch_instructors(target_date)
        unpaid_count = self._fetch_unpaid_count()
        session_details = self._fetch_session_details(target_date)
        instructor_summary = self._fetch_instructor_summary(target_date)

        total = present_count + absent_count + cancelled_count
        attendance_rate = present_count / total if total > 0 else 0.0

        return DailyReportAggregateDTO(
            date=target_date.isoformat(),
            total_revenue=revenue,
            new_enrollments=new_enrollments,
            sessions_held=sessions_held,
            absent_count=absent_count,
            present_count=present_count,
            attendance_rate=attendance_rate,
            payment_count=payment_count,
            payment_methods=payment_methods,
            payment_details=payment_details,
            instructors_list=instructors_list,
            unpaid_count=unpaid_count,
            session_details=session_details,
            payments_by_type=payments_by_type,
            instructor_summary=instructor_summary,
        )

    def _fetch_revenue(self, target_date: date) -> float:
        try:
            stmt = text("""
                SELECT COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
                     - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS net_revenue
                FROM receipts r
                JOIN payments p ON p.receipt_id = r.id
                WHERE DATE(COALESCE(r.paid_at, r.created_at)) = :target_date
            """)
            result = self._session.execute(stmt, {"target_date": target_date}).scalar()
            return float(result or 0.0)
        except Exception as e:
            logger.warning(f"Could not fetch daily revenue: {e}")
            return 0.0

    def _fetch_sessions_held(self, target_date: date) -> int:
        stmt = select(func.count()).select_from(CourseSession).where(
            CourseSession.session_date == target_date,
            CourseSession.status == "completed",
        )
        return self._session.exec(stmt).one() or 0

    def _fetch_attendance(self, target_date: date) -> tuple[int, int, int]:
        session_ids_subq = select(CourseSession.id).where(
            CourseSession.session_date == target_date
        )
        present = self._session.exec(
            select(func.count()).select_from(Attendance).where(
                Attendance.session_id.in_(session_ids_subq),
                Attendance.status == "present",
            )
        ).one() or 0
        absent = self._session.exec(
            select(func.count()).select_from(Attendance).where(
                Attendance.session_id.in_(session_ids_subq),
                Attendance.status == "absent",
            )
        ).one() or 0
        cancelled = self._session.exec(
            select(func.count()).select_from(Attendance).where(
                Attendance.session_id.in_(session_ids_subq),
                Attendance.status == "cancelled",
            )
        ).one() or 0
        return present, absent, cancelled

    def _fetch_new_enrollments(self, target_date: date) -> int:
        stmt = select(func.count()).select_from(Enrollment).where(
            func.coalesce(Enrollment.enrolled_at, Enrollment.created_at) >= target_date,
            func.coalesce(Enrollment.enrolled_at, Enrollment.created_at) < target_date + timedelta(days=1),
        )
        return self._session.exec(stmt).one() or 0

    def _fetch_payments(self, target_date: date) -> tuple[
        List[Payment], int, dict[str, int], List[PaymentDetailItem], List[PaymentTypeGroup]
    ]:
        payment_stmt = (
            select(Payment)
            .join(Receipt, Payment.receipt_id == Receipt.id)
            .where(
                func.coalesce(Receipt.paid_at, Receipt.created_at) >= target_date,
                func.coalesce(Receipt.paid_at, Receipt.created_at) < target_date + timedelta(days=1),
                Payment.deleted_at.is_(None),
            )
        )
        payments = list(self._session.exec(payment_stmt).all())
        payment_count = len(payments)
        payment_methods: dict[str, int] = {}
        payment_details: list[PaymentDetailItem] = []

        for payment in payments:
            method = str(payment.payment_type) if payment.payment_type else "unknown"
            payment_methods[method] = payment_methods.get(method, 0) + 1

            try:
                student = self._session.get(Student, payment.student_id)
                student_name = student.full_name if student else "Unknown"
                group_name = "N/A"
                if payment.enrollment_id:
                    enrollment = self._session.get(Enrollment, payment.enrollment_id)
                    if enrollment and enrollment.group_id:
                        from app.modules.academics.models.group_models import Group
                        group = self._session.get(Group, enrollment.group_id)
                        group_name = group.name if group else "N/A"

                payment_details.append(PaymentDetailItem(
                    student_name=student_name,
                    group_name=group_name,
                    amount=float(payment.amount),
                    payment_type=method,
                ))
            except Exception as e:
                logger.warning(f"Could not fetch payment details for payment {payment.id}: {e}")

        payment_details.sort(key=lambda x: x.amount, reverse=True)

        from itertools import groupby
        payments_by_type: list[PaymentTypeGroup] = []
        payment_details_by_type = sorted(payment_details, key=lambda x: x.payment_type)
        for ptype, group in groupby(payment_details_by_type, key=lambda x: x.payment_type):
            items = list(group)
            payments_by_type.append(PaymentTypeGroup(
                payment_type=ptype,
                subtotal=sum(item.amount for item in items),
                count=len(items),
                items=items,
            ))

        return payments, payment_count, payment_methods, payment_details, payments_by_type

    def _fetch_instructors(self, target_date: date) -> list[str]:
        try:
            instructor_stmt = text("""
                SELECT DISTINCT e.full_name
                FROM sessions s
                JOIN employees e ON s.actual_instructor_id = e.id
                WHERE s.session_date = :target_date
            """)
            result = self._session.execute(instructor_stmt, {"target_date": target_date})
            return [row[0] for row in result]
        except Exception as e:
            logger.warning(f"Could not fetch instructors: {e}")
            return []

    def _fetch_session_details(self, target_date: date) -> list[SessionDetailItem]:
        try:
            sessions = self._session.exec(
                select(CourseSession).where(
                    CourseSession.session_date == target_date,
                    CourseSession.status == "completed",
                )
            ).all()

            details = []
            for session_obj in sessions:
                instructor_name = ""
                if session_obj.actual_instructor_id:
                    from app.modules.hr.models.employee_models import Employee
                    emp = self._session.get(Employee, session_obj.actual_instructor_id)
                    instructor_name = emp.full_name if emp else "Unknown"

                session_time = f"{session_obj.start_time.strftime('%H:%M')} - {session_obj.end_time.strftime('%H:%M')}"

                attendance_records = self._session.exec(
                    select(Attendance).where(Attendance.session_id == session_obj.id)
                ).all()

                present_count = sum(1 for a in attendance_records if a.status == "present")
                absent_count = sum(1 for a in attendance_records if a.status == "absent")
                cancelled_count = sum(1 for a in attendance_records if a.status == "cancelled")

                present_names = []
                absent_names = []
                for a in attendance_records:
                    student = self._session.get(Student, a.student_id)
                    name = student.full_name if student else "Unknown"
                    if a.status == "present":
                        present_names.append(name)
                    elif a.status == "absent":
                        absent_names.append(name)

                details.append(SessionDetailItem(
                    instructor_name=instructor_name,
                    session_time=session_time,
                    present_count=present_count,
                    absent_count=absent_count,
                    cancelled_count=cancelled_count,
                    student_names_present=", ".join(present_names),
                    student_names_absent=", ".join(absent_names),
                ))

            return details
        except Exception as e:
            logger.warning(f"Could not fetch session details: {e}")
            return []

    def _fetch_instructor_summary(self, target_date: date) -> list[InstructorSummaryItem]:
        try:
            stmt = text("""
                SELECT e.full_name, COUNT(s.id) AS session_count
                FROM sessions s
                JOIN employees e ON s.actual_instructor_id = e.id
                WHERE s.session_date = :target_date
                GROUP BY e.full_name
                ORDER BY session_count DESC
            """)
            result = self._session.execute(stmt, {"target_date": target_date})
            return [
                InstructorSummaryItem(instructor_name=row[0], session_count=row[1])
                for row in result
            ]
        except Exception as e:
            logger.warning(f"Could not fetch instructor summary: {e}")
            return []

    def _fetch_unpaid_count(self) -> int:
        try:
            unpaid_stmt = text("""
                SELECT COUNT(DISTINCT e.id)
                FROM enrollments e
                LEFT JOIN (
                    SELECT enrollment_id, COALESCE(SUM(amount), 0) as total_paid
                    FROM payments
                    WHERE deleted_at IS NULL
                    GROUP BY enrollment_id
                ) p ON e.id = p.enrollment_id
                WHERE e.status = 'active'
                AND (e.amount_due - COALESCE(e.discount_applied, 0) - COALESCE(p.total_paid, 0)) > 0
            """)
            result = self._session.exec(unpaid_stmt).one()
            return int(result[0]) if result else 0
        except Exception as e:
            logger.warning(f"Could not fetch unpaid count: {e}")
            return 0
