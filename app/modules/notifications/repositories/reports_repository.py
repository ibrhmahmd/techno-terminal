from datetime import date, timedelta
import logging
from typing import List

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select, func

from app.modules.notifications.schemas.report_dto import (
    DailyReportAggregateDTO,
    InstructorSummaryItem,
    PaymentDetailItem,
    PaymentTypeGroup,
    SessionDetailItem,
    TomorrowPreviewDTO,
    UnpaidAttendeeItem,
)
from app.modules.academics.models.session_models import CourseSession
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.finance.models.payment import Payment

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
        except SQLAlchemyError as e:
            logger.warning(f"Could not fetch daily revenue: {e}")
            return 0.0

    def _fetch_sessions_held(self, target_date: date) -> int:
        stmt = select(func.count()).select_from(CourseSession).where(
            CourseSession.session_date == target_date,
            CourseSession.status == "completed",
        )
        return self._session.exec(stmt).one() or 0

    def _fetch_attendance(self, target_date: date) -> tuple[int, int, int]:
        stmt = text("""
            SELECT
                COALESCE(COUNT(*) FILTER (WHERE a.status = 'present'), 0) AS present_count,
                COALESCE(COUNT(*) FILTER (WHERE a.status = 'absent'), 0) AS absent_count,
                COALESCE(COUNT(*) FILTER (WHERE a.status = 'cancelled'), 0) AS cancelled_count
            FROM attendance a
            JOIN sessions s ON a.session_id = s.id
            WHERE s.session_date = :target_date
        """)
        result = self._session.execute(stmt, {"target_date": target_date}).one()
        return result.present_count, result.absent_count, result.cancelled_count

    def _fetch_new_enrollments(self, target_date: date) -> int:
        stmt = select(func.count()).select_from(Enrollment).where(
            func.date(func.coalesce(Enrollment.enrolled_at, Enrollment.created_at)) >= target_date,
            func.date(func.coalesce(Enrollment.enrolled_at, Enrollment.created_at)) < target_date + timedelta(days=1),
        )
        return self._session.exec(stmt).one() or 0

    def _fetch_payments(self, target_date: date) -> tuple[
        List[Payment], int, dict[str, int], List[PaymentDetailItem], List[PaymentTypeGroup]
    ]:
        stmt = text("""
            SELECT p.amount, p.payment_type,
                   COALESCE(s.full_name, 'Unknown') AS student_name,
                   COALESCE(g.name, 'N/A') AS group_name
            FROM payments p
            JOIN receipts r ON p.receipt_id = r.id
            LEFT JOIN students s ON p.student_id = s.id
            LEFT JOIN enrollments e ON p.enrollment_id = e.id
            LEFT JOIN groups g ON e.group_id = g.id
            WHERE DATE(COALESCE(r.paid_at, r.created_at)) = :target_date
              AND p.deleted_at IS NULL
        """)
        rows = self._session.execute(stmt, {"target_date": target_date}).all()
        payment_count = len(rows)
        payment_methods: dict[str, int] = {}
        payment_details: list[PaymentDetailItem] = []

        for row in rows:
            amount, ptype, student_name, group_name = row
            method = str(ptype) if ptype else "unknown"
            payment_methods[method] = payment_methods.get(method, 0) + 1
            payment_details.append(PaymentDetailItem(
                student_name=student_name,
                group_name=group_name,
                amount=float(amount),
                payment_type=method,
            ))

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

        return [], payment_count, payment_methods, payment_details, payments_by_type

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
        except SQLAlchemyError as e:
            logger.warning(f"Could not fetch instructors: {e}")
            return []

    def _fetch_session_details(self, target_date: date) -> list[SessionDetailItem]:
        try:
            session_stmt = text("""
                SELECT s.id, s.start_time, s.end_time,
                       COALESCE(e.full_name, '') AS instructor_name
                FROM sessions s
                LEFT JOIN employees e ON s.actual_instructor_id = e.id
                WHERE s.session_date = :target_date
                  AND s.status = 'completed'
                ORDER BY s.id
            """)
            sessions = self._session.execute(session_stmt, {"target_date": target_date}).all()

            session_ids = [row[0] for row in sessions]
            if not session_ids:
                return []

            attend_stmt = text("""
                SELECT a.session_id, a.status,
                       COALESCE(st.full_name, 'Unknown') AS student_name
                FROM attendance a
                LEFT JOIN students st ON a.student_id = st.id
                WHERE a.session_id = ANY(:session_ids)
                ORDER BY a.session_id
            """)
            attend_rows = self._session.execute(attend_stmt, {"session_ids": session_ids}).all()

            attendance_map: dict[int, dict[str, list[str]]] = {}
            counts_map: dict[int, dict[str, int]] = {}
            for sid in session_ids:
                attendance_map[sid] = {"present": [], "absent": []}
                counts_map[sid] = {"present": 0, "absent": 0, "cancelled": 0}

            for attend_sid, status, student_name in attend_rows:
                if status in ("present", "absent"):
                    attendance_map[attend_sid][status].append(student_name)
                if status in counts_map.get(attend_sid, {}):
                    counts_map[attend_sid][status] += 1
                elif status == "cancelled" and attend_sid in counts_map:
                    counts_map[attend_sid]["cancelled"] += 1

            details = []
            for row in sessions:
                sid, start_time, end_time, instructor_name = row
                session_time = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                c = counts_map.get(sid, {"present": 0, "absent": 0, "cancelled": 0})
                a = attendance_map.get(sid, {"present": [], "absent": []})
                details.append(SessionDetailItem(
                    instructor_name=instructor_name,
                    session_time=session_time,
                    present_count=c["present"],
                    absent_count=c["absent"],
                    cancelled_count=c["cancelled"],
                    student_names_present=", ".join(a["present"]),
                    student_names_absent=", ".join(a["absent"]),
                ))

            return details
        except SQLAlchemyError as e:
            logger.warning(f"Could not fetch session details: {e}")
            return []

    def _fetch_instructor_summary(self, target_date: date) -> list[InstructorSummaryItem]:
        try:
            stmt = text("""
                SELECT e.full_name, COUNT(s.id) AS session_count
                FROM sessions s
                JOIN employees e ON s.actual_instructor_id = e.id
                WHERE s.session_date = :target_date
                  AND s.status = 'completed'
                GROUP BY e.full_name
                ORDER BY session_count DESC
            """)
            result = self._session.execute(stmt, {"target_date": target_date})
            return [
                InstructorSummaryItem(instructor_name=row[0], session_count=row[1])
                for row in result
            ]
        except SQLAlchemyError as e:
            logger.warning(f"Could not fetch instructor summary: {e}")
            return []

    def fetch_session3_unpaid(self, target_date: date) -> list[UnpaidAttendeeItem]:
        """Students enrolled in groups that had session 3 today, with debt."""
        try:
            stmt = text("""
                SELECT DISTINCT
                    st.id AS student_id,
                    st.full_name AS student_name,
                    COALESCE(g.name, '') AS group_name,
                    SUM(CASE WHEN vb.balance < 0 THEN -vb.balance ELSE 0 END)
                        OVER (PARTITION BY st.id) AS amount_owed
                FROM sessions s
                JOIN groups g ON s.group_id = g.id
                JOIN enrollments e ON e.group_id = s.group_id AND e.level_number = s.level_number AND e.status = 'active'
                JOIN students st ON e.student_id = st.id
                JOIN v_enrollment_balance vb ON vb.student_id = st.id
                WHERE s.session_date = :target_date
                  AND s.session_number = 3
                  AND s.status IN ('completed', 'scheduled')
                  AND vb.balance < 0
                ORDER BY amount_owed DESC
            """)
            rows = self._session.execute(stmt, {"target_date": target_date}).all()
            return [
                UnpaidAttendeeItem(
                    student_name=row.student_name,
                    group_name=row.group_name,
                    amount_owed=float(row.amount_owed),
                    payment_status="not_paid",
                )
                for row in rows
            ]
        except SQLAlchemyError as e:
            logger.warning(f"Could not fetch session-3 unpaid attendees: {e}")
            return []

    def fetch_tomorrow_preview(self, today: date) -> TomorrowPreviewDTO:
        """Sessions scheduled for tomorrow with unpaid attendee alerts."""
        tomorrow = today + timedelta(days=1)
        try:
            # Count sessions for tomorrow
            session_stmt = text("""
                SELECT COUNT(DISTINCT s.id) AS session_count,
                       COUNT(DISTINCT e.student_id) AS expected_student_count
                FROM sessions s
                JOIN enrollments e ON e.group_id = s.group_id AND e.level_number = s.level_number
                WHERE s.session_date = :tomorrow
                  AND s.status = 'scheduled'
            """)
            count_result = self._session.execute(session_stmt, {"tomorrow": tomorrow}).one()
            session_count = count_result.session_count or 0
            expected_count = count_result.expected_student_count or 0

            if session_count == 0:
                return TomorrowPreviewDTO(
                    session_count=0, expected_student_count=0,
                    unpaid_attendees=[], has_sessions=False
                )

            # Students with debt who are expected tomorrow
            unpaid_stmt = text("""
                SELECT DISTINCT
                    st.full_name AS student_name,
                    COALESCE(g.name, 'N/A') AS group_name,
                    SUM(CASE WHEN vb.balance < 0 THEN -vb.balance ELSE 0 END)
                        OVER (PARTITION BY st.id) AS amount_owed,
                    CASE WHEN vb.balance < 0 THEN 'not_paid' ELSE 'paid' END AS payment_status
                FROM sessions s
                JOIN enrollments e ON e.group_id = s.group_id AND e.level_number = s.level_number
                JOIN students st ON e.student_id = st.id
                JOIN v_enrollment_balance vb ON vb.student_id = st.id
                LEFT JOIN groups g ON e.group_id = g.id
                WHERE s.session_date = :tomorrow
                  AND s.status = 'scheduled'
                  AND vb.balance < 0
                ORDER BY amount_owed DESC
            """)
            unpaid_rows = self._session.execute(unpaid_stmt, {"tomorrow": tomorrow}).all()
            unpaid_attendees = [
                UnpaidAttendeeItem(
                    student_name=row.student_name,
                    group_name=row.group_name,
                    amount_owed=float(row.amount_owed),
                    payment_status=str(row.payment_status),
                )
                for row in unpaid_rows
            ]

            return TomorrowPreviewDTO(
                session_count=session_count,
                expected_student_count=expected_count,
                unpaid_attendees=unpaid_attendees,
                has_sessions=True,
            )
        except SQLAlchemyError as e:
            logger.warning(f"Could not fetch tomorrow preview: {e}")
            return TomorrowPreviewDTO(
                session_count=0, expected_student_count=0,
                unpaid_attendees=[], has_sessions=False
            )

