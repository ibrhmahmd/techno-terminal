from datetime import date, timedelta
from decimal import Decimal
from itertools import groupby
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
    PeriodReportAggregateDTO,
    SessionDetailItem,
    TomorrowPreviewDTO,
    TopDebtorItem,
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

    def fetch_cumulative_unpaid(self, as_of_date: date) -> list[UnpaidAttendeeItem]:
        """All active enrollments with 3+ attended sessions and a negative balance."""
        try:
            stmt = text("""
                SELECT DISTINCT
                    st.full_name AS student_name,
                    COALESCE(g.name, '') AS group_name,
                    COALESCE(co.name, '') AS course_name,
                    -vb.balance AS amount_owed
                FROM enrollments e
                JOIN students st ON e.student_id = st.id
                JOIN groups g ON e.group_id = g.id
                LEFT JOIN courses co ON g.course_id = co.id
                JOIN v_enrollment_balance vb ON vb.enrollment_id = e.id
                JOIN attendance a ON a.student_id = st.id
                JOIN sessions s ON a.session_id = s.id
                    AND s.group_id = e.group_id
                    AND s.level_number = e.level_number
                    AND s.session_date <= :as_of_date
                WHERE e.status = 'active'
                  AND a.status = 'present'
                  AND vb.balance < 0
                GROUP BY st.id, st.full_name, g.name, co.name, vb.balance, e.id
                HAVING COUNT(a.id) >= 3
                ORDER BY amount_owed DESC
            """)
            rows = self._session.execute(stmt, {"as_of_date": as_of_date}).all()
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
            logger.warning(f"Could not fetch cumulative unpaid attendees: {e}")
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

    # ── Period (weekly / monthly) aggregates ──────────────────────────────────

    def populate_detailed_arrays(self, dto: PeriodReportAggregateDTO, start_date: date, end_date: date) -> None:
        session = self._session

        # 1. Session Details
        try:
            session_stmt = text("""
                SELECT s.id, s.start_time, s.end_time, s.session_date,
                       COALESCE(e.full_name, '') AS instructor_name
                FROM sessions s
                LEFT JOIN employees e ON s.actual_instructor_id = e.id
                WHERE s.session_date BETWEEN :start AND :end
                  AND s.status = 'completed'
                ORDER BY s.session_date DESC, s.id
            """)
            sessions = session.execute(session_stmt, {"start": start_date, "end": end_date}).all()

            session_ids = [row[0] for row in sessions]
            if session_ids:
                attend_stmt = text("""
                    SELECT a.session_id, a.status,
                           COALESCE(st.full_name, 'Unknown') AS student_name
                    FROM attendance a
                    LEFT JOIN students st ON a.student_id = st.id
                    WHERE a.session_id = ANY(:session_ids)
                    ORDER BY a.session_id
                """)
                attend_rows = session.execute(attend_stmt, {"session_ids": session_ids}).all()

                attendance_map = {sid: {"present": [], "absent": []} for sid in session_ids}
                counts_map = {sid: {"present": 0, "absent": 0, "cancelled": 0} for sid in session_ids}

                for attend_sid, status, student_name in attend_rows:
                    if status in ("present", "absent"):
                        attendance_map[attend_sid][status].append(student_name)
                    if status in counts_map.get(attend_sid, {}):
                        counts_map[attend_sid][status] += 1
                    elif status == "cancelled" and attend_sid in counts_map:
                        counts_map[attend_sid]["cancelled"] += 1

                for row in sessions:
                    sid, start_time, end_time, session_date, instructor_name = row
                    session_time_str = f"{session_date.strftime('%Y-%m-%d')} {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                    c = counts_map.get(sid, {"present": 0, "absent": 0, "cancelled": 0})
                    a = attendance_map.get(sid, {"present": [], "absent": []})
                    dto.session_details.append(SessionDetailItem(
                        instructor_name=instructor_name,
                        session_time=session_time_str,
                        present_count=c["present"],
                        absent_count=c["absent"],
                        cancelled_count=c["cancelled"],
                        student_names_present=", ".join(a["present"]),
                        student_names_absent=", ".join(a["absent"]),
                    ))
        except Exception as e:
            logger.warning(f"Could not populate session arrays: {e}")

        # 2. Payments
        try:
            payment_stmt = text("""
                SELECT p.amount, p.payment_type,
                       COALESCE(st.full_name, 'Unknown') AS student_name,
                       COALESCE(g.name, 'N/A') AS group_name
                FROM payments p
                JOIN receipts r ON p.receipt_id = r.id
                LEFT JOIN students st ON p.student_id = st.id
                LEFT JOIN enrollments e ON p.enrollment_id = e.id
                LEFT JOIN groups g ON e.group_id = g.id
                WHERE DATE(COALESCE(r.paid_at, r.created_at)) BETWEEN :start AND :end
                  AND p.deleted_at IS NULL
            """)
            pay_rows = session.execute(payment_stmt, {"start": start_date, "end": end_date}).all()
            for row in pay_rows:
                amount, ptype, student_name, group_name = row
                method = str(ptype) if ptype else "unknown"
                dto.payment_details.append(PaymentDetailItem(
                    student_name=student_name,
                    group_name=group_name,
                    amount=float(amount),
                    payment_type=method,
                ))

            dto.payment_details.sort(key=lambda x: x.amount, reverse=True)
            payment_details_by_type = sorted(dto.payment_details, key=lambda x: x.payment_type)
            for ptype, group_iter in groupby(payment_details_by_type, key=lambda x: x.payment_type):
                items = list(group_iter)
                dto.payments_by_type.append(PaymentTypeGroup(
                    payment_type=ptype,
                    subtotal=sum(item.amount for item in items),
                    count=len(items),
                    items=items,
                ))
        except Exception as e:
            logger.warning(f"Could not populate payment arrays: {e}")

        # 3. Debtors
        try:
            debtor_stmt = text("""
                SELECT s.full_name AS student_name,
                       g.name AS group_name,
                       COALESCE(-v.balance, 0) AS amount_owed
                FROM v_enrollment_balance v
                JOIN students s ON v.student_id = s.id
                JOIN groups g ON v.group_id = g.id
                WHERE v.balance < 0
            """)
            debt_rows = session.execute(debtor_stmt).all()
            for r in debt_rows:
                dto.cumulative_unpaid_debtors.append(UnpaidAttendeeItem(
                    student_name=r.student_name,
                    group_name=r.group_name,
                    amount_owed=float(r.amount_owed),
                    payment_status="unpaid"
                ))
            
            top_debtor_stmt = text("""
                SELECT s.full_name AS student_name,
                       COALESCE(SUM(-v.balance), 0) AS amount_owed
                FROM v_enrollment_balance v
                JOIN students s ON v.student_id = s.id
                WHERE v.balance < 0
                GROUP BY s.id, s.full_name
                ORDER BY amount_owed DESC
                LIMIT 5
            """)
            top_rows = session.execute(top_debtor_stmt).all()
            for tr in top_rows:
                dto.top_debtors.append(TopDebtorItem(
                    student_name=tr.student_name,
                    amount_owed=float(tr.amount_owed)
                ))
        except Exception as e:
            logger.warning(f"Could not populate debtor arrays: {e}")

    def get_weekly_aggregates(self, week_start: date, week_end: date) -> PeriodReportAggregateDTO:
        """Fetch enriched weekly metrics."""
        
        dto = PeriodReportAggregateDTO()
        
        try:
            session = self._session
            # 1. Total Revenue (exclude voided payments)
            rev_res = session.execute(text("""
                SELECT COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0) 
                     - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS total_revenue
                FROM receipts r
                JOIN payments p ON p.receipt_id = r.id
                WHERE DATE(COALESCE(r.paid_at, r.created_at)) BETWEEN :start AND :end
                  AND p.deleted_at IS NULL
            """), {"start": week_start, "end": week_end}).one_or_none()
            dto.total_revenue = Decimal(str(rev_res.total_revenue)) if rev_res and rev_res.total_revenue is not None else Decimal("0.00")

            # 2. New Enrollments
            enr_res = session.execute(text("""
                SELECT COUNT(*) AS count
                FROM enrollments 
                WHERE DATE(COALESCE(enrolled_at, created_at)) BETWEEN :start AND :end
            """), {"start": week_start, "end": week_end}).one_or_none()
            dto.new_enrollments = enr_res.count if enr_res else 0

            # 2b. New Students (distinct students whose first enrollment falls in period)
            stud_res = session.execute(text("""
                SELECT COUNT(DISTINCT student_id) AS new_students
                FROM enrollments 
                WHERE DATE(COALESCE(enrolled_at, created_at)) BETWEEN :start AND :end 
                  AND student_id NOT IN (
                      SELECT student_id FROM enrollments WHERE DATE(COALESCE(enrolled_at, created_at)) < :start
                  )
            """), {"start": week_start, "end": week_end}).one_or_none()
            dto.new_students = stud_res.new_students if stud_res else 0

            # 2c. Dropped Enrollments
            drop_res = session.execute(text("""
                SELECT COUNT(*) AS dropped_enrollments
                FROM enrollments 
                WHERE status = 'dropped' AND DATE(updated_at) BETWEEN :start AND :end
            """), {"start": week_start, "end": week_end}).one_or_none()
            dto.dropped_enrollments = drop_res.dropped_enrollments if drop_res else 0

            # 3. Total Sessions
            sess_res = session.execute(text("""
                SELECT COUNT(*) AS count
                FROM sessions 
                WHERE session_date BETWEEN :start AND :end AND status = 'completed'
            """), {"start": week_start, "end": week_end}).one_or_none()
            dto.total_sessions = sess_res.count if sess_res else 0

            # 4. Debt (Snapshot)
            debt_res = session.execute(text("""
                SELECT COUNT(DISTINCT student_id) AS debtor_count,
                       COALESCE(SUM(-balance), 0) AS total_debt
                FROM v_enrollment_balance WHERE balance < 0
            """)).one_or_none()
            if debt_res:
                dto.debtor_count = debt_res.debtor_count
                dto.total_debt = float(debt_res.total_debt)

            # 5. Top Groups (exclude voided payments)
            top_groups_rows = session.execute(text("""
                SELECT g.name AS group_name, COALESCE(SUM(p.amount), 0) AS revenue
                FROM groups g
                JOIN enrollments e ON e.group_id = g.id
                JOIN payments p ON p.enrollment_id = e.id
                JOIN receipts r ON p.receipt_id = r.id
                WHERE DATE(COALESCE(r.paid_at, r.created_at)) BETWEEN :start AND :end
                  AND p.transaction_type IN ('payment','charge')
                  AND p.deleted_at IS NULL
                GROUP BY g.id, g.name
                ORDER BY revenue DESC LIMIT 5
            """), {"start": week_start, "end": week_end}).all()
                
            if top_groups_rows:
                tr = "".join(f'<tr><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;">{r.group_name}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:right;">{float(r.revenue):,.2f}</td></tr>' for r in top_groups_rows)
                dto.top_groups = f'<table style="width:100%;font-size:12px;border-collapse:collapse;"><tr><th style="padding:4px 8px;text-align:left;background:#f8f9ff;">Group</th><th style="padding:4px 8px;text-align:right;background:#f8f9ff;">Revenue (EGP)</th></tr>{tr}</table>'
            else:
                dto.top_groups = "<p style='font-size:12px;color:#64748b;'>No revenue generated this week.</p>"

            # 6. Revenue by course (exclude voided payments)
            course_rows = session.execute(text("""
                SELECT c.name AS course_name, COALESCE(SUM(p.amount), 0) AS revenue
                FROM courses c
                JOIN groups g ON g.course_id = c.id
                JOIN enrollments e ON e.group_id = g.id
                JOIN payments p ON p.enrollment_id = e.id
                JOIN receipts r ON p.receipt_id = r.id
                WHERE DATE(COALESCE(r.paid_at, r.created_at)) BETWEEN :start AND :end
                  AND p.transaction_type IN ('payment','charge')
                  AND p.deleted_at IS NULL
                GROUP BY c.id, c.name
                ORDER BY revenue DESC
            """), {"start": week_start, "end": week_end}).all()
                
            if course_rows:
                tr = "".join(f'<tr><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;">{r.course_name}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:right;">{float(r.revenue):,.2f}</td></tr>' for r in course_rows)
                dto.revenue_by_course = f'<table style="width:100%;font-size:12px;border-collapse:collapse;"><tr><th style="padding:4px 8px;text-align:left;background:#f8f9ff;">Course</th><th style="padding:4px 8px;text-align:right;background:#f8f9ff;">Revenue (EGP)</th></tr>{tr}</table>'
            else:
                dto.revenue_by_course = "<p style='font-size:12px;color:#64748b;'>No revenue generated this week.</p>"

            # 7. Attendance Rate (Period Bounded)
            att_res = session.execute(text("""
                SELECT 
                    COALESCE(COUNT(*) FILTER (WHERE a.status = 'present'), 0) AS present_count,
                    COUNT(a.id) AS total_count
                FROM attendance a
                JOIN sessions s ON a.session_id = s.id
                WHERE s.session_date BETWEEN :start AND :end AND s.status = 'completed'
            """), {"start": week_start, "end": week_end}).one_or_none()
            if att_res and att_res.total_count > 0:
                dto.attendance_rate = (att_res.present_count / att_res.total_count) * 100
            else:
                dto.attendance_rate = 0.0

            # 8. Active Students (Period Bounded - enrolled before end and not dropped before start, or just snapshot)
            # We will use snapshot as it represents the active base
            act_res = session.execute(text("SELECT COUNT(*) AS active_students FROM enrollments WHERE status = 'active'")).one_or_none()
            dto.active_students = act_res.active_students if act_res else 0

            # 9. Top Instructors (NEW)
            inst_rows = session.execute(text("""
                SELECT e.full_name AS instructor_name, COUNT(s.id) AS session_count
                FROM employees e
                JOIN sessions s ON s.actual_instructor_id = e.id
                WHERE s.session_date BETWEEN :start AND :end AND s.status = 'completed'
                GROUP BY e.id, e.full_name
                ORDER BY session_count DESC LIMIT 5
            """), {"start": week_start, "end": week_end}).all()
            if inst_rows:
                tr = "".join(f'<tr><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;">{r.instructor_name}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:right;">{r.session_count}</td></tr>' for r in inst_rows)
                dto.top_instructors = f'<table style="width:100%;font-size:12px;border-collapse:collapse;"><tr><th style="padding:4px 8px;text-align:left;background:#f8f9ff;">Instructor</th><th style="padding:4px 8px;text-align:right;background:#f8f9ff;">Sessions Held</th></tr>{tr}</table>'
            else:
                dto.top_instructors = "<p style='font-size:12px;color:#64748b;'>No sessions held this week.</p>"

            # 10. Populate Detailed Arrays
            self.populate_detailed_arrays(dto, week_start, week_end)

        except Exception as e:
            logger.warning(f"Could not fetch weekly aggregates: {e}")

        return dto

    def get_monthly_aggregates(self, month_start: date, month_end: date) -> PeriodReportAggregateDTO:
        """Fetch enriched monthly metrics."""
        
        dto = PeriodReportAggregateDTO()

        try:
            session = self._session
            # 1. Total Revenue (exclude voided payments)
            rev_res = session.execute(text("""
                SELECT COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0) 
                     - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS total_revenue
                FROM receipts r
                JOIN payments p ON p.receipt_id = r.id
                WHERE DATE(COALESCE(r.paid_at, r.created_at)) BETWEEN :start AND :end
                  AND p.deleted_at IS NULL
            """), {"start": month_start, "end": month_end}).one_or_none()
            dto.total_revenue = Decimal(str(rev_res.total_revenue)) if rev_res and rev_res.total_revenue is not None else Decimal("0.00")

            # 2. Enrollments (New & Dropped)
            enr_res = session.execute(text("""
                SELECT 
                    COUNT(*) FILTER (WHERE DATE(COALESCE(enrolled_at, created_at)) BETWEEN :start AND :end) AS new_enrollments,
                    COUNT(*) FILTER (WHERE status = 'dropped' AND DATE(updated_at) BETWEEN :start AND :end) AS dropped_enrollments
                FROM enrollments 
            """), {"start": month_start, "end": month_end}).one_or_none()
            if enr_res:
                dto.new_enrollments = enr_res.new_enrollments
                dto.dropped_enrollments = enr_res.dropped_enrollments

            # 3. Total Sessions
            sess_res = session.execute(text("""
                SELECT COUNT(*) AS count
                FROM sessions 
                WHERE session_date BETWEEN :start AND :end AND status = 'completed'
            """), {"start": month_start, "end": month_end}).one_or_none()
            dto.total_sessions = sess_res.count if sess_res else 0

            # 4. Debt (Snapshot)
            debt_res = session.execute(text("""
                SELECT COUNT(DISTINCT student_id) AS debtor_count,
                       COALESCE(SUM(-balance), 0) AS total_debt
                FROM v_enrollment_balance WHERE balance < 0
            """)).one_or_none()
            if debt_res:
                dto.debtor_count = debt_res.debtor_count
                dto.total_debt = float(debt_res.total_debt)

            # 5. New Students
            stud_res = session.execute(text("""
                SELECT COUNT(DISTINCT student_id) AS new_students
                FROM enrollments 
                WHERE DATE(COALESCE(enrolled_at, created_at)) BETWEEN :start AND :end 
                  AND student_id NOT IN (
                      SELECT student_id FROM enrollments WHERE DATE(COALESCE(enrolled_at, created_at)) < :start
                  )
            """), {"start": month_start, "end": month_end}).one_or_none()
            dto.new_students = stud_res.new_students if stud_res else 0

            # 6. Active Students Snapshot
            act_res = session.execute(text("SELECT COUNT(*) AS active_students FROM enrollments WHERE status = 'active'")).one_or_none()
            dto.active_students = act_res.active_students if act_res else 0

            # Top courses
            course_rows = session.execute(text("""
                SELECT c.name AS course_name, COUNT(e.id) AS enrollment_count
                FROM courses c
                JOIN groups g ON g.course_id = c.id
                JOIN enrollments e ON e.group_id = g.id
                WHERE DATE(COALESCE(e.enrolled_at, e.created_at)) BETWEEN :start AND :end
                GROUP BY c.id, c.name
                ORDER BY enrollment_count DESC LIMIT 5
            """), {"start": month_start, "end": month_end}).all()
                
            if course_rows:
                tr = "".join(f'<tr><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;">{r.course_name}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:right;">{r.enrollment_count}</td></tr>' for r in course_rows)
                dto.top_courses = f'<table style="width:100%;font-size:12px;border-collapse:collapse;"><tr><th style="padding:4px 8px;text-align:left;background:#f8f9ff;">Course</th><th style="padding:4px 8px;text-align:right;background:#f8f9ff;">New Enrollments</th></tr>{tr}</table>'
            else:
                dto.top_courses = "<p style='font-size:12px;color:#64748b;'>No new enrollments this month.</p>"

            # Revenue breakdown by type (exclude voided payments)
            type_rows = session.execute(text("""
                SELECT p.payment_type, COALESCE(SUM(p.amount), 0) AS revenue
                FROM payments p
                JOIN receipts r ON p.receipt_id = r.id
                WHERE DATE(COALESCE(r.paid_at, r.created_at)) BETWEEN :start AND :end
                  AND p.transaction_type IN ('payment','charge')
                  AND p.deleted_at IS NULL
                GROUP BY p.payment_type
                ORDER BY revenue DESC
            """), {"start": month_start, "end": month_end}).all()
                
            if type_rows:
                tr = "".join(f'<tr><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-transform:capitalize;">{r.payment_type}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:right;">{r.revenue:,.2f}</td></tr>' for r in type_rows)
                dto.revenue_breakdown = f'<table style="width:100%;font-size:12px;border-collapse:collapse;"><tr><th style="padding:4px 8px;text-align:left;background:#f8f9ff;">Type</th><th style="padding:4px 8px;text-align:right;background:#f8f9ff;">Revenue (EGP)</th></tr>{tr}</table>'
            else:
                dto.revenue_breakdown = "<p style='font-size:12px;color:#64748b;'>No revenue generated this month.</p>"

            # 7. Attendance Rate (Period Bounded)
            att_res = session.execute(text("""
                SELECT 
                    COALESCE(COUNT(*) FILTER (WHERE a.status = 'present'), 0) AS present_count,
                    COUNT(a.id) AS total_count
                FROM attendance a
                JOIN sessions s ON a.session_id = s.id
                WHERE s.session_date BETWEEN :start AND :end AND s.status = 'completed'
            """), {"start": month_start, "end": month_end}).one_or_none()
            if att_res and att_res.total_count > 0:
                dto.attendance_rate = (att_res.present_count / att_res.total_count) * 100
            else:
                dto.attendance_rate = 0.0

            # 8. Top Instructors (NEW)
            inst_rows = session.execute(text("""
                SELECT e.full_name AS instructor_name, COUNT(s.id) AS session_count, COUNT(DISTINCT a.student_id) as students_taught
                FROM employees e
                JOIN sessions s ON s.actual_instructor_id = e.id
                LEFT JOIN attendance a ON a.session_id = s.id AND a.status = 'present'
                WHERE s.session_date BETWEEN :start AND :end AND s.status = 'completed'
                GROUP BY e.id, e.full_name
                ORDER BY session_count DESC LIMIT 5
            """), {"start": month_start, "end": month_end}).all()
            if inst_rows:
                tr = "".join(f'<tr><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;">{r.instructor_name}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:center;">{r.session_count}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:right;">{r.students_taught}</td></tr>' for r in inst_rows)
                dto.top_instructors = f'<table style="width:100%;font-size:12px;border-collapse:collapse;"><tr><th style="padding:4px 8px;text-align:left;background:#f8f9ff;">Instructor</th><th style="padding:4px 8px;text-align:center;background:#f8f9ff;">Sessions Held</th><th style="padding:4px 8px;text-align:right;background:#f8f9ff;">Students Taught</th></tr>{tr}</table>'
            else:
                dto.top_instructors = "<p style='font-size:12px;color:#64748b;'>No sessions held this month.</p>"

            # 9. Course Performance Matrix (NEW)
            cpm_rows = session.execute(text("""
                SELECT 
                    c.name AS course_name,
                    (SELECT COALESCE(SUM(p2.amount), 0)
                     FROM payments p2
                     JOIN enrollments e2 ON p2.enrollment_id = e2.id
                     JOIN groups g2 ON e2.group_id = g2.id
                     JOIN receipts r2 ON p2.receipt_id = r2.id
                     WHERE g2.course_id = c.id 
                       AND p2.transaction_type IN ('payment','charge')
                       AND DATE(COALESCE(r2.paid_at, r2.created_at)) BETWEEN :start AND :end
                    ) AS revenue,
                    (SELECT COUNT(*) FROM enrollments e3 
                     JOIN groups g3 ON e3.group_id = g3.id
                     WHERE g3.course_id = c.id 
                       AND DATE(COALESCE(e3.enrolled_at, e3.created_at)) BETWEEN :start AND :end
                    ) AS enrollments_count,
                    (SELECT COUNT(*) FROM enrollments e4 
                     JOIN groups g4 ON e4.group_id = g4.id
                     WHERE g4.course_id = c.id 
                       AND e4.status = 'dropped' 
                       AND DATE(e4.updated_at) BETWEEN :start AND :end
                    ) AS drops_count
                FROM courses c
                ORDER BY revenue DESC, enrollments_count DESC
                LIMIT 10
            """), {"start": month_start, "end": month_end}).all()
                
            # Filter out courses with 0 revenue, 0 new enrollments and 0 drops so we only show active ones
            cpm_rows = [r for r in cpm_rows if r.revenue > 0 or r.enrollments_count > 0 or r.drops_count > 0]
                
            if cpm_rows:
                tr = "".join(f'<tr><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;">{r.course_name}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:right;">{float(r.revenue):,.2f}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:center;">{r.enrollments_count}</td><td style="padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:center;">{r.drops_count}</td></tr>' for r in cpm_rows)
                dto.course_performance_matrix = f'<table style="width:100%;font-size:12px;border-collapse:collapse;"><tr><th style="padding:4px 8px;text-align:left;background:#f8f9ff;">Course</th><th style="padding:4px 8px;text-align:right;background:#f8f9ff;">Rev (EGP)</th><th style="padding:4px 8px;text-align:center;background:#f8f9ff;">New</th><th style="padding:4px 8px;text-align:center;background:#f8f9ff;">Drops</th></tr>{tr}</table>'
            else:
                dto.course_performance_matrix = "<p style='font-size:12px;color:#64748b;'>No course activity this month.</p>"

            # 10. Populate Detailed Arrays
            self.populate_detailed_arrays(dto, month_start, month_end)

        except Exception as e:
            logger.warning(f"Could not fetch monthly aggregates: {e}")

        return dto
