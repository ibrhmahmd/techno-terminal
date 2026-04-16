from typing import Optional, Sequence, Tuple
from sqlmodel import Session, select, delete, func
from sqlalchemy import or_
import json
from datetime import datetime
from decimal import Decimal

from app.modules.crm.interfaces import IStudentRepository, StudentSummaryDTO, StudentBalanceSummaryDTO, AttendanceStatsDTO
from app.api.schemas.crm.student_details import SiblingInfo
from app.modules.crm.models import Student, StudentStatus, StudentParent, Parent
from app.shared.audit_utils import apply_create_audit

class StudentRepository(IStudentRepository):
    """
    Repository for student data access.
    Session is injected via constructor — never acquired internally.
    Never calls session.commit(). Only flush().
    """
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, student: Student) -> Student:
        self._session.add(student)
        self._session.flush()
        return student

    def get_by_id(self, student_id: int) -> Optional[Student]:
        return self._session.get(Student, student_id)

    def get_all(self, skip: int, limit: int) -> list[Student]:
        stmt = select(Student).offset(skip).limit(limit)
        return list(self._session.exec(stmt).all())

    def search(self, query: str) -> list[Student]:
        term = f"%{query}%"
        return list(self._session.exec(
            select(Student).where(
                or_(Student.full_name.ilike(term), Student.phone.ilike(term))
            ).limit(50)
        ).all())

    def count(self, active_only: bool = True) -> int:
        stmt = select(func.count()).select_from(Student)
        if active_only:
            stmt = stmt.where(Student.is_active.is_(True))
        return self._session.exec(stmt).one()

    def count_by_status(self, status: StudentStatus) -> int:
        return self._session.exec(
            select(func.count()).select_from(Student).where(Student.status == status)
        ).one()

    def update_status(self, student_id: int, new_status: StudentStatus,
                      user_id: Optional[int], notes: Optional[str]) -> Optional[Student]:
        student = self._session.get(Student, student_id)
        if not student:
            return None
        
        old_status = student.status
        def _get_status_value(st):
            if st is None:
                return None
            return st.value if hasattr(st, 'value') else str(st)
            
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "changed_by": user_id,
            "old_status": _get_status_value(old_status),
            "new_status": _get_status_value(new_status),
            "notes": notes
        }
        history = student.status_history or []
        if isinstance(history, str):
            history = json.loads(history) if history else []
        history.append(audit_entry)
        student.status_history = history
        student.status = new_status
        student.is_active = new_status in [StudentStatus.ACTIVE, StudentStatus.WAITING]
        if notes:
            student.waiting_notes = notes
        
        self._session.add(student)
        self._session.flush()
        return student

    def set_waiting_priority(self, student_id: int, priority: int) -> Optional[Student]:
        student = self._session.get(Student, student_id)
        if not student or student.status != StudentStatus.WAITING:
            return None
        student.waiting_priority = priority
        self._session.add(student)
        self._session.flush()
        return student

    def delete(self, student_id: int) -> bool:
        """
        Deletes ONLY student + cascade via ORM (StudentParent).
        Cross-domain cleanup (attendance, payments) delegated to StudentService.
        """
        student = self._session.get(Student, student_id)
        if not student:
            return False
        self._session.delete(student)
        self._session.flush()
        return True

    def get_with_parent(self, student_id: int) -> Optional[tuple[Student, Optional[Parent]]]:
        student = self._session.get(Student, student_id)
        if not student:
            return None
        primary_link = self._session.exec(
            select(StudentParent)
            .where(StudentParent.student_id == student_id)
            .where(StudentParent.is_primary.is_(True))
        ).first()
        parent = None
        if primary_link and primary_link.parent_id:
            parent = self._session.get(Parent, primary_link.parent_id)
        return (student, parent)

    def get_all_enriched(self, include_inactive: bool = False) -> list[StudentSummaryDTO]:
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from app.modules.academics.models.group_models import Group
        stmt = (
            select(Student, Group)
            .outerjoin(Enrollment, (Enrollment.student_id == Student.id) & (Enrollment.status == 'active'))
            .outerjoin(Group, Enrollment.group_id == Group.id)
        )
        if not include_inactive:
            stmt = stmt.where(Student.is_active.is_(True))
            
        results = self._session.exec(stmt).all()
        # Ensure distinct by student ID
        student_map = {}
        for student, group in results:
            if student.id not in student_map:
                student_map[student.id] = StudentSummaryDTO(
                    id=student.id,
                    full_name=student.full_name,
                    phone=student.phone,
                    gender=student.gender,
                    status=str(student.status) if student.status else ("active" if student.is_active else "inactive"),
                    is_active=student.is_active,
                    current_group_id=group.id if group else None,
                    current_group_name=group.group_name if group else None,
                    date_of_birth=student.date_of_birth.date() if hasattr(student.date_of_birth, 'date') else student.date_of_birth
                )
        return list(student_map.values())

    def get_student_balance_summary(self, student_id: int) -> StudentBalanceSummaryDTO:
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from app.modules.finance import Payment
        enrollments = self._session.exec(
            select(Enrollment)
            .where(Enrollment.student_id == student_id)
            .where(Enrollment.status.in_(['active', 'completed']))
        ).all()
        total_due = Decimal('0.00')
        total_discounts = Decimal('0.00')
        total_paid = Decimal('0.00')
        unpaid_count = 0
        for enrollment in enrollments:
            due = Decimal(str(enrollment.amount_due or 0))
            discount = Decimal(str(enrollment.discount_applied or 0))
            result = self._session.exec(
                select(func.sum(Payment.amount))
                .where(Payment.enrollment_id == enrollment.id)
                .where(Payment.transaction_type == 'payment')
            ).first()
            paid = Decimal(str(result[0] or 0)) if result and result[0] else Decimal('0.00')
            total_due += due
            total_discounts += discount
            total_paid += paid
            if (due - discount - paid) > 0:
                unpaid_count += 1
        net_balance = float(total_paid - (total_due - total_discounts))
        return StudentBalanceSummaryDTO(
            total_due=float(total_due),
            total_discounts=float(total_discounts),
            total_paid=float(total_paid),
            net_balance=net_balance,
            enrollment_count=len(enrollments),
            unpaid_enrollments=unpaid_count
        )

    def get_student_siblings_with_details(self, student_id: int) -> list[SiblingInfo]:
        from app.modules.enrollments.models.enrollment_models import Enrollment
        parent_links = self._session.exec(
            select(StudentParent).where(StudentParent.student_id == student_id)
        ).all()
        if not parent_links:
            return []
        parent_ids = [link.parent_id for link in parent_links]
        sibling_links = self._session.exec(
            select(StudentParent, Student, Parent)
            .join(Student, StudentParent.student_id == Student.id)
            .join(Parent, StudentParent.parent_id == Parent.id)
            .where(StudentParent.parent_id.in_(parent_ids))
            .where(StudentParent.student_id != student_id)
        ).all()
        seen_ids = set()
        siblings_data = []
        for link, sibling, parent in sibling_links:
            if sibling.id in seen_ids:
                continue
            seen_ids.add(sibling.id)
            age = None
            if sibling.date_of_birth:
                today = datetime.now()
                dob = sibling.date_of_birth
                age = today.year - dob.year
                if (today.month, today.day) < (dob.month, dob.day):
                    age -= 1
            enrollment_count = self._session.exec(
                select(func.count(Enrollment.id))
                .where(Enrollment.student_id == sibling.id)
                .where(Enrollment.status == 'active')
            ).one()
            siblings_data.append(SiblingInfo(
                student_id=sibling.id,
                full_name=sibling.full_name,
                age=age,
                gender=sibling.gender,
                status=str(sibling.status) if sibling.status else "active",
                parent_id=parent.id,
                parent_name=parent.full_name,
                enrollments_count=enrollment_count,
            ))
        return siblings_data

    def get_attendance_stats(self, student_id: int) -> AttendanceStatsDTO:
        from app.modules.attendance.models.attendance_models import Attendance
        from app.modules.enrollments.models.enrollment_models import Enrollment
        counts = dict(self._session.exec(
            select(Attendance.status, func.count(Attendance.id))
            .join(Enrollment, Attendance.enrollment_id == Enrollment.id)
            .where(Enrollment.student_id == student_id)
            .group_by(Attendance.status)
        ).all())
        total = sum((v for k, v in counts.items() if v))
        attended = counts.get("present", 0)
        absent = counts.get("absent", 0)
        cancelled = counts.get("cancelled", 0)
        denom = total - cancelled
        return AttendanceStatsDTO(
            total_sessions=total,
            attended=attended,
            absent=absent,
            cancelled=cancelled,
            attendance_rate=round(attended / denom, 3) if denom > 0 else 0.0
        )

    def link_parent(
        self,
        student_id: int,
        parent_id: int,
        relationship: Optional[str] = None,
        is_primary: bool = False,
    ) -> "StudentParent":
        """Link a student to a parent."""
        from app.modules.crm.models.student_models import StudentParent
        link = StudentParent(
            student_id=student_id,
            parent_id=parent_id,
            relationship=relationship,
            is_primary=is_primary,
        )
        self._session.add(link)
        self._session.flush()
        return link

    def get_student_parents(self, student_id: int) -> list["StudentParent"]:
        """Get all parent links for a student."""
        from app.modules.crm.models.student_models import StudentParent
        stmt = select(StudentParent).where(StudentParent.student_id == student_id)
        return list(self._session.exec(stmt).all())

    def log_status_change(
        self,
        student_id: int,
        previous_status: Optional[str],
        new_status: str,
        changed_by_user_id: Optional[int] = None,
        notes: Optional[str] = None,
        action: Optional[str] = None,
        new_priority: Optional[int] = None,
    ) -> None:
        """Log a status change in the history table."""
        # For now, just log to a simple table or skip if table doesn't exist
        # This will be implemented when the migration is applied
        # The status_history table was created in migration 021
        try:
            from sqlalchemy import text
            query = text("""
                INSERT INTO student_status_history 
                (student_id, previous_status, new_status, changed_by_user_id, notes, created_at)
                VALUES (:student_id, :previous_status, :new_status, :changed_by_user_id, :notes, NOW())
            """)
            self._session.exec(
                query,
                params={
                    "student_id": student_id,
                    "previous_status": previous_status,
                    "new_status": new_status,
                    "changed_by_user_id": changed_by_user_id,
                    "notes": notes,
                }
            )
        except Exception:
            # If the table doesn't exist yet, silently skip
            pass

    def get_by_status(self, status: StudentStatus) -> list[Student]:
        """Get all students with a specific status."""
        stmt = select(Student).where(Student.status == status)
        return list(self._session.exec(stmt).all())

    def get_waiting_list(self) -> list[Student]:
        """Get all students on the waiting list, ordered by priority."""
        stmt = (
            select(Student)
            .where(Student.status == StudentStatus.WAITING)
            .order_by(Student.waiting_priority.nulls_last())
        )
        return list(self._session.exec(stmt).all())

    def get_active_enrollment_with_details(
        self, student_id: int
    ) -> Optional[Tuple[int, str, int, str, int, Optional[str], int]]:
        """
        Get active enrollment with joined group, course, and instructor details.
        Returns: (enrollment_id, group_name, group_id, course_name, course_id, instructor_name, level_number) or None.
        """
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from app.modules.academics.models.group_models import Group
        from app.modules.academics.models.course_models import Course
        from app.modules.auth.models.user_models import User

        stmt = (
            select(
                Enrollment.id,
                Group.name,
                Group.id,
                Course.name,
                Course.id,
                User.full_name,
                Enrollment.level_number,
            )
            .join(Group, Enrollment.group_id == Group.id)
            .join(Course, Group.course_id == Course.id)
            .outerjoin(User, Group.instructor_id == User.id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.status == "active",
            )
            .order_by(Enrollment.created_at.desc())
            .limit(1)
        )
        result = self._session.exec(stmt).first()
        return result
        return list(self._session.exec(stmt).all())